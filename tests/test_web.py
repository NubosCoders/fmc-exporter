import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from collector.web import ApiHandler
from tests.test_state import reset_state


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

    def setUp(self):
        reset_state()

    def test_health_starting(self):
        status, body = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "UP")
        self.assertEqual(body["collector_status"], "STARTING")
        self.assertFalse(body["healthy"])
        self.assertEqual(body["version"], "1.4.0")
        self.assertEqual(body["consecutive_failures"], 0)
        self.assertEqual(body["total_failures"], 0)

    def test_health_healthy(self):
        from collector import state

        with state.state_lock:
            state.collector_state.update(
                {
                    "status": "HEALTHY",
                    "healthy": True,
                    "fmc_connected": True,
                    "last_attempt": 100,
                    "last_success": 101,
                }
            )

        status, body = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["collector_status"], "HEALTHY")
        self.assertTrue(body["healthy"])
        self.assertTrue(body["fmc_connected"])
        self.assertEqual(body["last_success"], 101)

    def test_health_degraded(self):
        from collector import state

        with state.state_lock:
            state.collector_state.update(
                {
                    "status": "DEGRADED",
                    "healthy": False,
                    "fmc_connected": False,
                    "last_error": "timeout",
                    "consecutive_failures": 3,
                    "total_failures": 7,
                }
            )

        status, body = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["collector_status"], "DEGRADED")
        self.assertFalse(body["healthy"])
        self.assertEqual(body["last_error"], "timeout")
        self.assertEqual(body["consecutive_failures"], 3)
        self.assertEqual(body["total_failures"], 7)

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
