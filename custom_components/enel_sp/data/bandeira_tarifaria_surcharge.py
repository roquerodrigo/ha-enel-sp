"""Adicional da bandeira tarifária que a ANEEL acionou em um mês."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date


@dataclass(frozen=True)
class EnelSpBandeiraTarifariaSurcharge:
    """Bandeira acionada no mês e o acréscimo, em BRL/kWh, sobre a tarifa."""

    month: date
    name: str
    rate: float
