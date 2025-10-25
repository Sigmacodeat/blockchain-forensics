"""
Performance-Optimierungen für Enterprise-Scale Blockchain Forensik
================================================================

Optimierungen für:
- Millionen Transaktionen
- Parallele Verarbeitung
- Datenbank-Optimierungen
- Caching-Strategien
- Memory-Management
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance-Metriken für Monitoring"""
    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    records_processed: int = 0
    memory_used_mb: float = 0
    cpu_time_seconds: float = 0

    def complete(self):
        """Markiert Operation als abgeschlossen"""
        self.end_time = datetime.utcnow()

    @property
    def duration_seconds(self) -> float:
        """Berechnet Dauer"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    @property
    def throughput_per_second(self) -> float:
        """Berechnet Durchsatz"""
        if self.duration_seconds > 0:
            return self.records_processed / self.duration_seconds
        return 0


class ParallelProcessor:
    """Parallele Verarbeitung für große Datenmengen"""

    def __init__(self, max_workers: int = 10, batch_size: int = 1000):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_batch_parallel(self, items: List[Any], processor_func, **kwargs) -> List[Any]:
        """Verarbeitet Items parallel in Batches"""
        if not items:
            return []

        results = []
        batches = [items[i:i + self.batch_size] for i in range(0, len(items), self.batch_size)]

        # Parallele Verarbeitung der Batches
        loop = asyncio.get_event_loop()

        for batch in batches:
            # Führe Batch-Verarbeitung parallel aus
            tasks = [
                loop.run_in_executor(self.executor, processor_func, item, **kwargs)
                for item in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Sammle Ergebnisse und Fehler
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                else:
                    results.append(result)

        return results

    def __del__(self):
        """Cleanup Executor"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)


class DatabaseOptimizer:
    """Datenbank-Optimierungen für große Datenmengen"""

    def __init__(self):
        self.indexes_created = False

    def optimize_indexes(self, db_connection):
        """Erstellt optimale Indexes für Forensik-Abfragen"""
        if self.indexes_created:
            return

        # Performance-kritische Indexes
        indexes = [
            # Adress-basierte Abfragen
            "CREATE INDEX IF NOT EXISTS idx_addresses_risk_score ON addresses (risk_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_addresses_last_seen ON addresses (last_seen DESC)",
            "CREATE INDEX IF NOT EXISTS idx_addresses_chain_labels ON addresses (chain, labels)",

            # Transaktions-basierte Abfragen
            "CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions (timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_value ON transactions (value_usd DESC)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_addresses ON transactions (from_address, to_address)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_hash ON transactions (tx_hash)",

            # Alert-basierte Abfragen
            "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts (timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts (severity)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_type_address ON alerts (alert_type, address)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts (acknowledged)",

            # Cross-Chain Abfragen
            "CREATE INDEX IF NOT EXISTS idx_bridge_events_timestamp ON bridge_events (timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_bridge_events_chains ON bridge_events (from_chain, to_chain)",

            # Graph-Abfragen für Beziehungsanalyse
            "CREATE INDEX IF NOT EXISTS idx_graph_nodes_address ON graph_nodes (address)",
            "CREATE INDEX IF NOT EXISTS idx_graph_edges_source_target ON graph_edges (source_address, target_address)",
        ]

        for index_sql in indexes:
            try:
                db_connection.execute(index_sql)
                logger.info(f"Created index: {index_sql.split()[:3]}")
            except Exception as e:
                logger.warning(f"Could not create index: {e}")

        self.indexes_created = True

    def optimize_queries(self, query: str, params: Dict = None) -> str:
        """Optimiert Abfragen für bessere Performance"""
        # Query-Optimierungen
        optimizations = [
            # Force Index Hints für kritische Abfragen
            (r"SELECT.*FROM transactions", "SELECT /*+ FORCE_INDEX(transactions idx_transactions_timestamp) */ * FROM transactions"),
            (r"SELECT.*FROM addresses", "SELECT /*+ FORCE_INDEX(addresses idx_addresses_risk_score) */ * FROM addresses"),
        ]

        optimized_query = query
        for pattern, replacement in optimizations:
            import re
            optimized_query = re.sub(pattern, replacement, optimized_query)

        return optimized_query


