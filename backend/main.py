"""Kayle Damage Simulator — dependency-free backend (Python stdlib only).

Run from the project root:  python run.py
Serves the API under /api/* and the static frontend from frontend/.
"""
import os
import json
import gzip
import math
import mimetypes
import secrets
import threading
import time
import traceback
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from .data.kayle_data import kayle_stats_at, default_ability_ranks
from .data.items_data import ITEMS, item_list_for_api
from .data.enemy_data import ENEMY_PRESETS, enemy_stats
from .data.runes_data import (
    SHARDS,
    RUNE_MATH,
    RUNE_PATHS,
    runes_for_api,
)
from .engine import simulate_build

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
DEPLOY_VERSION = (
    os.environ.get("RENDER_GIT_COMMIT") or "20260718-security1"
)[:12]
IS_RENDER = os.environ.get("RENDER", "").lower() == "true"


def frontend_asset_version():
    """Keep production assets commit-pinned and local edits cache-safe."""
    if IS_RENDER:
        return DEPLOY_VERSION
    latest_asset_mtime = max(
        path.stat().st_mtime_ns
        for path in (
            FRONTEND / "style.css",
            FRONTEND / "app.js",
            FRONTEND.parent / "backend" / "data" / "__init__.py",
            FRONTEND.parent / "backend" / "data" / "items_data.py",
            FRONTEND.parent / "backend" / "data" / "runes_data.py",
            FRONTEND.parent / "backend" / "data" / "enemy_data.py",
            FRONTEND.parent / "backend" / "data" / "kayle_data.py",
        )
    )
    return f"dev-{latest_asset_mtime:x}"

MAX_BODY_BYTES = 256 * 1024
MAX_BUILDS = 8
MAX_ITEMS_PER_BUILD = 6
MAX_COMBO_ACTIONS = 100
MAX_BUILD_NAME_LENGTH = 60
MAX_WAIT_SECONDS = 60.0
MAX_SIMULATIONS_PER_MINUTE = 30
MAX_CONCURRENT_SIMULATIONS = max(
    1, min(4, int(os.environ.get("MAX_CONCURRENT_SIMULATIONS", "2"))))
SIMULATION_SLOTS = threading.BoundedSemaphore(MAX_CONCURRENT_SIMULATIONS)
RATE_LIMIT_LOCK = threading.Lock()
RATE_LIMIT_BUCKETS = {}

# These catalogs do not change while a deployed process is running. Building
# them once also makes the initial bootstrap request cheaper on small hosts.
ITEM_CATALOG = item_list_for_api()
RUNE_CATALOG = runes_for_api()
ENEMY_PRESET_CATALOG = [
    {"key": key, "name": value["name"], "scaling": value["scaling"]}
    for key, value in ENEMY_PRESETS.items()
]
RUNE_NAMES = {
    rune["id"]: rune["name"]
    for path in RUNE_PATHS for slot in path["slots"] for rune in slot
}
DAMAGE_RUNE_IDS = {
    rune["id"]
    for path in RUNE_PATHS for slot in path["slots"] for rune in slot
    if rune["dmg"]
}
RUNE_IDS = set(RUNE_NAMES)
RUNE_PATH_IDS = {path["id"] for path in RUNE_PATHS}
SHARD_KEYS = {
    option["key"]
    for slot in SHARDS
    for option in slot["options"]
}
ACTION_TYPES = {"AA", "Q", "W", "E", "R", "ITEM_ACTIVE", "WAIT"}


class RequestValidationError(ValueError):
    """A safe validation message that may be returned to an API client."""


def _mapping(value, label):
    if not isinstance(value, dict):
        raise RequestValidationError(f"{label} must be an object")
    return value


def _sequence(value, label, maximum):
    if not isinstance(value, list):
        raise RequestValidationError(f"{label} must be an array")
    if len(value) > maximum:
        raise RequestValidationError(
            f"{label} is limited to {maximum} entries")
    return value


