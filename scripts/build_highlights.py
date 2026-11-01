#!/usr/bin/env python3
"""Build the Parts $10+ pages from the LotLedger database.

Reads store_inventory (the BrickLink inventory LotLedger already syncs) and
rewrites docs/highlights.json plus one photo page per lot.

Photos are files you drop in docs/assets/parts/highlights, named:

    {BrickLink inventory id}_1.jpg
    {BrickLink inventory id}_2.jpg

The number can keep going. jpg, jpeg, png, webp, heic, and gif are picked up
on the next build. Existing photos are left in place when a price changes.

    python3 scripts/build_highlights.py
    python3 scripts/build_highlights.py --db ~/Projects/Lotledger/data/lotledger.db
    python3 scripts/build_highlights.py photos

`photos` serves a page on your Wi-Fi so a phone on the same network can take
a picture and save it under the next number for that lot.
"""

from __future__ import annotations

import argparse
import json
import re
import socket
import sqlite3
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs"
PHOTO_DIR = SITE / "assets" / "parts" / "highlights"
DATA_PATH = SITE / "highlights.json"
PAGE_DIR = SITE / "highlights"
MIN_DOLLARS = 10
STORE = "Ganorabricks"
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".gif"}
LOT_FILE = re.compile(r"^(\d+)_(\d+)(\.[A-Za-z0-9]+)$")
MAX_UPLOAD = 20 * 1024 * 1024


def money3(millis: int) -> str:
    sign = "-" if millis < 0 else ""
    millis = abs(int(millis or 0))
    return f"{sign}${millis // 1000:,}.{millis % 1000:03d}"


def candidate_dbs(explicit: str | None) -> list[Path]:
    if explicit:
        return [Path(explicit).expanduser()]
    env = __import__("os").environ.get("LOTLEDGER_DB")
    home = Path.home()
    found = []
    if env:
        found.append(Path(env).expanduser())
    found.extend(
        [
            home / "Projects" / "Lotledger" / "data" / "lotledger.db",
            home / "PROJECTS" / "LOTLEDGER" / "DATA" / "LOTLEDGER.DB",
            home / "projects" / "lotledger" / "data" / "lotledger.db",
        ]
    )
    return found


MAC_DB = Path("/Users/AIRTONLADEIRAFERREIRA/PROJECTS/LOTLEDGER/DATA/LOTLEDGER.DB")


def find_db(explicit: str | None) -> Path:
    tried = candidate_dbs(explicit)
    for path in tried:
        if path.is_file():
            return path
    lines = "\n".join(f"  - {path}" for path in tried)
    home = Path.home()
    hint = ""
    if str(home) == "/home/ubuntu" or not Path("/Users").is_dir():
        hint = (
            "\n\nThis is the cloud computer, so it cannot see the database on your Mac. "
            "Open Terminal on the Mac, cd into the Store folder, and run:\n\n"
            f"  python3 scripts/build_highlights.py --db \"{MAC_DB}\"\n"
        )
    raise SystemExit(f"LotLedger database not found. Looked in:\n{lines}{hint}")


