"""Sensor que expõe quantas contas aguardam pagamento."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass

from ..entity import EnelSpEntity


class EnelSpOpenBillsCountSensor(EnelSpEntity, SensorEntity):
    """Número de contas que aguardam pagamento, incluindo as vencidas."""

    _attr_translation_key = "open_bills_count"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        """Retorna um id único derivado da config entry e da instalação."""
        entry_id = self.coordinator.config_entry.entry_id
        return f"{entry_id}_{self._installation.number}_open_bills_count"

    @property
    def native_value(self) -> int | None:
        """Retorna o número de contas que aguardam pagamento."""
        data = self.installation_data
        return None if data is None else len(data.open_bills)
