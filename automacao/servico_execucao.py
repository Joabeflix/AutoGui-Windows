from __future__ import annotations

import threading
from collections.abc import Callable

from automacao.excecoes import ErroAutomacao, ExecucaoInterrompida
from automacao.executor import ExecutorAutomacao
from automacao.validacao import validar_automacao
from modelos.automacao import Automacao
from modelos.execucao import EstadoExecucao, EventoExecucao


class ServicoExecucao:
    def __init__(self, ao_evento: Callable[[EventoExecucao], None]) -> None:
        self._ao_evento = ao_evento
        self._estado = EstadoExecucao.PARADA
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._evento_pausa = threading.Event()
        self._evento_parar = threading.Event()

    @property
    def estado(self) -> EstadoExecucao:
        return self._estado

    def executar(self, automacao: Automacao) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                raise ErroAutomacao("Ja existe uma automacao em execucao.")

            automacao_validada = validar_automacao(
                automacao,
                permitir_sem_comandos=False,
            )
            automacao_validada.caminho_arquivo = automacao.caminho_arquivo

            self._evento_pausa.clear()
            self._evento_parar.clear()
            self._alterar_estado(EstadoExecucao.EXECUTANDO)
            self._thread = threading.Thread(
                target=self._rodar_em_background,
                args=(automacao_validada,),
                daemon=True,
            )
            self._thread.start()

    def pausar(self) -> None:
        if self._estado != EstadoExecucao.EXECUTANDO:
            return
        self._evento_pausa.set()
        self._alterar_estado(EstadoExecucao.PAUSADA)
        self._emitir("log", "Execucao pausada pelo usuario.")

    def continuar_execucao(self) -> None:
        if self._estado != EstadoExecucao.PAUSADA:
            return
        self._evento_pausa.clear()
        self._alterar_estado(EstadoExecucao.EXECUTANDO)
        self._emitir("log", "Execucao retomada.")

    def parar(self) -> None:
        if self._estado == EstadoExecucao.PARADA:
            return
        self._evento_parar.set()
        self._evento_pausa.clear()
        self._emitir("log", "Solicitada parada da automacao.")

    def _rodar_em_background(self, automacao: Automacao) -> None:
        executor = ExecutorAutomacao(
            automacao,
            ao_log=lambda mensagem: self._emitir("log", mensagem),
            ao_passo=lambda indice: self._emitir("passo", indice_passo=indice),
            deve_parar=self._evento_parar.is_set,
            esta_pausada=self._evento_pausa.is_set,
        )

        try:
            executor.executar()
        except ExecucaoInterrompida:
            self._emitir("log", "Automacao interrompida.")
        except Exception as exc:
            self._emitir("erro", f"Falha na execucao: {exc}")
        finally:
            self._evento_pausa.clear()
            self._evento_parar.clear()
            self._emitir("passo", indice_passo=None)
            self._alterar_estado(EstadoExecucao.PARADA)

    def _alterar_estado(self, estado: EstadoExecucao) -> None:
        self._estado = estado
        self._ao_evento(EventoExecucao(tipo="estado", estado=estado))

    def _emitir(
        self,
        tipo: str,
        mensagem: str = "",
        *,
        indice_passo: int | None = None,
    ) -> None:
        self._ao_evento(
            EventoExecucao(
                tipo=tipo,
                mensagem=mensagem,
                indice_passo=indice_passo,
            )
        )
