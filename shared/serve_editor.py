from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
import base64, csv, json, mimetypes, re

ROOT = Path(__file__).resolve().parents[1]
CHAR_DIR = ROOT / "characters"
FIELDS = ["character_id", "character_name", "phase", "timeline", "event", "platform", "platform_label", "post_id", "content", "image_file", "visibility", "unlock_condition", "timestamp_mode", "notes"]
SAFE_ID = re.compile(r"[^A-Za-z0-9_\-]")

def safe_name(value):
    value = SAFE_ID.sub("_", value or "image").strip("_")
    return value or "image"

def character_path(character_id):
    path = (CHAR_DIR / safe_name(character_id)).resolve()
    if not str(path).startswith(str(CHAR_DIR.resolve())):
        raise ValueError("bad character")
    return path

def read_json_body(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8")) if raw else {}

def write_json(handler, payload, status=200):
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)

def load_feed(character_id):
    cdir = character_path(character_id)
    feed_json = cdir / "feed.json"
    if feed_json.exists():
        data = json.loads(feed_json.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "rows" in data:
            return data
    feed_csv = cdir / "feed.csv"
    rows = list(csv.DictReader(feed_csv.open("r", encoding="utf-8-sig"))) if feed_csv.exists() else []
    return {"schema_version": 1, "rows": rows}

def save_feed(character_id, rows):
    cdir = character_path(character_id)
    cdir.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "rows": rows}
    (cdir / "feed.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with (cdir / "feed.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def do_GET(self):
        path = unquote(self.path.split("?", 1)[0])
        if path == "/api/characters":
            chars = []
            for cdir in sorted(p for p in CHAR_DIR.iterdir() if p.is_dir()):
                data = load_feed(cdir.name)
                rows = data.get("rows", [])
                name = rows[0].get("character_name", cdir.name) if rows else cdir.name
                chars.append({"id": cdir.name, "name": name, "count": len(rows)})
            return write_json(self, {"characters": chars})
        if path.startswith("/api/feed/"):
            character_id = path.rsplit("/", 1)[-1]
            return write_json(self, load_feed(character_id))
        return super().do_GET()
    def do_POST(self):
        path = unquote(self.path.split("?", 1)[0])
        if path.startswith("/api/feed/"):
            character_id = path.rsplit("/", 1)[-1]
            data = read_json_body(self)
            rows = data.get("rows", [])
            save_feed(character_id, rows)
            return write_json(self, {"ok": True, "rows": len(rows)})
        if path.startswith("/api/upload/"):
            parts = path.split("/")
            character_id = parts[3] if len(parts) > 3 else ""
            post_id = parts[4] if len(parts) > 4 else ""
            data = read_json_body(self)
            data_url = data.get("data_url", "")
            if "," not in data_url:
                return write_json(self, {"ok": False, "error": "missing data_url"}, 400)
            header, encoded = data_url.split(",", 1)
            mime = header.split(";", 1)[0].replace("data:", "") or "image/png"
            ext = mimetypes.guess_extension(mime) or ".png"
            if ext == ".jpe": ext = ".jpg"
            filename = safe_name(post_id or data.get("post_id", "image")) + ext
            cdir = character_path(character_id)
            image_dir = cdir / "images"
            image_dir.mkdir(parents=True, exist_ok=True)
            (image_dir / filename).write_bytes(base64.b64decode(encoded))
            return write_json(self, {"ok": True, "image_file": "images/" + filename, "filename": filename})
        return write_json(self, {"ok": False, "error": "unknown endpoint"}, 404)

def main():
    port = 8765
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"DiaryOS feed editor running: http://127.0.0.1:{port}/editor.html")
    print("Press Ctrl+C to stop.")
    server.serve_forever()
if __name__ == "__main__": main()