def load_lots(db_path: Path, min_milli: int) -> list[dict]:
    uri = f"file:{db_path}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
    except sqlite3.Error as exc:
        raise SystemExit(f"Could not open {db_path}: {exc}") from exc
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT bl_inventory_id, item_no, item_name, color_name, new_or_used,
                   quantity, unit_price_milli, description, remarks
            FROM store_inventory
            WHERE is_stock_room = 0
              AND is_retain = 0
              AND quantity > 0
              AND unit_price_milli >= ?
            ORDER BY unit_price_milli DESC, item_name COLLATE NOCASE, bl_inventory_id
            """,
            (min_milli,),
        ).fetchall()
    except sqlite3.Error as exc:
        raise SystemExit(
            "This database does not have the LotLedger store_inventory table "
            f"({exc})."
        ) from exc
    finally:
        conn.close()
    return [lot_record(row) for row in rows]


def lot_record(row: sqlite3.Row) -> dict:
    lot_id = str(row["bl_inventory_id"]).strip()
    item_no = (row["item_no"] or "").strip()
    name = (row["item_name"] or "").strip() or item_no or f"Lot {lot_id}"
    color = (row["color_name"] or "").strip()
    condition = {"N": "New", "U": "Used"}.get((row["new_or_used"] or "").upper(), (row["new_or_used"] or "").strip())
    title = f"{color} {name}".strip()
    millis = int(row["unit_price_milli"] or 0)
    return {
        "id": lot_id,
        "item_no": item_no,
        "name": name,
        "title": title,
        "color": color,
        "condition": condition,
        "qty": int(row["quantity"] or 0),
        "price_milli": millis,
        "price": money3(millis),
        "description": (row["description"] or "").strip(),
        "remarks": (row["remarks"] or "").strip(),
        "bricklink_url": (
            f"https://store.bricklink.com/{STORE}?p={STORE}&itemID={quote(lot_id)}#/shop"
        ),
        "brickowl_url": (
            "https://www.brickowl.com/search/catalog?query="
            f"{quote(item_no)}&seller={STORE}"
            if item_no
            else f"https://{STORE.lower()}.brickowl.com/"
        ),
        "photos": [],
        "photo_page": f"highlights/{lot_id}.html",
    }


def photo_files(photo_dir: Path, lot_id: str) -> list[Path]:
    if not photo_dir.is_dir():
        return []
    matched = []
    prefix = f"{lot_id}_"
    for path in photo_dir.iterdir():
        if not path.is_file():
            continue
        match = LOT_FILE.match(path.name)
        if match and match.group(1) == lot_id and path.suffix.lower() in PHOTO_EXTS:
            matched.append((int(match.group(2)), path.name.lower(), path))
    matched.sort()
    return [path for _n, _name, path in matched]


def attach_photos(lots: list[dict], photo_dir: Path) -> None:
    for lot in lots:
        files = photo_files(photo_dir, lot["id"])
        lot["photos"] = [f"assets/parts/highlights/{path.name}" for path in files]


def load_previous(data_path: Path) -> list[dict]:
    if not data_path.is_file():
        return []
    try:
        payload = json.loads(data_path.read_text())
    except json.JSONDecodeError:
        return []
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and item.get("id")]


def orphan_photo_ids(photo_dir: Path, keep_ids: set[str]) -> list[str]:
    if not photo_dir.is_dir():
        return []
    found = set()
    for path in photo_dir.iterdir():
        match = LOT_FILE.match(path.name)
        if match and path.suffix.lower() in PHOTO_EXTS and match.group(1) not in keep_ids:
            found.add(match.group(1))
    return sorted(found, key=lambda value: int(value))


def confirm_removal(removed: list[dict], photo_dir: Path, assume: bool | None) -> bool:
    if not removed:
        return False
    print("These lots are no longer $10 or more in the for-sale inventory:")
    for lot in removed:
        count = len(photo_files(photo_dir, str(lot["id"])))
        photos = f"{count} photo" if count == 1 else f"{count} photos"
        print(f"  {lot['id']}  {lot.get('price', '')}  {lot.get('title', '')}  ({photos})")
    if assume is True:
        print("Deleting them because --yes was passed.")
        return True
    if assume is False:
        print("Keeping them because --keep was passed.")
        return False
    if not sys.stdin.isatty():
        print("Keeping them. Re-run in a terminal to be asked, or pass --yes to delete.")
        return False
    answer = input("Delete these listings and their photos? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def delete_lot_files(lot_id: str, photo_dir: Path, page_dir: Path) -> None:
    for path in photo_files(photo_dir, lot_id):
        path.unlink()
        print(f"  deleted {path.name}")
    page = page_dir / f"{lot_id}.html"
    if page.is_file():
        page.unlink()
        print(f"  deleted {page.relative_to(SITE)}")


LIST_START = "<!-- highlights:start -->"
LIST_END = "<!-- highlights:end -->"


def render_lot_list(lots: list[dict]) -> str:
    if not lots:
        return """<div class="empty-gallery">
            <p class="empty-title">Photos coming soon</p>
            <p>When a part is worth a closer look, its photo will show up here. The full inventory stays on BrickLink and BrickOwl.</p>
        </div>"""
    rows = []
    for lot in lots:
        count = len(lot.get("photos") or [])
        if count == 0:
            photo_label = "See photos"
        elif count == 1:
            photo_label = "See photos (1)"
        else:
            photo_label = f"See photos ({count})"
        meta = " · ".join(
            bit for bit in (lot.get("item_no"), lot.get("condition"), f"qty {lot.get('qty', 0)}") if bit
        )
        page = html_escape(lot["photo_page"])
        title = html_escape(lot["title"])
        if lot.get("photos"):
            thumb = (
                f'<a class="highlight-thumb" href="{page}">'
                f'<img src="{html_escape(lot["photos"][0])}" alt=""></a>'
            )
        else:
            thumb = f'<a class="highlight-thumb" href="{page}">No photo</a>'
        rows.append(
            f"""<li class="highlight-row">
            {thumb}
            <div class="highlight-main">
                <a class="highlight-title" href="{page}">{title}</a>
                <p class="card-copy">{html_escape(meta)}</p>
                <p class="highlight-links">
                    <a href="{html_escape(lot['bricklink_url'])}" target="_blank" rel="noopener noreferrer">BrickLink</a>
                    <a href="{html_escape(lot['brickowl_url'])}" target="_blank" rel="noopener noreferrer">BrickOwl</a>
                </p>
            </div>
            <p class="highlight-price">{html_escape(lot.get('price', ''))}</p>
            <a class="btn-stud" href="{page}">{photo_label}</a>
        </li>"""
        )
    return '<ul class="highlight-list">\n' + "\n".join(rows) + "\n</ul>"


def write_highlights_page(lots: list[dict]) -> None:
    block = render_lot_list(lots)
    page = SITE / "part-highlights.html"
    if page.is_file() and LIST_START in page.read_text() and LIST_END in page.read_text():
        text = page.read_text()
        pre, rest = text.split(LIST_START, 1)
        _, post = rest.split(LIST_END, 1)
        page.write_text(f"{pre}{LIST_START}\n{block}\n{LIST_END}{post}")
        return
    page.write_text(
        "<!DOCTYPE html>\n<html><body>\n"
        f"{LIST_START}\n{block}\n{LIST_END}\n</body></html>\n"
    )


def write_site(lots: list[dict], min_milli: int) -> None:
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    PAGE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "min_milli": min_milli,
        "photo_dir": "docs/assets/parts/highlights",
        "items": lots,
    }
    DATA_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    write_highlights_page(lots)
    current_ids = {lot["id"] for lot in lots}
    for lot in lots:
        (PAGE_DIR / f"{lot['id']}.html").write_text(photo_page(lot))
    if PAGE_DIR.is_dir():
        for page in PAGE_DIR.glob("*.html"):
            if page.stem not in current_ids:
                page.unlink()


def photo_page(lot: dict) -> str:
    title = html_escape(lot["title"])
    bits = [bit for bit in (lot.get("item_no"), lot.get("condition"), f"qty {lot.get('qty', 0)}") if bit]
    meta = html_escape(" · ".join(bits))
    images = "\n".join(
        f'        <img src="../{html_escape(src)}" alt="{title}">'
        for src in lot.get("photos") or []
    )
    if not images:
        images = """        <div class="empty-gallery">
            <p class="empty-title">No photos yet</p>
            <p>Photos for this lot will show up here after they are added.</p>
        </div>"""
    extra = ""
    if lot.get("remarks"):
        extra += f"<p>{html_escape(lot['remarks'])}</p>"
    if lot.get("description"):
        extra += f"<p>{html_escape(lot['description'])}</p>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Ganorabricks</title>
    <link rel="stylesheet" href="../style.css">
</head>
<body>
<div id="navbar"></div>
<section class="page-intro">
    <p><a class="text-link" href="../part-highlights.html">Parts $10+</a></p>
    <h1 class="section-title">{title}</h1>
    <p>{meta}</p>
    <p class="highlight-price">{html_escape(lot.get("price", ""))}</p>
    {extra}
    <div class="card-actions">
        <a class="btn-stud" href="{html_escape(lot['bricklink_url'])}" target="_blank" rel="noopener noreferrer">BrickLink</a>
        <a class="btn-stud btn-orange" href="{html_escape(lot['brickowl_url'])}" target="_blank" rel="noopener noreferrer">BrickOwl</a>
    </div>
</section>
<section>
    <h2 class="section-title">Photos</h2>
    <div class="lot-photos">
{images}
    </div>
</section>
<div id="footer"></div>
<script src="../script.js"></script>
<script>loadSiteChrome();</script>
</body>
</html>
"""


