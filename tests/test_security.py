import http.client
import json
import math
import threading
import unittest
from types import SimpleNamespace

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

    def test_e_aa_cancel_option_requires_a_boolean(self):
        payload = minimal_payload()
        payload["options"]["use_e_for_aa_cancel"] = True
        validated = validate_simulation_payload(payload)
        self.assertIs(validated["options"]["use_e_for_aa_cancel"], True)

        payload["options"]["use_e_for_aa_cancel"] = "yes"
        with self.assertRaisesRegex(RequestValidationError, "true or false"):
            validate_simulation_payload(payload)

    def test_gluttonous_stacks_are_integer_and_capped_at_ten(self):
        payload = minimal_payload()
        payload["options"]["gluttonous_stacks"] = 10
        validated = validate_simulation_payload(payload)
        self.assertEqual(validated["options"]["gluttonous_stacks"], 10)

        for invalid in (10.5, 11, -1):
            with self.subTest(invalid=invalid):
                payload = minimal_payload()
                payload["options"]["gluttonous_stacks"] = invalid
                with self.assertRaises(RequestValidationError):
                    validate_simulation_payload(payload)

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

    def test_falsey_values_do_not_bypass_collection_type_validation(self):
        cases = (
            (("enemy",), [], "enemy must be an object"),
            (("options",), [], "options must be an object"),
            (("builds",), "", "builds must be an array"),
            (("combo",), {}, "combo must be an array"),
            (("builds", 0, "items"), {}, r"builds\[0\]\.items must be an array"),
            (("builds", 0, "runes"), [], r"builds\[0\]\.runes must be an object"),
            (
                ("builds", 0, "runes", "selected"),
                {},
                r"builds\[0\]\.runes\.selected must be an array",
            ),
            (
                ("builds", 0, "runes", "shards"),
                {},
                r"builds\[0\]\.runes\.shards must be an array",
            ),
        )
        for path, invalid, message in cases:
            with self.subTest(path=path):
                payload = minimal_payload()
                target = payload
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = invalid
                with self.assertRaisesRegex(RequestValidationError, message):
                    validate_simulation_payload(payload)

    def test_ability_ranks_respect_level_caps_and_available_points(self):
        payload = minimal_payload()
        payload["level"] = 1
        payload["ability_ranks"] = {"Q": 1, "W": 1, "E": 0, "R": 0}
        with self.assertRaisesRegex(RequestValidationError, "more than 1 points"):
            validate_simulation_payload(payload)

        payload["ability_ranks"] = {"Q": 0, "W": 0, "E": 0, "R": 1}
        with self.assertRaisesRegex(RequestValidationError, "between 0 and 0"):
            validate_simulation_payload(payload)

        payload["ability_ranks"] = {"Q": 1, "W": 0, "E": 0, "R": 0}
        validated = validate_simulation_payload(payload)
        self.assertEqual(validated["ability_ranks"], payload["ability_ranks"])

    def test_illegal_item_combinations_are_rejected(self):
        cases = (
            (["nashors_tooth", "nashors_tooth"], "duplicates"),
            (["boots", "berserkers_greaves"], "Boots"),
            (["lich_bane", "essence_reaver"], "Spellblade"),
            (["dorans_ring", "dark_seal"], "Starter"),
            (["void_staff", "cryptbloom"], "Blight"),
            (["terminus", "lord_dominiks_regards"], "Fatality"),
            (["bloodletters_curse", "terminus"], "Blight"),
            (["lord_dominiks_regards", "terminus"], "Fatality"),
        )
        for items, message in cases:
            with self.subTest(items=items):
                payload = minimal_payload()
                payload["builds"][0]["items"] = items
                with self.assertRaisesRegex(RequestValidationError, message):
                    validate_simulation_payload(payload)

    def test_legal_item_boundaries_are_preserved(self):
        payload = minimal_payload()
        payload["builds"][0]["items"] = [
            "lord_dominiks_regards",
            "bloodletters_curse",
            "nashors_tooth",
            "rabadons_deathcap",
            "berserkers_greaves",
            "yun_tal_wildarrows",
        ]
        validated = validate_simulation_payload(payload)
        self.assertEqual(
            validated["builds"][0]["items"],
            payload["builds"][0]["items"],
        )

        for key in (
                "gunmetal_greaves", "swiftmarch", "spellslingers_shoes",
                "immortal_path", "chainlaced_crushers", "armored_advance"):
            with self.subTest(key=key, level=18):
                payload = minimal_payload()
                payload["builds"][0]["items"] = [key]
                validate_simulation_payload(payload)
            for level in (19, 20):
                with self.subTest(key=key, level=level):
                    payload = minimal_payload()
                    payload["level"] = level
                    payload["builds"][0]["items"] = [key]
                    with self.assertRaisesRegex(
                            RequestValidationError, "levels 19"):
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

    def test_client_key_ignores_spoofable_forwarding_headers(self):
        request = SimpleNamespace(
            headers={"X-Forwarded-For": "198.51.100.10, 192.0.2.2"},
            client_address=("2001:0db8:0:0:0:0:0:1", 12345),
        )
        first = Handler._client_key(request)
        request.headers["X-Forwarded-For"] = "203.0.113.99"
        self.assertEqual(Handler._client_key(request), first)
        self.assertEqual(first, "peer:2001:db8::1")

        request.client_address = ("not-an-ip-address", 12345)
        self.assertEqual(Handler._client_key(request), "peer:unknown")


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

    def test_illegal_item_build_returns_bad_request(self):
        payload = minimal_payload()
        payload["builds"][0]["items"] = ["lich_bane", "essence_reaver"]
        connection = self.connection()
        connection.request(
            "POST", "/api/simulate",
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        body = json.loads(response.read())
        self.assertEqual(response.status, 400)
        self.assertIn("Spellblade", body["error"])
        connection.close()


if __name__ == "__main__":
    unittest.main()
