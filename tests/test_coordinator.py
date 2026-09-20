from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from custom_components.enel_sp.const import DOMAIN
from custom_components.enel_sp.coordinator import (
    FAILURE_GRACE_PERIOD,
    EnelSpDataUpdateCoordinator,
)
from custom_components.enel_sp.exceptions import (
    EnelSpApiClientAuthenticationError,
    EnelSpApiClientError,
)

from .conftest import ACCOUNT, ACTIVE_INSTALLATION, BILLS


@pytest.fixture(autouse=True)
def importer():
    with patch(
        "custom_components.enel_sp.coordinator.EnelSpStatisticsImporter"
    ) as importer_class:
        importer_class.return_value.async_import = AsyncMock()
        yield importer_class


def _make_coordinator(hass, scan_interval=timedelta(minutes=5)):
    coord = EnelSpDataUpdateCoordinator(hass=hass, scan_interval=scan_interval)
    client = AsyncMock()
    client.async_get_account = AsyncMock(return_value=ACCOUNT)
    client.async_get_bills = AsyncMock(return_value=BILLS)
    runtime_data = type("D", (), {"client": client})()
    entry = type("E", (), {"entry_id": "eid", "runtime_data": runtime_data})()
    coord.config_entry = entry
    return coord, client


def test_init_sets_domain_name(hass):
    coord = EnelSpDataUpdateCoordinator(hass=hass, scan_interval=timedelta(seconds=300))
    assert coord.name == DOMAIN


def test_init_sets_update_interval(hass):
    coord = EnelSpDataUpdateCoordinator(hass=hass, scan_interval=timedelta(seconds=42))
    assert coord.update_interval == timedelta(seconds=42)


async def test_update_data_keys_active_installations_by_number(hass):
    coord, client = _make_coordinator(hass)
    payload = await coord._async_update_data()
    assert payload.account is ACCOUNT
    assert set(payload.installations) == {ACTIVE_INSTALLATION.number}
    assert payload.installations[ACTIVE_INSTALLATION.number].bills == BILLS
    client.async_get_bills.assert_awaited_once_with(ACTIVE_INSTALLATION)


async def test_update_data_imports_the_history(hass, importer):
    coord, _ = _make_coordinator(hass)
    payload = await coord._async_update_data()
    importer.assert_called_once_with(hass)
    imported = list(importer.return_value.async_import.await_args.args[0])
    assert imported == list(payload.installations.values())


async def test_update_data_skips_the_history_import_on_failure(
    hass, sample_payload, importer
):
    coord, client = _make_coordinator(hass)
    coord.data = sample_payload
    client.async_get_account.side_effect = EnelSpApiClientError("blip")
    await coord._async_update_data()
    importer.assert_not_called()


async def test_update_data_raises_update_failed_on_api_error(hass):
    coord, client = _make_coordinator(hass)
    client.async_get_account.side_effect = EnelSpApiClientError("down")
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_update_data_raises_update_failed_when_bills_fail(hass):
    coord, client = _make_coordinator(hass)
    client.async_get_bills.side_effect = EnelSpApiClientError("down")
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_update_data_raises_auth_failed_on_auth_error(hass):
    coord, client = _make_coordinator(hass)
    client.async_get_account.side_effect = EnelSpApiClientAuthenticationError("no")
    with pytest.raises(ConfigEntryAuthFailed):
        await coord._async_update_data()


async def test_update_data_serves_last_known_data_within_grace_period(
    hass, sample_payload
):
    coord, client = _make_coordinator(hass)
    coord.data = sample_payload
    client.async_get_account.side_effect = EnelSpApiClientError("blip")
    assert await coord._async_update_data() is sample_payload


async def test_update_data_raises_update_failed_after_grace_period(
    hass, sample_payload
):
    coord, client = _make_coordinator(hass)
    coord.data = sample_payload
    client.async_get_account.side_effect = EnelSpApiClientError("down")
    coord._first_failure_at = (
        dt_util.utcnow() - FAILURE_GRACE_PERIOD - timedelta(seconds=1)
    )
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_update_data_clears_failure_window_after_success(hass):
    coord, _ = _make_coordinator(hass)
    coord._first_failure_at = dt_util.utcnow()
    await coord._async_update_data()
    assert coord._first_failure_at is None


async def test_auth_error_is_not_absorbed_by_the_grace_period(hass, sample_payload):
    coord, client = _make_coordinator(hass)
    coord.data = sample_payload
    client.async_get_account.side_effect = EnelSpApiClientAuthenticationError("no")
    with pytest.raises(ConfigEntryAuthFailed):
        await coord._async_update_data()
