from __future__ import annotations

import json
import socket
from datetime import date
from typing import NamedTuple
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.enel_sp.api import (
    EnelSpApiClient,
    _sanitized_error_text,
)
from custom_components.enel_sp.const import (
    ACCOUNTS_BASE_URL,
    PORTAL_BASE_URL,
    SAML_SERVICE_PROVIDER,
)
from custom_components.enel_sp.data import EnelSpBillStatus, EnelSpTariffFlag
from custom_components.enel_sp.exceptions import (
    EnelSpApiClientAuthenticationError,
    EnelSpApiClientCommunicationError,
    EnelSpApiClientError,
)

from .conftest import ACTIVE_INSTALLATION

SAMLSSO_URL = f"{ACCOUNTS_BASE_URL}/samlsso?spEntityID={SAML_SERVICE_PROVIDER}"
COMMONAUTH_URL = f"{ACCOUNTS_BASE_URL}/commonauth"
LOGIN_PAGE_URL = f"{PORTAL_BASE_URL}/pt-saopaulo/login.html?sessionDataKey=key-123"
FAILED_LOGIN_URL = (
    f"{LOGIN_PAGE_URL}&authFailure=true&authFailureMsg=login.fail.message"
)
ACS_URL = f"{PORTAL_BASE_URL}/pt-saopaulo/saml_login"
SAML_FORM_ACTION = f"{PORTAL_BASE_URL}/pt-saopaulo/login.html"
CURRENT_USER_URL = f"{PORTAL_BASE_URL}/bin/enel-br/pt-saopaulo/currentuser"
ENVIRONMENT_URL = f"{PORTAL_BASE_URL}/bin/enel-br/pt-saopaulo/environment"
SERVICES_URL = "https://exp-portalsp-pro.example.cloudhub.io/api"
USAGE_HISTORY_URL = f"{SERVICES_URL}/usagehistory"
WEB_SERVICES_URL = "https://exp-portalweb-pro.example.cloudhub.io/api"
COMPOSITION_URL = f"{WEB_SERVICES_URL}/validatecomposicaofatura"

LOGIN_SHELL = "<html><body><app-root></app-root></body></html>"
SAML_PAGE = (
    f'<html><body><form method="post" action="{SAML_FORM_ACTION}">'
    '<input type="hidden" name="SAMLResponse" '
    'value="PHNhbWwycD5hc3NlcnRpb248L3NhbWwycD4=" />'
    '<input type="hidden" name="RelayState" value="ENEL_SP_WEB_BRA&amp;x" />'
    "</form></body></html>"
)
WSO2_SAML_PAGE = (
    "<html><body><p>You are now redirected back to the portal.</p>"
    f"<form method='post' action='{SAML_FORM_ACTION}'><p>"
    "<input type='hidden' name='SAMLResponse' "
    "value='PHNhbWwycD5hc3NlcnRpb248L3NhbWwycD4='/>"
    "<input type='hidden' name='RelayState' value='ENEL_SP_WEB_BRA'/>"
    "<button type='submit'>POST</button></p></form>"
    "<script type='text/javascript'>document.forms[0].submit();</script>"
    "</body></html>"
)
ENVIRONMENT_PAGE = (
    'var siteConfig = {"appRoot":"/content/x.html","portalSPUri":"'
    + SERVICES_URL
    + '/","portalWEBUri":"'
    + WEB_SERVICES_URL
    + '","production":true};'
)
CURRENT_USER = {
    "enel_id": "6f1a2b3c-0000-4000-8000-000000000000",
    "access_token": "abc.def.ghi",
    "E_NOME": "Maria",
    "E_SOBRENOME": "Silva",
    "E_BANDEIRA": "AMARELA",
    "ET_INST": [
        {
            "ANLAGE": "0123456789",
            "APELIDO": "Casa ",
            "ENDERECO": "R Exemplo, 100",
            "PARTNER": "0012345678",
            "VERTRAG": "0098765432",
            "VKONT": "123456789012",
            "NIVEL_TENSAO": "BT",
            "SERIE": "000000000012345678",
            "EINZDAT": "20250801",
            "AUSZDAT": "99991231",
        },
        {
            "ANLAGE": "0100000001",
            "APELIDO": "",
            "ENDERECO": "Av Antiga, 1",
            "PARTNER": "0012345678",
            "VERTRAG": "0011111111",
            "VKONT": "123456789099",
            "NIVEL_TENSAO": "BT",
            "SERIE": "",
            "EINZDAT": "20190101",
            "AUSZDAT": "20211231",
        },
        {"APELIDO": "no installation number"},
    ],
}


