"""Tudo o que o coordinator guarda para uma instalação."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .bill_status import EnelSpBillStatus

if TYPE_CHECKING:
    from .bill import EnelSpBill
    from .installation import EnelSpInstallation


@dataclass(frozen=True)
class EnelSpInstallationData:
    """Uma instalação com as suas contas, da mais antiga à mais nova."""

    installation: EnelSpInstallation
    bills: tuple[EnelSpBill, ...]

    @property
    def latest_bill(self) -> EnelSpBill | None:
        """Retorna a conta mais recente que o portal publicou, se houver."""
        return self.bills[-1] if self.bills else None

    @property
    def open_bills(self) -> tuple[EnelSpBill, ...]:
        """Retorna as contas que ainda aguardam pagamento, incluindo as vencidas."""
        return tuple(
            bill for bill in self.bills if bill.status is not EnelSpBillStatus.PAID
        )

    @property
    def open_amount(self) -> float:
        """Retorna o valor total das contas que aguardam pagamento."""
        return round(sum(bill.amount for bill in self.open_bills), 2)
