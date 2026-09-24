from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from custom_components.enel_sp.data import (
    EnelSpBillComposition,
    EnelSpEnergyPriceSource,
    EnelSpInstallationData,
    EnelSpTariffCatalog,
    EnelSpTaxRates,
)
from custom_components.enel_sp.pricing import EnelSpEnergyPriceCalculator

from .conftest import (
    ACTIVE_INSTALLATION,
    AUGUST_COMPOSITION,
    AUGUST_PIS_COFINS_RATE,
    BILLS,
    CATALOG,
    COMPOSITIONS,
    CURRENT_RESIDENTIAL_TARIFF,
    SEPTEMBER_BANDEIRA_TARIFARIA,
    make_bill,
)

TODAY = date(2026, 9, 24)


def _data(bills=BILLS, compositions=COMPOSITIONS) -> EnelSpInstallationData:
    return EnelSpInstallationData(
        installation=ACTIVE_INSTALLATION, bills=bills, compositions=compositions
    )


def test_price_uses_the_current_aneel_tariff_of_the_billed_class():
    price = EnelSpEnergyPriceCalculator(CATALOG).calculate(_data(), TODAY)
    assert price is not None
    assert price.source is EnelSpEnergyPriceSource.ANEEL
    assert price.tariff == CURRENT_RESIDENTIAL_TARIFF
    assert price.tariff_rate == pytest.approx(0.78938)
    assert price.bandeira_tarifaria_surcharge == SEPTEMBER_BANDEIRA_TARIFARIA
    assert price.rate_before_taxes == pytest.approx(0.78938 + 0.04463)


def test_price_grosses_up_icms_and_pis_cofins():
    price = EnelSpEnergyPriceCalculator(CATALOG).calculate(_data(), TODAY)
    assert price is not None
    assert price.tax_rates.icms == pytest.approx(0.18)
    assert price.tax_rates.pis_cofins == pytest.approx(AUGUST_PIS_COFINS_RATE)
    expected = (0.78938 + 0.04463) / (0.82 * (1 - AUGUST_PIS_COFINS_RATE))
    assert price.price == pytest.approx(expected)
    assert price.tax_bill == BILLS[-1]
    assert price.other_items == 9.39


def test_price_follows_a_new_tariff_before_any_bill_reflects_it():
    next_tariff = replace(
        CURRENT_RESIDENTIAL_TARIFF,
        distribution_rate=0.5,
        energy_rate=0.35,
        valid_from=date(2027, 7, 4),
        valid_until=date(2028, 7, 3),
    )
    catalog = replace(CATALOG, tariffs=(*CATALOG.tariffs, next_tariff))
    price = EnelSpEnergyPriceCalculator(catalog).calculate(_data(), date(2027, 7, 10))
    assert price is not None
    assert price.tariff == next_tariff


def test_price_uses_the_billed_rate_without_the_catalog():
    price = EnelSpEnergyPriceCalculator(None).calculate(_data(), TODAY)
    assert price is not None
    assert price.source is EnelSpEnergyPriceSource.BILL
    assert price.tariff is None
    assert price.bandeira_tarifaria_surcharge is None
    assert price.tariff_rate == pytest.approx(236.81 / 300)


def test_price_uses_the_billed_rate_when_no_bill_matches_a_tariff():
    bills = tuple(
        replace(bill, energy_amount=round(bill.consumption * 0.61, 2)) for bill in BILLS
    )
    price = EnelSpEnergyPriceCalculator(CATALOG).calculate(_data(bills=bills), TODAY)
    assert price is not None
    assert price.source is EnelSpEnergyPriceSource.BILL
    assert price.tariff_rate == pytest.approx(0.61)
    assert price.bandeira_tarifaria_surcharge == SEPTEMBER_BANDEIRA_TARIFARIA


def test_price_takes_the_taxes_from_the_latest_bill_that_allows_it():
    july = EnelSpBillComposition(
        year=2026,
        month=7,
        energy=100.0,
        distribution=100.0,
        transmission=30.0,
        sector_charges=60.0,
        losses=20.0,
        taxes=100.0,
        other_items=17.17,
    )
    august_without_taxes = replace(AUGUST_COMPOSITION, taxes=0.0)
    price = EnelSpEnergyPriceCalculator(CATALOG).calculate(
        _data(compositions=(july, august_without_taxes)), TODAY
    )
    assert price is not None
    assert price.tax_bill == BILLS[1]
    assert price.other_items == 17.17


def test_price_needs_a_bill_composition():
    assert (
        EnelSpEnergyPriceCalculator(CATALOG).calculate(_data(compositions=()), TODAY)
        is None
    )


def test_price_needs_a_billed_rate_when_no_tariff_matches():
    bills = (replace(BILLS[-1], consumption=0, energy_amount=0.0),)
    catalog = EnelSpTariffCatalog(tariffs=(), bandeira_tarifaria_surcharges=())
    assert (
        EnelSpEnergyPriceCalculator(catalog).calculate(_data(bills=bills), TODAY)
        is None
    )


def test_tax_rates_match_a_real_bill():
    bill = replace(make_bill(2026, 7, 441.06, 415, 0), icms=76.29, icms_rate=18.0)
    composition = EnelSpBillComposition(
        year=2026,
        month=7,
        energy=116.11,
        distribution=87.24,
        transmission=25.40,
        sector_charges=81.09,
        losses=19.89,
        taxes=94.16,
        other_items=17.17,
    )
    tax_rates = EnelSpTaxRates.from_bill(bill, composition)
    assert tax_rates is not None
    assert composition.supply_amount == 423.89
    assert tax_rates.pis_cofins == pytest.approx(17.87 / 347.60)
    assert 415 * (0.46394 + 0.31182) * tax_rates.gross_up_factor == pytest.approx(
        413.87, abs=0.05
    )
