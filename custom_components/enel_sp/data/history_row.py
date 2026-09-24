"""Formato tipado de uma linha ``ET_HISTORICO`` do serviço de histórico de consumo."""

from __future__ import annotations

from typing import TypedDict


class EnelSpHistoryRow(TypedDict, total=False):
    """Um mês faturado como o backend SAP o serializa."""

    BILLING_PERIOD: str
    VALOR_TOTAL: float | None
    VALOR_CONSUMO: float | None
    VALOR_DIAS: int | None
    VALOR_CONSUMO_DIA: float | None
    VENCIMENTO: str
    STATUS: str
    VALOR_LEIT_PER1: float | None
    VALOR_ICMS: float | str | None
    VALOR_ICMS_FAT: float | None
    VALOR_DIAS_FAT: float | None
    VALOR_IMPO: float | None
    VALOR_JUROS: float | None
