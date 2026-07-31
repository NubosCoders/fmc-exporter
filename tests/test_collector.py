import os
import tempfile
import unittest
from unittest.mock import patch

from collector.cache import (
    get_cache,
    get_devices_cache,
    set_cache,
    set_devices_cache,
)
from collector import collector, fmc, state
from collector.fmc import FmcError
from collector.models import normalize_tunnel
from collector.tunnels import get_tunnels


class CollectorDataTests(unittest.TestCase):
    def test_empty_ip_lists_are_normalized_to_none(self):
        tunnel = normalize_tunnel(
            {
                "vpnTopology": None,
                "peerA": {"device": None, "ipAddresses": {"v4": []}},
                "peerB": {"ipAddresses": {"v4": None}},
            }
        )
        self.assertIsNone(tunnel["peerAIP"])
        self.assertIsNone(tunnel["peerBIP"])

    @patch("collector.tunnels.api_get", return_value={"items": None})
    def test_null_items_are_treated_as_empty(self, _api_get):
        result = get_tunnels({}, "domain")
        self.assertEqual(result["stats"], {
            "total": 0,
            "up": 0,
            "down": 0,
            "unknown": 0,
        })

    @patch(
        "collector.tunnels.api_get",
        return_value={
            "items": [
                {"state": "TUNNEL_UP"},
                {"state": "TUNNEL_DOWN"},
                {"state": "NEW_FMC_STATE"},
            ]
        },
    )
    def test_unknown_states_are_not_counted_as_down(self, _api_get):
        result = get_tunnels({}, "domain")
        self.assertEqual(result["stats"], {
            "total": 3,
            "up": 1,
            "down": 1,
            "unknown": 1,
        })

    def test_cache_returns_an_independent_snapshot(self):
        set_cache({"timestamp": 1, "stats": {}, "tunnels": [{"id": "one"}]})
        snapshot = get_cache()
        snapshot["tunnels"][0]["id"] = "changed"
        self.assertEqual(get_cache()["tunnels"][0]["id"], "one")

    def test_devices_cache_returns_an_independent_snapshot(self):
        set_devices_cache(
            {"timestamp": 1, "stats": {"total": 1}, "devices": [{"id": "one"}]}
        )
        snapshot = get_devices_cache()
        snapshot["devices"][0]["id"] = "changed"
        self.assertEqual(get_devices_cache()["devices"][0]["id"], "one")


class AtomicSnapshotTests(unittest.TestCase):
    def test_snapshot_is_written_when_enabled(self):
        from collector import utils

        with tempfile.TemporaryDirectory() as directory:
            output = os.path.join(directory, "fmc.json")
            with patch.object(utils, "OUTPUT_FILE", output):
                utils.save_json({"tunnels": []})
            self.assertTrue(os.path.exists(output))

    @patch("collector.collector.save_json", side_effect=OSError("read-only"))
    @patch("collector.collector.set_success")
    @patch(
        "collector.collector.get_devices",
        return_value={"timestamp": 1, "stats": {"total": 0}, "devices": []},
    )
    @patch(
        "collector.collector.get_tunnels",
        return_value={"timestamp": 1, "stats": {}, "tunnels": []},
    )
    def test_optional_snapshot_error_does_not_fail_collection(
        self,
        _get_tunnels,
        _get_devices,
        set_success,
        _save_json,
    ):
        with self.assertLogs("collector.collector", level="ERROR"):
            token, domain = collector.collect_once(
                {"access": "token"},
                "domain",
            )
        self.assertEqual(token, {"access": "token"})
        self.assertEqual(domain, "domain")
        set_success.assert_called_once_with()

    @patch("collector.collector.set_success")
    @patch(
        "collector.collector.get_devices",
        side_effect=FmcError("device inventory unavailable"),
    )
    @patch(
        "collector.collector.get_tunnels",
        return_value={"timestamp": 2, "stats": {}, "tunnels": [{"id": "new"}]},
    )
    def test_device_error_preserves_previous_inventory_and_degrades_health(
        self,
        _get_tunnels,
        _get_devices,
        set_success,
    ):
        set_devices_cache(
            {
                "timestamp": 1,
                "stats": {"total": 1},
                "devices": [{"id": "previous"}],
            }
        )

        state.set_attempt()
        with self.assertRaises(FmcError) as raised:
            collector.collect_once({"access": "token"}, "domain")
        state.set_error(raised.exception)

        self.assertEqual(get_cache()["tunnels"][0]["id"], "new")
        self.assertEqual(get_devices_cache()["devices"][0]["id"], "previous")
        self.assertEqual(state.get_state()["status"], "DEGRADED")
        self.assertIn("device inventory unavailable", state.get_state()["last_error"])
        set_success.assert_not_called()


class TlsTests(unittest.TestCase):
    def test_system_ca_bundle_is_used_by_default(self):
        with tempfile.NamedTemporaryFile() as ca_file:
            with (
                patch.object(fmc, "FMC_CA_BUNDLE", None),
                patch.object(fmc, "FMC_TLS_VERIFY", True),
                patch.object(fmc, "SYSTEM_CA_BUNDLE", ca_file.name),
            ):
                self.assertEqual(fmc.tls_verify(), ca_file.name)

    def test_explicit_ca_bundle_has_priority(self):
        with patch.object(fmc, "FMC_CA_BUNDLE", "/certs/private-ca.crt"):
            self.assertEqual(fmc.tls_verify(), "/certs/private-ca.crt")

    def test_tls_verification_can_be_disabled_explicitly(self):
        with (
            patch.object(fmc, "FMC_CA_BUNDLE", None),
            patch.object(fmc, "FMC_TLS_VERIFY", False),
        ):
            self.assertFalse(fmc.tls_verify())


if __name__ == "__main__":
    unittest.main()
