"""Uma instalação (ponto de fornecimento) listada na conta do cliente."""

from __future__ import annotations

from dataclasses import dataclass

_OPEN_ENDED_MOVE_OUT = "99991231"


@dataclass(frozen=True)
class EnelSpInstallation:
    """Identidade de uma instalação e as chaves SAP usadas para consultar seus dados."""

    number: str
    nickname: str
    address: str
    partner: str
    contract: str
    contract_account: str
    voltage_level: str
    meter_serial: str
    move_in: str
    move_out: str

    @property
    def active(self) -> bool:
        """Informa se o cliente ainda mantém a instalação."""
        return self.move_out in ("", _OPEN_ENDED_MOVE_OUT)

    @property
    def name(self) -> str:
        """Retorna o apelido dado pelo cliente ou, na ausência dele, o número."""
        return self.nickname or self.number
