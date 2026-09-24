"""Formato tipado de nível superior de async_get_config_entry_diagnostics."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from . import JsonObject
    from .diagnostics_entry import EnelSpDiagnosticsEntry


class EnelSpDiagnosticsPayload(TypedDict):
    """Formato de nível superior retornado por async_get_config_entry_diagnostics."""

    entry: EnelSpDiagnosticsEntry
    coordinator_data: JsonObject | None
    tariff_data: JsonObject | None
