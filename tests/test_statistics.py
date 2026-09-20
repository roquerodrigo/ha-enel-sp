from __future__ import annotations

from datetime import date
from functools import partial
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    get_metadata,
    statistics_during_period,
)
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.enel_sp.data import EnelSpInstallationData
from custom_components.enel_sp.statistics import EnelSpStatisticsImporter

from .conftest import ACTIVE_INSTALLATION, BILLS

ENERGY_ID = "enel_sp:0123456789_energy"
COST_ID = "enel_sp:0123456789_cost"
TRANSLATIONS = {
    "component.enel_sp.entity.sensor.bill_consumption.name": "Bill consumption",
    "component.enel_sp.entity.sensor.bill_amount.name": "Bill amount",
}
DATA = EnelSpInstallationData(installation=ACTIVE_INSTALLATION, bills=BILLS)


def _month_start(year: int, month: int):
    return dt_util.start_of_local_day(date(year, month, 1))


def _last_row(statistic_id: str, year: int, month: int, total: float) -> dict:
    return {
        statistic_id: [{"start": _month_start(year, month).timestamp(), "sum": total}]
    }


@pytest.fixture
def recorder():
    with (
        patch("custom_components.enel_sp.statistics.get_instance") as get_instance,
        patch(
            "custom_components.enel_sp.statistics.get_last_statistics",
            return_value={},
        ) as last_statistics,
        patch(
            "custom_components.enel_sp.statistics.async_add_external_statistics"
        ) as add_statistics,
        patch(
            "custom_components.enel_sp.statistics.async_get_cached_translations",
            return_value=TRANSLATIONS,
        ),
    ):
        get_instance.return_value.async_add_executor_job = AsyncMock(
            side_effect=lambda func, *args: func(*args)
        )
        yield SimpleNamespace(last=last_statistics, add=add_statistics)


def _import_call(recorder, statistic_id: str):
    for call in recorder.add.call_args_list:
        if call.args[1]["statistic_id"] == statistic_id:
            return call
    pytest.fail(f"{statistic_id} was not imported")


def _rows(recorder, statistic_id: str) -> list[dict]:
    return _import_call(recorder, statistic_id).args[2]


def _metadata(recorder, statistic_id: str) -> dict:
    return _import_call(recorder, statistic_id).args[1]


async def test_first_import_writes_every_bill(recorder):
    await EnelSpStatisticsImporter(MagicMock()).async_import([DATA])
    rows = _rows(recorder, ENERGY_ID)
    assert [row["start"] for row in rows] == [
        _month_start(2026, 6),
        _month_start(2026, 7),
        _month_start(2026, 8),
    ]
    assert [row["sum"] for row in rows] == [350.0, 750.0, 1050.0]
    assert [row["state"] for row in rows] == [3900, 4300, 4600]


async def test_first_import_writes_the_cost_series(recorder):
    await EnelSpStatisticsImporter(MagicMock()).async_import([DATA])
    rows = _rows(recorder, COST_ID)
    assert [row["state"] for row in rows] == [350.10, 420.80, 290.70]
    assert [row["sum"] for row in rows] == [350.10, 770.90, 1061.60]


async def test_metadata_describes_energy_and_currency(recorder):
    await EnelSpStatisticsImporter(MagicMock()).async_import([DATA])
    energy = _metadata(recorder, ENERGY_ID)
    assert energy["source"] == "enel_sp"
    assert energy["has_sum"] is True
    assert energy["unit_of_measurement"] == "kWh"
    assert energy["unit_class"] == "energy"
    assert energy["name"] == "Casa Bill consumption"
    cost = _metadata(recorder, COST_ID)
    assert cost["name"] == "Casa Bill amount"
    assert cost["unit_of_measurement"] == "BRL"
    assert cost["unit_class"] is None


async def test_later_imports_append_only_newer_months(recorder):
    recorder.last.side_effect = lambda _hass, _n, statistic_id, *_, **__: (
        _last_row(statistic_id, 2026, 7, 1000.0)
        if statistic_id == ENERGY_ID
        else _last_row(statistic_id, 2026, 7, 900.0)
    )
    await EnelSpStatisticsImporter(MagicMock()).async_import([DATA])
    energy = _rows(recorder, ENERGY_ID)
    assert [row["start"] for row in energy] == [_month_start(2026, 8)]
    assert energy[0]["sum"] == 1300.0
    assert _rows(recorder, COST_ID)[0]["sum"] == 1190.70


async def test_only_metadata_is_sent_when_no_month_is_newer(recorder):
    recorder.last.side_effect = lambda _hass, _n, statistic_id, *_, **__: _last_row(
        statistic_id, 2026, 8, 1050.0
    )
    await EnelSpStatisticsImporter(MagicMock()).async_import([DATA])
    assert _rows(recorder, ENERGY_ID) == []
    assert _rows(recorder, COST_ID) == []
    assert _metadata(recorder, ENERGY_ID)["name"] == "Casa Bill consumption"


async def test_missing_cost_row_restarts_the_cost_sum(recorder):
    recorder.last.side_effect = lambda _hass, _n, statistic_id, *_, **__: (
        _last_row(statistic_id, 2026, 7, 790.0) if statistic_id == ENERGY_ID else {}
    )
    await EnelSpStatisticsImporter(MagicMock()).async_import([DATA])
    assert _rows(recorder, COST_ID)[0]["sum"] == 290.70


async def test_history_lands_in_long_term_statistics(hass, setup_integration):
    await async_wait_recording_done(hass)
    stats = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        dt_util.utc_from_timestamp(0),
        None,
        {ENERGY_ID, COST_ID},
        "month",
        None,
        {"sum", "state"},
    )
    assert [round(row["sum"], 3) for row in stats[ENERGY_ID]] == [350, 750, 1050]
    assert [row["state"] for row in stats[ENERGY_ID]] == [3900, 4300, 4600]
    assert [round(row["sum"], 2) for row in stats[COST_ID]] == [
        350.10,
        770.90,
        1061.60,
    ]
    metadata = await get_instance(hass).async_add_executor_job(
        partial(get_metadata, hass, statistic_ids={ENERGY_ID})
    )
    assert metadata[ENERGY_ID][1]["name"] == "Casa Bill consumption"
