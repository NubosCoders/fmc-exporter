import time
from threading import Thread

from .cache import set_cache
from .config import UPDATE_INTERVAL
from .fmc import FmcAuthenticationError, FmcError, get_domain, login
from .state import set_attempt, set_error, set_fmc_disconnected, set_success
from .tunnels import get_tunnels
from .utils import save_json
from .web import start_http


def collect_forever():
    token = None
    domain = None

    while True:
        set_attempt()

        try:
            # Авторизация находится внутри рабочего цикла, чтобы временная
            # недоступность FMC не завершала процесс collector.
            if token is None or domain is None:
                token = login()
                domain = get_domain(token)

            tunnels = get_tunnels(token, domain)

            set_cache(tunnels)
            save_json(tunnels)
            set_success()

        except FmcAuthenticationError as error:
            set_error(error)
            set_fmc_disconnected()
            token = None
            domain = None
            print("Collector authentication error:", error, flush=True)

        except FmcError as error:
            set_error(error)
            set_fmc_disconnected()
            print("Collector FMC error:", error, flush=True)

        except Exception as error:
            set_error(error)
            print("Collector error:", error, flush=True)

        time.sleep(UPDATE_INTERVAL)


def main():
    # Keep the HTTP server in the main thread so its failure stops the process.
    Thread(
        target=collect_forever,
        daemon=True,
        name="fmc-collector",
    ).start()
    start_http()
