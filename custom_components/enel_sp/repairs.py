"""
Plataforma de Repairs do enel_sp.

Liga esta integração ao registro de Issues / Repairs do Home Assistant. Use
``async_raise_deprecated_api_issue`` (ou um helper próprio) de qualquer ponto da
integração para expor ao usuário um problema recuperável; a UI exibe o botão "Fix", que
volta para cá por meio de ``async_create_fix_flow``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

ISSUE_DEPRECATED_API: str = "deprecated_api"

# Contrato do HA para o argumento data passado a async_create_fix_flow.
type RepairsFixFlowData = dict[str, str | int | float | None]


async def async_create_fix_flow(
    hass: HomeAssistant,  # noqa: ARG001
    issue_id: str,  # noqa: ARG001
    data: RepairsFixFlowData | None,  # noqa: ARG001
) -> RepairsFlow:
    """
    Retorna o fix flow de uma issue.

    Ramifique por ``issue_id`` aqui quando houver vários tipos de issue.
    """
    return ConfirmRepairFlow()


def async_raise_deprecated_api_issue(hass: HomeAssistant) -> None:
    """
    Exemplo de helper: levanta a issue de API obsoleta.

    Chame a partir do coordinator / setup ao detectar a condição recuperável que a issue
    descreve.
    """
    ir.async_create_issue(
        hass,
        DOMAIN,
        ISSUE_DEPRECATED_API,
        is_fixable=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_DEPRECATED_API,
    )
