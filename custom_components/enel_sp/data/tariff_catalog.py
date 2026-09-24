"""Tarifas e bandeiras da Enel São Paulo publicadas pela ANEEL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import date

    from . import EnelSpTariffSeries
    from .aneel_tariff import EnelSpAneelTariff
    from .bandeira_tarifaria_surcharge import EnelSpBandeiraTarifariaSurcharge
    from .bill import EnelSpBill

BILLED_AMOUNT_TOLERANCE = 0.05


@dataclass(frozen=True)
class EnelSpTariffCatalog:
    """Tarifas de aplicação das classes de baixa tensão e os adicionais de bandeira."""

    tariffs: tuple[EnelSpAneelTariff, ...]
    bandeira_tarifaria_surcharges: tuple[EnelSpBandeiraTarifariaSurcharge, ...]

    def billed_series(self, bills: Iterable[EnelSpBill]) -> EnelSpTariffSeries | None:
        """
        Descobre a classe de consumo cuja tarifa a Enel aplicou nas contas.

        A conta não informa a classe, mas o valor da energia sem tributos é o consumo
        vezes a tarifa de aplicação. A conta mais recente que fecha com uma tarifa
        homologada revela a classe; contas que atravessam um reajuste misturam duas
        tarifas e não fecham com nenhuma, então são puladas. Quando classes diferentes
        têm a mesma tarifa, a subclasse padrão vence a de benefício tarifário.
        """
        for bill in sorted(
            bills, key=lambda bill: (bill.year, bill.month), reverse=True
        ):
            if bill.consumption <= 0 or bill.energy_amount <= 0:
                continue
            matches = [
                tariff
                for tariff in self.tariffs
                if abs(tariff.rate * bill.consumption - bill.energy_amount)
                <= BILLED_AMOUNT_TOLERANCE
            ]
            if matches:
                return min(
                    matches,
                    key=lambda tariff: (not tariff.is_base_subclass, tariff.series),
                ).series
        return None

    def tariff_for(
        self, series: EnelSpTariffSeries, day: date
    ) -> EnelSpAneelTariff | None:
        """Retorna a tarifa da classe em vigor no dia, ou a vigência mais recente."""
        tariffs = sorted(
            (
                tariff
                for tariff in self.tariffs
                if tariff.series == series and tariff.valid_from <= day
            ),
            key=lambda tariff: tariff.valid_from,
            reverse=True,
        )
        current = next((tariff for tariff in tariffs if tariff.is_valid_on(day)), None)
        return current or next(iter(tariffs), None)

    def bandeira_tarifaria_surcharge_for(
        self, day: date
    ) -> EnelSpBandeiraTarifariaSurcharge | None:
        """Retorna a bandeira do mês do dia, ou a mais recente já publicada."""
        published = sorted(
            (
                surcharge
                for surcharge in self.bandeira_tarifaria_surcharges
                if surcharge.month <= day
            ),
            key=lambda surcharge: surcharge.month,
            reverse=True,
        )
        return next(iter(published), None)
