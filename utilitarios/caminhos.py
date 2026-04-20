from __future__ import annotations

import sys
from pathlib import Path


def pasta_base_aplicacao() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def caminho_recurso(*partes: str) -> Path:
    return pasta_base_aplicacao().joinpath(*partes)
