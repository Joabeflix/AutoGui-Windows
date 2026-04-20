from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CampoAcao:
    nome: str
    rotulo: str
    tipo: str
    obrigatorio: bool = True
    padrao: Any = ""
    ajuda: str = ""


@dataclass(frozen=True, slots=True)
class DefinicaoAcao:
    nome: str
    titulo: str
    descricao: str
    campos: tuple[CampoAcao, ...]


DEFINICOES_ACOES: dict[str, DefinicaoAcao] = {
    "escrever": DefinicaoAcao(
        nome="escrever",
        titulo="Escrever texto",
        descricao="Digita um texto exatamente como foi informado.",
        campos=(
            CampoAcao("texto", "Texto", "texto", ajuda="Conteudo que sera digitado."),
        ),
    ),
    "pressionar": DefinicaoAcao(
        nome="pressionar",
        titulo="Pressionar tecla",
        descricao="Pressiona uma tecla uma ou mais vezes.",
        campos=(
            CampoAcao("tecla", "Tecla", "texto", ajuda="Exemplo: tab, enter, home."),
            CampoAcao("quantidade", "Quantidade", "inteiro", obrigatorio=False, padrao=1),
        ),
    ),
    "atalho": DefinicaoAcao(
        nome="atalho",
        titulo="Atalho de teclado",
        descricao="Executa uma combinacao de teclas.",
        campos=(
            CampoAcao(
                "teclas",
                "Teclas",
                "lista_texto",
                ajuda="Separe as teclas por virgula. Exemplo: ctrl, s",
            ),
        ),
    ),
    "clicar": DefinicaoAcao(
        nome="clicar",
        titulo="Clicar",
        descricao="Clica em uma coordenada da tela.",
        campos=(
            CampoAcao("x", "Posicao X", "inteiro"),
            CampoAcao("y", "Posicao Y", "inteiro"),
        ),
    ),
    "duplo_clique": DefinicaoAcao(
        nome="duplo_clique",
        titulo="Duplo clique",
        descricao="Executa um duplo clique em uma coordenada.",
        campos=(
            CampoAcao("x", "Posicao X", "inteiro"),
            CampoAcao("y", "Posicao Y", "inteiro"),
        ),
    ),
    "mover_mouse": DefinicaoAcao(
        nome="mover_mouse",
        titulo="Mover mouse",
        descricao="Move o cursor para uma coordenada.",
        campos=(
            CampoAcao("x", "Posicao X", "inteiro"),
            CampoAcao("y", "Posicao Y", "inteiro"),
            CampoAcao("duracao", "Duracao", "decimal", obrigatorio=False, padrao=0.0),
        ),
    ),
    "rolar": DefinicaoAcao(
        nome="rolar",
        titulo="Rolar tela",
        descricao="Rola a tela para cima ou para baixo.",
        campos=(
            CampoAcao("quantidade", "Quantidade", "inteiro", ajuda="Use negativo para descer."),
        ),
    ),
    "esperar": DefinicaoAcao(
        nome="esperar",
        titulo="Esperar",
        descricao="Aguarda um periodo antes de seguir.",
        campos=(
            CampoAcao("segundos", "Segundos", "decimal"),
        ),
    ),
}


def listar_acoes() -> list[str]:
    return list(DEFINICOES_ACOES)


def obter_definicao(acao: str) -> DefinicaoAcao:
    return DEFINICOES_ACOES[acao]


def formatar_comando(comando: dict[str, Any]) -> str:
    acao = comando.get("acao", "")
    partes: list[str] = []

    for campo in DEFINICOES_ACOES.get(acao, DefinicaoAcao("", "", "", ())).campos:
        if campo.nome not in comando:
            continue
        valor = comando[campo.nome]
        if isinstance(valor, list):
            valor = ", ".join(str(item) for item in valor)
        partes.append(f"{campo.rotulo}: {valor}")

    esperar_apos = comando.get("esperar_apos")
    if esperar_apos not in (None, "", 0, 0.0):
        partes.append(f"Esperar apos: {esperar_apos}s")

    return " | ".join(partes) if partes else "Sem parametros"
