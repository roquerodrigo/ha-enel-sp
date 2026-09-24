from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.enel_sp.const import DOMAIN, TARIFF_UPDATE_INTERVAL_SECONDS
from custom_components.enel_sp.exceptions import EnelSpApiClientError
from custom_components.enel_sp.tariff_coordinator import (
    EnelSpTariffUpdateCoordinator,
)

from .conftest import CATALOG


def _make_coordinator(hass):
    client = MagicMock()
    client.async_get_catalog = AsyncMock(return_value=CATALOG)
    return EnelSpTariffUpdateCoordinator(hass=hass, client=client), client


def test_init_names_and_schedules_the_coordinator(hass):
    coord, _ = _make_coordinator(hass)
    assert coord.name == f"{DOMAIN}_tariffs"
    assert coord.update_interval == timedelta(seconds=TARIFF_UPDATE_INTERVAL_SECONDS)


async def test_update_data_returns_the_catalog(hass):
    coord, _ = _make_coordinator(hass)
    assert await coord._async_update_data() is CATALOG


async def test_update_data_serves_the_last_known_catalog_on_failure(hass):
    coord, client = _make_coordinator(hass)
    coord.data = CATALOG
    client.async_get_catalog.side_effect = EnelSpApiClientError("down")
    assert await coord._async_update_data() is CATALOG


async def test_update_data_fails_without_a_known_catalog(hass):
    coord, client = _make_coordinator(hass)
    client.async_get_catalog.side_effect = EnelSpApiClientError("down")
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()
