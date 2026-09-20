"""Situação de pagamento normalizada de uma conta."""

from __future__ import annotations

from enum import StrEnum


class EnelSpBillStatus(StrEnum):
    """Indica se uma conta foi paga, aguarda pagamento ou está vencida."""

    PAID = "paid"
    OPEN = "open"
    OVERDUE = "overdue"
    UNKNOWN = "unknown"
