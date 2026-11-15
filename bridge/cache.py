import json
import time
from pathlib import Path
from collections import OrderedDict

BRIDGE_DIR = Path(__file__).resolve().parent


def _tracked_paths():
    return [
        BRIDGE_DIR.parent / "graph.json",
        BRIDGE_DIR / "bridge_nodes.json",
        BRIDGE_DIR / "lucky-config.yaml",
    ]


def _signature():
    sig = {}
    for p in _tracked_paths():
        try:
            sig[str(p)] = p.stat().st_mtime
        except OSError:
            sig[str(p)] = 0
    return sig


CACHE_FILE = BRIDGE_DIR / ".lucky_cache.json"


class ContextCache:
    def __init__(self, max_size=100):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
        self._signature = _signature()
        self._load_from_disk()

    def _load_from_disk(self):
        try:
            if not CACHE_FILE.exists():
                return
            with open(CACHE_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return
        if not isinstance(data, dict):
            return
        if data.get("signature") != self._signature:
            return
        payload = data.get("cache")
        if isinstance(payload, dict):
            for k, v in payload.items():
                self.cache[k] = v
        stats = data.get("stats")
        if isinstance(stats, dict):
            for k in self.stats:
                if k in stats:
                    self.stats[k] = stats[k]

    def _persist(self):
        try:
            data = {
                "signature": self._signature,
                "cache": {k: v for k, v in self.cache.items()},
                "stats": self.stats,
            }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _check_signature(self):
        new_sig = _signature()
        if new_sig != self._signature:
            self._signature = new_sig
            self.cache.clear()

    def get(self, query_key):
        self._check_signature()
        if query_key in self.cache:
            self.cache.move_to_end(query_key)
            self.stats["hits"] += 1
            return self.cache[query_key]
        else:
            self.stats["misses"] += 1
            return None

    def set(self, query_key, value):
        self._check_signature()
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
            self.stats["evictions"] += 1
        self.cache[query_key] = {
            "value": value,
            "timestamp": time.time(),
            "query_key": query_key,
        }
        self._persist()

    def clear(self):
        self.cache.clear()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
        try:
            if CACHE_FILE.exists():
                CACHE_FILE.unlink()
        except Exception:
            pass


cache = ContextCache()
