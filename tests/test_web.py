import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from collector.web import ApiHandler


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
        cls.thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True,
        )
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def get(self, path):
        connection = HTTPConnection(
            "127.0.0.1",
            self.server.server_port,
            timeout=2,
        )
        connection.request("GET", path)
        response = connection.getresponse()
        body = response.read()
        connection.close()
        return response.status, json.loads(body)

    def test_health_responds(self):
        status, body = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "UP")

    def test_tunnels_responds_while_collector_is_degraded(self):
        status, body = self.get("/tunnels")
        self.assertEqual(status, 200)
        self.assertIn("tunnels", body)

    def test_query_string_does_not_change_route(self):
        status, body = self.get("/health?full=true")
        self.assertEqual(status, 200)
        self.assertIn("collector_status", body)

    def test_root_is_not_an_endpoint(self):
        status, body = self.get("/")
        self.assertEqual(status, 404)
        self.assertEqual(body, {"error": "Not found"})


if __name__ == "__main__":
    unittest.main()
