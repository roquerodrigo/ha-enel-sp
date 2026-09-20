"""Cliente da área do cliente da Enel São Paulo."""

from __future__ import annotations

import asyncio
import html
import json
import re
import socket
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, cast
from uuid import uuid4

import aiohttp
from yarl import URL

from .const import (
    ACCOUNTS_BASE_URL,
    LOGGER,
    PORTAL_BASE_URL,
    PORTAL_SITE,
    SAML_SERVICE_PROVIDER,
)
from .data import (
    EnelSpAccount,
    EnelSpBill,
    EnelSpHttpResponse,
    EnelSpInstallation,
    EnelSpTariffFlag,
)
from .exceptions import (
    EnelSpApiClientAuthenticationError,
    EnelSpApiClientCommunicationError,
    EnelSpApiClientError,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .data import (
        EnelSpCurrentUser,
        EnelSpCurrentUserResponse,
        EnelSpEnvironment,
        EnelSpHistoryRow,
        EnelSpInstallationRow,
        EnelSpServiceResponse,
        JsonObject,
        JsonValue,
    )


_URL_QUERY_STRING = re.compile(r"\?\S*")
_INPUT_TAG = re.compile(r"<input[^>]*>", re.IGNORECASE)
_INPUT_NAME = re.compile(r"""\bname=(["'])(.+?)\1""", re.IGNORECASE)
_INPUT_VALUE = re.compile(r"""\bvalue=(["'])(.*?)\1""", re.IGNORECASE)
_PAGE_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_SITE_CONFIG_OBJECT = re.compile(r"\{.*\}", re.DOTALL)
_BILLING_PERIOD = re.compile(r"^(\d{4})/(\d{2})$")
_SERVICE_DATE = re.compile(r"^(\d{4})(\d{2})(\d{2})$")

_REQUEST_TIMEOUT_SECONDS = 60
_HTTP_UNAUTHORIZED = 401
_HTTP_SESSION_EXPIRED = 498
_SAML_RESPONSE_FIELD = "SAMLResponse"
_AUTH_FAILURE_QUERY = "authFailure"
_CHANNEL = "ZINT"
_CLIENT_IP_PLACEHOLDER = "123"
_WEB_SYSTEM = "WEB"
_BROWSER_HEADERS: Mapping[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Transforma os erros de sessão do portal em erros de autenticação."""
    if response.status in (_HTTP_UNAUTHORIZED, _HTTP_SESSION_EXPIRED):
        msg = "The portal session is not authenticated"
        raise EnelSpApiClientAuthenticationError(msg)
    response.raise_for_status()


def _sanitized_error_text(exception: BaseException) -> str:
    """
    Remove as query strings de URL do texto de erro do upstream antes do log.

    As bibliotecas de cliente HTTP citam a URL da requisição nas mensagens de exceção, e
    o Home Assistant grava no log a mensagem de um ``UpdateFailed`` a cada atualização
    que falha. O provedor de identidade carrega a sessão de login na query string,
    portanto ela é ocultada na saída.
    """
    return _URL_QUERY_STRING.sub("?<redacted>", str(exception))


def _parse_json_object(text: str, what: str) -> JsonObject:
    """Interpreta um objeto JSON, nomeando o payload no erro quando não é um."""
    try:
        parsed = json.loads(text)
    except ValueError as exception:
        msg = f"Failed to parse {what}: {exception}"
        raise EnelSpApiClientError(msg) from exception
    if not isinstance(parsed, dict):
        msg = f"Failed to parse {what}: unexpected shape"
        raise EnelSpApiClientError(msg)
    return cast("JsonObject", parsed)


def _parse_hidden_inputs(page: str) -> dict[str, str]:
    """Coleta os pares ``name``/``value`` de todos os inputs de uma página HTML."""
    inputs: dict[str, str] = {}
    for tag in _INPUT_TAG.findall(page):
        name = _INPUT_NAME.search(tag)
        value = _INPUT_VALUE.search(tag)
        if name and value:
            inputs[html.unescape(name.group(2))] = html.unescape(value.group(2))
    return inputs


def _describe_page(response: EnelSpHttpResponse) -> str:
    """
    Resume uma página inesperada para uma mensagem de erro sem vazar segredos.

    O provedor de identidade carrega a sessão de login na query string e a assertion no
    corpo, portanto só são reportados o host, o caminho, o status, o título da página e
    os nomes dos campos do formulário.
    """
    url = URL(response.url)
    title = _PAGE_TITLE.search(response.text)
    fields = ", ".join(sorted(_parse_hidden_inputs(response.text))) or "none"
    return (
        f"{url.host}{url.path} (HTTP {response.status}, title "
        f"{html.unescape(title.group(1)).strip()!r}, fields: {fields})"
        if title
        else f"{url.host}{url.path} (HTTP {response.status}, fields: {fields})"
    )


def _has_saml_response(page: str) -> bool:
    """Indica se uma página do provedor de identidade traz um formulário SAML."""
    return _SAML_RESPONSE_FIELD in _parse_hidden_inputs(page)


def _service_timestamp() -> str:
    """Retorna o timestamp da requisição no formato que o front-end do portal envia."""
    return (
        datetime.now(tz=UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    )


def _number(value: float | str | None) -> float:
    """Lê um campo numérico do serviço que pode vir como texto ou estar ausente."""
    if value in (None, ""):
        return 0.0
    return float(value)


def _parse_service_date(raw: str | None) -> date | None:
    """Lê uma data ``YYYYMMDD`` do serviço; brancos e zeros significam sem data."""
    match = _SERVICE_DATE.match(raw or "")
    if match is None or match.group(1) == "0000":
        return None
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _installation_from_row(row: EnelSpInstallationRow) -> EnelSpInstallation:
    """Monta uma instalação a partir de uma linha de ``ET_INST``."""
    return EnelSpInstallation(
        number=row.get("ANLAGE", ""),
        nickname=row.get("APELIDO", "").strip(),
        address=row.get("ENDERECO", "").strip(),
        partner=row.get("PARTNER", ""),
        contract=row.get("VERTRAG", ""),
        contract_account=row.get("VKONT", ""),
        voltage_level=row.get("NIVEL_TENSAO", ""),
        meter_serial=row.get("SERIE", "").lstrip("0"),
        move_in=row.get("EINZDAT", ""),
        move_out=row.get("AUSZDAT", ""),
    )


def _account_from_current_user(user: EnelSpCurrentUser) -> EnelSpAccount:
    """Monta a conta a partir do cadastro do usuário atual do portal."""
    installations = tuple(
        _installation_from_row(row)
        for row in user.get("ET_INST") or []
        if row.get("ANLAGE")
    )
    name = " ".join(
        part for part in (user.get("E_NOME", ""), user.get("E_SOBRENOME", "")) if part
    )
    return EnelSpAccount(
        enel_id=user.get("enel_id", ""),
        name=name,
        tariff_flag=EnelSpTariffFlag.from_portal(user.get("E_BANDEIRA", "")),
        installations=installations,
    )


def _bill_from_row(row: EnelSpHistoryRow) -> EnelSpBill | None:
    """Monta uma conta de uma linha de ``ET_HISTORICO``, ou None sem período."""
    match = _BILLING_PERIOD.match(row.get("BILLING_PERIOD", ""))
    if match is None:
        return None
    return EnelSpBill(
        year=int(match.group(1)),
        month=int(match.group(2)),
        amount=round(_number(row.get("VALOR_TOTAL")), 2),
        consumption=_number(row.get("VALOR_CONSUMO")),
        days=int(_number(row.get("VALOR_DIAS"))),
        daily_consumption=round(_number(row.get("VALOR_CONSUMO_DIA")), 3),
        due_date=_parse_service_date(row.get("VENCIMENTO")),
        status_text=row.get("STATUS", "").strip(),
        meter_reading=_number(row.get("VALOR_LEIT_PER1")),
        icms=round(_number(row.get("VALOR_ICMS_FAT")), 2),
        taxes=round(_number(row.get("VALOR_IMPO")), 2),
        interest=round(_number(row.get("VALOR_JUROS")), 2),
    )


def _bills_from_rows(rows: list[EnelSpHistoryRow]) -> tuple[EnelSpBill, ...]:
    """Transforma as linhas do histórico em contas, da mais antiga à mais nova."""
    bills = [bill for row in rows if (bill := _bill_from_row(row)) is not None]
    return tuple(sorted(bills, key=lambda bill: (bill.year, bill.month)))


class EnelSpApiClient:
    """
    Cliente da área do cliente da Enel São Paulo.

    O login passa pelo provedor de identidade SAML da Enel: o provedor inicia uma sessão
    de login, as credenciais são enviadas ao endpoint ``commonauth`` e a assertion SAML
    que ele devolve é entregue ao portal, que então responde ``currentuser`` com o
    cadastro do cliente e o bearer token que os serviços apoiados no SAP esperam no
    cabeçalho ``enel-jwt-token``. Qualquer 401 posterior significa que uma dessas
    sessões expirou, e os métodos públicos fazem login de novo uma vez antes de
    desistir.
    """

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Inicializa."""
        self._username = username
        self._password = password
        self._session = session
        self._session_id = str(uuid4())
        self._token: str | None = None
        self._services_url: str | None = None

    async def async_login(self) -> EnelSpAccount:
        """Faz login pelo provedor de identidade e carrega o cadastro do cliente."""
        landing = await self._request(
            f"{ACCOUNTS_BASE_URL}/samlsso?spEntityID={SAML_SERVICE_PROVIDER}"
        )
        saml_page = (
            landing.text
            if _has_saml_response(landing.text)
            else await self._async_authenticate(landing)
        )
        await self._async_deliver_saml_response(saml_page)
        try:
            account = await self._async_load_current_user()
        except EnelSpApiClientAuthenticationError as exception:
            msg = "Failed to log in: the portal did not accept the SAML session"
            raise EnelSpApiClientError(msg) from exception
        LOGGER.debug("Logged in to the Enel portal")
        return account

    async def async_get_account(self) -> EnelSpAccount:
        """Retorna o cadastro do cliente, fazendo login quando a sessão expirou."""
        if self._token is None:
            return await self.async_login()
        try:
            return await self._async_load_current_user()
        except EnelSpApiClientAuthenticationError:
            LOGGER.debug("Portal session expired; logging in again")
            return await self.async_login()

    async def async_get_bills(
        self, installation: EnelSpInstallation
    ) -> tuple[EnelSpBill, ...]:
        """Retorna os meses faturados de uma instalação, do mais antigo ao mais novo."""
        if self._token is None:
            await self.async_login()
        try:
            return await self._async_fetch_bills(installation)
        except EnelSpApiClientAuthenticationError:
            LOGGER.debug("Services token expired; logging in again")
            await self.async_login()
            return await self._async_fetch_bills(installation)

    async def _async_authenticate(self, landing: EnelSpHttpResponse) -> str:
        """Envia as credenciais ao provedor de identidade e retorna a resposta dele."""
        session_data_key = URL(landing.url).query.get("sessionDataKey")
        if not session_data_key:
            msg = (
                "Failed to log in: the identity provider did not start a session, "
                f"got {_describe_page(landing)}"
            )
            raise EnelSpApiClientError(msg)
        reply = await self._request(
            f"{ACCOUNTS_BASE_URL}/commonauth",
            data={
                "username": self._username,
                "password": self._password,
                "sessionDataKey": session_data_key,
                "tocommonauth": "true",
            },
        )
        if _has_saml_response(reply.text):
            return reply.text
        if _AUTH_FAILURE_QUERY in URL(reply.url).query or "login" in reply.url:
            msg = "Failed to log in: the identity provider rejected the credentials"
            raise EnelSpApiClientAuthenticationError(msg)
        msg = (
            "Failed to log in: no SAML response in the identity provider reply, "
            f"got {_describe_page(reply)}"
        )
        raise EnelSpApiClientError(msg)

    async def _async_deliver_saml_response(self, page: str) -> None:
        """
        Envia a assertion SAML ao portal para que ele abra a própria sessão.

        O formulário do provedor de identidade aponta para ``login.html``, que recusa o
        POST com 403; quem consome a assertion e grava os cookies da sessão é o
        ``saml_login`` do site, então o destino do formulário é ignorado.
        """
        await self._request(
            f"{PORTAL_BASE_URL}/{PORTAL_SITE}/saml_login",
            data=_parse_hidden_inputs(page),
        )

    async def _async_load_current_user(self) -> EnelSpAccount:
        """Lê do portal o cadastro do cliente e o token dos serviços."""
        reply = await self._request(
            f"{PORTAL_BASE_URL}/bin/enel-br/{PORTAL_SITE}/currentuser",
            json={},
            headers={"sid": self._session_id},
        )
        parsed = cast(
            "EnelSpCurrentUserResponse",
            _parse_json_object(reply.text, "the current user"),
        )
        user = parsed.get("currentUser")
        if not user or not user.get("access_token"):
            msg = "Failed to load the current user: the portal has no session"
            raise EnelSpApiClientAuthenticationError(msg)
        self._token = user["access_token"]
        return _account_from_current_user(user)

    async def _async_fetch_bills(
        self, installation: EnelSpInstallation
    ) -> tuple[EnelSpBill, ...]:
        """Chama o serviço de histórico de consumo para uma instalação."""
        body: JsonObject = {
            "Header": {
                "Funcionalidad": "usagehistory",
                "CodSistema": _WEB_SYSTEM,
                "SistemaOrigen": _WEB_SYSTEM,
                "FechaHora": _service_timestamp(),
            },
            "Body": {
                "I_CANAL": _CHANNEL,
                "I_COD_SERV": "AF",
                "I_SSO_GUID": "GUID",
                "I_PARTNER": installation.partner,
                "I_VERTRAG": installation.contract,
                "I_VKONT": installation.contract_account,
            },
        }
        reply = await self._request(
            f"{await self._async_services_url()}/usagehistory",
            json=body,
            headers={
                "enel-jwt-token": self._token or "",
                "SID": self._session_id,
                "CLIENT_IP": _CLIENT_IP_PLACEHOLDER,
                "Accept": "application/json, text/plain, */*",
            },
        )
        response = cast(
            "EnelSpServiceResponse",
            _parse_json_object(reply.text, "the usage history"),
        )
        service_body = response.get("Body") or {}
        if service_body.get("E_RESULT"):
            reason = service_body.get("E_MSG") or service_body.get(
                "DescripcionResultado", ""
            )
            msg = f"Failed to fetch the usage history: {reason}"
            raise EnelSpApiClientError(msg)
        return _bills_from_rows(service_body.get("ET_HISTORICO") or [])

    async def _async_services_url(self) -> str:
        """Resolve o gateway dos serviços SAP pela configuração do site do portal."""
        if self._services_url is None:
            reply = await self._request(
                f"{PORTAL_BASE_URL}/bin/enel-br/{PORTAL_SITE}/environment"
            )
            match = _SITE_CONFIG_OBJECT.search(reply.text)
            environment = cast(
                "EnelSpEnvironment",
                _parse_json_object(
                    match.group(0) if match else "", "the site configuration"
                ),
            )
            services_url = environment.get("portalSPUri")
            if not services_url:
                msg = "Failed to read the site configuration: no services gateway"
                raise EnelSpApiClientError(msg)
            self._services_url = services_url.rstrip("/")
        return self._services_url

    async def _request(
        self,
        url: str,
        *,
        data: Mapping[str, str] | None = None,
        json: Mapping[str, JsonValue] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> EnelSpHttpResponse:
        """Executa um POST quando há corpo, senão um GET, e guarda o resultado."""
        method = "get" if data is None and json is None else "post"
        try:
            async with asyncio.timeout(_REQUEST_TIMEOUT_SECONDS):
                response = await self._session.request(
                    method=method,
                    url=url,
                    data=data,
                    json=json,
                    headers={**_BROWSER_HEADERS, **(headers or {})},
                )
                _verify_response_or_raise(response)
                return EnelSpHttpResponse(
                    status=response.status,
                    url=str(response.url),
                    text=await response.text(),
                )

        except TimeoutError as exception:
            detail = _sanitized_error_text(exception)
            msg = f"Timeout error fetching information - {detail}"
            raise EnelSpApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            detail = _sanitized_error_text(exception)
            msg = f"Error fetching information - {detail}"
            raise EnelSpApiClientCommunicationError(msg) from exception
        except EnelSpApiClientError:
            raise
        except Exception as exception:
            msg = f"Failed to process the API response: {exception}"
            raise EnelSpApiClientError(msg) from exception
