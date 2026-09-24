from __future__ import annotations

import json
import socket
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.enel_sp.aneel_api import EnelSpAneelApiClient
from custom_components.enel_sp.const import (
    ANEEL_BANDEIRA_TARIFARIA_RESOURCE_ID,
    ANEEL_DATASTORE_URL,
    ANEEL_TARIFFS_RESOURCE_ID,
    ENEL_SP_CNPJ,
)
from custom_components.enel_sp.exceptions import (
    EnelSpApiClientCommunicationError,
    EnelSpApiClientError,
)

TARIFF_RECORD = {
    "_id": 1,
    "DscREH": "RESOLUÇÃO HOMOLOGATÓRIA Nº 3.596, DE 3 DE JULHO DE 2026 ",
    "SigAgente": "ELETROPAULO",
    "DatInicioVigencia": "2026-07-04",
    "DatFimVigencia": "2027-07-03",
    "DscSubGrupo": "B1",
    "DscClasse": "Residencial",
    "DscSubClasse": "Residencial",
    "VlrTUSD": "472,42",
    "VlrTE": "316,96",
}
BANDEIRA_TARIFARIA_RECORDS = [
    {
        "DatCompetencia": "2026-09-01",
        "NomBandeiraAcionada": "Amarela",
        "VlrAdicionalBandeira": "18,85",
    },
    {
        "DatCompetencia": "2026-04-01",
        "NomBandeiraAcionada": "Verde",
        "VlrAdicionalBandeira": ",00",
    },
    {
        "DatCompetencia": "2021-09-01",
        "NomBandeiraAcionada": "Escassez Hídrica",
        "VlrAdicionalBandeira": "1.420,00",
    },
]


def _search_response(records: list[dict]) -> str:
    return json.dumps({"success": True, "result": {"records": records}})


def _response(text: str) -> MagicMock:
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.text = AsyncMock(return_value=text)
    return response


def _client(*texts: str) -> tuple[EnelSpAneelApiClient, MagicMock]:
    session = MagicMock()
    session.get = AsyncMock(side_effect=[_response(text) for text in texts])
    return EnelSpAneelApiClient(session), session


def _failing_client(side_effect: BaseException) -> EnelSpAneelApiClient:
    session = MagicMock()
    session.get = AsyncMock(side_effect=side_effect)
    return EnelSpAneelApiClient(session)


async def test_catalog_converts_the_tariffs_to_brl_per_kwh():
    client, _ = _client(
        _search_response([TARIFF_RECORD]),
        _search_response(BANDEIRA_TARIFARIA_RECORDS),
    )
    catalog = await client.async_get_catalog()
    tariff = catalog.tariffs[0]
    assert tariff.series == ("B1", "Residencial", "Residencial")
    assert tariff.distribution_rate == pytest.approx(0.47242)
    assert tariff.energy_rate == pytest.approx(0.31696)
    assert tariff.rate == pytest.approx(0.78938)
    assert tariff.valid_from == date(2026, 7, 4)
    assert tariff.valid_until == date(2027, 7, 3)
    assert (
        tariff.resolution == "RESOLUÇÃO HOMOLOGATÓRIA Nº 3.596, DE 3 DE JULHO DE 2026"
    )


async def test_catalog_reads_the_bandeira_tarifaria_surcharges():
    client, _ = _client(
        _search_response([TARIFF_RECORD]),
        _search_response(BANDEIRA_TARIFARIA_RECORDS),
    )
    catalog = await client.async_get_catalog()
    surcharges = catalog.bandeira_tarifaria_surcharges
    assert [(item.month, item.name) for item in surcharges] == [
        (date(2026, 9, 1), "Amarela"),
        (date(2026, 4, 1), "Verde"),
        (date(2021, 9, 1), "Escassez Hídrica"),
    ]
    assert [item.rate for item in surcharges] == pytest.approx([0.01885, 0.0, 1.42])


async def test_catalog_filters_the_enel_sp_low_voltage_tariffs():
    client, session = _client(
        _search_response([TARIFF_RECORD]),
        _search_response(BANDEIRA_TARIFARIA_RECORDS),
    )
    await client.async_get_catalog()
    tariff_call, bandeira_tarifaria_call = session.get.await_args_list
    assert tariff_call.args == (ANEEL_DATASTORE_URL,)
    params = tariff_call.kwargs["params"]
    assert params["resource_id"] == ANEEL_TARIFFS_RESOURCE_ID
    assert params["sort"] == "DatInicioVigencia desc"
    filters = json.loads(params["filters"])
    assert filters["NumCNPJDistribuidora"] == ENEL_SP_CNPJ
    assert filters["DscBaseTarifaria"] == "Tarifa de Aplicação"
    assert filters["DscModalidadeTarifaria"] == "Convencional"
    assert filters["DscSubGrupo"] == ["B1", "B2", "B3"]
    bandeira_tarifaria_params = bandeira_tarifaria_call.kwargs["params"]
    assert (
        bandeira_tarifaria_params["resource_id"] == ANEEL_BANDEIRA_TARIFARIA_RESOURCE_ID
    )
    assert bandeira_tarifaria_params["sort"] == "DatCompetencia desc"


async def test_catalog_treats_missing_records_as_empty():
    client, _ = _client(
        json.dumps({"success": True, "result": {}}),
        json.dumps({"success": True, "result": {"records": None}}),
    )
    catalog = await client.async_get_catalog()
    assert catalog.tariffs == ()
    assert catalog.bandeira_tarifaria_surcharges == ()


async def test_unsuccessful_search_raises_api_error():
    client, _ = _client(json.dumps({"success": False, "error": {}}))
    with pytest.raises(EnelSpApiClientError, match="not successful"):
        await client.async_get_catalog()


async def test_non_object_json_raises_api_error():
    client, _ = _client("[]")
    with pytest.raises(EnelSpApiClientError, match="not successful"):
        await client.async_get_catalog()


async def test_invalid_json_raises_api_error():
    client, _ = _client("<html>maintenance</html>")
    with pytest.raises(EnelSpApiClientError, match="Failed to parse the ANEEL data"):
        await client.async_get_catalog()


async def test_malformed_record_raises_api_error():
    client, _ = _client(
        _search_response([{**TARIFF_RECORD, "DatInicioVigencia": "04/07/2026"}]),
        _search_response(BANDEIRA_TARIFARIA_RECORDS),
    )
    with pytest.raises(EnelSpApiClientError, match="Failed to parse the ANEEL tariffs"):
        await client.async_get_catalog()


@pytest.mark.parametrize(
    "side_effect",
    [TimeoutError(), aiohttp.ClientError("boom"), socket.gaierror("dns")],
)
async def test_transport_errors_raise_communication_error(side_effect):
    with pytest.raises(EnelSpApiClientCommunicationError):
        await _failing_client(side_effect).async_get_catalog()


def test_communication_error_is_api_error():
    assert issubclass(EnelSpApiClientCommunicationError, EnelSpApiClientError)
