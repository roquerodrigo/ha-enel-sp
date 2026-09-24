from __future__ import annotations

from dataclasses import replace
from datetime import date
from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from custom_components.enel_sp.const import DOMAIN
from custom_components.enel_sp.data import (
    EnelSpInstallationData,
    EnelSpPayload,
    EnelSpTariffFlag,
)
from custom_components.enel_sp.sensor.bill_amount import EnelSpBillAmountSensor
from custom_components.enel_sp.sensor.bill_consumption import (
    EnelSpBillConsumptionSensor,
)
from custom_components.enel_sp.sensor.bill_due_date import EnelSpBillDueDateSensor
from custom_components.enel_sp.sensor.bill_status import EnelSpBillStatusSensor
from custom_components.enel_sp.sensor.energy_price import EnelSpEnergyPriceSensor
from custom_components.enel_sp.sensor.meter_reading import EnelSpMeterReadingSensor
from custom_components.enel_sp.sensor.open_bills_amount import (
    EnelSpOpenBillsAmountSensor,
)
from custom_components.enel_sp.sensor.open_bills_count import (
    EnelSpOpenBillsCountSensor,
)
from custom_components.enel_sp.sensor.tariff_flag import EnelSpTariffFlagSensor

from .conftest import (
    ACCOUNT,
    ACTIVE_INSTALLATION,
    AUGUST_PIS_COFINS_RATE,
    BILLS,
    CATALOG,
    INACTIVE_INSTALLATION,
    SEPTEMBER_BANDEIRA_TARIFARIA,
)

SENSORS_PER_INSTALLATION = 9


def _coordinator(payload, catalog=CATALOG):
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "eid"
    coordinator.config_entry.runtime_data.tariff_coordinator.data = catalog
    coordinator.data = payload
    return coordinator


def _expected_price(bandeira_tarifaria_rate: float) -> float:
    return (0.78938 + bandeira_tarifaria_rate) / (0.82 * (1 - AUGUST_PIS_COFINS_RATE))


def _state_by_unique_id(hass, entry, suffix: str):
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_{suffix}"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state


async def test_every_active_installation_gets_its_sensors(hass, setup_integration):
    assert len(hass.states.async_all("sensor")) == SENSORS_PER_INSTALLATION


async def test_bill_amount_state(hass, setup_integration):
    state = _state_by_unique_id(hass, setup_integration, "0123456789_bill_amount")
    assert state.state == "290.7"
    assert state.attributes["unit_of_measurement"] == "BRL"
    assert state.attributes["device_class"] == "monetary"
    assert state.attributes["state_class"] == "total"
    assert (
        state.attributes["last_reset"]
        == dt_util.start_of_local_day(date(2026, 8, 1)).isoformat()
    )
    assert state.attributes["installation_number"] == "0123456789"
    assert state.attributes["bill_month"] == 8
    assert state.attributes["taxes"] == 25.32


async def test_bill_consumption_state(hass, setup_integration):
    state = _state_by_unique_id(hass, setup_integration, "0123456789_bill_consumption")
    assert state.state == "300"
    assert state.attributes["unit_of_measurement"] == "kWh"
    assert state.attributes["device_class"] == "energy"
    assert state.attributes["daily_average"] == 10.0


async def test_bill_due_date_state(hass, setup_integration):
    state = _state_by_unique_id(hass, setup_integration, "0123456789_bill_due_date")
    midnight = dt_util.start_of_local_day(date(2026, 8, 10))
    assert state.state == dt_util.as_utc(midnight).isoformat()
    assert state.attributes["device_class"] == "timestamp"


async def test_bill_status_and_flag_states(hass, setup_integration):
    status = _state_by_unique_id(hass, setup_integration, "0123456789_bill_status")
    assert status.state == "paid"
    assert status.attributes["portal_status"] == "Paga"
    assert status.attributes["options"] == ["paid", "open", "overdue", "unknown"]
    flag = _state_by_unique_id(hass, setup_integration, "0123456789_tariff_flag")
    assert flag.state == "yellow"


async def test_devices_are_named_after_the_installation(hass, setup_integration):
    device = dr.async_get(hass).async_get_device(
        identifiers={(DOMAIN, f"{setup_integration.entry_id}_0123456789")}
    )
    assert device is not None
    assert device.name == "Casa"


