import os
import tempfile
import unittest
from unittest.mock import patch

from collector.cache import get_cache, set_cache
from collector import fmc
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


class AtomicSnapshotTests(unittest.TestCase):
    def test_snapshot_is_written_when_enabled(self):
        from collector import utils

        with tempfile.TemporaryDirectory() as directory:
            output = os.path.join(directory, "fmc.json")
            with patch.object(utils, "OUTPUT_FILE", output):
                utils.save_json({"tunnels": []})
            self.assertTrue(os.path.exists(output))


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
