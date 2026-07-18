import http.client
import json
import math
import threading
import unittest

from backend.data.runes_data import runes_for_api
from backend.main import (
    Handler,
    MAX_BODY_BYTES,
    MAX_BUILDS,
    MAX_COMBO_ACTIONS,
    MAX_ITEMS_PER_BUILD,
    MAX_SIMULATIONS_PER_MINUTE,
    RATE_LIMIT_BUCKETS,
    RATE_LIMIT_LOCK,
    RequestValidationError,
    SimulatorHTTPServer,
    _rate_limit,
    validate_simulation_payload,
)


def minimal_payload():
    return {
        "level": 18,
        "ability_ranks": {"Q": 5, "W": 5, "E": 5, "R": 3},
        "builds": [{
            "name": "Security test",
            "items": [],
            "runes": {"selected": [], "shards": []},
        }],
        "enemy": {
            "hp": 3500, "current_hp": 3500, "bonus_hp": 0,
            "armor": 100, "mr": 100,
        },
        "combo": [{"type": "AA"}],
        "options": {},
    }


class SecurityValidationTests(unittest.TestCase):
    def test_rune_catalog_exposes_keys_and_retains_riot_ids_as_metadata(self):
        catalog = runes_for_api()
        precision = next(
            path for path in catalog["paths"] if path["key"] == "precision")
        fleet = next(
            rune for slot in precision["slots"] for rune in slot
            if rune["key"] == "fleet_footwork")
        self.assertEqual(precision["id"], 8000)
        self.assertEqual(fleet["id"], 8021)

    def test_normal_frontend_shards_remain_valid(self):
        payload = minimal_payload()
        payload["builds"][0]["runes"]["shards"] = [
            "adaptive", "adaptive", "health",
        ]
        validated = validate_simulation_payload(payload)
        self.assertEqual(
            validated["builds"][0]["runes"]["shards"],
            ["adaptive", "adaptive", "health"],
        )

    def test_public_runes_use_readable_keys_instead_of_numeric_ids(self):
        payload = minimal_payload()
        payload["builds"][0]["runes"].update({
            "primary": "precision",
            "secondary": "sorcery",
            "selected": ["fleet_footwork", "legend_alacrity"],
        })
        validated = validate_simulation_payload(payload)
        self.assertEqual(
            validated["builds"][0]["runes"]["selected"],
            ["fleet_footwork", "legend_alacrity"],
        )

        payload["builds"][0]["runes"]["selected"] = [8021]
        with self.assertRaisesRegex(RequestValidationError, "rune key"):
            validate_simulation_payload(payload)

    def test_public_collection_limits_are_enforced(self):
        payload = minimal_payload()
        payload["builds"] = [{} for _ in range(MAX_BUILDS + 1)]
        with self.assertRaisesRegex(RequestValidationError, "limited"):
            validate_simulation_payload(payload)

        payload = minimal_payload()
        payload["combo"] = [{"type": "AA"}] * (MAX_COMBO_ACTIONS + 1)
        with self.assertRaisesRegex(RequestValidationError, "limited"):
            validate_simulation_payload(payload)

        payload = minimal_payload()
        payload["builds"][0]["items"] = ["boots"] * (MAX_ITEMS_PER_BUILD + 1)
        with self.assertRaisesRegex(RequestValidationError, "limited"):
            validate_simulation_payload(payload)

    def test_nonfinite_numbers_and_unknown_actions_are_rejected(self):
        for invalid in (math.nan, math.inf, -math.inf):
            payload = minimal_payload()
            payload["enemy"]["hp"] = invalid
            with self.assertRaisesRegex(RequestValidationError, "finite"):
                validate_simulation_payload(payload)

        payload = minimal_payload()
        payload["combo"] = [{"type": "RUN_COMMAND"}]
        with self.assertRaisesRegex(RequestValidationError, "not supported"):
            validate_simulation_payload(payload)

    def test_unified_e_and_known_catalog_values_are_required(self):
        payload = minimal_payload()
        payload["combo"] = [{"type": "E", "timing": "delayed"}]
        with self.assertRaisesRegex(RequestValidationError, "unified instant E"):
            validate_simulation_payload(payload)

        payload = minimal_payload()
        payload["builds"][0]["items"] = ["not_an_item"]
        with self.assertRaisesRegex(RequestValidationError, "known item"):
            validate_simulation_payload(payload)

    def test_rate_limiter_has_a_bounded_public_budget(self):
        key = "security-test-client"
        with RATE_LIMIT_LOCK:
            RATE_LIMIT_BUCKETS.pop(key, None)
        for index in range(MAX_SIMULATIONS_PER_MINUTE):
            self.assertEqual(_rate_limit(key, now=float(index) / 100), 0)
        self.assertGreater(_rate_limit(key, now=1.0), 0)
        with RATE_LIMIT_LOCK:
            RATE_LIMIT_BUCKETS.pop(key, None)


class SecurityHTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = SimulatorHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def connection(self):
        return http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=3)

    def test_security_headers_and_server_fingerprint(self):
        connection = self.connection()
        connection.request("GET", "/")
        response = connection.getresponse()
        response.read()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Server"), "KayleSimulator")
        self.assertEqual(response.getheader("X-Frame-Options"), "DENY")
        self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")
        self.assertIn("default-src 'self'", response.getheader(
            "Content-Security-Policy"))
        connection.close()

    def test_oversized_body_is_rejected_before_reading(self):
        connection = self.connection()
        connection.putrequest("POST", "/api/simulate")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", str(MAX_BODY_BYTES + 1))
        connection.endheaders()
        response = connection.getresponse()
        body = json.loads(response.read())
        self.assertEqual(response.status, 413)
        self.assertIn("limited", body["error"])
        connection.close()

    def test_json_content_type_is_required(self):
        connection = self.connection()
        connection.request(
            "POST", "/api/simulate", body="{}",
            headers={"Content-Type": "text/plain"})
        response = connection.getresponse()
        response.read()
        self.assertEqual(response.status, 415)
        connection.close()

    def test_normal_frontend_payload_is_accepted(self):
        payload = minimal_payload()
        payload["builds"][0]["runes"].update({
            "primary": "precision",
            "secondary": "sorcery",
            "selected": ["fleet_footwork", "legend_alacrity"],
            "shards": ["adaptive", "adaptive", "health"],
        })
        connection = self.connection()
        connection.request(
            "POST", "/api/simulate",
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        body = json.loads(response.read())
        self.assertEqual(response.status, 200)
        self.assertEqual(len(body["results"]), 1)
        connection.close()


if __name__ == "__main__":
    unittest.main()
