from copy import deepcopy
from threading import Lock


cached_data = {
    "timestamp": 0,
    "stats": {},
    "tunnels": []
}
cache_lock = Lock()


def get_cache():
    with cache_lock:
        return deepcopy(cached_data)


def set_cache(data):
    global cached_data
    with cache_lock:
        cached_data = deepcopy(data)
