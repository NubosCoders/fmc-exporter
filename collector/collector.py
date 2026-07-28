import time
from threading import Thread

from .cache import set_cache
from .config import UPDATE_INTERVAL
from .fmc import get_domain, login
from .state import set_attempt, set_error, set_success
from .tunnels import get_tunnels
from .utils import save_json
from .web import start_http


def main():
    # HTTP API должен запускаться независимо от доступности FMC.
    Thread(
        target=start_http,
        daemon=True,
        name="fmc-http-server",
    ).start()

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

        except Exception as error:
            set_error(error)

            print(
                "Collector error:",
                error,
                flush=True,
            )

            error_text = str(error)
            if (
                "Refresh token failed" in error_text
                or "HTTP 401" in error_text
                or "Login failed" in error_text
            ):
                print(
                    "FMC authentication will be retried",
                    flush=True,
                )
                token = None
                domain = None

        time.sleep(UPDATE_INTERVAL)