def _history_row(period: str, amount: float, consumption: float, reading: float):
    return {
        "BILLING_PERIOD": period,
        "VALOR_TOTAL": amount,
        "VALOR_CONSUMO": consumption,
        "VALOR_DIAS": 30,
        "VALOR_CONSUMO_DIA": consumption / 30,
        "VENCIMENTO": "20260915",
        "STATUS": "Paga",
        "VALOR_LEIT_PER1": reading,
        "VALOR_ICMS": "18",
        "VALOR_ICMS_FAT": 50.25,
        "VALOR_DIAS_FAT": 236.81,
        "VALOR_IMPO": 20.15,
        "VALOR_JUROS": "0.68",
    }


USAGE_HISTORY = {
    "Header": {"IdPeticion": "x"},
    "Body": {
        "E_RESULT": "",
        "E_MSG": "",
        "ET_HISTORICO": [
            _history_row("2026/08", 290.70, 300, 4600),
            _history_row("2026/06", 350.10, 350, 3900),
            _history_row("2026/07", 420.80, 400, 4300),
            {"BILLING_PERIOD": "", "VALOR_TOTAL": 1},
        ],
    },
}


BILL_COMPOSITION = {
    "Header": {"IdPeticion": "x"},
    "Body": {
        "E_RESULT": "",
        "E_MSG": "",
        "ET_COMPOSICAO": [
            {
                "BILLING_PERIOD": "08/2026",
                "ENERGIA": 84.21,
                "DISTRIBUICAO": 62.12,
                "TRANSMISSAO": 18.94,
                "ENCARGOS": 59.56,
                "TRIBUTOS": 68.94,
                "DEMAIS_ITENS": 0.29,
                "PERDAS": 14.39,
            },
            {"BILLING_PERIOD": "2026/07", "ENERGIA": 1},
        ],
    },
}


class FakeCall(NamedTuple):
    method: str
    url: str
    data: dict | None
    json: dict | None
    headers: dict


def _response(body: str, url: str, status: int = 200) -> MagicMock:
    response = MagicMock()
    response.status = status
    response.url = url
    response.raise_for_status = MagicMock()
    response.text = AsyncMock(return_value=body)
    return response


class FakeEnel:
    """Roteia as requisições como o provedor de identidade e o portal fazem."""

    def __init__(
        self,
        *,
        accept_credentials: bool = True,
        idp_session: bool = False,
        usage_history: dict | None = None,
        current_user: dict | None = None,
        saml_page: str = SAML_PAGE,
    ) -> None:
        self.accept_credentials = accept_credentials
        self.idp_session = idp_session
        self.saml_page = saml_page
        self.usage_history = usage_history or USAGE_HISTORY
        self.bill_composition = BILL_COMPOSITION
        self.current_user = CURRENT_USER if current_user is None else current_user
        self.portal_session = False
        self.token_valid = True
        self.calls: list[FakeCall] = []
        self.routes = {
            SAMLSSO_URL: self._samlsso,
            COMMONAUTH_URL: self._commonauth,
            ACS_URL: self._acs,
            CURRENT_USER_URL: self._current_user,
            ENVIRONMENT_URL: self._environment,
            USAGE_HISTORY_URL: self._usage_history,
            COMPOSITION_URL: self._bill_composition,
        }

    async def request(self, method, url, **kwargs):
        self.calls.append(
            FakeCall(method, url, kwargs["data"], kwargs["json"], kwargs["headers"])
        )
        handler = self.routes.get(url)
        return handler(url) if handler else _response("", url, status=404)

    def _samlsso(self, url):
        if self.idp_session:
            return _response(self.saml_page, url)
        return _response(LOGIN_SHELL, LOGIN_PAGE_URL)

    def _commonauth(self, url):
        if self.accept_credentials:
            return _response(self.saml_page, url)
        return _response(LOGIN_SHELL, FAILED_LOGIN_URL)

    def _acs(self, url):
        self.portal_session = True
        return _response("", url)

    def _current_user(self, url):
        if not self.portal_session:
            return _response("Unauthorized", url, status=401)
        return _response(json_dumps({"currentUser": self.current_user}), url)

    def _environment(self, url):
        return _response(ENVIRONMENT_PAGE, url)

    def _usage_history(self, url):
        if not self.token_valid:
            self.token_valid = True
            return _response("", url, status=401)
        return _response(json_dumps(self.usage_history), url)

    def _bill_composition(self, url):
        if not self.token_valid:
            self.token_valid = True
            return _response("", url, status=401)
        return _response(json_dumps(self.bill_composition), url)

    def calls_to(self, url: str) -> list[FakeCall]:
        return [call for call in self.calls if call.url == url]


