"""Cliente dos dados abertos da ANEEL: tarifas homologadas e bandeiras tarifárias."""

from __future__ import annotations

import asyncio
import json
import socket
from datetime import date
from typing import TYPE_CHECKING, TypedDict, cast

import aiohttp

from .const import (
    ANEEL_BANDEIRA_TARIFARIA_RESOURCE_ID,
    ANEEL_DATASTORE_URL,
    ANEEL_TARIFFS_RESOURCE_ID,
    ENEL_SP_CNPJ,
)
from .data import (
    EnelSpAneelTariff,
    EnelSpBandeiraTarifariaSurcharge,
    EnelSpTariffCatalog,
)
from .exceptions import EnelSpApiClientCommunicationError, EnelSpApiClientError

if TYPE_CHECKING:
    from .data import JsonObject

_REQUEST_TIMEOUT_SECONDS = 60
_KILO = 1000
_TARIFF_RECORDS_LIMIT = 200
_BANDEIRA_TARIFARIA_RECORDS_LIMIT = 24
_LOW_VOLTAGE_SUBGROUPS = ("B1", "B2", "B3")
_TARIFF_FILTERS: JsonObject = {
    "NumCNPJDistribuidora": ENEL_SP_CNPJ,
    "DscBaseTarifaria": "Tarifa de Aplicação",
    "DscModalidadeTarifaria": "Convencional",
    "DscDetalhe": "Não se aplica",
    "DscUnidadeTerciaria": "MWh",
    "DscSubGrupo": list(_LOW_VOLTAGE_SUBGROUPS),
}


class _TariffRecord(TypedDict, total=False):
    """Linha do conjunto de tarifas homologadas das distribuidoras."""

    DscSubGrupo: str
    DscClasse: str
    DscSubClasse: str
    VlrTUSD: str
    VlrTE: str
    DatInicioVigencia: str
    DatFimVigencia: str
    DscREH: str


class _BandeiraTarifariaRecord(TypedDict, total=False):
    """Linha do conjunto de acionamentos de bandeira tarifária."""

    DatCompetencia: str
    NomBandeiraAcionada: str
    VlrAdicionalBandeira: str


class _SearchResult(TypedDict, total=False):
    """Página de registros devolvida pelo ``datastore_search``."""

    records: list[JsonObject]


class _SearchResponse(TypedDict, total=False):
    """Envelope das respostas da API CKAN."""

    success: bool
    result: _SearchResult


def _decimal(value: str | None) -> float:
    """Lê um número no formato brasileiro (``1.234,56``, ``,00``)."""
    if not value:
        return 0.0
    return float(value.replace(".", "").replace(",", "."))


def _tariff_from_record(record: _TariffRecord) -> EnelSpAneelTariff:
    """Monta uma tarifa em BRL/kWh a partir de uma linha em BRL/MWh."""
    return EnelSpAneelTariff(
        subgroup=record.get("DscSubGrupo", ""),
        consumer_class=record.get("DscClasse", ""),
        subclass=record.get("DscSubClasse", ""),
        distribution_rate=_decimal(record.get("VlrTUSD")) / _KILO,
        energy_rate=_decimal(record.get("VlrTE")) / _KILO,
        valid_from=date.fromisoformat(record.get("DatInicioVigencia", "")),
        valid_until=date.fromisoformat(record.get("DatFimVigencia", "")),
        resolution=record.get("DscREH", "").strip(),
    )


def _bandeira_tarifaria_surcharge_from_record(
    record: _BandeiraTarifariaRecord,
) -> EnelSpBandeiraTarifariaSurcharge:
    """Monta o adicional de bandeira em BRL/kWh a partir de uma linha em BRL/MWh."""
    return EnelSpBandeiraTarifariaSurcharge(
        month=date.fromisoformat(record.get("DatCompetencia", "")),
        name=record.get("NomBandeiraAcionada", "").strip(),
        rate=_decimal(record.get("VlrAdicionalBandeira")) / _KILO,
    )


class EnelSpAneelApiClient:
    """
    Cliente da API CKAN do portal de dados abertos da ANEEL.

    As tarifas vêm já filtradas para a Enel São Paulo, na modalidade convencional das
    classes de baixa tensão; os adicionais de bandeira valem para todo o país.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Inicializa."""
        self._session = session

    async def async_get_catalog(self) -> EnelSpTariffCatalog:
        """Retorna as tarifas homologadas e as bandeiras mais recentes."""
        tariff_records = await self._async_search(
            resource_id=ANEEL_TARIFFS_RESOURCE_ID,
            filters=_TARIFF_FILTERS,
            sort="DatInicioVigencia desc",
            limit=_TARIFF_RECORDS_LIMIT,
        )
        bandeira_tarifaria_records = await self._async_search(
            resource_id=ANEEL_BANDEIRA_TARIFARIA_RESOURCE_ID,
            filters={},
            sort="DatCompetencia desc",
            limit=_BANDEIRA_TARIFARIA_RECORDS_LIMIT,
        )
        try:
            return EnelSpTariffCatalog(
                tariffs=tuple(
                    _tariff_from_record(cast("_TariffRecord", record))
                    for record in tariff_records
                ),
                bandeira_tarifaria_surcharges=tuple(
                    _bandeira_tarifaria_surcharge_from_record(
                        cast("_BandeiraTarifariaRecord", record)
                    )
                    for record in bandeira_tarifaria_records
                ),
            )
        except ValueError as exception:
            msg = f"Failed to parse the ANEEL tariffs: {exception}"
            raise EnelSpApiClientError(msg) from exception

    async def _async_search(
        self,
        *,
        resource_id: str,
        filters: JsonObject,
        sort: str,
        limit: int,
    ) -> list[JsonObject]:
        """Consulta um conjunto de dados e retorna os registros da primeira página."""
        params = {
            "resource_id": resource_id,
            "filters": json.dumps(filters, ensure_ascii=False),
            "sort": sort,
            "limit": str(limit),
        }
        try:
            async with asyncio.timeout(_REQUEST_TIMEOUT_SECONDS):
                response = await self._session.get(ANEEL_DATASTORE_URL, params=params)
                response.raise_for_status()
                text = await response.text()
        except TimeoutError as exception:
            msg = f"Timeout error fetching the ANEEL data - {exception}"
            raise EnelSpApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching the ANEEL data - {exception}"
            raise EnelSpApiClientCommunicationError(msg) from exception
        try:
            parsed = cast("_SearchResponse", json.loads(text))
        except ValueError as exception:
            msg = f"Failed to parse the ANEEL data: {exception}"
            raise EnelSpApiClientError(msg) from exception
        if not isinstance(parsed, dict) or not parsed.get("success"):
            msg = "Failed to fetch the ANEEL data: the search was not successful"
            raise EnelSpApiClientError(msg)
        return parsed.get("result", {}).get("records") or []
