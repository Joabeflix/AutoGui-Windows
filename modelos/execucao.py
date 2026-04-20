from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EstadoExecucao(StrEnum):
    PARADA = "parada"
    EXECUTANDO = "executando"
    PAUSADA = "pausada"


@dataclass(slots=True)
class EventoExecucao:
    tipo: str
    mensagem: str = ""
    estado: str | None = None
    indice_passo: int | None = None
