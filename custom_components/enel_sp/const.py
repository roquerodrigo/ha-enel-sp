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

DEFAULT_SCAN_INTERVAL_SECONDS = 3600
MIN_SCAN_INTERVAL_SECONDS = 300
