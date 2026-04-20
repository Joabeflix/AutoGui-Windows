# Plataforma Visual de Automacao

Sistema desktop em Python para montar, salvar e executar automacoes do `pyautogui` por uma interface visual em `ttkbootstrap`.

## Estrutura

```text
AutoGui Windows/
|-- automacao/
|-- automacoes/
|-- interface/
|-- modelos/
|-- persistencia/
|-- main.py
`-- README.md
```

## Como rodar

1. Instale as dependencias:

```bash
pip install pyautogui ttkbootstrap
```

2. Execute a aplicacao:

```bash
python main.py
```

## Como usar

- Crie ou carregue uma automacao pela lista lateral.
- Edite nome, pausa global, pausa inicial e fail-safe.
- Se quiser, ative a opcao de execucao em loop para reiniciar automaticamente apos o ultimo passo.
- Adicione passos pelo editor de acao.
- Reordene, edite, duplique ou remova passos na coluna central.
- Salve a automacao para gerar um JSON dentro da pasta `automacoes/`.
- Use os botoes de execucao para executar, pausar, continuar ou parar.

## Arquitetura resumida

- `automacao/`: catalogo de acoes, validacao, engine de execucao e servico com thread.
- `persistencia/`: leitura, escrita, listagem, renomeacao e exclusao de automacoes em JSON.
- `interface/`: janela principal, editor dinamico de acoes e cards dos passos.
- `modelos/`: estruturas compartilhadas da automacao e dos eventos de execucao.

Os JSONs continuam com campos em portugues e servem como formato interno de persistencia para toda a interface.

## Creditos

Desenvolvimento e conceito da ideia: `Joabe Alves`.
