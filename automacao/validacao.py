from __future__ import annotations

from copy import deepcopy
from typing import Any

from automacao.catalogo import DEFINICOES_ACOES, CampoAcao
from automacao.excecoes import ErroValidacao
from modelos.automacao import Automacao, ConfiguracaoAutomacao


def validar_automacao(
    dados: dict[str, Any] | Automacao,
    *,
    permitir_sem_comandos: bool = True,
) -> Automacao:
    bruto = dados.para_dict() if isinstance(dados, Automacao) else deepcopy(dados)

    if not isinstance(bruto, dict):
        raise ErroValidacao("A automacao deve ser um objeto JSON.")

    nome = bruto.get("nome", "")
    configuracao = bruto.get("configuracao", {})
    comandos = bruto.get("comandos", [])

    if not isinstance(nome, str) or not nome.strip():
        raise ErroValidacao("Informe um nome para a automacao.")

    if not isinstance(configuracao, dict):
        raise ErroValidacao("O bloco 'configuracao' precisa ser um objeto.")

    if not isinstance(comandos, list):
        raise ErroValidacao("O bloco 'comandos' precisa ser uma lista.")

    if not permitir_sem_comandos and not comandos:
        raise ErroValidacao("Adicione pelo menos uma acao antes de executar.")

    pausa_global = _validar_decimal(configuracao.get("pausa_global", 0.3), "configuracao.pausa_global")
    pausa_inicial = _validar_decimal(configuracao.get("pausa_inicial", 0.0), "configuracao.pausa_inicial")
    fail_safe = configuracao.get("fail_safe", True)
    executar_em_loop = configuracao.get("executar_em_loop", False)

    if not isinstance(fail_safe, bool):
        raise ErroValidacao("'configuracao.fail_safe' precisa ser true ou false.")
    if not isinstance(executar_em_loop, bool):
        raise ErroValidacao("'configuracao.executar_em_loop' precisa ser true ou false.")

    comandos_validados = [
        _validar_comando(comando, indice)
        for indice, comando in enumerate(comandos, start=1)
    ]

    automacao = Automacao(
        nome=nome.strip(),
        configuracao=ConfiguracaoAutomacao(
            pausa_global=pausa_global,
            fail_safe=fail_safe,
            pausa_inicial=pausa_inicial,
            executar_em_loop=executar_em_loop,
        ),
        comandos=comandos_validados,
    )

    if isinstance(dados, Automacao):
        automacao.caminho_arquivo = dados.caminho_arquivo

    return automacao


def _validar_comando(comando: Any, indice: int) -> dict[str, Any]:
    if not isinstance(comando, dict):
        raise ErroValidacao(f"O passo {indice} precisa ser um objeto.")

    acao = comando.get("acao")
    if not isinstance(acao, str) or acao not in DEFINICOES_ACOES:
        raise ErroValidacao(f"O passo {indice} usa uma acao invalida.")

    definicao = DEFINICOES_ACOES[acao]
    normalizado: dict[str, Any] = {"acao": acao}

    for campo in definicao.campos:
        valor = comando.get(campo.nome, campo.padrao)
        if _campo_vazio(valor):
            if campo.obrigatorio:
                raise ErroValidacao(f"O campo '{campo.rotulo}' e obrigatorio no passo {indice}.")
            continue
        normalizado[campo.nome] = _converter_valor(campo, valor, indice)

    esperar_apos = comando.get("esperar_apos", 0.0)
    normalizado["esperar_apos"] = _validar_decimal(
        esperar_apos,
        f"comandos[{indice}].esperar_apos",
    )

    return normalizado


def _converter_valor(campo: CampoAcao, valor: Any, indice: int) -> Any:
    try:
        if campo.tipo == "texto":
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError
            return valor

        if campo.tipo == "inteiro":
            if isinstance(valor, bool):
                raise ValueError
            return int(valor)

        if campo.tipo == "decimal":
            return _validar_decimal(valor, f"passo {indice} -> {campo.rotulo.lower()}")

        if campo.tipo == "lista_texto":
            if isinstance(valor, str):
                itens = [parte.strip() for parte in valor.split(",") if parte.strip()]
            elif isinstance(valor, list):
                itens = [str(item).strip() for item in valor if str(item).strip()]
            else:
                raise ValueError
            if len(itens) < 2:
                raise ValueError
            return itens
    except (TypeError, ValueError) as exc:
        raise ErroValidacao(
            f"O campo '{campo.rotulo}' do passo {indice} esta invalido."
        ) from exc

    raise ErroValidacao(f"Tipo de campo nao suportado: {campo.tipo}")


def _validar_decimal(valor: Any, campo: str) -> float:
    if isinstance(valor, bool):
        raise ErroValidacao(f"'{campo}' precisa ser numerico.")
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ErroValidacao(f"'{campo}' precisa ser numerico.") from exc
    if numero < 0:
        raise ErroValidacao(f"'{campo}' nao pode ser negativo.")
    return numero


def _campo_vazio(valor: Any) -> bool:
    return valor in (None, "")