def _number(value, label, minimum, maximum, integer=False):
    if isinstance(value, bool):
        raise RequestValidationError(f"{label} must be a number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise RequestValidationError(f"{label} must be a number") from None
    if not math.isfinite(number):
        raise RequestValidationError(f"{label} must be finite")
    if number < minimum or number > maximum:
        raise RequestValidationError(
            f"{label} must be between {minimum:g} and {maximum:g}")
    if integer:
        if not number.is_integer():
            raise RequestValidationError(f"{label} must be a whole number")
        return int(number)
    return number


def _optional_bool(source, key, target):
    if key not in source:
        return
    if not isinstance(source[key], bool):
        raise RequestValidationError(f"options.{key} must be true or false")
    target[key] = source[key]


def _reject_json_constant(value):
    raise RequestValidationError("JSON numbers must be finite")


def validate_simulation_payload(payload):
    """Validate and copy all public input before it reaches the engine."""
    payload = _mapping(payload, "request body")
    level = _number(payload.get("level", 18), "level", 1, 20, integer=True)

    raw_ranks = payload.get("ability_ranks")
    if raw_ranks is None:
        ranks = default_ability_ranks(level)
    else:
        raw_ranks = _mapping(raw_ranks, "ability_ranks")
        ranks = {
            ability: _number(
                raw_ranks.get(ability, 0),
                f"ability_ranks.{ability}",
                0,
                3 if ability == "R" else 5,
                integer=True,
            )
            for ability in ("Q", "W", "E", "R")
        }

    raw_enemy = _mapping(payload.get("enemy") or {}, "enemy")
    hp = _number(raw_enemy.get("hp", 3500), "enemy.hp", 1, 10_000_000)
    current_hp = _number(
        raw_enemy.get("current_hp", hp), "enemy.current_hp", 0, hp)
    enemy = {
        "hp": hp,
        "current_hp": current_hp,
        "bonus_hp": _number(
            raw_enemy.get("bonus_hp", 0), "enemy.bonus_hp", 0, 10_000_000),
        "armor": _number(
            raw_enemy.get("armor", 100), "enemy.armor", -10_000, 100_000),
        "mr": _number(
            raw_enemy.get("mr", 100), "enemy.mr", -10_000, 100_000),
    }

    raw_options = _mapping(payload.get("options") or {}, "options")
    options = {}
    for boolean_key in (
        "pre_stacked_zeal", "pre_stacked_rageblade",
        "pre_stacked_yun_tal", "fleet_starts_energized", "assume_river",
    ):
        _optional_bool(raw_options, boolean_key, options)
    numeric_options = {
        "game_time_min": (0, 1_000, False),
        "kayle_hp_pct": (0, 100, False),
        "dh_souls": (0, 10_000, True),
        "dark_seal_stacks": (0, 10, True),
        "legend_stacks": (0, 10, True),
        "relentless_stacks": (0, 5, True),
    }
    for key, (minimum, maximum, integer) in numeric_options.items():
        if key in raw_options:
            options[key] = _number(
                raw_options[key], f"options.{key}", minimum, maximum, integer)

    builds = []
    for index, raw_build in enumerate(_sequence(
            payload.get("builds") or [], "builds", MAX_BUILDS)):
        raw_build = _mapping(raw_build, f"builds[{index}]")
        name = raw_build.get("name", f"Build {index + 1}")
        if not isinstance(name, str):
            raise RequestValidationError(f"builds[{index}].name must be text")
        if len(name) > MAX_BUILD_NAME_LENGTH:
            raise RequestValidationError(
                f"builds[{index}].name is limited to {MAX_BUILD_NAME_LENGTH} characters")

        item_keys = []
        for item_index, key in enumerate(_sequence(
                raw_build.get("items") or [],
                f"builds[{index}].items",
                MAX_ITEMS_PER_BUILD)):
            if not isinstance(key, str) or key not in ITEMS:
                raise RequestValidationError(
                    f"builds[{index}].items[{item_index}] is not a known item")
            item_keys.append(key)

        raw_runes = _mapping(raw_build.get("runes") or {},
                             f"builds[{index}].runes")
        selected = []
        for rune_index, rune_id in enumerate(_sequence(
                raw_runes.get("selected") or [],
                f"builds[{index}].runes.selected", 6)):
            rune_id = _number(
                rune_id,
                f"builds[{index}].runes.selected[{rune_index}]",
                1,
                100_000,
                integer=True,
            )
            if rune_id not in RUNE_IDS:
                raise RequestValidationError(
                    f"builds[{index}].runes.selected[{rune_index}] is not a known rune")
            selected.append(rune_id)

        shards = []
        for shard_index, shard in enumerate(_sequence(
                raw_runes.get("shards") or [],
                f"builds[{index}].runes.shards", 3)):
            if not isinstance(shard, str) or shard not in SHARD_KEYS:
                raise RequestValidationError(
                    f"builds[{index}].runes.shards[{shard_index}] is not a known shard")
            shards.append(shard)

        safe_runes = {"selected": selected, "shards": shards}
        for path_key in ("primary", "secondary"):
            if path_key in raw_runes:
                path_id = _number(
                    raw_runes[path_key],
                    f"builds[{index}].runes.{path_key}",
                    1,
                    100_000,
                    integer=True,
                )
                if path_id not in RUNE_PATH_IDS:
                    raise RequestValidationError(
                        f"builds[{index}].runes.{path_key} is not a known path")
                safe_runes[path_key] = path_id

        builds.append({"name": name, "items": item_keys, "runes": safe_runes})

    combo = []
    for index, raw_action in enumerate(_sequence(
            payload.get("combo") or [], "combo", MAX_COMBO_ACTIONS)):
        raw_action = _mapping(raw_action, f"combo[{index}]")
        kind = raw_action.get("type")
        if kind not in ACTION_TYPES:
            raise RequestValidationError(f"combo[{index}].type is not supported")
        action = {"type": kind}
        if kind == "ITEM_ACTIVE":
            key = raw_action.get("item")
            if (not isinstance(key, str) or key not in ITEMS
                    or "active" not in ITEMS[key]):
                raise RequestValidationError(
                    f"combo[{index}].item is not a known active item")
            action["item"] = key
        elif kind == "WAIT":
            action["duration"] = _number(
                raw_action.get("duration", 0.1),
                f"combo[{index}].duration",
                0,
                MAX_WAIT_SECONDS,
            )
        elif kind == "E":
            timing = raw_action.get("timing", "instant")
            if timing != "instant":
                raise RequestValidationError(
                    f"combo[{index}].timing must use the unified instant E")
        combo.append(action)

    return {
        "level": level,
        "ability_ranks": ranks,
        "enemy": enemy,
        "combo": combo,
        "options": options,
        "builds": builds,
    }


def _rate_limit(client_key, now=None):
    """Return retry seconds, or zero when this client may simulate."""
    now = time.monotonic() if now is None else now
    cutoff = now - 60.0
    with RATE_LIMIT_LOCK:
        if client_key not in RATE_LIMIT_BUCKETS and len(RATE_LIMIT_BUCKETS) >= 4096:
            # New addresses share a bounded overflow bucket until old entries
            # expire, preventing an address-spoofing memory attack.
            client_key = "__overflow__"
        bucket = RATE_LIMIT_BUCKETS.setdefault(client_key, deque())
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= MAX_SIMULATIONS_PER_MINUTE:
            return max(1, math.ceil(60.0 - (now - bucket[0])))
        bucket.append(now)
        # Bound limiter memory even if many source addresses hit the service.
        if len(RATE_LIMIT_BUCKETS) > 4096:
            stale = [key for key, values in RATE_LIMIT_BUCKETS.items()
                     if not values or values[-1] <= cutoff]
            for key in stale[:2048]:
                RATE_LIMIT_BUCKETS.pop(key, None)
        return 0


def clamp_level(raw, default=18):
    try:
        return max(1, min(20, int(raw)))
    except (TypeError, ValueError):
        return default


def handle_simulate(payload: dict) -> dict:
    payload = validate_simulation_payload(payload)
    level = payload["level"]
    ranks = payload["ability_ranks"]
    enemy = payload["enemy"]
    combo = payload["combo"]
    options = payload["options"]
    results = []
    for build in payload.get("builds", []):
        selected_runes = (build.get("runes") or {}).get("selected", [])
        shards = (build.get("runes") or {}).get("shards", [])
        res = simulate_build(
            level=level,
            ranks={k: int(v) for k, v in ranks.items()},
            item_keys=build.get("items", []),
            enemy=enemy,
            combo=combo,
            options={**options, "rune_ids": selected_runes, "shards": shards},
        )
        res["build_name"] = build.get("name", "Build")
        res["items"] = build.get("items", [])
        res["runes"] = build.get("runes")
        # Damage-relevant runes without provided math are not yet applied — say so.
        selected = set((build.get("runes") or {}).get("selected", []))
        pending = sorted(RUNE_NAMES[i] for i in selected
                         if i in DAMAGE_RUNE_IDS and i not in RUNE_MATH)
        if pending:
            res["warnings"].append(
                "Rune math pending (not applied yet): " + ", ".join(pending))
        results.append(res)
    return {"results": results}


class Handler(BaseHTTPRequestHandler):

    # Keep connections reusable when the app is run without Render's HTTP/2
    # proxy in front of it.
    protocol_version = "HTTP/1.1"
    server_version = "KayleSimulator"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def version_string(self):
        return self.server_version

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        )
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("X-XSS-Protection", "0")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; connect-src 'self'; "
            "img-src 'self' https://cdn.communitydragon.org data:; "
            "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; "
            "form-action 'self'",
        )
        if IS_RENDER:
            self.send_header(
                "Strict-Transport-Security", "max-age=31536000")
        super().end_headers()

    def _send_json(self, data, status=200, cache_control="no-store"):
        body = json.dumps(
            data, separators=(",", ":"), allow_nan=False).encode("utf-8")
        use_gzip = "gzip" in self.headers.get("Accept-Encoding", "") and len(body) >= 1024
        if use_gzip:
            body = gzip.compress(body, compresslevel=6)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", cache_control)
        if use_gzip:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, versioned=False):
        if not path.is_file():
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        body = path.read_bytes()
        asset_version = frontend_asset_version() if path.name == "index.html" else ""
        if path.name == "index.html":
            body = body.replace(
                b"__DEPLOY_VERSION__", asset_version.encode("ascii"))
        is_text = ctype.startswith("text/") or ctype in {
            "application/javascript", "application/xml", "image/svg+xml",
        }
        use_gzip = (
            is_text and len(body) >= 1024
            and "gzip" in self.headers.get("Accept-Encoding", "")
        )
        if use_gzip:
            body = gzip.compress(body, compresslevel=6)

        stat = path.stat()
        encoding_tag = "-gz" if use_gzip else ""
        deploy_tag = f"-{asset_version}" if path.name == "index.html" else ""
        etag = f'"{stat.st_mtime_ns:x}-{stat.st_size:x}{deploy_tag}{encoding_tag}"'
        if path.name == "index.html":
            cache_control = "no-cache"
        elif versioned:
            cache_control = "public, max-age=31536000, immutable"
        elif "icons" in path.parts:
            cache_control = "public, max-age=604800"
        else:
            cache_control = "public, max-age=3600, must-revalidate"

        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("Cache-Control", cache_control)
            self.send_header("ETag", etag)
            if is_text:
                self.send_header("Vary", "Accept-Encoding")
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", cache_control)
        self.send_header("ETag", etag)
        if use_gzip:
            self.send_header("Content-Encoding", "gzip")
        if is_text:
            self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        qs = parse_qs(url.query)
        route = url.path

        if route == "/healthz":
            self._send_json({"status": "ok"}, cache_control="no-store")
        elif route == "/api/bootstrap":
            level = clamp_level(qs.get("level", [18])[0])
            preset = qs.get("preset", ["dummy"])[0]
            if preset not in ENEMY_PRESETS:
                self._send_json({"error": f"unknown preset '{preset}'"}, 400)
                return
            self._send_json({
                "items": ITEM_CATALOG,
                "runes": RUNE_CATALOG,
                "enemy_presets": ENEMY_PRESET_CATALOG,
                "champion": {
                    "stats": kayle_stats_at(level),
                    "default_ranks": default_ability_ranks(level),
                },
                "enemy": enemy_stats(preset, level),
            }, cache_control="public, max-age=300")
        elif route == "/api/champion":
            level = clamp_level(qs.get("level", [18])[0])
            self._send_json({
                "stats": kayle_stats_at(level),
                "default_ranks": default_ability_ranks(level),
            }, cache_control="public, max-age=86400")
        elif route == "/api/items":
            self._send_json(ITEM_CATALOG, cache_control="public, max-age=300")
        elif route == "/api/runes":
            self._send_json(RUNE_CATALOG, cache_control="public, max-age=300")
        elif route == "/api/enemy_presets":
            self._send_json(ENEMY_PRESET_CATALOG, cache_control="public, max-age=300")
        elif route == "/api/enemy_preset":
            preset = qs.get("preset", ["average"])[0]
            level = clamp_level(qs.get("level", [18])[0])
            if preset not in ENEMY_PRESETS:
                self._send_json({"error": f"unknown preset '{preset}'"}, 400)
                return
            self._send_json(enemy_stats(preset, level),
                            cache_control="public, max-age=86400")
        elif route.startswith("/api/"):
            self.send_error(404)
        else:
            # static frontend; block path traversal
            rel = route.lstrip("/") or "index.html"
            target = (FRONTEND / rel).resolve()
            if FRONTEND not in target.parents and target != FRONTEND:
                self.send_error(403)
                return
            self._send_file(target, versioned="v" in qs)

    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/api/simulate":
            self.send_error(404)
            return
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].lower()
        if content_type != "application/json":
            self.close_connection = True
            self._send_json({"error": "Content-Type must be application/json"}, 415)
            return
        if self.headers.get("Content-Encoding", "identity").lower() != "identity":
            self.close_connection = True
            self._send_json({"error": "Compressed request bodies are not supported"}, 415)
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except (TypeError, ValueError):
            self.close_connection = True
            self._send_json({"error": "A valid Content-Length is required"}, 411)
            return
        if length < 1:
            self.close_connection = True
            self._send_json({"error": "A non-empty JSON body is required"}, 400)
            return
        if length > MAX_BODY_BYTES:
            self.close_connection = True
            self._send_json(
                {"error": f"Request body is limited to {MAX_BODY_BYTES} bytes"}, 413)
            return

        try:
            body = self.rfile.read(length)
            if len(body) != length:
                raise RequestValidationError("Request body ended before Content-Length")
            payload = json.loads(
                body,
                parse_constant=_reject_json_constant,
            )
            retry_after = _rate_limit(self._client_key())
            if retry_after:
                self.send_response(429)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Retry-After", str(retry_after))
                response = json.dumps({
                    "error": "Too many simulations; please wait before retrying",
                }, separators=(",", ":")).encode("utf-8")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)
                return
            if not SIMULATION_SLOTS.acquire(blocking=False):
                self.send_response(429)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Retry-After", "1")
                response = b'{"error":"Simulator is busy; please retry shortly"}'
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)
                return
            try:
                result = handle_simulate(payload)
            finally:
                SIMULATION_SLOTS.release()
            self._send_json(result)
        except RequestValidationError as exc:
            self._send_json({"error": str(exc)}, 400)
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json({"error": "Request body must contain valid JSON"}, 400)
        except Exception:
            error_id = secrets.token_hex(4)
            print(f"Simulation error {error_id}")
            traceback.print_exc()
            self._send_json(
                {"error": f"Simulation failed (reference {error_id})"}, 500)

    def handle_expect_100(self):
        try:
            length = int(self.headers.get("Content-Length", ""))
        except (TypeError, ValueError):
            length = -1
        if length < 1 or length > MAX_BODY_BYTES:
            self.close_connection = True
            self._send_json({"error": "Request body size is invalid"}, 413)
            return False
        return super().handle_expect_100()

    def _client_key(self):
        forwarded = self.headers.get("X-Forwarded-For", "")
        if IS_RENDER and forwarded:
            return forwarded.split(",", 1)[0].strip()[:64]
        return str(self.client_address[0])[:64]

    def log_message(self, fmt, *args):
        # Icon requests otherwise produce most of the logs on hosted builds.
        status = str(args[1]) if len(args) > 1 else ""
        if self.path.startswith("/api/") or status.startswith(("4", "5")):
            print(f"[{self.address_string()}] {fmt % args}")


class SimulatorHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 64


def main():
    server = SimulatorHTTPServer((HOST, PORT), Handler)
    print(f"Kayle Damage Simulator running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
