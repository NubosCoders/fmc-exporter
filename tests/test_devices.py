import unittest
from unittest.mock import call, patch

from collector.devices import get_devices, normalize_device
from collector.fmc import FmcError


class DeviceNormalizationTests(unittest.TestCase):
    def test_confirmed_fmc_fields_are_normalized(self):
        device = normalize_device(
            {
                "id": "device-uuid",
                "name": "FTD-1",
                "model": "Cisco Secure Firewall",
                "sw_version": "7.4.2",
                "hostName": "192.0.2.10",
                "healthStatus": "GREEN",
                "version": "ignored-response-version",
            }
        )

        self.assertEqual(
            device,
            {
                "id": "device-uuid",
                "name": "FTD-1",
                "model": "Cisco Secure Firewall",
                "version": "7.4.2",
                "management_ip": "192.0.2.10",
                "health_status": "GREEN",
            },
        )

    def test_missing_fields_are_null_except_documented_unknown_health(self):
        self.assertEqual(
            normalize_device({"id": "device-uuid"}),
            {
                "id": "device-uuid",
                "name": None,
                "model": None,
                "version": None,
                "management_ip": None,
                "health_status": "UNKNOWN",
            },
        )


class DeviceCollectionTests(unittest.TestCase):
    @patch("collector.devices.time.time", return_value=123)
    @patch("collector.devices.api_get", return_value={"items": None})
    def test_empty_inventory_is_valid(self, _api_get, _time):
        self.assertEqual(
            get_devices({"access": "token"}, "domain"),
            {
                "timestamp": 123,
                "stats": {"total": 0},
                "devices": [],
            },
        )

    @patch("collector.devices.time.time", return_value=456)
    @patch(
        "collector.devices.api_get",
        side_effect=[
            {
                "items": [{"id": "one"}, {"id": "two"}],
                "paging": {"offset": 0, "limit": 2, "count": 3, "pages": 2},
            },
            {
                "items": [{"id": "three"}],
                "paging": {"offset": 2, "limit": 2, "count": 3, "pages": 2},
            },
        ],
    )
    def test_all_pages_are_collected(self, api_get, _time):
        result = get_devices(
            {"access": "token"},
            "domain-uuid",
            page_limit=2,
        )

        self.assertEqual(result["timestamp"], 456)
        self.assertEqual(result["stats"], {"total": 3})
        self.assertEqual(
            [device["id"] for device in result["devices"]],
            ["one", "two", "three"],
        )
        self.assertEqual(
            api_get.call_args_list,
            [
                call(
                    "/api/fmc_config/v1/domain/domain-uuid/devices/"
                    "devicerecords?offset=0&limit=2&expanded=true",
                    {"access": "token"},
                ),
                call(
                    "/api/fmc_config/v1/domain/domain-uuid/devices/"
                    "devicerecords?offset=2&limit=2&expanded=true",
                    {"access": "token"},
                ),
            ],
        )

    @patch("collector.devices.api_get", return_value={"items": {"id": "bad"}})
    def test_non_list_items_are_rejected(self, _api_get):
        with self.assertRaisesRegex(FmcError, "non-list items"):
            get_devices({"access": "token"}, "domain")

    def test_invalid_page_limit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "positive integer"):
            get_devices({"access": "token"}, "domain", page_limit=0)


if __name__ == "__main__":
    unittest.main()
