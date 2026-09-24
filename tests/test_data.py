from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from custom_components.enel_sp.data import (
    EnelSpBillStatus,
    EnelSpInstallationData,
    EnelSpTariffFlag,
    EnelSpTaxRates,
)

from .conftest import (
    ACTIVE_INSTALLATION,
    AUGUST_BANDEIRA_TARIFARIA,
    AUGUST_COMPOSITION,
    BILLS,
    CATALOG,
    COMPOSITIONS,
    CURRENT_RESIDENTIAL_TARIFF,
    CURRENT_SOCIAL_DISCOUNT_TARIFF,
    INACTIVE_INSTALLATION,
    PREVIOUS_RESIDENTIAL_TARIFF,
    RESIDENTIAL_SERIES,
    SEPTEMBER_BANDEIRA_TARIFARIA,
    make_bill,
)


def test_active_installation_has_an_open_ended_move_out():
    assert ACTIVE_INSTALLATION.active is True
    assert replace(ACTIVE_INSTALLATION, move_out="").active is True


def test_inactive_installation_has_a_past_move_out():
    assert INACTIVE_INSTALLATION.active is False


def test_installation_name_falls_back_to_the_number():
    assert replace(ACTIVE_INSTALLATION, nickname="").name == "0123456789"


def test_bill_period_start_is_the_first_day_of_the_month():
    assert BILLS[-1].period_start == date(2026, 8, 1)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Paga", EnelSpBillStatus.PAID),
        ("PAGA", EnelSpBillStatus.PAID),
        ("Em aberto", EnelSpBillStatus.OPEN),
        ("Pendente", EnelSpBillStatus.OPEN),
        ("Vencida", EnelSpBillStatus.OVERDUE),
        ("Em atraso", EnelSpBillStatus.OVERDUE),
        ("", EnelSpBillStatus.UNKNOWN),
        ("Negociada", EnelSpBillStatus.UNKNOWN),
    ],
)
def test_bill_status_is_classified_from_the_portal_text(text, expected):
    assert replace(BILLS[-1], status_text=text).status is expected


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("VERDE", EnelSpTariffFlag.GREEN),
        ("AMARELA", EnelSpTariffFlag.YELLOW),
        ("VERMELHA", EnelSpTariffFlag.RED_LEVEL_1),
        ("VERMELHA1", EnelSpTariffFlag.RED_LEVEL_1),
        ("VERMELHA2", EnelSpTariffFlag.RED_LEVEL_2),
        (" amarela ", EnelSpTariffFlag.YELLOW),
        ("", EnelSpTariffFlag.UNKNOWN),
        ("AZUL", EnelSpTariffFlag.UNKNOWN),
    ],
)
def test_tariff_flag_is_mapped_from_the_portal_code(code, expected):
    assert EnelSpTariffFlag.from_portal(code) is expected


def test_installation_data_latest_bill_is_the_last_one():
    data = EnelSpInstallationData(installation=ACTIVE_INSTALLATION, bills=BILLS)
    assert data.latest_bill == BILLS[-1]
    assert data.open_bills == ()
    assert data.open_amount == 0.0


def test_installation_data_without_bills():
    data = EnelSpInstallationData(installation=ACTIVE_INSTALLATION, bills=())
    assert data.latest_bill is None
    assert data.open_amount == 0.0


def test_installation_data_sums_the_unpaid_bills():
    open_bill = replace(make_bill(2026, 8, 290.70, 300, 4600), status_text="Em aberto")
    overdue_bill = replace(make_bill(2026, 7, 420.80, 400, 4300), status_text="Vencida")
    data = EnelSpInstallationData(
        installation=ACTIVE_INSTALLATION, bills=(BILLS[0], overdue_bill, open_bill)
    )
    assert data.open_bills == (overdue_bill, open_bill)
    assert data.open_amount == 711.50


def test_catalog_finds_the_class_of_the_latest_bill_with_a_single_tariff():
    assert CATALOG.billed_series(BILLS) == RESIDENTIAL_SERIES


