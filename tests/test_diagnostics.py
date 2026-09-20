from __future__ import annotations

from custom_components.enel_sp.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_redacts_username(hass, setup_integration):
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diag["entry"]["data"]["username"] == "**REDACTED**"


async def test_diagnostics_redacts_password(hass, setup_integration):
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diag["entry"]["data"]["password"] == "**REDACTED**"


async def test_diagnostics_includes_entry_metadata(hass, setup_integration):
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diag["entry"]["domain"] == "enel_sp"
    assert diag["entry"]["version"] == 1
    assert "title" in diag["entry"]


async def test_diagnostics_serializes_and_redacts_the_payload(hass, setup_integration):
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    data = diag["coordinator_data"]
    assert data["account"]["enel_id"] == "**REDACTED**"
    assert data["account"]["name"] == "**REDACTED**"
    assert data["account"]["tariff_flag"] == "yellow"
    installation = data["installations"]["0123456789"]
    assert installation["installation"]["address"] == "**REDACTED**"
    assert installation["installation"]["number"] == "0123456789"
    latest = installation["bills"][-1]
    assert latest["amount"] == 290.70
    assert latest["due_date"] == "2026-08-10"


async def test_diagnostics_coordinator_data_none_before_first_refresh(
    hass, setup_integration
):
    setup_integration.runtime_data.coordinator.data = None
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diag["coordinator_data"] is None


async def test_diagnostics_options_redacted_when_present(hass, setup_integration):
    diag = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert isinstance(diag["entry"]["options"], dict)
