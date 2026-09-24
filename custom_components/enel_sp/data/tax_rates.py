"""Alíquotas dos tributos que a Enel cobra por kWh, deduzidas de uma conta."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bill import EnelSpBill
    from .bill_composition import EnelSpBillComposition


@dataclass(frozen=True)
class EnelSpTaxRates:
    """ICMS e PIS/COFINS efetivos, como frações do valor com tributos."""

    icms: float
    pis_cofins: float

    @classmethod
    def from_bill(
        cls, bill: EnelSpBill, composition: EnelSpBillComposition
    ) -> EnelSpTaxRates | None:
        """
        Deduz as alíquotas de uma conta, ou None quando ela não permite.

        O ICMS incide sobre o valor do fornecimento com todos os tributos, e o PIS e
        a COFINS sobre esse mesmo valor sem o ICMS. A conta informa a alíquota de
        ICMS, mas o PIS e a COFINS mudam todo mês e só aparecem somados aos demais
        tributos; descontar o ICMS dos tributos e da base recupera a alíquota deles.
        """
        base_without_icms = composition.supply_amount - bill.icms
        pis_cofins_amount = composition.taxes - bill.icms
        if base_without_icms <= 0 or pis_cofins_amount < 0:
            return None
        return cls(
            icms=bill.icms_rate / 100,
            pis_cofins=pis_cofins_amount / base_without_icms,
        )

    @property
    def gross_up_factor(self) -> float:
        """Retorna o multiplicador que leva um valor sem tributos ao valor cobrado."""
        return 1 / ((1 - self.icms) * (1 - self.pis_cofins))
