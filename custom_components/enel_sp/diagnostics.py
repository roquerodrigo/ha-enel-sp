"""Suporte a diagnóstico do enel_sp."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING, cast

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

if TYPE_CHECKING:
    from collections.abc import Mapping

    from homeassistant.core import HomeAssistant

    from .data import (
        EnelSpConfigEntry,
        EnelSpDiagnosticsEntry,
        EnelSpDiagnosticsPayload,
        EnelSpPayload,
        EnelSpTariffCatalog,
        JsonObject,
    )

TO_REDACT: frozenset[str] = frozenset(
    {
        CONF_PASSWORD,
        CONF_USERNAME,
        "enel_id",
        "name",
        "address",
        "partner",
        "contract",
        "contract_account",
        "meter_serial",
        "nickname",
    }
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: EnelSpConfigEntry,
) -> EnelSpDiagnosticsPayload:
    """Retorna o diagnóstico de uma config entry."""
    redacted_data = cast(
        "Mapping[str, str]",
        async_redact_data(dict(entry.data), set(TO_REDACT)),
    )
    redacted_options = cast(
        "Mapping[str, str | int]",
        async_redact_data(dict(entry.options), set(TO_REDACT)),
    )
    diag_entry: EnelSpDiagnosticsEntry = {
        "title": entry.title,
        "version": entry.version,
        "domain": entry.domain,
        "data": redacted_data,
        "options": redacted_options,
    }
    payload: EnelSpPayload | None = entry.runtime_data.coordinator.data
    coordinator_data: JsonObject | None = None
    if payload is not None:
        # Datas e enums não são JSON por si sós; a ida e volta pelo encoder com
        # ``default=str`` os transforma em texto de uma vez.
        serializable = json.loads(json.dumps(asdict(payload), default=str))
        coordinator_data = cast(
            "JsonObject", async_redact_data(serializable, set(TO_REDACT))
        )
    catalog: EnelSpTariffCatalog | None = entry.runtime_data.tariff_coordinator.data
    tariff_data: JsonObject | None = None
    if catalog is not None:
        tariff_data = cast(
            "JsonObject", json.loads(json.dumps(asdict(catalog), default=str))
        )
    return {
        "entry": diag_entry,
        "coordinator_data": coordinator_data,
        "tariff_data": tariff_data,
    }
