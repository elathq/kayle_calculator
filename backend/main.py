"""Kayle Damage Simulator — dependency-free backend (Python stdlib only).

Run from the project root:  python run.py
Serves the API under /api/* and the static frontend from frontend/.
"""
import os
import json
import gzip
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from .data.kayle_data import kayle_stats_at, default_ability_ranks
from .data.items_data import item_list_for_api
from .data.enemy_data import ENEMY_PRESETS, enemy_stats
from .data.runes_data import runes_for_api, RUNE_MATH, RUNE_PATHS
from .engine import simulate_build

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
DEPLOY_VERSION = (
    os.environ.get("RENDER_GIT_COMMIT") or "20260718-performance1"
)[:12]

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


def clamp_level(raw, default=18):
    try:
        return max(1, min(20, int(raw)))
    except (TypeError, ValueError):
        return default


def handle_simulate(payload: dict) -> dict:
    level = clamp_level(payload.get("level"))
    ranks = payload.get("ability_ranks") or default_ability_ranks(level)
    enemy = payload.get("enemy") or {"hp": 3500, "armor": 100, "mr": 100}
    enemy = {
        "hp": float(enemy.get("hp", 3500)),
        "current_hp": float(enemy.get("current_hp", enemy.get("hp", 3500))),
        "bonus_hp": float(enemy.get("bonus_hp", 0)),
        "armor": float(enemy.get("armor", 100)),
        "mr": float(enemy.get("mr", 100)),
    }
    combo = payload.get("combo") or []
    options = payload.get("options") or {}
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

    def _send_json(self, data, status=200, cache_control="no-store"):
        body = json.dumps(data, separators=(",", ":")).encode("utf-8")
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
        if path.name == "index.html":
            body = body.replace(b"__DEPLOY_VERSION__", DEPLOY_VERSION.encode("ascii"))
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
        deploy_tag = f"-{DEPLOY_VERSION}" if path.name == "index.html" else ""
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
        self.send_header("X-Content-Type-Options", "nosniff")
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
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            self._send_json(handle_simulate(payload))
        except Exception as exc:  # surface engine errors to the UI
            self._send_json({"error": f"{type(exc).__name__}: {exc}"}, 400)

    def log_message(self, fmt, *args):
        # Icon requests otherwise produce most of the logs on hosted builds.
        status = str(args[1]) if len(args) > 1 else ""
        if self.path.startswith("/api/") or status.startswith(("4", "5")):
            print(f"[{self.address_string()}] {fmt % args}")


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Kayle Damage Simulator running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
