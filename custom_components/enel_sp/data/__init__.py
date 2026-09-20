"""Tipos próprios do enel_sp."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from .account import EnelSpAccount
from .bill import EnelSpBill
from .bill_status import EnelSpBillStatus
from .config_data import EnelSpConfigData
from .current_user import EnelSpCurrentUser, EnelSpCurrentUserResponse
from .diagnostics_entry import EnelSpDiagnosticsEntry
from .diagnostics_payload import EnelSpDiagnosticsPayload
from .environment import EnelSpEnvironment
from .history_row import EnelSpHistoryRow
from .http_response import EnelSpHttpResponse
from .installation import EnelSpInstallation
from .installation_data import EnelSpInstallationData
from .installation_row import EnelSpInstallationRow
from .options_data import EnelSpOptionsData
from .payload import EnelSpPayload
from .runtime import EnelSpData
from .service_response import EnelSpServiceBody, EnelSpServiceResponse
from .tariff_flag import EnelSpTariffFlag

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | Mapping[str, JsonValue]
type JsonObject = Mapping[str, JsonValue]

type EnelSpConfigEntry = ConfigEntry[EnelSpData]

__all__ = [
    "EnelSpAccount",
    "EnelSpBill",
    "EnelSpBillStatus",
    "EnelSpConfigData",
    "EnelSpConfigEntry",
    "EnelSpCurrentUser",
    "EnelSpCurrentUserResponse",
    "EnelSpData",
    "EnelSpDiagnosticsEntry",
    "EnelSpDiagnosticsPayload",
    "EnelSpEnvironment",
    "EnelSpHistoryRow",
    "EnelSpHttpResponse",
    "EnelSpInstallation",
    "EnelSpInstallationData",
    "EnelSpInstallationRow",
    "EnelSpOptionsData",
    "EnelSpPayload",
    "EnelSpServiceBody",
    "EnelSpServiceResponse",
    "EnelSpTariffFlag",
    "JsonObject",
    "JsonPrimitive",
    "JsonValue",
]
