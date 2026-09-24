"""Coordinator das tarifas e bandeiras publicadas pela ANEEL."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER, TARIFF_UPDATE_INTERVAL_SECONDS
from .exceptions import EnelSpApiClientError

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .aneel_api import EnelSpAneelApiClient
    from .data import EnelSpConfigEntry, EnelSpTariffCatalog


class EnelSpTariffUpdateCoordinator(DataUpdateCoordinator["EnelSpTariffCatalog"]):
    """Coordinator que mantém as tarifas homologadas e as bandeiras da ANEEL."""

    config_entry: EnelSpConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: EnelSpAneelApiClient,
        config_entry: EnelSpConfigEntry | None = None,
    ) -> None:
        """Inicializa."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=f"{DOMAIN}_tariffs",
            update_interval=timedelta(seconds=TARIFF_UPDATE_INTERVAL_SECONDS),
            always_update=False,
            config_entry=config_entry,
        )
        self._client = client

    async def _async_update_data(self) -> EnelSpTariffCatalog:
        """
        Busca o catálogo, mantendo o último conhecido se a ANEEL falhar.

        Tarifas mudam uma vez por ano e bandeiras uma vez por mês, então o catálogo
        anterior continua correto durante uma indisponibilidade do portal da ANEEL.
        """
        try:
            return await self._client.async_get_catalog()
        except EnelSpApiClientError as exception:
            last_known_catalog: EnelSpTariffCatalog | None = self.data
            if last_known_catalog is None:
                raise UpdateFailed(exception) from exception
            LOGGER.warning(
                "Failed to fetch the ANEEL tariffs; serving the last known ones: %s",
                exception,
            )
            return last_known_catalog
