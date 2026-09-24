"""Composição do valor de uma conta mensal, como a Enel a discrimina."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EnelSpBillComposition:
    """
    Parcelas em BRL que somam o valor de uma conta.

    ``taxes`` reúne o ICMS, o PIS e a COFINS; ``other_items`` reúne o que não é
    cobrado por kWh, como a contribuição de iluminação pública, créditos e ajustes.
    """

    year: int
    month: int
    energy: float
    distribution: float
    transmission: float
    sector_charges: float
    losses: float
    taxes: float
    other_items: float

    @property
    def supply_amount(self) -> float:
        """Retorna o valor do fornecimento, com os tributos que incidem nele."""
        return round(
            self.energy
            + self.distribution
            + self.transmission
            + self.sector_charges
            + self.losses
            + self.taxes,
            2,
        )