async def test_installations_listed_later_are_added(hass, setup_integration):
    coordinator = setup_integration.runtime_data.coordinator
    payload: EnelSpPayload = coordinator.data
    coordinator.async_set_updated_data(
        EnelSpPayload(
            account=payload.account,
            installations={
                **payload.installations,
                INACTIVE_INSTALLATION.number: EnelSpInstallationData(
                    installation=INACTIVE_INSTALLATION, bills=BILLS[:1]
                ),
            },
        )
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 2 * SENSORS_PER_INSTALLATION
    state = _state_by_unique_id(hass, setup_integration, "0100000001_bill_amount")
    assert state.state == "350.1"


async def test_installations_dropped_by_the_portal_become_unavailable(
    hass, setup_integration
):
    coordinator = setup_integration.runtime_data.coordinator
    payload: EnelSpPayload = coordinator.data
    coordinator.async_set_updated_data(
        EnelSpPayload(account=payload.account, installations={})
    )
    await hass.async_block_till_done()
    state = _state_by_unique_id(hass, setup_integration, "0123456789_bill_amount")
    assert state.state == "unavailable"


def test_bill_amount_sensor(sample_payload):
    sensor = EnelSpBillAmountSensor(_coordinator(sample_payload), ACTIVE_INSTALLATION)
    assert sensor.unique_id == "eid_0123456789_bill_amount"
    assert sensor.native_value == 290.70
    assert sensor.device_class is SensorDeviceClass.MONETARY
    assert sensor.state_class is SensorStateClass.TOTAL
    assert sensor.last_reset == dt_util.start_of_local_day(date(2026, 8, 1))
    assert sensor.extra_state_attributes["icms"] == 52.33


def test_bill_amount_sensor_without_bill():
    payload = EnelSpPayload(account=ACCOUNT, installations={})
    sensor = EnelSpBillAmountSensor(_coordinator(payload), ACTIVE_INSTALLATION)
    assert sensor.native_value is None
    assert sensor.last_reset is None
    assert "icms" not in sensor.extra_state_attributes


def test_bill_consumption_sensor(sample_payload):
    sensor = EnelSpBillConsumptionSensor(
        _coordinator(sample_payload), ACTIVE_INSTALLATION
    )
    assert sensor.unique_id == "eid_0123456789_bill_consumption"
    assert sensor.native_value == 300
    assert sensor.device_class is SensorDeviceClass.ENERGY
    assert sensor.last_reset == dt_util.start_of_local_day(date(2026, 8, 1))
    assert sensor.extra_state_attributes["days"] == 30


def test_bill_consumption_sensor_without_bill():
    payload = EnelSpPayload(account=ACCOUNT, installations={})
    sensor = EnelSpBillConsumptionSensor(_coordinator(payload), ACTIVE_INSTALLATION)
    assert sensor.native_value is None
    assert sensor.last_reset is None


def test_bill_due_date_sensor(sample_payload):
    sensor = EnelSpBillDueDateSensor(_coordinator(sample_payload), ACTIVE_INSTALLATION)
    assert sensor.unique_id == "eid_0123456789_bill_due_date"
    assert sensor.native_value == dt_util.start_of_local_day(date(2026, 8, 10))
    assert sensor.device_class is SensorDeviceClass.TIMESTAMP


def test_bill_due_date_sensor_without_bill():
    payload = EnelSpPayload(account=ACCOUNT, installations={})
    assert (
        EnelSpBillDueDateSensor(_coordinator(payload), ACTIVE_INSTALLATION).native_value
        is None
    )


def test_bill_status_sensor(sample_payload):
    sensor = EnelSpBillStatusSensor(_coordinator(sample_payload), ACTIVE_INSTALLATION)
    assert sensor.unique_id == "eid_0123456789_bill_status"
    assert sensor.native_value == "paid"
    assert sensor.device_class is SensorDeviceClass.ENUM
    assert sensor.extra_state_attributes["portal_status"] == "Paga"


def test_bill_status_sensor_without_bill():
    payload = EnelSpPayload(account=ACCOUNT, installations={})
    sensor = EnelSpBillStatusSensor(_coordinator(payload), ACTIVE_INSTALLATION)
    assert sensor.native_value is None
    assert "portal_status" not in sensor.extra_state_attributes


def test_meter_reading_sensor(sample_payload):
    sensor = EnelSpMeterReadingSensor(_coordinator(sample_payload), ACTIVE_INSTALLATION)
    assert sensor.unique_id == "eid_0123456789_meter_reading"
    assert sensor.native_value == 4600
    assert sensor.state_class is SensorStateClass.TOTAL_INCREASING


def test_meter_reading_sensor_without_bill():
    payload = EnelSpPayload(account=ACCOUNT, installations={})
    assert (
        EnelSpMeterReadingSensor(
            _coordinator(payload), ACTIVE_INSTALLATION
        ).native_value
        is None
    )


def test_open_bills_sensors_with_unpaid_bills():
    bills = (
        BILLS[0],
        replace(BILLS[1], status_text="Vencida"),
        replace(BILLS[2], status_text="Em aberto"),
    )
    payload = EnelSpPayload(
        account=ACCOUNT,
        installations={
            ACTIVE_INSTALLATION.number: EnelSpInstallationData(
                installation=ACTIVE_INSTALLATION, bills=bills
            )
        },
    )
    amount = EnelSpOpenBillsAmountSensor(_coordinator(payload), ACTIVE_INSTALLATION)
    count = EnelSpOpenBillsCountSensor(_coordinator(payload), ACTIVE_INSTALLATION)
    assert amount.unique_id == "eid_0123456789_open_bills_amount"
    assert amount.native_value == 711.50
    assert amount.device_class is SensorDeviceClass.MONETARY
    assert count.unique_id == "eid_0123456789_open_bills_count"
    assert count.native_value == 2


def test_open_bills_sensors_without_installation():
    payload = EnelSpPayload(account=ACCOUNT, installations={})
    amount = EnelSpOpenBillsAmountSensor(_coordinator(payload), ACTIVE_INSTALLATION)
    count = EnelSpOpenBillsCountSensor(_coordinator(payload), ACTIVE_INSTALLATION)
    assert amount.native_value is None
    assert count.native_value is None


def test_tariff_flag_sensor(sample_payload):
    sensor = EnelSpTariffFlagSensor(_coordinator(sample_payload), ACTIVE_INSTALLATION)
    assert sensor.unique_id == "eid_0123456789_tariff_flag"
    assert sensor.native_value == EnelSpTariffFlag.YELLOW.value
    assert sensor.options == [
        "green",
        "yellow",
        "red_level_1",
        "red_level_2",
        "unknown",
    ]


def test_tariff_flag_sensor_before_first_refresh():
    sensor = EnelSpTariffFlagSensor(_coordinator(None), ACTIVE_INSTALLATION)
    assert sensor.native_value is None


async def test_energy_price_state(hass, setup_integration):
    state = _state_by_unique_id(hass, setup_integration, "0123456789_energy_price")
    assert float(state.state) == pytest.approx(
        _expected_price(SEPTEMBER_BANDEIRA_TARIFARIA.rate), abs=1e-5
    )
    assert state.attributes["unit_of_measurement"] == "BRL/kWh"
    assert state.attributes["state_class"] == "measurement"
    assert state.attributes["tariff_source"] == "aneel"
    assert state.attributes["tariff_class"] == "Residencial"
    assert state.attributes["bandeira_tarifaria"] == "Vermelha P1"
    assert state.attributes["icms_rate"] == 18.0
    assert state.attributes["other_items"] == 9.39


async def test_energy_price_follows_the_tariff_coordinator(hass, setup_integration):
    tariff_coordinator = setup_integration.runtime_data.tariff_coordinator
    tariff_coordinator.async_set_updated_data(
        replace(CATALOG, bandeira_tarifaria_surcharges=())
    )
    await hass.async_block_till_done()
    state = _state_by_unique_id(hass, setup_integration, "0123456789_energy_price")
    assert float(state.state) == pytest.approx(_expected_price(0.0), abs=1e-5)
    assert "bandeira_tarifaria" not in state.attributes


def test_energy_price_sensor(sample_payload):
    sensor = EnelSpEnergyPriceSensor(_coordinator(sample_payload), ACTIVE_INSTALLATION)
    assert sensor.unique_id == "eid_0123456789_energy_price"
    attributes = sensor.extra_state_attributes
    assert attributes["tusd"] == 0.47242
    assert attributes["te"] == 0.31696
    assert attributes["tariff"] == 0.78938
    assert attributes["tariff_subgroup"] == "B1"
    assert attributes["tariff_subclass"] == "Residencial"
    assert attributes["tariff_valid_from"] == "2026-07-04"
    assert attributes["tariff_resolution"] == "RESOLUÇÃO HOMOLOGATÓRIA Nº 3.596"
    assert attributes["pis_cofins_rate"] == round(AUGUST_PIS_COFINS_RATE * 100, 4)
    assert attributes["tax_bill_year"] == 2026
    assert attributes["tax_bill_month"] == 8


def test_energy_price_sensor_without_the_catalog(sample_payload):
    sensor = EnelSpEnergyPriceSensor(
        _coordinator(sample_payload, catalog=None), ACTIVE_INSTALLATION
    )
    assert sensor.native_value == pytest.approx(
        (236.81 / 300) / (0.82 * (1 - AUGUST_PIS_COFINS_RATE)), abs=1e-5
    )
    attributes = sensor.extra_state_attributes
    assert attributes["tariff_source"] == "bill"
    assert "tusd" not in attributes
    assert "bandeira_tarifaria" not in attributes


def test_energy_price_sensor_without_a_bill_composition():
    payload = EnelSpPayload(
        account=ACCOUNT,
        installations={
            ACTIVE_INSTALLATION.number: EnelSpInstallationData(
                installation=ACTIVE_INSTALLATION, bills=BILLS
            )
        },
    )
    sensor = EnelSpEnergyPriceSensor(_coordinator(payload), ACTIVE_INSTALLATION)
    assert sensor.native_value is None
    assert "tariff_source" not in sensor.extra_state_attributes


def test_energy_price_sensor_without_installation():
    payload = EnelSpPayload(account=ACCOUNT, installations={})
    sensor = EnelSpEnergyPriceSensor(_coordinator(payload), ACTIVE_INSTALLATION)
    assert sensor.native_value is None