def json_dumps(value: dict) -> str:
    return json.dumps(value)


def _client(fake: FakeEnel) -> EnelSpApiClient:
    session = MagicMock()
    session.request = AsyncMock(side_effect=fake.request)
    return EnelSpApiClient(username="user@example.com", password="p", session=session)


def _failing_client(side_effect: BaseException) -> EnelSpApiClient:
    session = MagicMock()
    session.request = AsyncMock(side_effect=side_effect)
    return EnelSpApiClient(username="u", password="p", session=session)


def test_communication_error_is_api_error():
    assert issubclass(EnelSpApiClientCommunicationError, EnelSpApiClientError)


def test_auth_error_is_api_error():
    assert issubclass(EnelSpApiClientAuthenticationError, EnelSpApiClientError)


async def test_login_walks_the_saml_flow_in_order():
    fake = FakeEnel()
    await _client(fake).async_login()
    assert [call.url for call in fake.calls] == [
        SAMLSSO_URL,
        COMMONAUTH_URL,
        ACS_URL,
        CURRENT_USER_URL,
    ]


async def test_login_posts_the_credentials_with_the_session_key():
    fake = FakeEnel()
    await _client(fake).async_login()
    assert fake.calls_to(COMMONAUTH_URL)[0].data == {
        "username": "user@example.com",
        "password": "p",
        "sessionDataKey": "key-123",
        "tocommonauth": "true",
    }


async def test_login_delivers_the_saml_assertion_to_the_portal():
    fake = FakeEnel()
    await _client(fake).async_login()
    assert fake.calls_to(ACS_URL)[0].data == {
        "SAMLResponse": "PHNhbWwycD5hc3NlcnRpb248L3NhbWwycD4=",
        "RelayState": "ENEL_SP_WEB_BRA&x",
    }


async def test_login_ignores_the_form_action_the_identity_provider_sends():
    fake = FakeEnel()
    await _client(fake).async_login()
    assert not fake.calls_to(SAML_FORM_ACTION)


async def test_login_sends_one_session_id_everywhere():
    fake = FakeEnel()
    client = _client(fake)
    await client.async_login()
    await client.async_get_bills(ACTIVE_INSTALLATION)
    portal_sid = fake.calls_to(CURRENT_USER_URL)[0].headers["sid"]
    services_sid = fake.calls_to(USAGE_HISTORY_URL)[0].headers["SID"]
    assert len(portal_sid) == 36
    assert services_sid == portal_sid


async def test_login_reads_the_single_quoted_form_the_identity_provider_sends():
    fake = FakeEnel(saml_page=WSO2_SAML_PAGE)
    await _client(fake).async_login()
    assert fake.calls_to(ACS_URL)[0].data == {
        "SAMLResponse": "PHNhbWwycD5hc3NlcnRpb248L3NhbWwycD4=",
        "RelayState": "ENEL_SP_WEB_BRA",
    }


async def test_login_skips_the_credentials_when_the_idp_session_is_alive():
    fake = FakeEnel(idp_session=True)
    await _client(fake).async_login()
    assert fake.calls_to(COMMONAUTH_URL) == []
    assert fake.calls_to(ACS_URL)


async def test_login_returns_the_account():
    account = await _client(FakeEnel()).async_login()
    assert account.name == "Maria Silva"
    assert account.tariff_flag is EnelSpTariffFlag.YELLOW
    assert [i.number for i in account.installations] == ["0123456789", "0100000001"]
    assert [i.number for i in account.active_installations] == ["0123456789"]


