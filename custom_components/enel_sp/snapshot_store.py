"""Último payload do portal guardado em disco, para o setup não esperar pelo portal."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import TYPE_CHECKING, TypedDict, cast

from homeassistant.helpers.storage import Store

from .const import DOMAIN, LOGGER
from .data import (
    EnelSpAccount,
    EnelSpBill,
    EnelSpBillComposition,
    EnelSpInstallation,
    EnelSpInstallationData,
    EnelSpPayload,
    EnelSpTariffFlag,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

STORAGE_VERSION = 1


class _StoredInstallation(TypedDict):
    number: str
    nickname: str
    address: str
    partner: str
    contract: str
    contract_account: str
    voltage_level: str
    meter_serial: str
    move_in: str
    move_out: str


class _StoredBill(TypedDict):
    year: int
    month: int
    amount: float
    consumption: float
    days: int
    daily_consumption: float
    due_date: str | None
    status_text: str
    meter_reading: float
    icms: float
    icms_rate: float
    energy_amount: float
    taxes: float
    interest: float


class _StoredComposition(TypedDict):
    year: int
    month: int
    energy: float
    distribution: float
    transmission: float
    sector_charges: float
    losses: float
    taxes: float
    other_items: float


class _StoredInstallationData(TypedDict):
    installation: _StoredInstallation
    bills: list[_StoredBill]
    compositions: list[_StoredComposition]


class _StoredAccount(TypedDict):
    enel_id: str
    name: str
    tariff_flag: str
    installations: list[_StoredInstallation]


class _StoredPayload(TypedDict):
    account: _StoredAccount
    installations: list[_StoredInstallationData]


class EnelSpSnapshotStore:
    """
    Guarda o último payload que o portal entregou para uma config entry.

    O portal leva mais de dez segundos para responder ao login e às consultas, e as
    contas só mudam uma vez por mês; com o payload salvo, o setup cria as entidades na
    hora e o portal é consultado em segundo plano.
    """

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Inicializa."""
        self._store: Store[_StoredPayload] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}"
        )

    async def async_load(self) -> EnelSpPayload | None:
        """Retorna o payload salvo, ou None se não houver um legível."""
        stored = await self._store.async_load()
        if stored is None:
            return None
        try:
            return _payload_from_stored(stored)
        except (KeyError, TypeError, ValueError) as exception:
            LOGGER.warning("Failed to restore the saved portal data: %s", exception)
            return None

    async def async_save(self, payload: EnelSpPayload) -> None:
        """Substitui o payload salvo."""
        await self._store.async_save(_stored_from_payload(payload))

    async def async_remove(self) -> None:
        """Apaga o payload salvo."""
        await self._store.async_remove()


def _stored_from_payload(payload: EnelSpPayload) -> _StoredPayload:
    return {
        "account": {
            "enel_id": payload.account.enel_id,
            "name": payload.account.name,
            "tariff_flag": payload.account.tariff_flag.value,
            "installations": [
                _stored_from_installation(installation)
                for installation in payload.account.installations
            ],
        },
        "installations": [
            {
                "installation": _stored_from_installation(data.installation),
                "bills": [_stored_from_bill(bill) for bill in data.bills],
                "compositions": [
                    cast("_StoredComposition", asdict(composition))
                    for composition in data.compositions
                ],
            }
            for data in payload.installations.values()
        ],
    }


def _stored_from_installation(installation: EnelSpInstallation) -> _StoredInstallation:
    return cast("_StoredInstallation", asdict(installation))


def _stored_from_bill(bill: EnelSpBill) -> _StoredBill:
    stored = cast("_StoredBill", asdict(bill))
    stored["due_date"] = bill.due_date.isoformat() if bill.due_date else None
    return stored


def _payload_from_stored(stored: _StoredPayload) -> EnelSpPayload:
    account = stored["account"]
    installations = (
        EnelSpInstallationData(
            installation=EnelSpInstallation(**data["installation"]),
            bills=tuple(_bill_from_stored(bill) for bill in data["bills"]),
            compositions=tuple(
                EnelSpBillComposition(**composition)
                for composition in data["compositions"]
            ),
        )
        for data in stored["installations"]
    )
    return EnelSpPayload(
        account=EnelSpAccount(
            enel_id=account["enel_id"],
            name=account["name"],
            tariff_flag=EnelSpTariffFlag(account["tariff_flag"]),
            installations=tuple(
                EnelSpInstallation(**installation)
                for installation in account["installations"]
            ),
        ),
        installations={data.installation.number: data for data in installations},
    )


def _bill_from_stored(stored: _StoredBill) -> EnelSpBill:
    due_date = stored["due_date"]
    return EnelSpBill(
        year=stored["year"],
        month=stored["month"],
        amount=stored["amount"],
        consumption=stored["consumption"],
        days=stored["days"],
        daily_consumption=stored["daily_consumption"],
        due_date=date.fromisoformat(due_date) if due_date else None,
        status_text=stored["status_text"],
        meter_reading=stored["meter_reading"],
        icms=stored["icms"],
        icms_rate=stored["icms_rate"],
        energy_amount=stored["energy_amount"],
        taxes=stored["taxes"],
        interest=stored["interest"],
    )
