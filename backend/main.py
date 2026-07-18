"""Kayle Damage Simulator — dependency-free backend (Python stdlib only).

Run from the project root:  python run.py
Serves the API under /api/* and the static frontend from frontend/.
"""
import os
import json
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
    rune_names = {r["id"]: r["name"] for p in RUNE_PATHS for s in p["slots"] for r in s}
    dmg_ids = {r["id"] for p in RUNE_PATHS for s in p["slots"] for r in s if r["dmg"]}
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
        pending = sorted(rune_names[i] for i in selected
                         if i in dmg_ids and i not in RUNE_MATH)
        if pending:
            res["warnings"].append(
                "Rune math pending (not applied yet): " + ", ".join(pending))
        results.append(res)
    return {"results": results}


class Handler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path):
        if not path.is_file():
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        # This is a local simulator under active development. Prevent the
        # browser from keeping stale JavaScript/CSS after a code change.
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        qs = parse_qs(url.query)
        route = url.path

        if route == "/api/champion":
            level = clamp_level(qs.get("level", [18])[0])
            self._send_json({
                "stats": kayle_stats_at(level),
                "default_ranks": default_ability_ranks(level),
            })
        elif route == "/api/items":
            self._send_json(item_list_for_api())
        elif route == "/api/runes":
            self._send_json(runes_for_api())
        elif route == "/api/enemy_presets":
            self._send_json([{"key": k, "name": v["name"], "scaling": v["scaling"]}
                             for k, v in ENEMY_PRESETS.items()])
        elif route == "/api/enemy_preset":
            preset = qs.get("preset", ["average"])[0]
            level = clamp_level(qs.get("level", [18])[0])
            if preset not in ENEMY_PRESETS:
                self._send_json({"error": f"unknown preset '{preset}'"}, 400)
                return
            self._send_json(enemy_stats(preset, level))
        elif route.startswith("/api/"):
            self.send_error(404)
        else:
            # static frontend; block path traversal
            rel = route.lstrip("/") or "index.html"
            target = (FRONTEND / rel).resolve()
            if FRONTEND not in target.parents and target != FRONTEND:
                self.send_error(403)
                return
            self._send_file(target)

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
