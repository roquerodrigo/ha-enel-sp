"""DataUpdateCoordinator do enel_sp."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, LOGGER
from .data import EnelSpInstallationData, EnelSpPayload
from .exceptions import (
    EnelSpApiClientAuthenticationError,
    EnelSpApiClientError,
)
from .statistics import EnelSpStatisticsImporter

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant

    from .api import EnelSpApiClient
    from .data import EnelSpBillComposition, EnelSpConfigEntry, EnelSpInstallation

FAILURE_GRACE_PERIOD = timedelta(hours=24)


class EnelSpDataUpdateCoordinator(DataUpdateCoordinator["EnelSpPayload"]):
    """Coordinator que busca a conta do cliente e as contas das suas instalações."""

    config_entry: EnelSpConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        scan_interval: timedelta,
        config_entry: EnelSpConfigEntry | None = None,
    ) -> None:
        """Inicializa."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
            always_update=False,
            config_entry=config_entry,
        )
        self._first_failure_at: datetime | None = None

    async def _async_update_data(self) -> EnelSpPayload:
        """Busca os dados no portal, absorvendo indisponibilidades na tolerância."""
        try:
            payload = await self._fetch_payload()
        except EnelSpApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except EnelSpApiClientError as exception:
            return self._handle_failure(exception)

        self._first_failure_at = None
        await EnelSpStatisticsImporter(self.hass).async_import(
            payload.installations.values()
        )
        return payload

    async def _fetch_payload(self) -> EnelSpPayload:
        """Carrega a conta do cliente e as contas das instalações que ele mantém."""
        client = self.config_entry.runtime_data.client
        account = await client.async_get_account()
        installations = {
            installation.number: EnelSpInstallationData(
                installation=installation,
                bills=await client.async_get_bills(installation),
                compositions=await self._fetch_compositions(client, installation),
            )
            for installation in account.active_installations
        }
        return EnelSpPayload(account=account, installations=installations)

    async def _fetch_compositions(
        self, client: EnelSpApiClient, installation: EnelSpInstallation
    ) -> tuple[EnelSpBillComposition, ...]:
        """
        Carrega a composição das contas, sem deixar uma falha dela derrubar as contas.

        A composição só serve para deduzir as alíquotas do preço da energia. Uma
        falha nela, mesmo de autenticação, não pode tornar as contas indisponíveis
        nem abrir uma reautenticação que as contas não pediram; a última composição
        conhecida continua valendo, porque ela só muda quando sai uma conta nova.
        """
        try:
            return await client.async_get_bill_compositions(installation)
        except EnelSpApiClientError as exception:
            LOGGER.warning(
                "Failed to fetch the bill composition of %s: %s",
                installation.number,
                exception,
            )
        last_known_data: EnelSpPayload | None = self.data
        last_known_installation = (
            last_known_data.installations.get(installation.number)
            if last_known_data is not None
            else None
        )
        return last_known_installation.compositions if last_known_installation else ()

    def _handle_failure(self, exception: EnelSpApiClientError) -> EnelSpPayload:
        """
        Serve os últimos dados enquanto a indisponibilidade for menor que a tolerância.

        As contas só mudam uma vez por mês, então manter os últimos valores conhecidos
        durante uma indisponibilidade do portal não custa nada em precisão e mantém
        todas as entidades disponíveis para automações e histórico. Uma
        indisponibilidade real ainda aparece quando a janela se fecha, e erros de
        autenticação nunca chegam aqui, portanto a reautenticação é solicitada de
        imediato.
        """
        now = dt_util.utcnow()
        if self._first_failure_at is None:
            self._first_failure_at = now

        last_known_data: EnelSpPayload | None = self.data
        if (
            last_known_data is not None
            and now - self._first_failure_at < FAILURE_GRACE_PERIOD
        ):
            LOGGER.warning(
                "Failed to fetch data; serving the last known values: %s", exception
            )
            return last_known_data

        raise UpdateFailed(exception) from exception
