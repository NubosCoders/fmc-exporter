import logging
import time
from threading import Thread

from .cache import set_cache, set_devices_cache
from .config import UPDATE_INTERVAL
from .devices import get_devices
from .fmc import FmcAuthenticationError, FmcError, get_domain, login
from .state import set_attempt, set_error, set_success
from .tunnels import get_tunnels
from .utils import save_json
from .web import start_http


logger = logging.getLogger(__name__)


def collect_once(token, domain):
    if token is None or domain is None:
        token = login()
        domain = get_domain(token)

    tunnels = get_tunnels(token, domain)
    set_cache(tunnels)

    devices = get_devices(token, domain)
    set_devices_cache(devices)

    set_success()

    try:
        save_json(tunnels)
    except Exception:
        # OUTPUT_FILE is a legacy optional snapshot. The in-memory cache is
        # already valid, so a file error must not mark FMC collection failed.
        logger.exception("Could not save optional JSON snapshot")

    return token, domain


def collect_forever():
    token = None
    domain = None

    while True:
        set_attempt()

        try:
            token, domain = collect_once(token, domain)

        except FmcAuthenticationError as error:
            set_error(error)
            token = None
            domain = None
            logger.exception("Collector authentication error: %s", error)

        except FmcError as error:
            set_error(error)
            logger.exception("Collector FMC error: %s", error)

        except Exception as error:
            set_error(error)
            logger.exception("Unexpected collector error: %s", error)

        time.sleep(UPDATE_INTERVAL)


def main():
    # Keep the HTTP server in the main thread so its failure stops the process.
    Thread(
        target=collect_forever,
        daemon=True,
        name="fmc-collector",
    ).start()
    start_http()
