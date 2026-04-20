from __future__ import annotations

import time
from collections.abc import Callable

import pyautogui

from automacao.acoes import executar_acao
from automacao.catalogo import obter_definicao
from automacao.excecoes import ExecucaoInterrompida
from modelos.automacao import Automacao


class ExecutorAutomacao:
    def __init__(
        self,
        automacao: Automacao,
        *,
        ao_log: Callable[[str], None] | None = None,
        ao_passo: Callable[[int | None], None] | None = None,
        deve_parar: Callable[[], bool] | None = None,
        esta_pausada: Callable[[], bool] | None = None,
    ) -> None:
        self.automacao = automacao
        self.ao_log = ao_log or (lambda mensagem: None)
        self.ao_passo = ao_passo or (lambda indice: None)
        self.deve_parar = deve_parar or (lambda: False)
        self.esta_pausada = esta_pausada or (lambda: False)

    def executar(self) -> None:
        pyautogui.PAUSE = self.automacao.configuracao.pausa_global
        pyautogui.FAILSAFE = self.automacao.configuracao.fail_safe

        pausa_inicial = self.automacao.configuracao.pausa_inicial
        if pausa_inicial > 0:
            self.ao_log(f"Pausa inicial de {pausa_inicial:.2f}s.")
            self._esperar_interrompivel(pausa_inicial)

        total = len(self.automacao.comandos)
        loop_ativo = self.automacao.configuracao.executar_em_loop
        self.ao_log(
            f"Iniciando automacao '{self.automacao.nome}' com {total} passo(s)."
            + (" Execucao em loop ativada." if loop_ativo else "")
        )

        rodada = 1
        while True:
            if loop_ativo:
                self.ao_log(f"Iniciando ciclo {rodada}.")

            for indice, comando in enumerate(self.automacao.comandos):
                self._verificar_controle()
                self.ao_passo(indice)
                definicao = obter_definicao(comando["acao"])
                self.ao_log(f"Passo {indice + 1}/{total}: {definicao.titulo}")

                if comando["acao"] == "esperar":
                    self._esperar_interrompivel(float(comando["segundos"]))
                else:
                    executar_acao(comando)

                esperar_apos = float(comando.get("esperar_apos", 0.0))
                if esperar_apos > 0:
                    self.ao_log(f"Aguardando {esperar_apos:.2f}s antes do proximo passo.")
                    self._esperar_interrompivel(esperar_apos)

            if not loop_ativo:
                break

            rodada += 1
            self.ao_log("Fim do ultimo passo. Voltando para o primeiro passo.")

        self.ao_passo(None)
        self.ao_log("Automacao concluida com sucesso.")

    def _esperar_interrompivel(self, total_segundos: float) -> None:
        restante = max(total_segundos, 0.0)
        while restante > 0:
            self._verificar_controle()
            intervalo = min(0.1, restante)
            time.sleep(intervalo)
            restante -= intervalo

    def _verificar_controle(self) -> None:
        if self.deve_parar():
            raise ExecucaoInterrompida("Execucao interrompida.")

        while self.esta_pausada():
            if self.deve_parar():
                raise ExecucaoInterrompida("Execucao interrompida.")
            time.sleep(0.1)
