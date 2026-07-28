import time

from .fmc import api_get
from .models import normalize_tunnel


def get_tunnels(token, domain):

    path = (
        f"/api/fmc_config/v1/domain/{domain}"
        "/health/tunnelstatuses?expanded=true"
    )

    data = api_get(path, token)

    result = {
        "timestamp": int(time.time()),
        "stats": {
            "total": 0,
            "up": 0,
            "down": 0
        },
        "tunnels": []
    }

    for item in data.get("items", []):

        tunnel = normalize_tunnel(item)

        result["tunnels"].append(tunnel)
        result["stats"]["total"] += 1

        if tunnel["state"] == "TUNNEL_UP":
            result["stats"]["up"] += 1
        else:
            result["stats"]["down"] += 1

    return result