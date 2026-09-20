"""Dados de runtime armazenados em entry.runtime_data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.loader import Integration

    from ..api import EnelSpApiClient
    from ..coordinator import EnelSpDataUpdateCoordinator


@dataclass
class EnelSpData:
    """Dados armazenados em entry.runtime_data para a Enel São Paulo."""

    client: EnelSpApiClient
    coordinator: EnelSpDataUpdateCoordinator
    integration: Integration
