"""Importação para as estatísticas de longo prazo dos meses que o portal mantém."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.translation import async_get_cached_translations
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify
from homeassistant.util.unit_conversion import EnergyConverter

from .const import CURRENCY_BRAZILIAN_REAL, DOMAIN, LOGGER

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime

    from homeassistant.core import HomeAssistant

    from .data import EnelSpBill, EnelSpInstallationData

type _LastRow = tuple[datetime, float]


def _period_start(bill: EnelSpBill) -> datetime:
    """Retorna o bucket de uma conta: a meia-noite local que inicia o seu mês."""
    return dt_util.start_of_local_day(bill.period_start)


class EnelSpStatisticsImporter:
    """
    Importa os meses faturados de cada instalação como estatísticas externas.

    O estado de um sensor carrega apenas a conta mais recente, enquanto o portal mantém
    treze meses de histórico. As estatísticas de longo prazo são onde o Home Assistant
    guarda esse tipo de histórico: elas alimentam o painel de energia e o card de
    gráfico de estatísticas. Cada instalação recebe ``enel_sp:<number>_energy`` em kWh,
    com a leitura do medidor como estado, e ``enel_sp:<number>_cost`` em BRL, nomeadas
    com a instalação e o sensor correspondente. As importações seguintes só acrescentam
    meses mais novos que a última linha armazenada, então uma conta que o portal revisa
    depois nunca é reescrita; os metadados são enviados a cada atualização para que as
    séries acompanhem uma instalação renomeada ou uma troca de idioma.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Vincula o importador à instância do Home Assistant em execução."""
        self._hass = hass

    async def async_import(
        self, installations: Iterable[EnelSpInstallationData]
    ) -> None:
        """Importa todas as instalações."""
        for data in installations:
            await self._async_import_installation(data)

    async def _async_import_installation(self, data: EnelSpInstallationData) -> None:
        """Acrescenta os meses de uma instalação que ainda não estão armazenados."""
        energy_id = f"{DOMAIN}:{slugify(data.installation.number)}_energy"
        cost_id = f"{DOMAIN}:{slugify(data.installation.number)}_cost"
        last_energy = await self._async_last_row(energy_id)
        last_cost = await self._async_last_row(cost_id)

        energy_sum = 0.0 if last_energy is None else last_energy[1]
        cost_sum = 0.0 if last_cost is None else last_cost[1]
        bills = [
            bill
            for bill in data.bills
            if last_energy is None or _period_start(bill) > last_energy[0]
        ]

        energy_rows: list[StatisticData] = []
        cost_rows: list[StatisticData] = []
        for bill in bills:
            start = _period_start(bill)
            energy_sum += bill.consumption
            cost_sum += bill.amount
            energy_rows.append(
                StatisticData(
                    start=start, state=bill.meter_reading, sum=round(energy_sum, 3)
                ),
            )
            cost_rows.append(
                StatisticData(start=start, state=bill.amount, sum=round(cost_sum, 2)),
            )

        if bills:
            LOGGER.debug(
                "Importing %d months of statistics for installation %s",
                len(bills),
                data.installation.number,
            )
        name = data.installation.name
        async_add_external_statistics(
            self._hass,
            self._metadata(
                energy_id,
                f"{name} {self._sensor_name('bill_consumption')}",
                unit_class=EnergyConverter.UNIT_CLASS,
                unit=UnitOfEnergy.KILO_WATT_HOUR,
            ),
            energy_rows,
        )
        async_add_external_statistics(
            self._hass,
            self._metadata(
                cost_id,
                f"{name} {self._sensor_name('bill_amount')}",
                unit_class=None,
                unit=CURRENCY_BRAZILIAN_REAL,
            ),
            cost_rows,
        )

    async def _async_last_row(self, statistic_id: str) -> _LastRow | None:
        """Retorna o início e a soma acumulada da última linha armazenada, se houver."""
        rows = await get_instance(self._hass).async_add_executor_job(
            partial(
                get_last_statistics,
                self._hass,
                1,
                statistic_id,
                convert_units=True,
                types={"sum"},
            ),
        )
        if not rows:
            return None
        last_row = rows[statistic_id][0]
        return dt_util.utc_from_timestamp(last_row["start"]), last_row["sum"] or 0.0

    def _sensor_name(self, translation_key: str) -> str:
        """Retorna o nome traduzido de um dos sensores da integração."""
        translations = async_get_cached_translations(
            self._hass, self._hass.config.language, "entity", DOMAIN
        )
        return translations.get(
            f"component.{DOMAIN}.entity.sensor.{translation_key}.name",
            translation_key,
        )

    def _metadata(
        self,
        statistic_id: str,
        name: str,
        *,
        unit_class: str | None,
        unit: str,
    ) -> StatisticMetaData:
        """Descreve uma série para o recorder."""
        return StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name=name,
            source=DOMAIN,
            statistic_id=statistic_id,
            unit_class=unit_class,
            unit_of_measurement=unit,
        )
