"""Constantes do enel_sp."""

from __future__ import annotations

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "enel_sp"
ATTRIBUTION = "Data provided by Enel Distribuição São Paulo"

ACCOUNTS_BASE_URL = "https://accounts.enel.com"
PORTAL_BASE_URL = "https://www.enel.com.br"
PORTAL_SITE = "pt-saopaulo"
SAML_SERVICE_PROVIDER = "ENEL_SP_WEB_BRA"
CURRENCY_BRAZILIAN_REAL = "BRL"
ENERGY_PRICE_UNIT = f"{CURRENCY_BRAZILIAN_REAL}/kWh"

ANEEL_DATASTORE_URL = "https://dadosabertos.aneel.gov.br/api/3/action/datastore_search"
ANEEL_TARIFFS_RESOURCE_ID = "fcf2906c-7c32-4b9b-a637-054e7a5234f4"
ANEEL_BANDEIRA_TARIFARIA_RESOURCE_ID = "0591b8f6-fe54-437b-b72b-1aa2efd46e42"
ENEL_SP_CNPJ = "61695227000193"
TARIFF_UPDATE_INTERVAL_SECONDS = 6 * 3600

DEFAULT_SCAN_INTERVAL_SECONDS = 3600
MIN_SCAN_INTERVAL_SECONDS = 300
