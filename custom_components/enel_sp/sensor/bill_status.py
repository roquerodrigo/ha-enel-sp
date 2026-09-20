"""Sensor que expõe a situação de pagamento da conta mais recente."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from ..data import EnelSpBillStatus
from ..entity import EnelSpEntity

if TYPE_CHECKING:
    from collections.abc import Mapping


class EnelSpBillStatusSensor(EnelSpEntity, SensorEntity):
    """Indica se a conta mais recente foi paga, está em aberto ou está vencida."""

    _attr_translation_key = "bill_status"
    _attr_device_class = SensorDeviceClass.ENUM

    @property
    def options(self) -> list[str]:
        """Lista todas as situações que o sensor pode reportar."""
        return [status.value for status in EnelSpBillStatus]

    @property
    def unique_id(self) -> str:
        """Retorna um id único derivado da config entry e da instalação."""
        entry_id = self.coordinator.config_entry.entry_id
        return f"{entry_id}_{self._installation.number}_bill_status"

    @property
    def native_value(self) -> str | None:
        """Retorna a situação normalizada da conta mais recente."""
        bill = self.latest_bill
        return None if bill is None else bill.status.value

    @property
    def extra_state_attributes(self) -> Mapping[str, str | int | float]:
        """Acrescenta o texto da situação exatamente como o portal o exibe."""
        attributes: dict[str, str | int | float] = dict(super().extra_state_attributes)
        bill = self.latest_bill
        if bill is not None:
            attributes["portal_status"] = bill.status_text
        return attributes
