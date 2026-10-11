import time
import json
from collections import OrderedDict

class ContextCache:
    """
    LRU Cache for query results and loaded skill nodes.
    Prevents re-fetching nodes from the graph during a conversation.
    """
    
    def __init__(self, max_size=100):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def get(self, query_key):
        """Retrieve cached result."""
        if query_key in self.cache:
            self.cache.move_to_end(query_key)
            self.stats["hits"] += 1
            return self.cache[query_key]
        else:
            self.stats["misses"] += 1
            return None
    
    def set(self, query_key, value):
        """Cache a result."""
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
            self.stats["evictions"] += 1
        
        self.cache[query_key] = {
            "value": value,
            "timestamp": time.time(),
            "query_key": query_key
        }
    
    def clear(self):
        self.cache.clear()

# Singleton instance
cache = ContextCache()