def html_escape(value) -> str:
    return (
        str(value if value is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def sync(db_path: Path, min_milli: int, assume_delete: bool | None) -> dict:
    current = load_lots(db_path, min_milli)
    attach_photos(current, PHOTO_DIR)
    current_ids = {lot["id"] for lot in current}
    previous = load_previous(DATA_PATH)
    removed = [lot for lot in previous if str(lot.get("id")) not in current_ids]
    # Photos whose lot is no longer listed and was not in the last page either.
    known = current_ids | {str(lot.get("id")) for lot in previous}
    for orphan_id in orphan_photo_ids(PHOTO_DIR, known):
        removed.append({"id": orphan_id, "title": "Photos only", "price": ""})
    do_delete = confirm_removal(removed, PHOTO_DIR, assume_delete)
    if do_delete:
        for lot in removed:
            delete_lot_files(str(lot["id"]), PHOTO_DIR, PAGE_DIR)
        final = current
    else:
        kept = []
        for lot in removed:
            lot = dict(lot)
            lot["id"] = str(lot["id"])
            files = photo_files(PHOTO_DIR, lot["id"])
            lot["photos"] = [f"assets/parts/highlights/{path.name}" for path in files]
            lot["photo_page"] = f"highlights/{lot['id']}.html"
            kept.append(lot)
        final = current + kept
    final.sort(key=lambda lot: (-int(lot.get("price_milli") or 0), lot.get("title") or "", lot["id"]))
    write_site(final, min_milli)
    with_photos = sum(1 for lot in final if lot.get("photos"))
    missing = len(final) - with_photos
    print(f"Published {len(final)} lots at {money3(min_milli)} and up.")
    print(f"Photos: {with_photos} with pictures, {missing} without.")
    for lot in final:
        count = len(lot.get("photos") or [])
        print(f"  {lot.get('price', ''):>10}  {lot.get('title', '')}  ->  {lot['photo_page']} ({count})")
    print(f"Open this file: {SITE / 'part-highlights.html'}")
    print(f"Photo folder: {PHOTO_DIR}")
    print("Name files {lot id}_1.jpg, {lot id}_2.jpg, and so on.")
    print("From your phone, on the same Wi-Fi: python3 scripts/build_highlights.py photos")
    return {"count": len(final), "removed": len(removed) if do_delete else 0, "kept_removed": 0 if do_delete else len(removed)}


def next_photo_index(lot_id: str) -> int:
    numbers = []
    for path in photo_files(PHOTO_DIR, lot_id):
        match = LOT_FILE.match(path.name)
        if match:
            numbers.append(int(match.group(2)))
    return (max(numbers) if numbers else 0) + 1


def lan_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def serve_photos(port: int) -> None:
    if not DATA_PATH.is_file():
        raise SystemExit("Run the build first so the $10+ list exists.")
    payload = json.loads(DATA_PATH.read_text())
    lots = payload.get("items") or []
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            print(f"  {self.address_string()} {fmt % args}")

        def do_GET(self):
            path = urlparse(self.path).path
            if path in {"/", "/index.html"}:
                body = capture_page(lots).encode()
                return self._send(200, "text/html; charset=utf-8", body)
            if path.startswith("/lot/"):
                lot_id = path.split("/", 2)[2]
                lot = next((item for item in lots if str(item["id"]) == lot_id), None)
                if lot is None or not re.fullmatch(r"\d+", lot_id):
                    return self._send(404, "text/plain", b"Unknown lot")
                fresh = dict(lot)
                fresh["photos"] = [f"assets/parts/highlights/{p.name}" for p in photo_files(PHOTO_DIR, lot_id)]
                return self._send(200, "text/html; charset=utf-8", lot_capture_page(fresh).encode())
            if path.startswith("/file/"):
                name = Path(unquote(path[len("/file/"):])).name
                match = LOT_FILE.match(name)
                target = PHOTO_DIR / name
                if not match or not target.is_file():
                    return self._send(404, "text/plain", b"No photo")
                kind = "image/jpeg"
                if target.suffix.lower() == ".png":
                    kind = "image/png"
                elif target.suffix.lower() == ".webp":
                    kind = "image/webp"
                elif target.suffix.lower() == ".gif":
                    kind = "image/gif"
                return self._send(200, kind, target.read_bytes())
            self._send(404, "text/plain", b"Not found")

        def do_POST(self):
            path = urlparse(self.path).path
            if not path.startswith("/lot/"):
                return self._send(404, "text/plain", b"Not found")
            lot_id = path.split("/", 2)[2]
            if not re.fullmatch(r"\d+", lot_id) or not any(str(item["id"]) == lot_id for item in lots):
                return self._send(404, "text/plain", b"Unknown lot")
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > MAX_UPLOAD:
                return self._send(400, "text/plain", b"Photo is empty or larger than 20 MB")
            raw_name = self.headers.get("X-Filename") or "photo.jpg"
            ext = Path(raw_name).suffix.lower()
            if ext not in PHOTO_EXTS:
                ext = ".jpg"
            data = self.rfile.read(length)
            dest = PHOTO_DIR / f"{lot_id}_{next_photo_index(lot_id)}{ext}"
            dest.write_bytes(data)
            print(f"Saved {dest.name}")
            body = json.dumps({"file": dest.name}).encode()
            self._send(200, "application/json", body)

        def _send(self, status, content_type, body: bytes):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    ip = lan_ip()
    print(f"Photo drop is running.")
    print(f"On this Mac: http://127.0.0.1:{port}")
    print(f"On your phone, same Wi-Fi: http://{ip}:{port}")
    print("Leave this running while you take pictures. Ctrl-C stops it.")
    print("After you finish, run the build again so the website picks up the new files.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


def capture_page(lots: list[dict]) -> str:
    rows = []
    for lot in lots:
        count = len(photo_files(PHOTO_DIR, str(lot["id"])))
        label = f"{count} photo" if count == 1 else f"{count} photos"
        rows.append(
            f"""<a class="shot-row" href="/lot/{html_escape(lot['id'])}">
              <span><strong>{html_escape(lot.get('title') or lot['id'])}</strong><br>{html_escape(lot.get('price', ''))} · {label}</span>
              <span>Add</span>
            </a>"""
        )
    body = "\n".join(rows) or "<p>No lots on the $10+ list yet. Run the build first.</p>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Add part photos</title>
  <style>
    body {{ font-family: -apple-system, Segoe UI, sans-serif; margin: 0; background: #ececec; color: #222; }}
    header {{ background: #d56900; color: white; padding: 16px; }}
    main {{ padding: 12px; display: grid; gap: 10px; }}
    .shot-row {{ display: flex; justify-content: space-between; gap: 12px; align-items: center;
      background: white; padding: 14px; border-radius: 10px; text-decoration: none; color: inherit;
      border-bottom: 4px solid #f57c00; }}
    input {{ width: 100%; padding: 12px; font-size: 16px; border-radius: 8px; border: 1px solid #ccc; }}
  </style>
</head>
<body>
  <header><strong>Parts $10+</strong><p>Pick a lot, then take the photo. It is saved on this Mac.</p></header>
  <main>
    <input id="filter" type="search" placeholder="Search name or lot id" autofocus>
    <div id="rows">{body}</div>
  </main>
  <script>
    const filter = document.getElementById("filter");
    filter.addEventListener("input", () => {{
      const q = filter.value.toLowerCase();
      document.querySelectorAll(".shot-row").forEach(row => {{
        row.hidden = q && !row.textContent.toLowerCase().includes(q);
      }});
    }});
  </script>
</body>
</html>"""


def lot_capture_page(lot: dict) -> str:
    shots = []
    for src in lot.get("photos") or []:
        name = src.rsplit("/", 1)[-1]
        shots.append(f'<img src="/file/{html_escape(name)}" alt="">')
    gallery = "\n".join(shots) or "<p>No photos yet.</p>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html_escape(lot.get('title') or lot['id'])}</title>
  <style>
    body {{ font-family: -apple-system, Segoe UI, sans-serif; margin: 0; background: #ececec; }}
    header {{ background: #d56900; color: white; padding: 16px; }}
    a {{ color: white; }}
    main {{ padding: 16px; display: grid; gap: 12px; }}
    button, label.cam {{ display: block; text-align: center; background: #0288d1; color: white;
      font-size: 1.1rem; font-weight: 700; padding: 16px; border-radius: 10px; border: 0; }}
    label.cam {{ background: #d56900; }}
    input[type=file] {{ display: none; }}
    img {{ width: 100%; border-radius: 10px; background: white; }}
    #status {{ min-height: 1.2em; font-weight: 700; }}
  </style>
</head>
<body>
  <header><a href="/">Back</a><h1>{html_escape(lot.get('title') or lot['id'])}</h1>
    <p>{html_escape(lot.get('price', ''))} · lot {html_escape(lot['id'])}</p></header>
  <main>
    <p id="status"></p>
    <label class="cam">Take photo<input id="camera" type="file" accept="image/*" capture="environment"></label>
    <label class="cam" style="background:#015b85">Choose from library<input id="library" type="file" accept="image/*" multiple></label>
    <div id="gallery">{gallery}</div>
  </main>
  <script>
    async function upload(file) {{
      const status = document.getElementById("status");
      status.textContent = "Saving " + file.name + "...";
      const response = await fetch("/lot/{html_escape(lot['id'])}", {{
        method: "POST",
        headers: {{ "X-Filename": file.name }},
        body: file
      }});
      if (!response.ok) {{
        status.textContent = "Could not save that photo.";
        return;
      }}
      const saved = await response.json();
      status.textContent = "Saved " + saved.file;
      const img = document.createElement("img");
      img.src = "/file/" + saved.file + "?t=" + Date.now();
      document.getElementById("gallery").prepend(img);
    }}
    function bind(id) {{
      document.getElementById(id).addEventListener("change", async (event) => {{
        for (const file of event.target.files) await upload(file);
        event.target.value = "";
      }});
    }}
    bind("camera");
    bind("library");
  </script>
</body>
</html>"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Parts $10+ pages from LotLedger.")
    parser.add_argument("command", nargs="?", choices=("build", "photos"), default="build")
    parser.add_argument("--db", help="Path to lotledger.db. Defaults to the usual LotLedger data folder.")
    parser.add_argument("--min", type=float, default=MIN_DOLLARS, help="Minimum unit price in dollars (default 10).")
    parser.add_argument("--yes", action="store_true", help="Delete listings and photos for lots that dropped off the list.")
    parser.add_argument("--keep", action="store_true", help="Keep listings and photos for lots that dropped off the list.")
    parser.add_argument("--port", type=int, default=8787, help="Port for the phone photo page.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.yes and args.keep:
        raise SystemExit("Pass only one of --yes or --keep.")
    if args.command == "photos":
        serve_photos(args.port)
        return
    db_path = find_db(args.db)
    print(f"Reading {db_path}")
    assume = True if args.yes else False if args.keep else None
    sync(db_path, int(round(args.min * 1000)), assume)


if __name__ == "__main__":
    main()
