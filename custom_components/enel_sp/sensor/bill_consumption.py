"""Sensor que expõe a energia faturada na conta mais recente."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.util import dt as dt_util

from ..entity import EnelSpEntity

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime


class EnelSpBillConsumptionSensor(EnelSpEntity, SensorEntity):
    """Energia consumida no mês de faturamento mais recente."""

    _attr_translation_key = "bill_consumption"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 0

    @property
    def unique_id(self) -> str:
        """Retorna um id único derivado da config entry e da instalação."""
        entry_id = self.coordinator.config_entry.entry_id
        return f"{entry_id}_{self._installation.number}_bill_consumption"

    @property
    def native_value(self) -> float | None:
        """Retorna a energia faturada na conta mais recente."""
        bill = self.latest_bill
        return None if bill is None else bill.consumption

    @property
    def last_reset(self) -> datetime | None:
        """Ancora o total no início do mês de faturamento."""
        bill = self.latest_bill
        return None if bill is None else dt_util.start_of_local_day(bill.period_start)

    @property
    def extra_state_attributes(self) -> Mapping[str, str | int | float]:
        """Acrescenta a duração do período de faturamento e a média diária."""
        attributes: dict[str, str | int | float] = dict(super().extra_state_attributes)
        bill = self.latest_bill
        if bill is not None:
            attributes["days"] = bill.days
            attributes["daily_average"] = bill.daily_consumption
        return attributes
