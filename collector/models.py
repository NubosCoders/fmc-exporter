def first_or_none(values):
    return values[0] if values else None


def mapping(value):
    return value if isinstance(value, dict) else {}


# Преобразуем данные о туннеле в удобный формат для сохранения в JSON
def normalize_tunnel(item):
    peer_a = mapping(item.get("peerA"))
    peer_b = mapping(item.get("peerB"))

    return {

        "id": item.get("id"),

        "name":
            mapping(item.get("vpnTopology"))
            .get("name"),

        "state":
            item.get("state"),


        "peerA":
            mapping(peer_a.get("device"))
            .get("name"),


        "peerAIP":
            first_or_none(
                mapping(peer_a.get("ipAddresses"))
                .get("v4")
            ),


        "peerB":
            mapping(peer_b.get("device"))
            .get("name"),


        "peerBIP":
            first_or_none(
                mapping(peer_b.get("ipAddresses"))
                .get("v4")
            ),


        "lastChange":
            item.get("lastChange")
    }
