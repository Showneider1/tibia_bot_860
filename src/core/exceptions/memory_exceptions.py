"""
Exceções relacionadas a operações de memória.
"""


class MemoryException(Exception):
    """Exceção base para erros de memória."""
    pass


class MemoryReadError(MemoryException):
    """Erro ao ler memória."""
    pass


class MemoryWriteError(MemoryException):
    """Erro ao escrever memória."""
    pass


class ProcessNotFoundError(MemoryException):
    """Processo não encontrado."""
    pass


class ProcessAccessDeniedError(MemoryException):
    """Acesso ao processo negado."""
    pass
