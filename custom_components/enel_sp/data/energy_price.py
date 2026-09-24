"""Preço da energia por kWh, com o adicional de bandeira e os tributos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .aneel_tariff import EnelSpAneelTariff
    from .bandeira_tarifaria_surcharge import EnelSpBandeiraTarifariaSurcharge
    from .bill import EnelSpBill
    from .energy_price_source import EnelSpEnergyPriceSource
    from .tax_rates import EnelSpTaxRates


@dataclass(frozen=True)
class EnelSpEnergyPrice:
    """
    Quanto custa cada kWh consumido agora, em BRL.

    ``tariff`` só existe quando a tarifa veio da ANEEL; sem ela, ``tariff_rate`` é a
    tarifa efetiva da conta mais recente. ``tax_bill`` é a conta de onde vieram as
    alíquotas, e os itens dela que não são cobrados por kWh ficam fora do preço.
    """

    tariff_rate: float
    source: EnelSpEnergyPriceSource
    tariff: EnelSpAneelTariff | None
    bandeira_tarifaria_surcharge: EnelSpBandeiraTarifariaSurcharge | None
    tax_rates: EnelSpTaxRates
    tax_bill: EnelSpBill
    other_items: float

    @property
    def rate_before_taxes(self) -> float:
        """Retorna a tarifa somada ao adicional de bandeira, sem tributos."""
        surcharge = (
            self.bandeira_tarifaria_surcharge.rate
            if self.bandeira_tarifaria_surcharge
            else 0.0
        )
        return self.tariff_rate + surcharge

    @property
    def price(self) -> float:
        """Retorna o preço do kWh com ICMS, PIS e COFINS."""
        return self.rate_before_taxes * self.tax_rates.gross_up_factor
