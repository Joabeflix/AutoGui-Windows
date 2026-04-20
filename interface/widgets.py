from __future__ import annotations

from collections.abc import Callable
import ttkbootstrap as ttk

from automacao.catalogo import formatar_comando, obter_definicao


class CartaoPasso(ttk.Frame):
    def __init__(
        self,
        master,
        *,
        indice: int,
        comando: dict[str, object],
        em_execucao: bool,
        ao_editar: Callable[[int], None],
        ao_remover: Callable[[int], None],
        ao_duplicar: Callable[[int], None],
        ao_subir: Callable[[int], None],
        ao_descer: Callable[[int], None],
    ) -> None:
        super().__init__(master, padding=10, borderwidth=1, relief="solid")
        self.columnconfigure(1, weight=1)

        destaque = "info" if em_execucao else "secondary"
        ttk.Label(
            self,
            text=f"Passo {indice + 1:02d}",
            bootstyle=destaque,
            width=12,
        ).grid(row=0, column=0, sticky="nw", padx=(0, 10))

        conteudo = ttk.Frame(self)
        conteudo.grid(row=0, column=1, sticky="ew")
        conteudo.columnconfigure(0, weight=1)

        titulo = obter_definicao(str(comando["acao"])).titulo
        ttk.Label(
            conteudo,
            text=titulo,
            font=("", 11, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            conteudo,
            text=formatar_comando(comando),
            wraplength=520,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        if em_execucao:
            ttk.Label(
                conteudo,
                text="Executando agora",
                bootstyle="info",
            ).grid(row=2, column=0, sticky="w", pady=(6, 0))

        botoes = ttk.Frame(self)
        botoes.grid(row=0, column=2, sticky="ne", padx=(12, 0))

        ttk.Button(botoes, text="Subir", width=9, command=lambda: ao_subir(indice)).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(botoes, text="Descer", width=9, command=lambda: ao_descer(indice)).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(botoes, text="Editar", width=9, command=lambda: ao_editar(indice)).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(botoes, text="Duplicar", width=9, command=lambda: ao_duplicar(indice)).grid(row=1, column=1, padx=2, pady=2)
        ttk.Button(botoes, text="Remover", width=20, bootstyle="danger-outline", command=lambda: ao_remover(indice)).grid(row=2, column=0, columnspan=2, padx=2, pady=2, sticky="ew")
