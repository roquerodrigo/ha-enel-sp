from __future__ import annotations

from dataclasses import replace

from custom_components.enel_sp.const import DOMAIN
from custom_components.enel_sp.snapshot_store import (
    STORAGE_VERSION,
    EnelSpSnapshotStore,
)

from .conftest import ACTIVE_INSTALLATION


async def test_load_returns_none_without_a_saved_payload(hass):
    assert await EnelSpSnapshotStore(hass, "eid").async_load() is None


async def test_saved_payload_round_trips(hass, sample_payload):
    await EnelSpSnapshotStore(hass, "eid").async_save(sample_payload)
    assert await EnelSpSnapshotStore(hass, "eid").async_load() == sample_payload


async def test_bill_without_due_date_round_trips(hass, sample_payload):
    data = sample_payload.installations[ACTIVE_INSTALLATION.number]
    payload = replace(
        sample_payload,
        installations={
            ACTIVE_INSTALLATION.number: replace(
                data, bills=(replace(data.bills[0], due_date=None),)
            )
        },
    )
    await EnelSpSnapshotStore(hass, "eid").async_save(payload)
    assert await EnelSpSnapshotStore(hass, "eid").async_load() == payload


async def test_payload_is_saved_per_entry(hass, hass_storage, sample_payload):
    await EnelSpSnapshotStore(hass, "eid").async_save(sample_payload)
    assert f"{DOMAIN}.eid" in hass_storage
    assert await EnelSpSnapshotStore(hass, "other").async_load() is None


async def test_unreadable_payload_is_ignored(hass, hass_storage, caplog):
    hass_storage[f"{DOMAIN}.eid"] = {
        "version": STORAGE_VERSION,
        "key": f"{DOMAIN}.eid",
        "data": {"account": {}},
    }
    assert await EnelSpSnapshotStore(hass, "eid").async_load() is None
    assert "Failed to restore the saved portal data" in caplog.text


async def test_remove_deletes_the_saved_payload(hass, hass_storage, sample_payload):
    store = EnelSpSnapshotStore(hass, "eid")
    await store.async_save(sample_payload)
    await store.async_remove()
    assert f"{DOMAIN}.eid" not in hass_storage
