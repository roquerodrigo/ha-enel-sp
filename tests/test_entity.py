from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.enel_sp.const import ATTRIBUTION, DOMAIN
from custom_components.enel_sp.entity import EnelSpEntity

from .conftest import ACTIVE_INSTALLATION, BILLS, INACTIVE_INSTALLATION


def _make_entity(
    installation=ACTIVE_INSTALLATION,
    payload=None,
    entry_id="eid",
    *,
    update_success=True,
) -> EnelSpEntity:
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = entry_id
    coordinator.data = payload
    coordinator.last_update_success = update_success
    return EnelSpEntity(coordinator=coordinator, installation=installation)


def test_attribution():
    assert _make_entity()._attr_attribution == ATTRIBUTION


def test_has_entity_name():
    assert _make_entity()._attr_has_entity_name is True


def test_device_info_identifiers_combine_entry_id_and_installation():
    identifiers = _make_entity(entry_id="my_id").device_info["identifiers"]
    assert identifiers == {(DOMAIN, "my_id_0123456789")}


def test_device_info_is_named_after_the_installation_nickname():
    info = _make_entity().device_info
    assert info["name"] == "Casa"
    assert info["manufacturer"] == "Enel"
    assert info["serial_number"] == "0123456789"


def test_device_info_model_keeps_the_portal_nickname():
    assert _make_entity().device_info["model"] == "Casa"


def test_installation_data_is_none_before_first_refresh():
    assert _make_entity(payload=None).installation_data is None


def test_installation_data_is_none_once_the_portal_drops_it(sample_payload):
    entity = _make_entity(installation=INACTIVE_INSTALLATION, payload=sample_payload)
    assert entity.installation_data is None
    assert entity.latest_bill is None
    assert entity.available is False


def test_installation_data_resolves_from_the_payload(sample_payload):
    entity = _make_entity(payload=sample_payload)
    assert entity.installation_data is sample_payload.installations["0123456789"]
    assert entity.latest_bill == BILLS[-1]
    assert entity.available is True


def test_unavailable_when_last_update_failed(sample_payload):
    assert _make_entity(payload=sample_payload, update_success=False).available is False


def test_extra_state_attributes_describe_the_installation_and_bill(sample_payload):
    assert _make_entity(payload=sample_payload).extra_state_attributes == {
        "installation_number": "0123456789",
        "meter_serial": "12345678",
        "bill_year": 2026,
        "bill_month": 8,
    }


def test_extra_state_attributes_without_bill():
    assert _make_entity(payload=None).extra_state_attributes == {
        "installation_number": "0123456789",
        "meter_serial": "12345678",
    }
