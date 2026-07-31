import time
from urllib.parse import urlencode

from .fmc import FmcError, api_get


DEVICE_PAGE_LIMIT = 100
DEVICE_RECORDS_PATH = "/devices/devicerecords"


def normalize_device(item):
    """Return the stable, Zabbix-friendly subset of an FMC Device record."""
    if not isinstance(item, dict):
        item = {}

    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "model": item.get("model"),
        "version": item.get("sw_version"),
        "management_ip": item.get("hostName"),
        "health_status": item.get("healthStatus") or "UNKNOWN",
    }


def _integer(value):
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def get_devices(token, domain, page_limit=DEVICE_PAGE_LIMIT):
    """Collect all Device records using FMC offset/limit pagination."""
    if not isinstance(page_limit, int) or isinstance(page_limit, bool) or page_limit <= 0:
        raise ValueError("page_limit must be a positive integer")

    result = {
        "timestamp": int(time.time()),
        "stats": {"total": 0},
        "devices": [],
    }
    offset = 0
    page_number = 0
    visited_offsets = set()

    while True:
        if offset in visited_offsets:
            raise FmcError("FMC device pagination did not advance")
        visited_offsets.add(offset)

        query = urlencode(
            {
                "offset": offset,
                "limit": page_limit,
                "expanded": "true",
            }
        )
        path = (
            f"/api/fmc_config/v1/domain/{domain}"
            f"{DEVICE_RECORDS_PATH}?{query}"
        )
        data = api_get(path, token)
        if not isinstance(data, dict):
            raise FmcError(f"GET {path} returned a non-object JSON response")

        items = data.get("items") or []
        if not isinstance(items, list):
            raise FmcError(f"GET {path} returned a non-list items field")

        result["devices"].extend(normalize_device(item) for item in items)
        page_number += 1

        paging = data.get("paging")
        paging = paging if isinstance(paging, dict) else {}
        total_count = _integer(paging.get("count"))
        total_pages = _integer(paging.get("pages"))

        if not items:
            break
        if total_count is not None and len(result["devices"]) >= total_count:
            break
        if total_pages is not None and page_number >= total_pages:
            break

        response_offset = _integer(paging.get("offset"))
        response_limit = _integer(paging.get("limit"))
        if response_offset is not None and response_limit and response_limit > 0:
            next_offset = response_offset + response_limit
        else:
            next_offset = offset + len(items)

        if next_offset <= offset:
            raise FmcError("FMC device pagination did not advance")

        # Without paging metadata, a short page is the last page.
        if total_count is None and total_pages is None and len(items) < page_limit:
            break
        offset = next_offset

    result["stats"]["total"] = len(result["devices"])
    return result
