# Преобразуем данные о туннеле в удобный формат для сохранения в JSON
def normalize_tunnel(item):

    return {

        "id": item.get("id"),

        "name":
            item.get("vpnTopology", {})
            .get("name"),

        "state":
            item.get("state"),


        "peerA":
            item.get("peerA", {})
            .get("device", {})
            .get("name"),


        "peerAIP":
            item.get("peerA", {})
            .get("ipAddresses", {})
            .get("v4", [None])[0],


        "peerB":
            item.get("peerB", {})
            .get("device", {})
            .get("name"),


        "peerBIP":
            item.get("peerB", {})
            .get("ipAddresses", {})
            .get("v4", [None])[0],


        "lastChange":
            item.get("lastChange")
    }