async def test_login_parses_the_installation_fields():
    account = await _client(FakeEnel()).async_login()
    installation = account.installations[0]
    assert installation.nickname == "Casa"
    assert installation.name == "Casa"
    assert installation.meter_serial == "12345678"
    assert installation.partner == "0012345678"
    assert installation.contract == "0098765432"
    assert installation.contract_account == "123456789012"
    assert account.installations[1].name == "0100000001"


async def test_login_rejected_raises_auth_error():
    with pytest.raises(EnelSpApiClientAuthenticationError, match="rejected"):
        await _client(FakeEnel(accept_credentials=False)).async_login()


async def test_login_without_session_key_raises_api_error():
    fake = FakeEnel()
    original = fake.request

    async def request(method, url, **kwargs):
        if url == SAMLSSO_URL:
            return _response(LOGIN_SHELL, f"{PORTAL_BASE_URL}/pt-saopaulo/login.html")
        return await original(method, url, **kwargs)

    fake.request = request
    with pytest.raises(
        EnelSpApiClientError,
        match=r"did not start a session, got www\.enel\.com\.br/pt-saopaulo/"
        r"login\.html \(HTTP 200, fields: none\)",
    ):
        await _client(fake).async_login()


async def test_login_without_saml_form_raises_api_error():
    fake = FakeEnel()
    original = fake.request

    async def request(method, url, **kwargs):
        if url == COMMONAUTH_URL:
            return _response(
                "<html><head><title>Retry</title></head><body>"
                '<form action="/retry.do"><input name="step" value="2"/></form>'
                "</body></html>",
                f"{ACCOUNTS_BASE_URL}/authenticationendpoint/retry.do?status=x",
            )
        return await original(method, url, **kwargs)

    fake.request = request
    with pytest.raises(
        EnelSpApiClientError,
        match=r"no SAML response .* accounts\.enel\.com/authenticationendpoint/"
        r"retry\.do \(HTTP 200, title 'Retry', fields: step\)",
    ):
        await _client(fake).async_login()


async def test_login_without_portal_session_raises_api_error():
    fake = FakeEnel()
    original = fake.request

    async def request(method, url, **kwargs):
        if url == ACS_URL:
            return _response("", url)
        return await original(method, url, **kwargs)

    fake.request = request
    with pytest.raises(EnelSpApiClientError, match="did not accept the SAML session"):
        await _client(fake).async_login()


async def test_login_without_token_in_current_user_raises_api_error():
    fake = FakeEnel(current_user={"enel_id": "x"})
    with pytest.raises(EnelSpApiClientError, match="did not accept the SAML session"):
        await _client(fake).async_login()


async def test_get_account_logs_in_first():
    fake = FakeEnel()
    account = await _client(fake).async_get_account()
    assert account.enel_id == CURRENT_USER["enel_id"]
    assert fake.calls_to(COMMONAUTH_URL)


async def test_get_account_reuses_the_session():
    fake = FakeEnel()
    client = _client(fake)
    await client.async_login()
    await client.async_get_account()
    assert len(fake.calls_to(COMMONAUTH_URL)) == 1
    assert len(fake.calls_to(CURRENT_USER_URL)) == 2


async def test_get_account_logs_in_again_when_the_portal_session_lapsed():
    fake = FakeEnel()
    client = _client(fake)
    await client.async_login()
    fake.portal_session = False
    await client.async_get_account()
    assert len(fake.calls_to(COMMONAUTH_URL)) == 2


async def test_get_bills_parses_and_sorts_the_history():
    bills = await _client(FakeEnel()).async_get_bills(ACTIVE_INSTALLATION)
    assert [(bill.year, bill.month) for bill in bills] == [
        (2026, 6),
        (2026, 7),
        (2026, 8),
    ]
    latest = bills[-1]
    assert latest.amount == 290.70
    assert latest.consumption == 300
    assert latest.days == 30
    assert latest.daily_consumption == 10.0
    assert latest.due_date == date(2026, 9, 15)
    assert latest.status is EnelSpBillStatus.PAID
    assert latest.meter_reading == 4600
    assert latest.icms == 50.25
    assert latest.icms_rate == 18.0
    assert latest.energy_amount == 236.81
    assert latest.taxes == 20.15
    assert latest.interest == 0.68


