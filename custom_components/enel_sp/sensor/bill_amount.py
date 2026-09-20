"""Sensor que expõe o valor da conta mais recente."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.util import dt as dt_util

from ..const import CURRENCY_BRAZILIAN_REAL
from ..entity import EnelSpEntity

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime


class EnelSpBillAmountSensor(EnelSpEntity, SensorEntity):
    """Valor cobrado na conta mais recente que o portal publicou."""

    _attr_translation_key = "bill_amount"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = CURRENCY_BRAZILIAN_REAL
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2

    @property
    def unique_id(self) -> str:
        """Retorna um id único derivado da config entry e da instalação."""
        entry_id = self.coordinator.config_entry.entry_id
        return f"{entry_id}_{self._installation.number}_bill_amount"

    @property
    def native_value(self) -> float | None:
        """Retorna o valor da conta mais recente."""
        bill = self.latest_bill
        return None if bill is None else bill.amount

    @property
    def last_reset(self) -> datetime | None:
        """Ancora o total no início do mês de faturamento."""
        bill = self.latest_bill
        return None if bill is None else dt_util.start_of_local_day(bill.period_start)

    @property
    def extra_state_attributes(self) -> Mapping[str, str | int | float]:
        """Acrescenta os tributos e os juros discriminados no valor."""
        attributes: dict[str, str | int | float] = dict(super().extra_state_attributes)
        bill = self.latest_bill
        if bill is not None:
            attributes["icms"] = bill.icms
            attributes["taxes"] = bill.taxes
            attributes["interest"] = bill.interest
            attributes["days"] = bill.days
        return attributes
