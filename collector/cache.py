cached_data = {
    "timestamp": 0,
    "stats": {},
    "tunnels": []
}


def get_cache():
    return cached_data


def set_cache(data):
    cached_data.clear()
    cached_data.update(data)