from __future__ import annotations

import copy
import queue
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

import ttkbootstrap as ttk
from ttkbootstrap import Window
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tooltip import ToolTip

from automacao.excecoes import ErroValidacao
from automacao.servico_execucao import ServicoExecucao
from automacao.validacao import validar_automacao
from interface.editor_acao import EditorAcaoFrame
from interface.widgets import CartaoPasso
from modelos.automacao import Automacao, ConfiguracaoAutomacao, ResumoAutomacao
from modelos.execucao import EstadoExecucao, EventoExecucao
from persistencia.repositorio_automacoes import RepositorioAutomacoes
from utilitarios.caminhos import caminho_recurso


class AplicacaoAutomacao(Window):
    def __init__(self) -> None:
        super().__init__(themename="flatly")
        self.title("Plataforma Visual de Automacao")
        self.geometry("1500x900")
        self.minsize(1280, 760)
        self._aplicar_icone_janela()

        self.repositorio = RepositorioAutomacoes()
        self.fila_eventos: queue.Queue[EventoExecucao] = queue.Queue()
        self.servico_execucao = ServicoExecucao(self.fila_eventos.put)
        self.automacao_atual = self._nova_estrutura_automacao()
        self.resumos_automacoes: list[ResumoAutomacao] = []
        self.indice_passo_em_execucao: int | None = None

        self.nome_var = tk.StringVar(value=self.automacao_atual.nome)
        self.pausa_global_var = tk.StringVar(value=str(self.automacao_atual.configuracao.pausa_global))
        self.pausa_inicial_var = tk.StringVar(value=str(self.automacao_atual.configuracao.pausa_inicial))
        self.fail_safe_var = tk.BooleanVar(value=self.automacao_atual.configuracao.fail_safe)
        self.executar_em_loop_var = tk.BooleanVar(value=self.automacao_atual.configuracao.executar_em_loop)
        self.estado_var = tk.StringVar(value="Parada")
        self.status_var = tk.StringVar(value="Pronto para criar ou carregar uma automacao.")
        self._tooltips: list[ToolTip] = []

        self._montar_layout()
        self._carregar_lista_automacoes()
        self._renderizar_passos()
        self.after(120, self._processar_eventos)

    def _montar_layout(self) -> None:
        self.columnconfigure(1, weight=3)
        self.columnconfigure(2, weight=2)
        self.rowconfigure(0, weight=1)

        self._montar_painel_esquerdo()
        self._montar_painel_central()
        self._montar_painel_direito()

        barra_status = ttk.Frame(self, padding=(12, 6))
        barra_status.grid(row=1, column=0, columnspan=3, sticky="ew")
        barra_status.columnconfigure(0, weight=1)
        ttk.Label(barra_status, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        ttk.Label(
            barra_status,
            text="Desenvolvimento e conceito: Joabe Alves",
            bootstyle="secondary",
        ).grid(row=0, column=1, sticky="e", padx=(12, 12))
        ttk.Label(barra_status, text="Estado:").grid(row=0, column=2, sticky="e", padx=(0, 6))
        ttk.Label(barra_status, textvariable=self.estado_var, bootstyle="info").grid(row=0, column=3, sticky="e")

    def _aplicar_icone_janela(self) -> None:
        caminho_icone = caminho_recurso("assets", "logo.ico")
        if caminho_icone.exists():
            try:
                self.iconbitmap(default=str(caminho_icone))
            except Exception:
                pass

    def _montar_painel_esquerdo(self) -> None:
        frame = ttk.Labelframe(self, text="Automacoes salvas", padding=12)
        frame.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(
            frame,
            text="Selecione uma automacao para abrir ou crie uma nova.",
            wraplength=220,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        lista_frame = ttk.Frame(frame)
        lista_frame.grid(row=1, column=0, sticky="nsew")
        lista_frame.columnconfigure(0, weight=1)
        lista_frame.rowconfigure(0, weight=1)

        self.lista_automacoes = tk.Listbox(lista_frame, activestyle="none")
        self.lista_automacoes.grid(row=0, column=0, sticky="nsew")
        self.lista_automacoes.bind("<<ListboxSelect>>", self._ao_selecionar_automacao)
        self._adicionar_tooltip(
            self.lista_automacoes,
            "Mostra os arquivos JSON ja salvos. Clique em um item para abrir a automacao na tela.",
        )

        scrollbar = ttk.Scrollbar(lista_frame, orient="vertical", command=self.lista_automacoes.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.lista_automacoes.configure(yscrollcommand=scrollbar.set)

        botoes = ttk.Frame(frame)
        botoes.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        botoes.columnconfigure((0, 1), weight=1)

        botao_nova = ttk.Button(botoes, text="Nova automacao", bootstyle="success", command=self._nova_automacao)
        botao_nova.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=4)
        self._adicionar_tooltip(
            botao_nova,
            "Cria uma automacao nova em branco para voce comecar do zero.",
        )

        botao_excluir = ttk.Button(botoes, text="Excluir automacao", bootstyle="danger", command=self._excluir_automacao_atual)
        botao_excluir.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=4)
        self._adicionar_tooltip(
            botao_excluir,
            "Apaga o arquivo JSON da automacao atual depois de pedir confirmacao.",
        )

        botao_recarregar = ttk.Button(botoes, text="Recarregar lista", command=self._carregar_lista_automacoes)
        botao_recarregar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=4)
        self._adicionar_tooltip(
            botao_recarregar,
            "Atualiza a lista de automacoes para mostrar arquivos novos ou alterados na pasta 'automacoes'.",
        )

    def _montar_painel_central(self) -> None:
        frame = ttk.Labelframe(self, text="Sequencia da automacao", padding=12)
        frame.grid(row=0, column=1, sticky="nsew", padx=6, pady=12)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        cabecalho = ttk.Frame(frame)
        cabecalho.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        cabecalho.columnconfigure(0, weight=1)

        ttk.Label(
            cabecalho,
            text="Os passos aparecem em ordem de execucao para facilitar a visualizacao.",
            wraplength=720,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        botao_adicionar = ttk.Button(
            cabecalho,
            text="Adicionar acao",
            bootstyle="primary",
            command=self._preparar_nova_acao,
        )
        botao_adicionar.grid(row=0, column=1, sticky="e")
        self._adicionar_tooltip(
            botao_adicionar,
            "Abre o editor de acao para incluir um novo passo na sequencia da automacao.",
        )

        self.scrolled_passos = ScrolledFrame(frame, autohide=True)
        self.scrolled_passos.grid(row=1, column=0, sticky="nsew")

    def _montar_painel_direito(self) -> None:
        frame = ttk.Frame(self)
        frame.grid(row=0, column=2, sticky="nsew", padx=(6, 12), pady=12)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=1)

        self._montar_dados_automacao(frame)
        self._montar_execucao(frame)
        self.editor_acao = EditorAcaoFrame(
            frame,
            ao_salvar=self._salvar_acao_do_editor,
            ao_cancelar=self._mensagem_status_limpa,
        )
        self.editor_acao.grid(row=2, column=0, sticky="ew", pady=(10, 10))
        self._montar_log(frame)

    def _montar_dados_automacao(self, master) -> None:
        frame = ttk.Labelframe(master, text="Dados da automacao", padding=12)
        frame.grid(row=0, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        label_nome = ttk.Label(frame, text="Nome")
        label_nome.grid(row=0, column=0, columnspan=2, sticky="w")
        self._adicionar_tooltip(
            label_nome,
            "Nome amigavel da automacao. Esse nome tambem sera usado para gerar o nome do arquivo JSON.",
        )

        entrada_nome = ttk.Entry(frame, textvariable=self.nome_var)
        entrada_nome.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        self._adicionar_tooltip(
            entrada_nome,
            "Escolha um nome facil de reconhecer, como 'Cadastro de pedidos' ou 'Abrir sistema'.",
        )

        label_pausa_global = ttk.Label(frame, text="Pausa global")
        label_pausa_global.grid(row=2, column=0, sticky="w")
        self._adicionar_tooltip(
            label_pausa_global,
            "Tempo padrao entre uma acao e outra do pyautogui. Ajuda a deixar a automacao menos apressada.",
        )

        label_pausa_inicial = ttk.Label(frame, text="Pausa inicial")
        label_pausa_inicial.grid(row=2, column=1, sticky="w")
        self._adicionar_tooltip(
            label_pausa_inicial,
            "Tempo de espera antes da automacao comecar. Use para posicionar a tela manualmente antes do inicio.",
        )

        entrada_pausa_global = ttk.Entry(frame, textvariable=self.pausa_global_var)
        entrada_pausa_global.grid(row=3, column=0, sticky="ew", pady=(4, 8), padx=(0, 4))
        self._adicionar_tooltip(
            entrada_pausa_global,
            "Exemplo: 0.3 significa uma pausa curta entre chamadas do pyautogui.",
        )

        entrada_pausa_inicial = ttk.Entry(frame, textvariable=self.pausa_inicial_var)
        entrada_pausa_inicial.grid(row=3, column=1, sticky="ew", pady=(4, 8), padx=(4, 0))
        self._adicionar_tooltip(
            entrada_pausa_inicial,
            "Exemplo: 5 significa esperar 5 segundos antes de executar o primeiro passo.",
        )

        check_fail_safe = ttk.Checkbutton(
            frame,
            text="Ativar fail-safe do pyautogui",
            variable=self.fail_safe_var,
            bootstyle="round-toggle",
        )
        check_fail_safe.grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self._adicionar_tooltip(
            check_fail_safe,
            "Se estiver ativado, mover o mouse rapidamente para um canto da tela interrompe a automacao. "
            "E uma protecao importante para emergencias.",
        )

        check_loop = ttk.Checkbutton(
            frame,
            text="Executar em loop",
            variable=self.executar_em_loop_var,
            bootstyle="round-toggle",
        )
        check_loop.grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self._adicionar_tooltip(
            check_loop,
            "Se estiver ativado, ao terminar o ultimo passo a automacao volta para o primeiro e continua ate voce parar.",
        )

        botoes = ttk.Frame(frame)
        botoes.grid(row=6, column=0, columnspan=2, sticky="ew")
        botoes.columnconfigure((0, 1), weight=1)

        botao_salvar = ttk.Button(botoes, text="Salvar automacao", bootstyle="success", command=self._salvar_automacao)
        botao_salvar.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self._adicionar_tooltip(
            botao_salvar,
            "Salva ou atualiza o arquivo JSON da automacao atual dentro da pasta 'automacoes'.",
        )

        botao_validar = ttk.Button(botoes, text="Validar automacao", bootstyle="info-outline", command=self._validar_automacao_atual)
        botao_validar.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self._adicionar_tooltip(
            botao_validar,
            "Confere se os campos obrigatorios foram preenchidos corretamente antes de salvar ou executar.",
        )

    def _montar_execucao(self, master) -> None:
        frame = ttk.Labelframe(master, text="Execucao", padding=12)
        frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        frame.columnconfigure((0, 1), weight=1)

        ttk.Label(
            frame,
            text="Use os controles abaixo para executar, pausar, continuar ou parar a automacao atual.",
            wraplength=360,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        botao_executar = ttk.Button(frame, text="Executar", bootstyle="success", command=self._executar_automacao)
        botao_executar.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=4)
        self._adicionar_tooltip(
            botao_executar,
            "Inicia a automacao atual sem travar a interface. A execucao acontece em segundo plano.",
        )

        botao_pausar = ttk.Button(frame, text="Pausar", bootstyle="warning", command=self._pausar_automacao)
        botao_pausar.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=4)
        self._adicionar_tooltip(
            botao_pausar,
            "Pausa a automacao no ponto atual. Use 'Continuar' para retomar de onde parou.",
        )

        botao_continuar = ttk.Button(frame, text="Continuar", bootstyle="info", command=self._continuar_automacao)
        botao_continuar.grid(row=2, column=0, sticky="ew", padx=(0, 4), pady=4)
        self._adicionar_tooltip(
            botao_continuar,
            "Retoma uma automacao que esteja pausada.",
        )

        botao_parar = ttk.Button(frame, text="Parar", bootstyle="danger", command=self._parar_automacao)
        botao_parar.grid(row=2, column=1, sticky="ew", padx=(4, 0), pady=4)
        self._adicionar_tooltip(
            botao_parar,
            "Solicita a interrupcao da automacao. A parada acontece assim que o executor atingir um ponto seguro.",
        )

    def _montar_log(self, master) -> None:
        frame = ttk.Labelframe(master, text="Log de execucao", padding=12)
        frame.grid(row=3, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.caixa_log = ScrolledText(frame, height=14, wrap="word")
        self.caixa_log.grid(row=0, column=0, sticky="nsew")
        self.caixa_log.configure(state="disabled")

    def _nova_estrutura_automacao(self) -> Automacao:
        return Automacao(
            nome="Nova automacao",
            configuracao=ConfiguracaoAutomacao(),
            comandos=[],
        )

    def _nova_automacao(self) -> None:
        if self._execucao_ativa():
            self._mostrar_erro("Pare a automacao atual antes de trocar de cadastro.")
            return
        self.automacao_atual = self._nova_estrutura_automacao()
        self._popular_campos_da_automacao()
        self.editor_acao.preparar_nova_acao()
        self.indice_passo_em_execucao = None
        self._renderizar_passos()
        self._registrar_log("Nova automacao criada na tela.")
        self.status_var.set("Nova automacao pronta para edicao.")

    def _carregar_lista_automacoes(self) -> None:
        self.resumos_automacoes = self.repositorio.listar()
        self.lista_automacoes.delete(0, tk.END)

        for resumo in self.resumos_automacoes:
            sufixo = "" if resumo.valido else " (arquivo com erro)"
            self.lista_automacoes.insert(tk.END, resumo.nome + sufixo)

        self.status_var.set(f"{len(self.resumos_automacoes)} automacao(oes) encontrada(s).")

    def _ao_selecionar_automacao(self, _evento=None) -> None:
        if self._execucao_ativa():
            return

        selecao = self.lista_automacoes.curselection()
        if not selecao:
            return

        resumo = self.resumos_automacoes[selecao[0]]
        if not resumo.valido:
            self._mostrar_erro(
                f"Nao foi possivel abrir '{resumo.nome}'.\n\nDetalhe: {resumo.mensagem_erro}"
            )
            return

        try:
            self.automacao_atual = self.repositorio.carregar(resumo.caminho)
        except Exception as exc:
            self._mostrar_erro(f"Falha ao carregar automacao: {exc}")
            return

        self._popular_campos_da_automacao()
        self.editor_acao.preparar_nova_acao()
        self.indice_passo_em_execucao = None
        self._renderizar_passos()
        self._registrar_log(f"Automacao '{self.automacao_atual.nome}' carregada.")
        self.status_var.set(f"Automacao '{self.automacao_atual.nome}' aberta para edicao.")

    def _popular_campos_da_automacao(self) -> None:
        self.nome_var.set(self.automacao_atual.nome)
        self.pausa_global_var.set(str(self.automacao_atual.configuracao.pausa_global))
        self.pausa_inicial_var.set(str(self.automacao_atual.configuracao.pausa_inicial))
        self.fail_safe_var.set(self.automacao_atual.configuracao.fail_safe)
        self.executar_em_loop_var.set(self.automacao_atual.configuracao.executar_em_loop)

    def _coletar_automacao_da_tela(self) -> Automacao:
        automacao = Automacao(
            nome=self.nome_var.get().strip(),
            configuracao=ConfiguracaoAutomacao(
                pausa_global=self.pausa_global_var.get().strip(),
                pausa_inicial=self.pausa_inicial_var.get().strip(),
                fail_safe=self.fail_safe_var.get(),
                executar_em_loop=self.executar_em_loop_var.get(),
            ),
            comandos=copy.deepcopy(self.automacao_atual.comandos),
            caminho_arquivo=self.automacao_atual.caminho_arquivo,
        )
        return validar_automacao(automacao, permitir_sem_comandos=True)

    def _salvar_automacao(self) -> None:
        if self._execucao_ativa():
            self._mostrar_erro("Pare a automacao atual antes de salvar.")
            return

        try:
            automacao = self._coletar_automacao_da_tela()
            caminho = self.repositorio.salvar(automacao)
        except Exception as exc:
            self._mostrar_erro(f"Nao foi possivel salvar a automacao.\n\n{exc}")
            return

        self.automacao_atual = automacao
        self.automacao_atual.caminho_arquivo = caminho
        self._carregar_lista_automacoes()
        self._selecionar_item_por_caminho(caminho)
        self._registrar_log(f"Automacao '{automacao.nome}' salva em {caminho.name}.")
        self.status_var.set(f"Automacao '{automacao.nome}' salva com sucesso.")

    def _validar_automacao_atual(self) -> None:
        try:
            validar_automacao(self._coletar_automacao_da_tela(), permitir_sem_comandos=False)
        except Exception as exc:
            self._mostrar_erro(f"Validacao falhou.\n\n{exc}")
            return
        self.status_var.set("Automacao validada com sucesso.")
        self._registrar_log("Validacao concluida sem erros.")

    def _excluir_automacao_atual(self) -> None:
        if self._execucao_ativa():
            self._mostrar_erro("Pare a automacao atual antes de excluir.")
            return

        caminho = self.automacao_atual.caminho_arquivo
        if not caminho:
            self._mostrar_erro("Essa automacao ainda nao foi salva.")
            return

        confirmar = messagebox.askyesno(
            "Confirmar exclusao",
            f"Deseja realmente excluir a automacao '{self.automacao_atual.nome}'?",
            parent=self,
        )
        if not confirmar:
            return

        self.repositorio.excluir(caminho)
        nome = self.automacao_atual.nome
        self._nova_automacao()
        self._carregar_lista_automacoes()
        self.status_var.set(f"Automacao '{nome}' excluida.")

    def _preparar_nova_acao(self) -> None:
        self.editor_acao.preparar_nova_acao()
        self.status_var.set("Preencha os dados da nova acao no editor ao lado.")

    def _salvar_acao_do_editor(self, comando_bruto: dict[str, object], indice: int | None) -> None:
        try:
            comando_validado = validar_automacao(
                {
                    "nome": "Validacao interna",
                    "configuracao": {
                        "pausa_global": 0.0,
                        "fail_safe": True,
                        "pausa_inicial": 0.0,
                    },
                    "comandos": [comando_bruto],
                },
                permitir_sem_comandos=False,
            ).comandos[0]
        except ErroValidacao as exc:
            self._mostrar_erro(str(exc))
            return

        if indice is None:
            self.automacao_atual.comandos.append(comando_validado)
            self.status_var.set("Acao adicionada com sucesso.")
        else:
            self.automacao_atual.comandos[indice] = comando_validado
            self.status_var.set(f"Passo {indice + 1} atualizado.")

        self.editor_acao.preparar_nova_acao()
        self._renderizar_passos()

    def _mensagem_status_limpa(self) -> None:
        self.status_var.set("Edicao de acao cancelada.")

    def _editar_comando(self, indice: int) -> None:
        self.editor_acao.carregar_para_edicao(self.automacao_atual.comandos[indice], indice)
        self.status_var.set(f"Editando passo {indice + 1}.")

    def _remover_comando(self, indice: int) -> None:
        self.automacao_atual.comandos.pop(indice)
        self.editor_acao.preparar_nova_acao()
        self._renderizar_passos()
        self.status_var.set(f"Passo {indice + 1} removido.")

    def _duplicar_comando(self, indice: int) -> None:
        self.automacao_atual.comandos.insert(
            indice + 1,
            copy.deepcopy(self.automacao_atual.comandos[indice]),
        )
        self._renderizar_passos()
        self.status_var.set(f"Passo {indice + 1} duplicado.")

    def _mover_comando(self, indice: int, deslocamento: int) -> None:
        novo_indice = indice + deslocamento
        if novo_indice < 0 or novo_indice >= len(self.automacao_atual.comandos):
            return
        comandos = self.automacao_atual.comandos
        comandos[indice], comandos[novo_indice] = comandos[novo_indice], comandos[indice]
        self._renderizar_passos()
        self.status_var.set("Ordem dos passos atualizada.")

    def _renderizar_passos(self) -> None:
        for widget in self.scrolled_passos.winfo_children():
            widget.destroy()

        if not self.automacao_atual.comandos:
            vazio = ttk.Label(
                self.scrolled_passos,
                text="Nenhum passo cadastrado ainda. Use o botao 'Adicionar acao' para montar a automacao.",
                wraplength=720,
                justify="left",
            )
            vazio.pack(fill="x", padx=8, pady=8)
            return

        for indice, comando in enumerate(self.automacao_atual.comandos):
            cartao = CartaoPasso(
                self.scrolled_passos,
                indice=indice,
                comando=comando,
                em_execucao=indice == self.indice_passo_em_execucao,
                ao_editar=self._editar_comando,
                ao_remover=self._remover_comando,
                ao_duplicar=self._duplicar_comando,
                ao_subir=lambda idx: self._mover_comando(idx, -1),
                ao_descer=lambda idx: self._mover_comando(idx, 1),
            )
            cartao.pack(fill="x", padx=8, pady=6)

    def _executar_automacao(self) -> None:
        try:
            automacao = self._coletar_automacao_da_tela()
            validar_automacao(automacao, permitir_sem_comandos=False)
            self.servico_execucao.executar(automacao)
        except Exception as exc:
            self._mostrar_erro(f"Nao foi possivel iniciar a automacao.\n\n{exc}")
            return

        self._registrar_log(f"Iniciando execucao de '{automacao.nome}'.")
        self.status_var.set("Execucao iniciada.")

    def _pausar_automacao(self) -> None:
        self.servico_execucao.pausar()

    def _continuar_automacao(self) -> None:
        self.servico_execucao.continuar_execucao()

    def _parar_automacao(self) -> None:
        self.servico_execucao.parar()

    def _processar_eventos(self) -> None:
        while not self.fila_eventos.empty():
            evento = self.fila_eventos.get_nowait()
            self._tratar_evento_execucao(evento)
        self.after(120, self._processar_eventos)

    def _tratar_evento_execucao(self, evento: EventoExecucao) -> None:
        if evento.tipo == "estado":
            estado = evento.estado or EstadoExecucao.PARADA
            self.estado_var.set(str(estado).capitalize())
            if estado == EstadoExecucao.PARADA:
                self.indice_passo_em_execucao = None
                self._renderizar_passos()
            return

        if evento.tipo == "passo":
            self.indice_passo_em_execucao = evento.indice_passo
            self._renderizar_passos()
            return

        if evento.tipo == "log":
            self._registrar_log(evento.mensagem)
            self.status_var.set(evento.mensagem)
            return

        if evento.tipo == "erro":
            self._registrar_log(evento.mensagem)
            self._mostrar_erro(evento.mensagem)

    def _registrar_log(self, mensagem: str) -> None:
        self.caixa_log.configure(state="normal")
        self.caixa_log.insert(tk.END, mensagem + "\n")
        self.caixa_log.see(tk.END)
        self.caixa_log.configure(state="disabled")

    def _mostrar_erro(self, mensagem: str) -> None:
        self.status_var.set(mensagem.splitlines()[0])
        messagebox.showerror("Aviso", mensagem, parent=self)

    def _selecionar_item_por_caminho(self, caminho) -> None:
        for indice, resumo in enumerate(self.resumos_automacoes):
            if resumo.caminho == caminho:
                self.lista_automacoes.selection_clear(0, tk.END)
                self.lista_automacoes.selection_set(indice)
                self.lista_automacoes.activate(indice)
                break

    def _execucao_ativa(self) -> bool:
        return self.servico_execucao.estado != EstadoExecucao.PARADA

    def _adicionar_tooltip(self, widget, texto: str) -> None:
        self._tooltips.append(
            ToolTip(
                widget,
                text=texto,
                wraplength=320,
                delay=300,
                position="bottom left",
            )
        )


def iniciar_aplicacao() -> None:
    app = AplicacaoAutomacao()
    app.mainloop()
