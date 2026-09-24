"""Formato tipado de uma linha ``ET_COMPOSICAO`` do serviço de composição da conta."""

from __future__ import annotations

from typing import TypedDict


class EnelSpCompositionRow(TypedDict, total=False):
    """Parcelas de um mês faturado como o backend SAP as serializa."""

    BILLING_PERIOD: str
    ENERGIA: float | None
    DISTRIBUICAO: float | None
    TRANSMISSAO: float | None
    ENCARGOS: float | None
    PERDAS: float | None
    TRIBUTOS: float | None
    DEMAIS_ITENS: float | None