async def test_get_bills_sends_the_installation_keys():
    fake = FakeEnel()
    await _client(fake).async_get_bills(ACTIVE_INSTALLATION)
    body = fake.calls_to(USAGE_HISTORY_URL)[0].json
    assert body["Header"]["Funcionalidad"] == "usagehistory"
    assert body["Header"]["CodSistema"] == "WEB"
    assert body["Body"]["I_CANAL"] == "ZINT"
    assert body["Body"]["I_PARTNER"] == "0012345678"
    assert body["Body"]["I_VERTRAG"] == "0098765432"
    assert body["Body"]["I_VKONT"] == "123456789012"


async def test_get_bills_authenticates_the_services_call():
    fake = FakeEnel()
    await _client(fake).async_get_bills(ACTIVE_INSTALLATION)
    headers = fake.calls_to(USAGE_HISTORY_URL)[0].headers
    assert headers["enel-jwt-token"] == "abc.def.ghi"
    assert headers["CLIENT_IP"] == "123"
    assert len(headers["SID"]) == 36


async def test_get_bills_reads_the_services_gateway_once():
    fake = FakeEnel()
    client = _client(fake)
    await client.async_get_bills(ACTIVE_INSTALLATION)
    await client.async_get_bills(ACTIVE_INSTALLATION)
    assert len(fake.calls_to(ENVIRONMENT_URL)) == 1


async def test_get_bills_logs_in_again_when_the_token_expired():
    fake = FakeEnel()
    client = _client(fake)
    await client.async_login()
    fake.token_valid = False
    bills = await client.async_get_bills(ACTIVE_INSTALLATION)
    assert len(bills) == 3
    assert len(fake.calls_to(COMMONAUTH_URL)) == 2


async def test_get_bills_reports_service_errors():
    history = {"Body": {"E_RESULT": "E", "E_MSG": "Instalação não encontrada"}}
    fake = FakeEnel(usage_history=history)
    with pytest.raises(EnelSpApiClientError, match="Instalação não encontrada"):
        await _client(fake).async_get_bills(ACTIVE_INSTALLATION)


async def test_get_bills_falls_back_to_the_result_description():
    history = {"Body": {"E_RESULT": "E", "DescripcionResultado": "Erro SAP"}}
    with pytest.raises(EnelSpApiClientError, match="Erro SAP"):
        await _client(FakeEnel(usage_history=history)).async_get_bills(
            ACTIVE_INSTALLATION
        )


async def test_get_bills_treats_missing_history_as_no_bills():
    history = {"Body": {"E_RESULT": "", "ET_HISTORICO": None}}
    bills = await _client(FakeEnel(usage_history=history)).async_get_bills(
        ACTIVE_INSTALLATION
    )
    assert bills == ()


async def test_get_bill_compositions_parses_the_composition():
    compositions = await _client(FakeEnel()).async_get_bill_compositions(
        ACTIVE_INSTALLATION
    )
    assert len(compositions) == 1
    composition = compositions[0]
    assert (composition.year, composition.month) == (2026, 8)
    assert composition.energy == 84.21
    assert composition.distribution == 62.12
    assert composition.transmission == 18.94
    assert composition.sector_charges == 59.56
    assert composition.losses == 14.39
    assert composition.taxes == 68.94
    assert composition.other_items == 0.29
    assert composition.supply_amount == 308.16


async def test_get_bill_compositions_calls_the_web_gateway():
    fake = FakeEnel()
    await _client(fake).async_get_bill_compositions(ACTIVE_INSTALLATION)
    call = fake.calls_to(COMPOSITION_URL)[0]
    assert call.json["Header"]["Funcionalidad"] == "getIndicadores"
    assert call.json["Body"]["I_COD_SERV"] == "HF"
    assert call.json["Body"]["I_CANAL"] == "ZINT"
    assert call.json["Body"]["I_VKONT"] == "123456789012"
    assert call.headers["enel-jwt-token"] == "abc.def.ghi"


async def test_get_bill_compositions_shares_the_site_configuration():
    fake = FakeEnel()
    client = _client(fake)
    await client.async_get_bills(ACTIVE_INSTALLATION)
    await client.async_get_bill_compositions(ACTIVE_INSTALLATION)
    assert len(fake.calls_to(ENVIRONMENT_URL)) == 1


