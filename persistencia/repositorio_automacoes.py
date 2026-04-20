from __future__ import annotations

import json
import re
from pathlib import Path

from automacao.excecoes import ErroAutomacao
from automacao.validacao import validar_automacao
from modelos.automacao import Automacao, ResumoAutomacao
from utilitarios.caminhos import pasta_base_aplicacao


class RepositorioAutomacoes:
    def __init__(self, pasta_base: str | Path = "automacoes") -> None:
        pasta = Path(pasta_base)
        if not pasta.is_absolute():
            pasta = pasta_base_aplicacao() / pasta
        self.pasta_base = pasta
        self.pasta_base.mkdir(parents=True, exist_ok=True)

    def listar(self) -> list[ResumoAutomacao]:
        resumos: list[ResumoAutomacao] = []

        for arquivo in sorted(self.pasta_base.glob("*.json")):
            try:
                with arquivo.open("r", encoding="utf-8") as ponteiro:
                    dados = json.load(ponteiro)
                nome = dados.get("nome") if isinstance(dados, dict) else None
                resumos.append(
                    ResumoAutomacao(
                        nome=str(nome).strip() if nome else arquivo.stem,
                        caminho=arquivo,
                    )
                )
            except Exception as exc:
                resumos.append(
                    ResumoAutomacao(
                        nome=arquivo.stem,
                        caminho=arquivo,
                        valido=False,
                        mensagem_erro=str(exc),
                    )
                )

        return sorted(resumos, key=lambda item: item.nome.lower())

    def carregar(self, caminho: str | Path) -> Automacao:
        arquivo = Path(caminho)
        with arquivo.open("r", encoding="utf-8") as ponteiro:
            dados = json.load(ponteiro)
        automacao = validar_automacao(dados, permitir_sem_comandos=True)
        automacao.caminho_arquivo = arquivo
        return automacao

    def salvar(self, automacao: Automacao) -> Path:
        automacao_validada = validar_automacao(automacao, permitir_sem_comandos=True)
        nome_arquivo = self._gerar_nome_arquivo(automacao_validada.nome)
        destino = self.pasta_base / nome_arquivo

        origem = automacao.caminho_arquivo
        if origem and origem.exists() and origem.resolve() != destino.resolve():
            if destino.exists():
                raise ErroAutomacao("Ja existe uma automacao salva com esse nome.")
            origem.rename(destino)

        with destino.open("w", encoding="utf-8") as ponteiro:
            json.dump(automacao_validada.para_dict(), ponteiro, ensure_ascii=False, indent=2)

        automacao.caminho_arquivo = destino
        return destino

    def excluir(self, caminho: str | Path) -> None:
        arquivo = Path(caminho)
        if arquivo.exists():
            arquivo.unlink()

    def _gerar_nome_arquivo(self, nome: str) -> str:
        texto = nome.strip().lower()
        texto = re.sub(r"[^a-z0-9]+", "_", texto)
        texto = texto.strip("_")
        return f"{texto or 'automacao'}.json"
