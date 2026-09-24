"""Origem da tarifa usada no preço da energia."""

from __future__ import annotations

from enum import StrEnum


class EnelSpEnergyPriceSource(StrEnum):
    """De onde veio a tarifa sem tributos do preço."""

    ANEEL = "aneel"
    BILL = "bill"
