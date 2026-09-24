"""Tipos próprios do enel_sp."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from .account import EnelSpAccount
from .aneel_tariff import EnelSpAneelTariff
from .bandeira_tarifaria_surcharge import EnelSpBandeiraTarifariaSurcharge
from .bill import EnelSpBill
from .bill_composition import EnelSpBillComposition
from .bill_status import EnelSpBillStatus
from .composition_row import EnelSpCompositionRow
from .config_data import EnelSpConfigData
from .current_user import EnelSpCurrentUser, EnelSpCurrentUserResponse
from .diagnostics_entry import EnelSpDiagnosticsEntry
from .diagnostics_payload import EnelSpDiagnosticsPayload
from .energy_price import EnelSpEnergyPrice
from .energy_price_source import EnelSpEnergyPriceSource
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
from .tariff_catalog import EnelSpTariffCatalog
from .tariff_flag import EnelSpTariffFlag
from .tax_rates import EnelSpTaxRates

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | Mapping[str, JsonValue]
type JsonObject = Mapping[str, JsonValue]

type EnelSpConfigEntry = ConfigEntry[EnelSpData]

type EnelSpTariffSeries = tuple[str, str, str]

__all__ = [
    "EnelSpAccount",
    "EnelSpAneelTariff",
    "EnelSpBandeiraTarifariaSurcharge",
    "EnelSpBill",
    "EnelSpBillComposition",
    "EnelSpBillStatus",
    "EnelSpCompositionRow",
    "EnelSpConfigData",
    "EnelSpConfigEntry",
    "EnelSpCurrentUser",
    "EnelSpCurrentUserResponse",
    "EnelSpData",
    "EnelSpDiagnosticsEntry",
    "EnelSpDiagnosticsPayload",
    "EnelSpEnergyPrice",
    "EnelSpEnergyPriceSource",
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
    "EnelSpTariffCatalog",
    "EnelSpTariffFlag",
    "EnelSpTariffSeries",
    "EnelSpTaxRates",
    "JsonObject",
    "JsonPrimitive",
    "JsonValue",
]
