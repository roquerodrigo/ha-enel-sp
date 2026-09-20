"""Sensor que expõe o vencimento da conta mais recente."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.util import dt as dt_util

from ..entity import EnelSpEntity

if TYPE_CHECKING:
    from datetime import datetime


class EnelSpBillDueDateSensor(EnelSpEntity, SensorEntity):
    """
    Vencimento da conta mais recente que o portal publicou.

    Reportado como um timestamp à meia-noite local, e não como uma data simples, para
    que o front-end mostre quanto tempo falta, como faz com outros prazos.
    """

    _attr_translation_key = "bill_due_date"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def unique_id(self) -> str:
        """Retorna um id único derivado da config entry e da instalação."""
        entry_id = self.coordinator.config_entry.entry_id
        return f"{entry_id}_{self._installation.number}_bill_due_date"

    @property
    def native_value(self) -> datetime | None:
        """Retorna o vencimento da conta mais recente à meia-noite local."""
        bill = self.latest_bill
        if bill is None or bill.due_date is None:
            return None
        return dt_util.start_of_local_day(bill.due_date)
