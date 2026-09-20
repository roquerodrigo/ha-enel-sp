"""Uma conta mensal de energia elétrica de uma instalação."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .bill_status import EnelSpBillStatus

_PAID_MARKERS = ("pag",)
_OVERDUE_MARKERS = ("venc", "atras")
_OPEN_MARKERS = ("abert", "pend", "emit")


@dataclass(frozen=True)
class EnelSpBill:
    """Conta de um mês de faturamento, com valores em BRL e energia em kWh."""

    year: int
    month: int
    amount: float
    consumption: float
    days: int
    daily_consumption: float
    due_date: date | None
    status_text: str
    meter_reading: float
    icms: float
    taxes: float
    interest: float

    @property
    def period_start(self) -> date:
        """Retorna o primeiro dia do mês de faturamento."""
        return date(self.year, self.month, 1)

    @property
    def status(self) -> EnelSpBillStatus:
        """
        Classifica a situação em texto livre do portal.

        O portal retorna rótulos em português como ``Paga``; casar pelos radicais das
        palavras mantém o mapeamento tolerante a variantes como ``Em aberto`` ou
        ``Vencida``, enquanto qualquer texto desconhecido cai em ``UNKNOWN``.
        """
        text = self.status_text.casefold()
        if any(marker in text for marker in _PAID_MARKERS):
            return EnelSpBillStatus.PAID
        if any(marker in text for marker in _OVERDUE_MARKERS):
            return EnelSpBillStatus.OVERDUE
        if any(marker in text for marker in _OPEN_MARKERS):
            return EnelSpBillStatus.OPEN
        return EnelSpBillStatus.UNKNOWN
