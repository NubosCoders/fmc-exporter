import unittest
from unittest.mock import patch

from collector import state


INITIAL_STATE = {
    "status": "STARTING",
    "healthy": False,
    "fmc_connected": False,
    "last_attempt": 0,
    "last_success": 0,
    "last_error": "",
    "last_error_time": 0,
    "consecutive_failures": 0,
    "total_failures": 0,
    "version": "1.4.0",
}


def reset_state():
    with state.state_lock:
        state.collector_state.clear()
        state.collector_state.update(INITIAL_STATE)


class StateTransitionTests(unittest.TestCase):
    def setUp(self):
        reset_state()

    def test_starting_to_healthy(self):
        with patch("collector.state.time.time", side_effect=[100, 101]):
            state.set_attempt()
            state.set_success()

        current = state.get_state()
        self.assertEqual(current["status"], "HEALTHY")
        self.assertTrue(current["healthy"])
        self.assertTrue(current["fmc_connected"])
        self.assertEqual(current["last_attempt"], 100)
        self.assertEqual(current["last_success"], 101)
        self.assertEqual(current["consecutive_failures"], 0)
        self.assertEqual(current["total_failures"], 0)

    def test_starting_to_degraded(self):
        with patch("collector.state.time.time", side_effect=[200, 201]):
            state.set_attempt()
            state.set_error(RuntimeError("FMC unavailable"))

        current = state.get_state()
        self.assertEqual(current["status"], "DEGRADED")
        self.assertFalse(current["healthy"])
        self.assertFalse(current["fmc_connected"])
        self.assertEqual(current["last_attempt"], 200)
        self.assertEqual(current["last_success"], 0)
        self.assertEqual(current["last_error"], "FMC unavailable")
        self.assertEqual(current["last_error_time"], 201)
        self.assertEqual(current["consecutive_failures"], 1)
        self.assertEqual(current["total_failures"], 1)

    def test_healthy_to_degraded_preserves_last_success(self):
        with patch("collector.state.time.time", side_effect=[300, 301, 400, 401]):
            state.set_attempt()
            state.set_success()
            state.set_attempt()
            state.set_error(RuntimeError("timeout"))

        current = state.get_state()
        self.assertEqual(current["status"], "DEGRADED")
        self.assertEqual(current["last_attempt"], 400)
        self.assertEqual(current["last_success"], 301)
        self.assertEqual(current["consecutive_failures"], 1)
        self.assertEqual(current["total_failures"], 1)

    def test_degraded_to_healthy_resets_only_consecutive_failures(self):
        with patch(
            "collector.state.time.time",
            side_effect=[500, 501, 600, 601, 700, 701],
        ):
            state.set_attempt()
            state.set_error(RuntimeError("first"))
            state.set_attempt()
            state.set_error(RuntimeError("second"))
            state.set_attempt()
            state.set_success()

        current = state.get_state()
        self.assertEqual(current["status"], "HEALTHY")
        self.assertEqual(current["last_attempt"], 700)
        self.assertEqual(current["last_success"], 701)
        self.assertEqual(current["last_error"], "")
        self.assertEqual(current["last_error_time"], 0)
        self.assertEqual(current["consecutive_failures"], 0)
        self.assertEqual(current["total_failures"], 2)

    def test_attempt_does_not_change_previous_result(self):
        with state.state_lock:
            state.collector_state.update(
                {
                    "status": "DEGRADED",
                    "last_success": 123,
                    "last_error": "previous error",
                    "consecutive_failures": 2,
                }
            )

        with patch("collector.state.time.time", return_value=800):
            state.set_attempt()

        current = state.get_state()
        self.assertEqual(current["last_attempt"], 800)
        self.assertEqual(current["status"], "DEGRADED")
        self.assertEqual(current["last_success"], 123)
        self.assertEqual(current["last_error"], "previous error")
        self.assertEqual(current["consecutive_failures"], 2)


if __name__ == "__main__":
    unittest.main()
