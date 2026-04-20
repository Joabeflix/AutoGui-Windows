from __future__ import annotations

from typing import Any, Callable

import pyautogui

from automacao.excecoes import ErroAcaoInvalida


ExecutorAcao = Callable[[dict[str, Any]], None]


def executar_escrever(comando: dict[str, Any]) -> None:
    pyautogui.write(comando["texto"])


def executar_pressionar(comando: dict[str, Any]) -> None:
    pyautogui.press(comando["tecla"], presses=int(comando.get("quantidade", 1)))


def executar_atalho(comando: dict[str, Any]) -> None:
    pyautogui.hotkey(*comando["teclas"])


def executar_clicar(comando: dict[str, Any]) -> None:
    pyautogui.click(x=comando["x"], y=comando["y"])


def executar_duplo_clique(comando: dict[str, Any]) -> None:
    pyautogui.doubleClick(x=comando["x"], y=comando["y"])


def executar_mover_mouse(comando: dict[str, Any]) -> None:
    pyautogui.moveTo(
        x=comando["x"],
        y=comando["y"],
        duration=float(comando.get("duracao", 0.0)),
    )


def executar_rolar(comando: dict[str, Any]) -> None:
    pyautogui.scroll(int(comando["quantidade"]))


def executar_esperar(_: dict[str, Any]) -> None:
    return


ACOES_REGISTRADAS: dict[str, ExecutorAcao] = {
    "escrever": executar_escrever,
    "pressionar": executar_pressionar,
    "atalho": executar_atalho,
    "clicar": executar_clicar,
    "duplo_clique": executar_duplo_clique,
    "mover_mouse": executar_mover_mouse,
    "rolar": executar_rolar,
    "esperar": executar_esperar,
}


def executar_acao(comando: dict[str, Any]) -> None:
    acao = comando["acao"]
    executor = ACOES_REGISTRADAS.get(acao)
    if executor is None:
        raise ErroAcaoInvalida(f"Acao nao registrada: {acao}")
    executor(comando)
