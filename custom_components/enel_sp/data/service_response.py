"""Envelope tipado compartilhado pelos serviços do portal apoiados no SAP."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from .history_row import EnelSpHistoryRow


class EnelSpServiceBody(TypedDict, total=False):
    """Corpo da resposta de um serviço; ``E_RESULT`` vem vazio em caso de sucesso."""

    E_RESULT: str
    E_MSG: str
    DescripcionResultado: str
    ET_HISTORICO: list[EnelSpHistoryRow] | None


class EnelSpServiceResponse(TypedDict, total=False):
    """Envelope de toda resposta de serviço no formato ``Header``/``Body``."""

    Body: EnelSpServiceBody
