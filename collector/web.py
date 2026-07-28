import json
import time

from http.server import (
    BaseHTTPRequestHandler,
    HTTPServer
)

from .cache import get_cache
from .config import HTTP_PORT
from .state import (
    START_TIME,
    collector_state
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

        self.wfile.write(body)


    def do_GET(self):

        if self.path == "/health":

            uptime = int(
                time.time() - START_TIME
            )

            self.send_json(
                200,
                {
                    "status": "UP",
                    "healthy": collector_state["healthy"],
                    "version": collector_state["version"],
                    "uptime": uptime,
                    "last_success": collector_state["last_success"],
                    "last_error": collector_state["last_error"],
                    "fmc_connected": collector_state["healthy"]
                }
            )

            return


        if self.path == "/tunnels":

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

    server = HTTPServer(
        ("0.0.0.0", HTTP_PORT),
        ApiHandler
    )

    print(
        f"HTTP server listening on :{HTTP_PORT}",
        flush=True
    )

    server.serve_forever()