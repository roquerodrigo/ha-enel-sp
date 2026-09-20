"""Sensor que expõe a bandeira tarifária em vigor para a conta do cliente."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from ..data import EnelSpTariffFlag
from ..entity import EnelSpEntity


class EnelSpTariffFlagSensor(EnelSpEntity, SensorEntity):
    """Bandeira tarifária que a ANEEL aplica neste mês."""

    _attr_translation_key = "tariff_flag"
    _attr_device_class = SensorDeviceClass.ENUM

    @property
    def options(self) -> list[str]:
        """Lista todas as bandeiras que o sensor pode reportar."""
        return [flag.value for flag in EnelSpTariffFlag]

    @property
    def unique_id(self) -> str:
        """Retorna um id único derivado da config entry e da instalação."""
        entry_id = self.coordinator.config_entry.entry_id
        return f"{entry_id}_{self._installation.number}_tariff_flag"

    @property
    def native_value(self) -> str | None:
        """Retorna a bandeira tarifária da conta do cliente."""
        payload = self.payload
        return None if payload is None else payload.account.tariff_flag.value
