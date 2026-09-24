"""Tarifa homologada pela ANEEL para uma classe de consumo da Enel São Paulo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from . import EnelSpTariffSeries

NOT_APPLICABLE = "Não se aplica"


@dataclass(frozen=True)
class EnelSpAneelTariff:
    """TUSD e TE sem tributos, em BRL/kWh, de uma classe durante uma vigência."""

    subgroup: str
    consumer_class: str
    subclass: str
    distribution_rate: float
    energy_rate: float
    valid_from: date
    valid_until: date
    resolution: str

    @property
    def rate(self) -> float:
        """Retorna a tarifa de aplicação: a soma da TUSD com a TE."""
        return self.distribution_rate + self.energy_rate

    @property
    def series(self) -> EnelSpTariffSeries:
        """Identifica a classe de consumo, que atravessa as vigências."""
        return (self.subgroup, self.consumer_class, self.subclass)

    @property
    def is_base_subclass(self) -> bool:
        """Informa se é a subclasse padrão da classe, sem benefício tarifário."""
        return self.subclass in (NOT_APPLICABLE, self.consumer_class)

    def is_valid_on(self, day: date) -> bool:
        """Informa se a tarifa está em vigor no dia."""
        return self.valid_from <= day <= self.valid_until
