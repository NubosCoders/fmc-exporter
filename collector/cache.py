from copy import deepcopy
from threading import Lock


cached_data = {
    "timestamp": 0,
    "stats": {},
    "tunnels": []
}
cache_lock = Lock()

cached_devices = {
    "timestamp": 0,
    "stats": {"total": 0},
    "devices": [],
}
devices_cache_lock = Lock()


def get_cache():
    with cache_lock:
        return deepcopy(cached_data)


def set_cache(data):
    global cached_data
    with cache_lock:
        cached_data = deepcopy(data)


def get_devices_cache():
    with devices_cache_lock:
        return deepcopy(cached_devices)


def set_devices_cache(data):
    global cached_devices
    with devices_cache_lock:
        cached_devices = deepcopy(data)
