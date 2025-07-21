import logging
import pickle
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import lmdb

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata for tracking access patterns"""

    value: Any
    size: int
    created_at: float
    last_accessed: float
    access_count: int = 0

    def touch(self) -> None:
        """Update access time and count"""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache statistics"""

    hot_hits: int = 0
    cold_hits: int = 0
    misses: int = 0
    total_requests: int = 0
    hot_size: int = 0
    cold_size: int = 0
    hot_memory_bytes: int = 0
    hot_max_memory_bytes: int = 0
    promotions: int = 0
    demotions: int = 0
    batch_operations: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate overall hit rate"""
        total_hits = self.hot_hits + self.cold_hits
        return (total_hits / self.total_requests * 100) if self.total_requests > 0 else 0.0

    @property
    def hot_hit_rate(self) -> float:
        """Calculate hot cache hit rate"""
        return (self.hot_hits / self.total_requests * 100) if self.total_requests > 0 else 0.0

    @property
    def memory_utilization(self) -> float:
        """Calculate memory utilization percentage"""
        return (self.hot_memory_bytes / self.hot_max_memory_bytes * 100) if self.hot_max_memory_bytes > 0 else 0.0


class CustomCache:
    """
    Custom two-tier cache with hot RAM storage and cold LMDB storage.
    Features batch promotion/demotion for efficiency and thread safety.
    """

    def __init__(
        self,
        hot_max_memory_mb: int = 300,
        cold_db_path: str = "/tmp/custom_cache",
        hot_threshold_percent: float = 80.0,
        batch_size: int = 50,
        cold_max_size_gb: int = 10,
    ):
        """
        Initialize the custom cache system.

        Args:
            hot_max_memory_mb: Maximum memory for hot cache in MB
            cold_db_path: Path to LMDB database for cold storage
            hot_threshold_percent: Threshold percentage to trigger demotion
            batch_size: Number of items to move in batch operations
            cold_max_size_gb: Maximum size for cold cache in GB
        """
        self.hot_max_memory_bytes = hot_max_memory_mb * 1024 * 1024
        self.cold_db_path = Path(cold_db_path)
        self.hot_threshold_percent = hot_threshold_percent
        self.batch_size = batch_size
        self.cold_max_size_bytes = cold_max_size_gb * 1024 * 1024 * 1024

        # Hot cache: OrderedDict for LRU behavior + metadata
        self._hot_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hot_memory_usage = 0

        # Thread safety
        self._lock = threading.RLock()

        # Statistics
        self._stats = CacheStats(hot_max_memory_bytes=self.hot_max_memory_bytes)

        # Initialize LMDB cold storage
        self._init_cold_storage()

        logger.info(f"CustomCache initialized: hot={hot_max_memory_mb}MB, cold={cold_db_path}, batch_size={batch_size}")

    def _init_cold_storage(self) -> None:
        """Initialize LMDB database for cold storage"""
        try:
            self.cold_db_path.mkdir(parents=True, exist_ok=True)

            # Initialize LMDB environment
            self._lmdb_env = lmdb.open(
                str(self.cold_db_path),
                map_size=self.cold_max_size_bytes,
                max_dbs=1,
                sync=False,  # Async writes for performance
                writemap=True,  # Use writemap for better performance
                lock=True,  # Enable locking for thread safety
            )

            # Create main database
            with self._lmdb_env.begin(write=True) as txn:
                self._cold_db = self._lmdb_env.open_db(b"cache", txn=txn, create=True)

            logger.info(f"LMDB cold storage initialized at {self.cold_db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize LMDB cold storage: {e}")
            raise

    def _estimate_size(self, obj: Any) -> int:
        """Estimate the memory size of an object"""
        try:
            # Use pickle to get accurate size estimate
            serialized = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
            return len(serialized)
        except Exception:
            # Fallback estimation
            return 1024 * 40  # 40KB default better safe than sorry

    def _should_demote(self) -> bool:
        """Check if hot cache should demote items to cold storage"""
        memory_usage_percent = (self._hot_memory_usage / self.hot_max_memory_bytes) * 100
        return memory_usage_percent >= self.hot_threshold_percent

    def _select_demotion_candidates(self) -> List[str]:
        """Select items for demotion using LRU strategy"""
        # Sort by last accessed time (oldest first)
        candidates = sorted(self._hot_cache.items(), key=lambda x: x[1].last_accessed)

        # Select batch_size oldest items
        return [key for key, _ in candidates[: self.batch_size]]

    def _select_promotion_candidates(self) -> List[str]:
        """Select items for promotion from cold storage based on access patterns"""
        candidates = []

        try:
            with self._lmdb_env.begin(write=False) as txn:
                cursor = txn.cursor(self._cold_db)

                # Collect items with their metadata
                items_with_access = []
                for key, value in cursor:
                    try:
                        entry_data = pickle.loads(value)
                        if isinstance(entry_data, dict) and "access_count" in entry_data:
                            items_with_access.append((key.decode("utf-8"), entry_data["access_count"]))
                    except Exception:
                        continue

                # Sort by access count (most accessed first)
                items_with_access.sort(key=lambda x: x[1], reverse=True)

                # Select top candidates up to batch_size
                candidates = [key for key, _ in items_with_access[: self.batch_size]]

        except Exception as e:
            logger.warning(f"Failed to select promotion candidates: {e}")

        return candidates

    def _batch_demote(self, keys: List[str]) -> None:
        """Move items from hot to cold storage in batch"""
        if not keys:
            return

        try:
            with self._lmdb_env.begin(write=True) as txn:
                for key in keys:
                    if key in self._hot_cache:
                        entry = self._hot_cache[key]

                        # Prepare data for cold storage with metadata
                        cold_data = {
                            "value": entry.value,
                            "created_at": entry.created_at,
                            "last_accessed": entry.last_accessed,
                            "access_count": entry.access_count,
                        }

                        # Store in cold cache
                        serialized_data = pickle.dumps(cold_data, protocol=pickle.HIGHEST_PROTOCOL)
                        txn.put(key.encode("utf-8"), serialized_data, db=self._cold_db)

                        # Remove from hot cache
                        self._hot_memory_usage -= entry.size
                        del self._hot_cache[key]

            self._stats.demotions += len(keys)
            self._stats.batch_operations += 1

            logger.debug(f"Batch demoted {len(keys)} items to cold storage")

        except Exception as e:
            logger.error(f"Failed to batch demote items: {e}")

    def _batch_promote(self, keys: List[str]) -> None:
        """Move items from cold to hot storage in batch"""
        if not keys:
            return

        # Check if we have enough space
        available_space = self.hot_max_memory_bytes - self._hot_memory_usage

        try:
            with self._lmdb_env.begin(write=True) as txn:
                promoted_count = 0

                for key in keys:
                    # Check if item exists in cold storage
                    cold_data_bytes = txn.get(key.encode("utf-8"), db=self._cold_db)
                    if cold_data_bytes is None:
                        continue

                    try:
                        cold_data = pickle.loads(cold_data_bytes)

                        # Estimate size and check if we have space
                        estimated_size = self._estimate_size(cold_data["value"])
                        if estimated_size > available_space:
                            break  # No more space

                        # Create hot cache entry
                        entry = CacheEntry(
                            value=cold_data["value"],
                            size=estimated_size,
                            created_at=cold_data["created_at"],
                            last_accessed=cold_data["last_accessed"],
                            access_count=cold_data["access_count"],
                        )

                        # Add to hot cache
                        self._hot_cache[key] = entry
                        self._hot_memory_usage += estimated_size
                        available_space -= estimated_size

                        # Remove from cold storage
                        txn.delete(key.encode("utf-8"), db=self._cold_db)

                        promoted_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to promote key {key}: {e}")
                        continue

                if promoted_count > 0:
                    self._stats.promotions += promoted_count
                    self._stats.batch_operations += 1
                    logger.debug(f"Batch promoted {promoted_count} items to hot storage")

        except Exception as e:
            logger.error(f"Failed to batch promote items: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get a single item from cache"""
        with self._lock:
            self._stats.total_requests += 1

            # Check hot cache first
            if key in self._hot_cache:
                entry = self._hot_cache[key]
                entry.touch()
                # Move to end (most recently used)
                self._hot_cache.move_to_end(key)

                self._stats.hot_hits += 1
                self._stats.hot_size = len(self._hot_cache)
                self._stats.hot_memory_bytes = self._hot_memory_usage

                return entry.value

            # Check cold cache
            try:
                with self._lmdb_env.begin(write=False) as txn:
                    cold_data_bytes = txn.get(key.encode("utf-8"), db=self._cold_db)

                    if cold_data_bytes is not None:
                        cold_data = pickle.loads(cold_data_bytes)
                        self._stats.cold_hits += 1

                        # Update cold storage access count
                        cold_data["last_accessed"] = time.time()
                        cold_data["access_count"] += 1

                        # Store updated metadata back to cold storage
                        updated_data = pickle.dumps(cold_data, protocol=pickle.HIGHEST_PROTOCOL)
                        with self._lmdb_env.begin(write=True) as write_txn:
                            write_txn.put(key.encode("utf-8"), updated_data, db=self._cold_db)

                        return cold_data["value"]

            except Exception as e:
                logger.warning(f"Error accessing cold cache for key {key}: {e}")

            # Cache miss
            self._stats.misses += 1
            return None

    def get_batch(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple items from cache efficiently"""
        results = {}

        with self._lock:
            hot_found = set()
            cold_keys = []

            # First pass: check hot cache
            for key in keys:
                self._stats.total_requests += 1

                if key in self._hot_cache:
                    entry = self._hot_cache[key]
                    entry.touch()
                    self._hot_cache.move_to_end(key)

                    results[key] = entry.value
                    hot_found.add(key)
                    self._stats.hot_hits += 1
                else:
                    cold_keys.append(key)

            # Second pass: check cold cache for remaining keys
            if cold_keys:
                try:
                    with self._lmdb_env.begin(write=True) as txn:
                        for key in cold_keys:
                            cold_data_bytes = txn.get(key.encode("utf-8"), db=self._cold_db)

                            if cold_data_bytes is not None:
                                cold_data = pickle.loads(cold_data_bytes)
                                results[key] = cold_data["value"]
                                self._stats.cold_hits += 1

                                # Update access metadata
                                cold_data["last_accessed"] = time.time()
                                cold_data["access_count"] += 1

                                updated_data = pickle.dumps(cold_data, protocol=pickle.HIGHEST_PROTOCOL)
                                txn.put(key.encode("utf-8"), updated_data, db=self._cold_db)
                            else:
                                self._stats.misses += 1

                except Exception as e:
                    logger.warning(f"Error in batch cold cache access: {e}")
                    # Count remaining keys as misses
                    self._stats.misses += len([k for k in cold_keys if k not in results])

            # Update stats
            self._stats.hot_size = len(self._hot_cache)
            self._stats.hot_memory_bytes = self._hot_memory_usage

            return results

    def set(self, key: str, value: Any) -> bool:
        """Set a single item in cache"""
        with self._lock:
            # Estimate size
            estimated_size = self._estimate_size(value)

            # Check if value is too large for hot cache
            if estimated_size > self.hot_max_memory_bytes:
                logger.warning(f"Value too large for hot cache: {estimated_size} bytes")
                return False

            # Remove if already exists in hot cache
            if key in self._hot_cache:
                old_entry = self._hot_cache[key]
                self._hot_memory_usage -= old_entry.size
                del self._hot_cache[key]

            # Check if we need to demote items
            if self._hot_memory_usage + estimated_size > self.hot_max_memory_bytes or self._should_demote():
                candidates = self._select_demotion_candidates()
                self._batch_demote(candidates)

            # Create new entry
            entry = CacheEntry(
                value=value, size=estimated_size, created_at=time.time(), last_accessed=time.time(), access_count=1
            )

            # Add to hot cache
            self._hot_cache[key] = entry
            self._hot_memory_usage += estimated_size

            # Update stats
            self._stats.hot_size = len(self._hot_cache)
            self._stats.hot_memory_bytes = self._hot_memory_usage

            return True

    def set_batch(self, items: Dict[str, Any]) -> int:
        """Set multiple items in cache, returns number of successfully stored items"""
        stored_count = 0

        with self._lock:
            for key, value in items.items():
                if self.set(key, value):
                    stored_count += 1

        return stored_count

    def delete(self, key: str) -> bool:
        """Delete an item from cache"""
        with self._lock:
            found = False

            # Remove from hot cache
            if key in self._hot_cache:
                entry = self._hot_cache[key]
                self._hot_memory_usage -= entry.size
                del self._hot_cache[key]
                found = True

            # Remove from cold cache
            try:
                with self._lmdb_env.begin(write=True) as txn:
                    if txn.delete(key.encode("utf-8"), db=self._cold_db):
                        found = True
            except Exception as e:
                logger.warning(f"Error deleting from cold cache: {e}")

            return found

    def clear(self) -> None:
        """Clear all caches"""
        with self._lock:
            # Clear hot cache
            self._hot_cache.clear()
            self._hot_memory_usage = 0

            # Clear cold cache
            try:
                with self._lmdb_env.begin(write=True) as txn:
                    txn.drop(self._cold_db, delete=False)
            except Exception as e:
                logger.warning(f"Error clearing cold cache: {e}")

            # Reset stats
            self._stats = CacheStats(hot_max_memory_bytes=self.hot_max_memory_bytes)

            logger.info("All caches cleared")

    def optimize(self) -> None:
        """Manually trigger cache optimization"""
        with self._lock:
            # Demote if needed
            if self._should_demote():
                candidates = self._select_demotion_candidates()
                self._batch_demote(candidates)

            # Promote frequently accessed items
            promotion_candidates = self._select_promotion_candidates()
            if promotion_candidates:
                self._batch_promote(promotion_candidates)

    def get_stats(self) -> CacheStats:
        """Get current cache statistics"""
        with self._lock:
            # Update current stats
            self._stats.hot_size = len(self._hot_cache)
            self._stats.hot_memory_bytes = self._hot_memory_usage

            # Count cold cache size
            try:
                with self._lmdb_env.begin(write=False) as txn:
                    self._stats.cold_size = txn.stat(self._cold_db)["entries"]
            except Exception:
                self._stats.cold_size = 0

            return self._stats

    def get_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        stats = self.get_stats()

        return {
            "configuration": {
                "hot_max_memory_mb": self.hot_max_memory_bytes // (1024 * 1024),
                "cold_db_path": str(self.cold_db_path),
                "hot_threshold_percent": self.hot_threshold_percent,
                "batch_size": self.batch_size,
            },
            "performance": {
                "hit_rate": stats.hit_rate,
                "hot_hit_rate": stats.hot_hit_rate,
                "memory_utilization": stats.memory_utilization,
            },
            "statistics": {
                "hot_hits": stats.hot_hits,
                "cold_hits": stats.cold_hits,
                "misses": stats.misses,
                "total_requests": stats.total_requests,
                "promotions": stats.promotions,
                "demotions": stats.demotions,
                "batch_operations": stats.batch_operations,
            },
            "storage": {
                "hot_cache_size": stats.hot_size,
                "cold_cache_size": stats.cold_size,
                "hot_memory_bytes": stats.hot_memory_bytes,
                "hot_max_memory_bytes": stats.hot_max_memory_bytes,
            },
        }

    def close(self) -> None:
        """Close the cache and cleanup resources"""
        with self._lock:
            try:
                if hasattr(self, "_lmdb_env"):
                    self._lmdb_env.close()
                logger.info("CustomCache closed successfully")
            except Exception as e:
                logger.error(f"Error closing cache: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
