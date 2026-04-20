from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
import ttkbootstrap as ttk
from ttkbootstrap.tooltip import ToolTip
import pyautogui

try:
    import winsound
except ImportError:  # pragma: no cover
    winsound = None

from automacao.catalogo import DefinicaoAcao, listar_acoes, obter_definicao
from automacao.excecoes import ErroValidacao


class EditorAcaoFrame(ttk.Labelframe):
    def __init__(
        self,
        master,
        *,
        ao_salvar: Callable[[dict[str, object], int | None], None],
        ao_cancelar: Callable[[], None],
    ) -> None:
        super().__init__(master, text="Editor de acao", padding=12)
        self.ao_salvar = ao_salvar
        self.ao_cancelar = ao_cancelar
        self.indice_em_edicao: int | None = None
        self.acao_var = tk.StringVar(value=listar_acoes()[0])
        self.esperar_apos_var = tk.StringVar(value="0")
        self.status_captura_var = tk.StringVar(value="")
        self.vars_campos: dict[str, tk.StringVar] = {}
        self.widgets_dinamicos: list[tk.Widget] = []
        self._tooltips: list[ToolTip] = []
        self._after_captura: str | None = None
        self._segundos_restantes_captura = 0
        self.botao_capturar_posicao: ttk.Button | None = None
        self._montar()
        self.preparar_nova_acao()

    def _montar(self) -> None:
        self.columnconfigure(0, weight=1)

        label_tipo = ttk.Label(self, text="Tipo de acao")
        label_tipo.grid(row=0, column=0, sticky="w")
        self._adicionar_tooltip(
            label_tipo,
            "Escolha o tipo de passo que a automacao vai executar.",
        )
        combo = ttk.Combobox(
            self,
            textvariable=self.acao_var,
            values=listar_acoes(),
            state="readonly",
        )
        combo.grid(row=1, column=0, sticky="ew", pady=(4, 8))
        combo.bind("<<ComboboxSelected>>", self._ao_mudar_acao)
        self._adicionar_tooltip(
            combo,
            "Cada tipo de acao mostra campos diferentes, como texto, tecla, coordenadas ou segundos.",
        )

        self.label_descricao = ttk.Label(self, text="", wraplength=320, justify="left")
        self.label_descricao.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        self.frame_campos = ttk.Frame(self)
        self.frame_campos.grid(row=3, column=0, sticky="nsew")
        self.frame_campos.columnconfigure(0, weight=1)

        self.frame_captura = ttk.Frame(self)
        self.frame_captura.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        self.frame_captura.columnconfigure(0, weight=1)

        label_espera = ttk.Label(self, text="Esperar apos (segundos)")
        label_espera.grid(row=5, column=0, sticky="w", pady=(8, 0))
        self._adicionar_tooltip(
            label_espera,
            "Tempo extra de espera depois deste passo especifico.",
        )

        entrada_espera = ttk.Entry(self, textvariable=self.esperar_apos_var)
        entrada_espera.grid(row=6, column=0, sticky="ew", pady=(4, 8))
        self._adicionar_tooltip(
            entrada_espera,
            "Exemplo: 1 significa esperar 1 segundo depois de concluir esta acao.",
        )

        botoes = ttk.Frame(self)
        botoes.grid(row=7, column=0, sticky="ew", pady=(4, 0))
        botoes.columnconfigure((0, 1), weight=1)

        self.botao_salvar = ttk.Button(
            botoes,
            text="Adicionar acao",
            bootstyle="success",
            command=self._salvar,
        )
        self.botao_salvar.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self._adicionar_tooltip(
            self.botao_salvar,
            "Adiciona um novo passo ou salva as alteracoes do passo que voce esta editando.",
        )

        botao_cancelar = ttk.Button(
            botoes,
            text="Cancelar",
            bootstyle="secondary",
            command=self._cancelar,
        )
        botao_cancelar.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self._adicionar_tooltip(
            botao_cancelar,
            "Cancela a edicao atual e limpa o formulario.",
        )

    def preparar_nova_acao(self) -> None:
        self.indice_em_edicao = None
        self.botao_salvar.configure(text="Adicionar acao")
        self.acao_var.set(listar_acoes()[0])
        self.esperar_apos_var.set("0")
        self._reconstruir_campos(obter_definicao(self.acao_var.get()))

    def carregar_para_edicao(self, comando: dict[str, object], indice: int) -> None:
        acao = str(comando["acao"])
        self.indice_em_edicao = indice
        self.botao_salvar.configure(text="Salvar alteracoes")
        self.acao_var.set(acao)
        self.esperar_apos_var.set(str(comando.get("esperar_apos", 0)))
        definicao = obter_definicao(acao)
        self._reconstruir_campos(definicao)

        for campo in definicao.campos:
            valor = comando.get(campo.nome, campo.padrao)
            if isinstance(valor, list):
                valor = ", ".join(str(item) for item in valor)
            self.vars_campos[campo.nome].set("" if valor is None else str(valor))

    def _ao_mudar_acao(self, *_args) -> None:
        self._reconstruir_campos(obter_definicao(self.acao_var.get()))

    def _reconstruir_campos(self, definicao: DefinicaoAcao) -> None:
        self._cancelar_captura()
        for widget in self.widgets_dinamicos:
            widget.destroy()
        self.widgets_dinamicos.clear()
        self.vars_campos.clear()
        self.label_descricao.configure(text=definicao.descricao)
        self.status_captura_var.set("")
        self._renderizar_area_captura(definicao)

        linha = 0
        for campo in definicao.campos:
            rotulo = ttk.Label(self.frame_campos, text=campo.rotulo)
            rotulo.grid(row=linha, column=0, sticky="w")
            self.widgets_dinamicos.append(rotulo)
            self._adicionar_tooltip(rotulo, campo.ajuda or f"Preencha o campo '{campo.rotulo}'.")
            linha += 1

            var = tk.StringVar(value="" if campo.padrao == "" else str(campo.padrao))
            self.vars_campos[campo.nome] = var
            entrada = ttk.Entry(self.frame_campos, textvariable=var)
            entrada.grid(row=linha, column=0, sticky="ew", pady=(4, 2))
            self.widgets_dinamicos.append(entrada)
            self._adicionar_tooltip(
                entrada,
                campo.ajuda or f"Informe o valor de '{campo.rotulo}' para esta acao.",
            )
            linha += 1

            if campo.ajuda:
                ajuda = ttk.Label(self.frame_campos, text=campo.ajuda, wraplength=320, justify="left")
                ajuda.grid(row=linha, column=0, sticky="w", pady=(0, 6))
                self.widgets_dinamicos.append(ajuda)
                linha += 1

    def _renderizar_area_captura(self, definicao: DefinicaoAcao) -> None:
        for widget in self.frame_captura.winfo_children():
            widget.destroy()

        possui_coordenadas = {"x", "y"}.issubset({campo.nome for campo in definicao.campos})
        self.botao_capturar_posicao = None

        if not possui_coordenadas:
            return

        self.botao_capturar_posicao = ttk.Button(
            self.frame_captura,
            text="Capturar posicao do mouse",
            bootstyle="info-outline",
            command=self._iniciar_captura_posicao,
        )
        self.botao_capturar_posicao.grid(row=0, column=0, sticky="w")
        self._adicionar_tooltip(
            self.botao_capturar_posicao,
            "Clique aqui, leve o mouse ate o local desejado e aguarde 7 segundos para salvar X e Y automaticamente.",
        )

        label_status = ttk.Label(
            self.frame_captura,
            textvariable=self.status_captura_var,
            wraplength=320,
            justify="left",
            bootstyle="secondary",
        )
        label_status.grid(row=1, column=0, sticky="w", pady=(6, 0))

    def _iniciar_captura_posicao(self) -> None:
        if "x" not in self.vars_campos or "y" not in self.vars_campos:
            return

        self._cancelar_captura()
        self._segundos_restantes_captura = 7
        if self.botao_capturar_posicao is not None:
            self.botao_capturar_posicao.configure(state="disabled")
        self._atualizar_contagem_captura()

    def _atualizar_contagem_captura(self) -> None:
        if self._segundos_restantes_captura > 0:
            self.status_captura_var.set(
                f"Leve o mouse ate o ponto desejado. Captura em {self._segundos_restantes_captura} segundo(s)."
            )
            self._segundos_restantes_captura -= 1
            self._after_captura = self.after(1000, self._atualizar_contagem_captura)
            return

        posicao = pyautogui.position()
        self.vars_campos["x"].set(str(posicao.x))
        self.vars_campos["y"].set(str(posicao.y))
        self.status_captura_var.set(
            f"Posicao salva com sucesso: X={posicao.x} e Y={posicao.y}."
        )
        self._emitir_beep_confirmacao()
        if self.botao_capturar_posicao is not None:
            self.botao_capturar_posicao.configure(state="normal")
        self._after_captura = None

    def _cancelar_captura(self) -> None:
        if self._after_captura is not None:
            self.after_cancel(self._after_captura)
            self._after_captura = None
        self._segundos_restantes_captura = 0
        if self.botao_capturar_posicao is not None:
            self.botao_capturar_posicao.configure(state="normal")

    def _emitir_beep_confirmacao(self) -> None:
        if winsound is not None:
            winsound.MessageBeep()
            return
        self.bell()

    def _salvar(self) -> None:
        comando = self._coletar_comando()
        self.ao_salvar(comando, self.indice_em_edicao)

    def _coletar_comando(self) -> dict[str, object]:
        acao = self.acao_var.get()
        if not acao:
            raise ErroValidacao("Escolha um tipo de acao.")

        comando: dict[str, object] = {"acao": acao}
        for nome, var in self.vars_campos.items():
            valor = var.get().strip()
            if valor != "":
                comando[nome] = valor

        esperar_apos = self.esperar_apos_var.get().strip()
        comando["esperar_apos"] = esperar_apos or "0"
        return comando

    def _cancelar(self) -> None:
        self._cancelar_captura()
        self.preparar_nova_acao()
        self.ao_cancelar()

    def _adicionar_tooltip(self, widget, texto: str) -> None:
        self._tooltips.append(
            ToolTip(
                widget,
                text=texto,
                wraplength=280,
                delay=300,
                position="bottom left",
            )
        )