class CachingLayer:
    """Erweiterte Caching-Strategie"""

    def __init__(self):
        self.memory_cache = {}
        self.redis_cache = None  # Platzhalter für Redis
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

    @lru_cache(maxsize=10000)
    def get_cached_address_data(self, address: str, chain: str) -> Optional[Dict]:
        """Cached Address-Daten"""
        return self._load_address_data(address, chain)

    def _load_address_data(self, address: str, chain: str) -> Optional[Dict]:
        """Lädt Address-Daten aus Datenbank"""
        # Platzhalter - echte Implementierung würde DB-Abfrage machen
        self.cache_stats["misses"] += 1
        return {"address": address, "chain": chain, "cached": True}

    def cache_transaction_batch(self, transactions: List[Dict], ttl_seconds: int = 300):
        """Cached Transaktions-Batch"""
        batch_key = f"tx_batch_{hash(str(transactions))}"

        # Memory Cache
        self.memory_cache[batch_key] = {
            "data": transactions,
            "timestamp": datetime.utcnow(),
            "ttl": ttl_seconds
        }

        # Redis Cache (falls verfügbar)
        if self.redis_cache:
            self.redis_cache.setex(batch_key, ttl_seconds, str(transactions))

    def get_cached_batch(self, batch_key: str) -> Optional[List[Dict]]:
        """Holt gecachte Transaktions-Batch"""
        # Prüfe Memory Cache
        if batch_key in self.memory_cache:
            cached = self.memory_cache[batch_key]
            if (datetime.utcnow() - cached["timestamp"]).total_seconds() < cached["ttl"]:
                self.cache_stats["hits"] += 1
                return cached["data"]

        # Prüfe Redis Cache
        if self.redis_cache:
            cached_data = self.redis_cache.get(batch_key)
            if cached_data:
                self.cache_stats["hits"] += 1
                return eval(cached_data)  # Sicherheitsrisiko in Produktion vermeiden

        self.cache_stats["misses"] += 1
        return None

    def cleanup_expired_cache(self):
        """Bereinigt abgelaufene Cache-Einträge"""
        now = datetime.utcnow()
        expired_keys = []

        for key, cached in self.memory_cache.items():
            if (now - cached["timestamp"]).total_seconds() > cached["ttl"]:
                expired_keys.append(key)

        for key in expired_keys:
            del self.memory_cache[key]
            self.cache_stats["evictions"] += 1

        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


