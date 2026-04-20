from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ConfiguracaoAutomacao:
    pausa_global: float = 0.3
    fail_safe: bool = True
    pausa_inicial: float = 0.0
    executar_em_loop: bool = False


@dataclass(slots=True)
class Automacao:
    nome: str
    configuracao: ConfiguracaoAutomacao = field(default_factory=ConfiguracaoAutomacao)
    comandos: list[dict[str, Any]] = field(default_factory=list)
    caminho_arquivo: Path | None = None

    def para_dict(self) -> dict[str, Any]:
        return {
            "nome": self.nome,
            "configuracao": {
                "pausa_global": self.configuracao.pausa_global,
                "fail_safe": self.configuracao.fail_safe,
                "pausa_inicial": self.configuracao.pausa_inicial,
                "executar_em_loop": self.configuracao.executar_em_loop,
            },
            "comandos": self.comandos,
        }


@dataclass(slots=True)
class ResumoAutomacao:
    nome: str
    caminho: Path
    valido: bool = True
    mensagem_erro: str | None = None
