import json
import time
from urllib.parse import urlparse

from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)

from .cache import get_cache
from .config import HTTP_PORT
from .state import (
    START_TIME,
    get_state,
)


class ApiHandler(BaseHTTPRequestHandler):

    def send_json(self, status_code, data):

        body = json.dumps(data).encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.end_headers()

        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # The client may time out or disconnect while a response is sent.
            # This must not produce a traceback or affect other requests.
            return


    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            state = get_state()

            uptime = int(
                time.time() - START_TIME
            )

            self.send_json(
                200,
                {
                    "status": "UP",
                    "collector_status": state["status"],
                    "healthy": state["healthy"],
                    "version": state["version"],
                    "uptime": uptime,
                    "last_attempt": state["last_attempt"],
                    "last_success": state["last_success"],
                    "last_error": state["last_error"],
                    "last_error_time": state["last_error_time"],
                    "fmc_connected": state["fmc_connected"],
                }
            )

            return


        if path == "/tunnels":

            self.send_json(
                200,
                get_cache()
            )

            return


        self.send_json(
            404,
            {
                "error": "Not found"
            }
        )


    def log_message(self, format, *args):
        return


def start_http():

    # Each client gets its own thread. A slow or disconnected healthcheck must
    # not block Zabbix or subsequent health/tunnel requests.
    server = ThreadingHTTPServer(
        ("0.0.0.0", HTTP_PORT),
        ApiHandler
    )

    print(
        f"HTTP server listening on :{HTTP_PORT}",
        flush=True
    )

    server.serve_forever()