class MemoryManager:
    """Memory-Management für große Datenmengen"""

    def __init__(self):
        self.memory_threshold_mb = 1000  # 1GB
        self.current_memory_mb = 0

    def check_memory_usage(self) -> Dict[str, Any]:
        """Prüft Memory-Verbrauch"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "threshold_mb": self.memory_threshold_mb,
            "usage_percentage": (memory_info.rss / 1024 / 1024) / self.memory_threshold_mb * 100
        }

    def should_throttle_processing(self) -> bool:
        """Entscheidet ob Verarbeitung gedrosselt werden sollte"""
        memory_info = self.check_memory_usage()
        return memory_info["usage_percentage"] > 80  # Throttle bei >80% Memory

    def force_garbage_collection(self):
        """Erzwingt Garbage Collection"""
        import gc
        gc.collect()
        logger.info("Forced garbage collection")

    def optimize_memory_usage(self, large_data_structure: Any):
        """Optimiert Memory-Verbrauch großer Datenstrukturen"""
        # Für sehr große Listen/Dicts: Chunking und Streaming
        if isinstance(large_data_structure, list) and len(large_data_structure) > 100000:
            return self._chunk_large_list(large_data_structure)
        elif isinstance(large_data_structure, dict) and len(large_data_structure) > 10000:
            return self._chunk_large_dict(large_data_structure)
        else:
            return large_data_structure

    def _chunk_large_list(self, large_list: List, chunk_size: int = 10000) -> Generator[List, None, None]:
        """Teilt große Listen in Chunks auf"""
        for i in range(0, len(large_list), chunk_size):
            yield large_list[i:i + chunk_size]

    def _chunk_large_dict(self, large_dict: Dict, chunk_size: int = 1000) -> Generator[Dict, None, None]:
        """Teilt große Dicts in Chunks auf"""
        items = list(large_dict.items())
        for i in range(0, len(items), chunk_size):
            yield dict(items[i:i + chunk_size])


class AsyncBatchProcessor:
    """Asynchrone Batch-Verarbeitung für hohe Durchsätze"""

    def __init__(self, batch_size: int = 1000, max_concurrent_batches: int = 5):
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.processing_queue = asyncio.Queue()
        self.results = []
        self.is_processing = False

    async def start_processing(self, processor_func, **kwargs):
        """Startet asynchrone Batch-Verarbeitung"""
        if self.is_processing:
            return

        self.is_processing = True
        self.results = []

        # Starte Worker-Tasks
        workers = [
            asyncio.create_task(self._batch_worker(processor_func, **kwargs))
            for _ in range(self.max_concurrent_batches)
        ]

        # Warte auf alle Worker
        await asyncio.gather(*workers)
        self.is_processing = False

    async def _batch_worker(self, processor_func, **kwargs):
        """Worker für Batch-Verarbeitung"""
        while True:
            try:
                batch = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)
                if batch is None:  # Sentinel value
                    break

                # Verarbeite Batch
                start_time = time.time()
                results = await processor_func(batch, **kwargs)
                processing_time = time.time() - start_time

                self.results.extend(results)
                logger.debug(f"Processed batch of {len(batch)} items in {processing_time:.2f}s")

                self.processing_queue.task_done()

            except asyncio.TimeoutError:
                # Keine Batches mehr verfügbar
                break
            except Exception as e:
                logger.error(f"Batch worker error: {e}")

    async def add_batch(self, batch: List[Any]):
        """Fügt Batch zur Verarbeitung hinzu"""
        await self.processing_queue.put(batch)

    async def finish_processing(self):
        """Beendet Verarbeitung"""
        # Sende Sentinel values für alle Worker
        for _ in range(self.max_concurrent_batches):
            await self.processing_queue.put(None)

        # Warte auf Queue-Entleerung
        await self.processing_queue.join()


class EnterprisePerformanceOptimizer:
    """Haupt-Optimierer für Enterprise-Performance"""

    def __init__(self):
        self.parallel_processor = ParallelProcessor(max_workers=20, batch_size=5000)
        self.db_optimizer = DatabaseOptimizer()
        self.cache_layer = CachingLayer()
        self.memory_manager = MemoryManager()
        self.batch_processor = AsyncBatchProcessor(batch_size=2000, max_concurrent_batches=10)

    async def optimize_for_large_scale(self, operation: str, data: Any) -> Dict[str, Any]:
        """Optimiert Operation für große Datenmengen"""
        metrics = PerformanceMetrics(operation=operation, start_time=datetime.utcnow())

        try:
            # Memory-Check
            if self.memory_manager.should_throttle_processing():
                logger.warning("High memory usage detected, throttling processing")
                await asyncio.sleep(1)  # Throttle

            # Daten-Optimierung
            if isinstance(data, (list, dict)) and len(data) > 10000:
                data = self.memory_manager.optimize_memory_usage(data)

            # Parallele Verarbeitung für große Datenmengen
            if isinstance(data, list) and len(data) > 1000:
                results = await self.parallel_processor.process_batch_parallel(
                    data, self._process_single_item, operation=operation
                )
            else:
                results = await self._process_sequential(data, operation)

            metrics.records_processed = len(results) if results else 0
            metrics.complete()

            logger.info(f"Operation {operation} completed: {metrics.throughput_per_second:.0f} records/s")

            return {
                "results": results,
                "metrics": {
                    "duration_seconds": metrics.duration_seconds,
                    "records_processed": metrics.records_processed,
                    "throughput_per_second": metrics.throughput_per_second,
                    "memory_usage_mb": self.memory_manager.check_memory_usage()["rss_mb"]
                }
            }

        except Exception as e:
            logger.error(f"Performance optimization error: {e}")
            metrics.complete()
            raise

    async def _process_single_item(self, item: Any, operation: str) -> Any:
        """Verarbeitet einzelnes Item"""
        # Platzhalter - echte Implementierung würde spezifische Verarbeitung machen
        await asyncio.sleep(0.001)  # Simuliere Verarbeitungszeit
        return {"processed": True, "item_id": id(item), "operation": operation}

    async def _process_sequential(self, data: Any, operation: str) -> List[Any]:
        """Sequentielle Verarbeitung für kleine Datenmengen"""
        if isinstance(data, list):
            results = []
            for item in data:
                result = await self._process_single_item(item, operation)
                results.append(result)
            return results
        else:
            return [await self._process_single_item(data, operation)]

    def get_performance_report(self) -> Dict[str, Any]:
        """Erstellt Performance-Bericht"""
        memory_info = self.memory_manager.check_memory_usage()
        cache_stats = self.cache_layer.cache_stats

        return {
            "memory_usage": memory_info,
            "cache_performance": {
                "hit_rate": cache_stats["hits"] / (cache_stats["hits"] + cache_stats["misses"]) if (cache_stats["hits"] + cache_stats["misses"]) > 0 else 0,
                "total_hits": cache_stats["hits"],
                "total_misses": cache_stats["misses"],
                "evictions": cache_stats["evictions"]
            },
            "processing_capacity": {
                "max_workers": self.parallel_processor.max_workers,
                "batch_size": self.parallel_processor.batch_size,
                "max_concurrent_batches": self.batch_processor.max_concurrent_batches
            },
            "recommendations": self._generate_performance_recommendations(memory_info, cache_stats)
        }

    def _generate_performance_recommendations(self, memory_info: Dict, cache_stats: Dict) -> List[str]:
        """Generiert Performance-Empfehlungen"""
        recommendations = []

        if memory_info["usage_percentage"] > 80:
            recommendations.append("Consider increasing memory limits or optimizing data structures")

        if cache_stats.get("hit_rate", 0) < 0.7:
            recommendations.append("Cache hit rate is low, consider adjusting cache strategy")

        if self.parallel_processor.max_workers < 10:
            recommendations.append("Consider increasing parallel workers for better throughput")

        return recommendations


# Singleton Instance
enterprise_optimizer = EnterprisePerformanceOptimizer()
