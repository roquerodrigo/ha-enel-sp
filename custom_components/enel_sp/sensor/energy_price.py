"""Sensor que expõe o preço atual do kWh, com bandeira e tributos."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.util import dt as dt_util

from ..const import ENERGY_PRICE_UNIT
from ..entity import EnelSpEntity
from ..pricing import EnelSpEnergyPriceCalculator

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ..data import EnelSpEnergyPrice

_RATE_PRECISION = 5
_PERCENT_PRECISION = 4


class EnelSpEnergyPriceSensor(EnelSpEntity, SensorEntity):
    """
    Preço do kWh consumido agora, para multiplicar pela energia medida ao vivo.

    Só inclui o que a Enel cobra por kWh: tarifa, bandeira, ICMS, PIS e COFINS. Os
    itens fixos da conta, como a iluminação pública, ficam no atributo
    ``other_items``.
    """

    _attr_translation_key = "energy_price"
    _attr_native_unit_of_measurement = ENERGY_PRICE_UNIT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 4

    async def async_added_to_hass(self) -> None:
        """Acompanha também as tarifas, que a ANEEL atualiza no próprio ritmo."""
        await super().async_added_to_hass()
        tariff_coordinator = (
            self.coordinator.config_entry.runtime_data.tariff_coordinator
        )
        self.async_on_remove(
            tariff_coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @property
    def unique_id(self) -> str:
        """Retorna um id único derivado da config entry e da instalação."""
        entry_id = self.coordinator.config_entry.entry_id
        return f"{entry_id}_{self._installation.number}_energy_price"

    @property
    def energy_price(self) -> EnelSpEnergyPrice | None:
        """Calcula o preço de hoje a partir das contas e das tarifas atuais."""
        data = self.installation_data
        if data is None:
            return None
        catalog = self.coordinator.config_entry.runtime_data.tariff_coordinator.data
        return EnelSpEnergyPriceCalculator(catalog).calculate(
            data, dt_util.now().date()
        )

    @property
    def native_value(self) -> float | None:
        """Retorna o preço do kWh com tributos."""
        energy_price = self.energy_price
        return (
            None if energy_price is None else round(energy_price.price, _RATE_PRECISION)
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, str | int | float]:
        """Detalha as parcelas do preço e de onde cada uma veio."""
        attributes: dict[str, str | int | float] = dict(super().extra_state_attributes)
        energy_price = self.energy_price
        if energy_price is None:
            return attributes
        attributes["tariff_source"] = energy_price.source.value
        attributes["tariff"] = round(energy_price.tariff_rate, _RATE_PRECISION)
        tariff = energy_price.tariff
        if tariff is not None:
            attributes["tusd"] = round(tariff.distribution_rate, _RATE_PRECISION)
            attributes["te"] = round(tariff.energy_rate, _RATE_PRECISION)
            attributes["tariff_subgroup"] = tariff.subgroup
            attributes["tariff_class"] = tariff.consumer_class
            attributes["tariff_subclass"] = tariff.subclass
            attributes["tariff_valid_from"] = tariff.valid_from.isoformat()
            attributes["tariff_resolution"] = tariff.resolution
        bandeira_tarifaria_surcharge = energy_price.bandeira_tarifaria_surcharge
        if bandeira_tarifaria_surcharge is not None:
            attributes["bandeira_tarifaria"] = bandeira_tarifaria_surcharge.name
            attributes["bandeira_tarifaria_month"] = (
                bandeira_tarifaria_surcharge.month.isoformat()
            )
            attributes["bandeira_tarifaria_surcharge"] = round(
                bandeira_tarifaria_surcharge.rate, _RATE_PRECISION
            )
        tax_rates = energy_price.tax_rates
        attributes["icms_rate"] = round(tax_rates.icms * 100, _PERCENT_PRECISION)
        attributes["pis_cofins_rate"] = round(
            tax_rates.pis_cofins * 100, _PERCENT_PRECISION
        )
        attributes["price_before_taxes"] = round(
            energy_price.rate_before_taxes, _RATE_PRECISION
        )
        attributes["tax_bill_year"] = energy_price.tax_bill.year
        attributes["tax_bill_month"] = energy_price.tax_bill.month
        attributes["other_items"] = energy_price.other_items
        return attributes
