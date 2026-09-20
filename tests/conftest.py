from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.enel_sp.data import (
    EnelSpAccount,
    EnelSpBill,
    EnelSpInstallation,
    EnelSpInstallationData,
    EnelSpPayload,
    EnelSpTariffFlag,
)

if TYPE_CHECKING:
    from collections.abc import Generator

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def mock_recorder_before_hass(async_test_recorder) -> None:
    """Resolve o banco de dados do recorder antes de a fixture hass iniciar."""


def make_bill(
    year: int, month: int, amount: float, consumption: float, reading: float
) -> EnelSpBill:
    return EnelSpBill(
        year=year,
        month=month,
        amount=amount,
        consumption=consumption,
        days=30,
        daily_consumption=round(consumption / 30, 3),
        due_date=date(year, month, 10),
        status_text="Paga",
        meter_reading=reading,
        icms=round(amount * 0.18, 2),
        taxes=25.32,
        interest=0.0,
    )


ACTIVE_INSTALLATION = EnelSpInstallation(
    number="0123456789",
    nickname="Casa",
    address="R Exemplo, 100 - Centro, Sao Paulo - SP",
    partner="0012345678",
    contract="0098765432",
    contract_account="123456789012",
    voltage_level="BT",
    meter_serial="12345678",
    move_in="20250801",
    move_out="99991231",
)
INACTIVE_INSTALLATION = EnelSpInstallation(
    number="0100000001",
    nickname="Casa antiga",
    address="Av Antiga, 1",
    partner="0012345678",
    contract="0011111111",
    contract_account="123456789099",
    voltage_level="BT",
    meter_serial="99999999",
    move_in="20190101",
    move_out="20211231",
)
BILLS = (
    make_bill(2026, 6, 350.10, 350, 3900),
    make_bill(2026, 7, 420.80, 400, 4300),
    make_bill(2026, 8, 290.70, 300, 4600),
)
ACCOUNT = EnelSpAccount(
    enel_id="6f1a2b3c-0000-4000-8000-000000000000",
    name="Maria Silva",
    tariff_flag=EnelSpTariffFlag.YELLOW,
    installations=(ACTIVE_INSTALLATION, INACTIVE_INSTALLATION),
)


@pytest.fixture
def sample_payload() -> EnelSpPayload:
    return EnelSpPayload(
        account=ACCOUNT,
        installations={
            ACTIVE_INSTALLATION.number: EnelSpInstallationData(
                installation=ACTIVE_INSTALLATION, bills=BILLS
            ),
        },
    )


@pytest.fixture
def mock_api_client() -> Generator:
    with patch("custom_components.enel_sp.EnelSpApiClient") as mock_class:
        instance = mock_class.return_value
        instance.async_login = AsyncMock(return_value=ACCOUNT)
        instance.async_get_account = AsyncMock(return_value=ACCOUNT)
        instance.async_get_bills = AsyncMock(return_value=BILLS)
        yield instance


@pytest.fixture
async def setup_integration(
    recorder_mock, hass, mock_api_client, enable_custom_integrations
):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.enel_sp.const import DOMAIN

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "user@example.com", "password": "pass"},
        unique_id="user_example_com",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
