"""Bandeira tarifária em vigor para a conta do cliente."""

from __future__ import annotations

from enum import StrEnum


class EnelSpTariffFlag(StrEnum):
    """Nível de cobrança extra que a ANEEL aplica ao consumo do mês."""

    GREEN = "green"
    YELLOW = "yellow"
    RED_LEVEL_1 = "red_level_1"
    RED_LEVEL_2 = "red_level_2"
    UNKNOWN = "unknown"

    @classmethod
    def from_portal(cls, value: str) -> EnelSpTariffFlag:
        """Mapeia o código em português do portal para o enum."""
        return _FLAGS_BY_PORTAL_CODE.get(value.strip().upper(), cls.UNKNOWN)


_FLAGS_BY_PORTAL_CODE = {
    "VERDE": EnelSpTariffFlag.GREEN,
    "AMARELA": EnelSpTariffFlag.YELLOW,
    "VERMELHA": EnelSpTariffFlag.RED_LEVEL_1,
    "VERMELHA1": EnelSpTariffFlag.RED_LEVEL_1,
    "VERMELHA2": EnelSpTariffFlag.RED_LEVEL_2,
}
