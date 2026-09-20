from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from custom_components.enel_sp.data import (
    EnelSpBillStatus,
    EnelSpInstallationData,
    EnelSpTariffFlag,
)

from .conftest import ACTIVE_INSTALLATION, BILLS, INACTIVE_INSTALLATION, make_bill


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
