"""
Utilitários de performance e profiling.
"""
import time
from functools import wraps
from src.infrastructure.logging.logger import get_logger


def timer(func):
    """Decorator para medir tempo de execução."""
    logger = get_logger(f"Timer.{func.__name__}")
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = (end - start) * 1000  # ms
        logger.debug(f"Executado em {elapsed:.2f}ms")
        return result
    
    return wrapper


class PerformanceMonitor:
    """Monitor de performance."""
    
    def __init__(self):
        self._metrics = {}
        self._log = get_logger("PerformanceMonitor")
    
    def record(self, metric_name: str, value: float) -> None:
        """Registra métrica."""
        if metric_name not in self._metrics:
            self._metrics[metric_name] = []
        
        self._metrics[metric_name].append(value)
        
        # Mantém apenas últimas 100 medições
        if len(self._metrics[metric_name]) > 100:
            self._metrics[metric_name].pop(0)
    
    def get_average(self, metric_name: str) -> float:
        """Retorna média de uma métrica."""
        if metric_name not in self._metrics or not self._metrics[metric_name]:
            return 0.0
        
        return sum(self._metrics[metric_name]) / len(self._metrics[metric_name])
    
    def get_stats(self, metric_name: str) -> dict:
        """Retorna estatísticas de uma métrica."""
        if metric_name not in self._metrics or not self._metrics[metric_name]:
            return {}
        
        values = self._metrics[metric_name]
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(values)
        }
    
    def report(self) -> None:
        """Imprime relatório de performance."""
        self._log.info("=" * 50)
        self._log.info("PERFORMANCE REPORT")
        self._log.info("=" * 50)
        
        for metric_name in self._metrics:
            stats = self.get_stats(metric_name)
            self._log.info(f"{metric_name}:")
            self._log.info(f"  Min: {stats['min']:.2f}ms")
            self._log.info(f"  Max: {stats['max']:.2f}ms")
            self._log.info(f"  Avg: {stats['avg']:.2f}ms")
        
        self._log.info("=" * 50)
