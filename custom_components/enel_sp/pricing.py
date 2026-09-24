"""Cálculo do preço da energia de uma instalação."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .data import EnelSpEnergyPrice, EnelSpEnergyPriceSource, EnelSpTaxRates

if TYPE_CHECKING:
    from datetime import date

    from .data import (
        EnelSpAneelTariff,
        EnelSpBill,
        EnelSpBillComposition,
        EnelSpInstallationData,
        EnelSpTariffCatalog,
    )


class EnelSpEnergyPriceCalculator:
    """
    Combina as contas da instalação com o catálogo da ANEEL em um preço por kWh.

    A classe de consumo e as alíquotas saem das contas da própria instalação, e a
    tarifa e a bandeira em vigor saem da ANEEL. Sem catálogo, ou quando nenhuma conta
    fecha com uma tarifa homologada (como na tarifa social, cobrada por faixas), a
    tarifa efetiva da conta mais recente toma o lugar da homologada.
    """

    def __init__(self, catalog: EnelSpTariffCatalog | None) -> None:
        """Inicializa."""
        self._catalog = catalog

    def calculate(
        self, data: EnelSpInstallationData, day: date
    ) -> EnelSpEnergyPrice | None:
        """Retorna o preço do kWh no dia, ou None se as contas não bastam."""
        taxed = _latest_taxed_bill(data)
        if taxed is None:
            return None
        tax_bill, composition, tax_rates = taxed
        tariff = self._aneel_tariff(data, day)
        if tariff is not None:
            tariff_rate = tariff.rate
            source = EnelSpEnergyPriceSource.ANEEL
        else:
            billed_rate = _billed_rate(data)
            if billed_rate is None:
                return None
            tariff_rate = billed_rate
            source = EnelSpEnergyPriceSource.BILL
        return EnelSpEnergyPrice(
            tariff_rate=tariff_rate,
            source=source,
            tariff=tariff,
            bandeira_tarifaria_surcharge=(
                self._catalog.bandeira_tarifaria_surcharge_for(day)
                if self._catalog
                else None
            ),
            tax_rates=tax_rates,
            tax_bill=tax_bill,
            other_items=composition.other_items,
        )

    def _aneel_tariff(
        self, data: EnelSpInstallationData, day: date
    ) -> EnelSpAneelTariff | None:
        """Retorna a tarifa em vigor da classe em que as contas foram faturadas."""
        if self._catalog is None:
            return None
        series = self._catalog.billed_series(data.bills)
        return None if series is None else self._catalog.tariff_for(series, day)


def _latest_taxed_bill(
    data: EnelSpInstallationData,
) -> tuple[EnelSpBill, EnelSpBillComposition, EnelSpTaxRates] | None:
    """Retorna a conta mais recente da qual as alíquotas podem ser deduzidas."""
    for bill in reversed(data.bills):
        composition = data.composition_for(bill)
        if composition is None:
            continue
        tax_rates = EnelSpTaxRates.from_bill(bill, composition)
        if tax_rates is not None:
            return bill, composition, tax_rates
    return None


def _billed_rate(data: EnelSpInstallationData) -> float | None:
    """Retorna a tarifa efetiva, sem tributos, da conta mais recente com consumo."""
    for bill in reversed(data.bills):
        if bill.consumption > 0 and bill.energy_amount > 0:
            return bill.energy_amount / bill.consumption
    return None