def test_catalog_prefers_the_base_subclass_among_equal_tariffs():
    catalog = replace(CATALOG, tariffs=(CURRENT_SOCIAL_DISCOUNT_TARIFF,))
    assert catalog.billed_series(BILLS[-1:]) == CURRENT_SOCIAL_DISCOUNT_TARIFF.series
    assert CATALOG.billed_series(BILLS[-1:]) == RESIDENTIAL_SERIES


def test_catalog_skips_bills_that_mix_two_tariffs():
    assert CATALOG.billed_series(BILLS[1:2]) is None
    assert CATALOG.billed_series(BILLS[:2]) == RESIDENTIAL_SERIES


def test_catalog_skips_bills_without_consumption():
    empty_bill = replace(BILLS[-1], consumption=0, energy_amount=0.0)
    assert CATALOG.billed_series((empty_bill,)) is None


def test_catalog_returns_the_tariff_in_force_on_the_day():
    assert (
        CATALOG.tariff_for(RESIDENTIAL_SERIES, date(2026, 7, 3))
        == PREVIOUS_RESIDENTIAL_TARIFF
    )
    assert (
        CATALOG.tariff_for(RESIDENTIAL_SERIES, date(2026, 7, 4))
        == CURRENT_RESIDENTIAL_TARIFF
    )


def test_catalog_keeps_the_latest_tariff_after_it_expires():
    assert (
        CATALOG.tariff_for(RESIDENTIAL_SERIES, date(2027, 8, 1))
        == CURRENT_RESIDENTIAL_TARIFF
    )


def test_catalog_has_no_tariff_before_the_first_one():
    assert CATALOG.tariff_for(RESIDENTIAL_SERIES, date(2025, 1, 1)) is None
    assert CATALOG.tariff_for(("B3", "x", "y"), date(2026, 9, 1)) is None


def test_catalog_returns_the_bandeira_tarifaria_of_the_month():
    assert (
        CATALOG.bandeira_tarifaria_surcharge_for(date(2026, 8, 31))
        == AUGUST_BANDEIRA_TARIFARIA
    )
    assert (
        CATALOG.bandeira_tarifaria_surcharge_for(date(2026, 10, 15))
        == SEPTEMBER_BANDEIRA_TARIFARIA
    )
    assert CATALOG.bandeira_tarifaria_surcharge_for(date(2026, 7, 31)) is None


def test_tariff_knows_its_base_subclass():
    assert CURRENT_RESIDENTIAL_TARIFF.is_base_subclass
    assert not CURRENT_SOCIAL_DISCOUNT_TARIFF.is_base_subclass
    assert replace(
        CURRENT_RESIDENTIAL_TARIFF, subclass="Não se aplica"
    ).is_base_subclass


def test_installation_data_finds_the_composition_of_a_bill():
    data = EnelSpInstallationData(
        installation=ACTIVE_INSTALLATION, bills=BILLS, compositions=COMPOSITIONS
    )
    assert data.composition_for(BILLS[-1]) == AUGUST_COMPOSITION
    assert data.composition_for(BILLS[0]) is None


def test_tax_rates_are_undefined_without_a_taxable_base():
    assert (
        EnelSpTaxRates.from_bill(
            replace(BILLS[-1], icms=AUGUST_COMPOSITION.supply_amount),
            AUGUST_COMPOSITION,
        )
        is None
    )
    assert (
        EnelSpTaxRates.from_bill(BILLS[-1], replace(AUGUST_COMPOSITION, taxes=0.0))
        is None
    )


def test_tax_rates_without_icms():
    composition = replace(AUGUST_COMPOSITION, taxes=10.0)
    tax_rates = EnelSpTaxRates.from_bill(
        replace(BILLS[-1], icms=0.0, icms_rate=0.0), composition
    )
    assert tax_rates is not None
    assert tax_rates.icms == 0.0
    assert tax_rates.gross_up_factor == pytest.approx(
        1 / (1 - 10.0 / composition.supply_amount)
    )