async def test_get_bill_compositions_logs_in_again_when_the_token_expired():
    fake = FakeEnel()
    client = _client(fake)
    await client.async_login()
    fake.token_valid = False
    compositions = await client.async_get_bill_compositions(ACTIVE_INSTALLATION)
    assert len(compositions) == 1
    assert len(fake.calls_to(COMMONAUTH_URL)) == 2


async def test_get_bill_compositions_reports_service_errors():
    fake = FakeEnel()
    fake.bill_composition = {"Body": {"E_RESULT": "E", "E_MSG": "Sem faturas"}}
    with pytest.raises(EnelSpApiClientError, match="bill composition: Sem faturas"):
        await _client(fake).async_get_bill_compositions(ACTIVE_INSTALLATION)


async def test_get_bill_compositions_treats_missing_rows_as_none():
    fake = FakeEnel()
    fake.bill_composition = {"Body": {"E_RESULT": "", "ET_COMPOSICAO": None}}
    assert await _client(fake).async_get_bill_compositions(ACTIVE_INSTALLATION) == ()


async def test_environment_without_gateway_raises_api_error():
    fake = FakeEnel()
    original = fake.request

    async def request(method, url, **kwargs):
        if url == ENVIRONMENT_URL:
            return _response('var siteConfig = {"production": true};', url)
        return await original(method, url, **kwargs)

    fake.request = request
    with pytest.raises(EnelSpApiClientError, match="no portalSPUri gateway"):
        await _client(fake).async_get_bills(ACTIVE_INSTALLATION)


async def test_invalid_json_raises_api_error():
    fake = FakeEnel()
    original = fake.request

    async def request(method, url, **kwargs):
        if url == USAGE_HISTORY_URL:
            return _response("<html>oops</html>", url)
        return await original(method, url, **kwargs)

    fake.request = request
    with pytest.raises(EnelSpApiClientError, match="parse the usage history"):
        await _client(fake).async_get_bills(ACTIVE_INSTALLATION)


async def test_non_object_json_raises_api_error():
    fake = FakeEnel()
    original = fake.request

    async def request(method, url, **kwargs):
        if url == USAGE_HISTORY_URL:
            return _response("[]", url)
        return await original(method, url, **kwargs)

    fake.request = request
    with pytest.raises(EnelSpApiClientError, match="unexpected shape"):
        await _client(fake).async_get_bills(ACTIVE_INSTALLATION)


async def test_request_timeout_raises_communication_error():
    with pytest.raises(EnelSpApiClientCommunicationError, match="Timeout"):
        await _failing_client(TimeoutError("timed out")).async_login()


async def test_request_client_error_raises_communication_error():
    with pytest.raises(EnelSpApiClientCommunicationError, match="Error fetching"):
        await _failing_client(aiohttp.ClientError("refused")).async_login()


async def test_request_socket_error_raises_communication_error():
    with pytest.raises(EnelSpApiClientCommunicationError, match="Error fetching"):
        await _failing_client(socket.gaierror("dns")).async_login()


async def test_request_unexpected_exception_raises_api_error():
    with pytest.raises(EnelSpApiClientError, match="Failed to process"):
        await _failing_client(RuntimeError("boom")).async_login()


async def test_request_http_error_raises_communication_error():
    response = _response("", SAMLSSO_URL, status=500)
    response.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=MagicMock(), history=()
    )
    session = MagicMock()
    session.request = AsyncMock(return_value=response)
    client = EnelSpApiClient(username="u", password="p", session=session)
    with pytest.raises(EnelSpApiClientCommunicationError):
        await client.async_login()


def test_sanitized_error_text_redacts_the_query_string():
    exception = aiohttp.ClientError(
        "Cannot connect to https://accounts.enel.com/samlsso?sessionDataKey=secret"
    )
    sanitized = _sanitized_error_text(exception)
    assert "secret" not in sanitized
    assert sanitized.endswith("samlsso?<redacted>")


def test_sanitized_error_text_keeps_text_without_a_query_string():
    assert _sanitized_error_text(TimeoutError("timed out")) == "timed out"
