"""Sensor que expõe a leitura do medidor feita para a conta mais recente."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy

from ..entity import EnelSpEntity


class EnelSpMeterReadingSensor(EnelSpEntity, SensorEntity):
    """Valor do contador lido no medidor para a conta mais recente."""

    _attr_translation_key = "meter_reading"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 0

    @property
    def unique_id(self) -> str:
        """Retorna um id único derivado da config entry e da instalação."""
        entry_id = self.coordinator.config_entry.entry_id
        return f"{entry_id}_{self._installation.number}_meter_reading"

    @property
    def native_value(self) -> float | None:
        """Retorna a leitura do medidor da conta mais recente."""
        bill = self.latest_bill
        return None if bill is None else bill.meter_reading
