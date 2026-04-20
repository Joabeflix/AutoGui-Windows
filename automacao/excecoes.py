class ErroAutomacao(Exception):
    """Erro base do dominio de automacao."""


class ErroValidacao(ErroAutomacao):
    """Erro para dados invalidos."""


class ErroAcaoInvalida(ErroAutomacao):
    """Erro para acoes nao suportadas."""


class ExecucaoInterrompida(ErroAutomacao):
    """Erro usado internamente quando a execucao e interrompida."""
