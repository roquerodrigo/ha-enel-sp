"""Sensor que expõe o valor ainda devido na instalação."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from ..const import CURRENCY_BRAZILIAN_REAL
from ..entity import EnelSpEntity


class EnelSpOpenBillsAmountSensor(EnelSpEntity, SensorEntity):
    """Total das contas que aguardam pagamento, incluindo as vencidas."""

    _attr_translation_key = "open_bills_amount"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = CURRENCY_BRAZILIAN_REAL
    _attr_suggested_display_precision = 2

    @property
    def unique_id(self) -> str:
        """Retorna um id único derivado da config entry e da instalação."""
        entry_id = self.coordinator.config_entry.entry_id
        return f"{entry_id}_{self._installation.number}_open_bills_amount"

    @property
    def native_value(self) -> float | None:
        """Retorna o valor ainda devido."""
        data = self.installation_data
        return None if data is None else data.open_amount
