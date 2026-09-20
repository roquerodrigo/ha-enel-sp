"""O que o cliente da API guarda de uma troca HTTP."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EnelSpHttpResponse:
    """Status, URL final após os redirecionamentos e corpo de uma resposta."""

    status: int
    url: str
    text: str
