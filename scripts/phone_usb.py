#!/usr/bin/env python3
"""Copy part photos from a phone plugged into this Mac with a USB cable.

    python3 scripts/build_highlights.py usb

Take the picture in the phone's Camera app, then press Enter in Terminal.
The newest photo is saved as {lot id}_{number}.jpg and the Parts $10+ pages
are updated. iPhone HEIC pictures are converted to JPEG.

Android works when USB debugging is on and `adb` is installed.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import re
import shutil
import site
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".gif"}
NO_PHONE_HELP = """No phone found on USB.

Plug the phone into this Mac with a data cable, not a charge-only cable.
Unlock it and leave it unlocked. On an iPhone, tap Trust and enter the passcode.
Quit Image Capture if it is open, then unplug the phone and plug it back in.

Then run this again:
  python3 scripts/build_highlights.py usb

For an Android phone, turn on USB debugging and install adb:
  brew install android-platform-tools
"""


class NoPhone(Exception):
    pass


class PhoneUseError(Exception):
    pass


@dataclass
class RemotePhoto:
    name: str
    remote: str
    modified: datetime | None = None
    size: int = 0


def image_rank(name: str) -> tuple[tuple[int, ...], int]:
    stem = Path(name).stem
    numbers = tuple(int(part) for part in re.findall(r"\d+", stem)) or (-1,)
    edited = 1 if re.search(r"E\d", stem, re.I) else 0
    return numbers, edited


def select_camera_files(folders: dict[str, list[str]], limit: int) -> list[tuple[str, str]]:
    """Pick the newest camera files. Folder 101 sorts ahead of folder 100."""
    ranked = []
    for folder, names in folders.items():
        prefix = re.match(r"(\d+)", folder)
        folder_no = int(prefix.group(1)) if prefix else -1
        for name in names:
            if Path(name).suffix.lower() not in IMAGE_EXTS or name.startswith("."):
                continue
            numbers, edited = image_rank(name)
            ranked.append((folder_no, numbers, edited, folder, name))
    ranked.sort(reverse=True)
    return [(folder, name) for _folder_no, _numbers, _edited, folder, name in ranked[:limit]]


def parse_indexes(text: str, count: int) -> list[int]:
    cleaned = text.strip().lower()
    if count < 1:
        raise ValueError("There are no photos on the phone to copy.")
    if cleaned in {"", "newest"}:
        return [0]
    if cleaned == "all":
        return list(range(count))
    indexes = []
    seen = set()
    for part in cleaned.replace(" ", "").split(","):
        if not part.isdigit():
            raise ValueError(f"Use photo numbers like 1 or 1,2. {part!r} is not a number.")
        number = int(part)
        if number < 1 or number > count:
            raise ValueError(f"Photo {number} is not in the list. Choose 1 through {count}.")
        if number - 1 not in seen:
            seen.add(number - 1)
            indexes.append(number - 1)
    if not indexes:
        raise ValueError("Name at least one photo number.")
    return indexes


def parse_adb_devices(text: str) -> list[tuple[str, str]]:
    rows = []
    for line in text.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            rows.append((parts[0], parts[1]))
    return rows


def format_when(value: datetime | None) -> str:
    if value is None:
        return ""
    if value.tzinfo is not None:
        value = value.astimezone()
    return value.strftime("%Y-%m-%d %H:%M")


def friendly_iphone_error(exc: Exception) -> str:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    if "password" in name or "locked" in text or "password" in text:
        return "The iPhone is locked. Unlock it, keep the cable connected, and run this again."
    if "pair" in name or "trust" in text or "denied" in text or "host" in name:
        return (
            "This Mac is not trusted yet. Unlock the iPhone, tap Trust, enter the passcode, "
            "and run this again."
        )
    if "no device" in text or "not connected" in text or "usbmux" in text or "device" in name:
        return NO_PHONE_HELP.strip()
    return (
        "Could not read the iPhone. Unlock it, tap Trust if it asks, and try again.\n"
        f"({type(exc).__name__}: {exc})"
    )


def _highlights():
    import build_highlights as highlights

    return highlights


def same_bytes(lot_id: str, src: Path) -> Path | None:
    highlights = _highlights()
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    for path in highlights.photo_files(highlights.PHOTO_DIR, lot_id):
        if hashlib.sha256(path.read_bytes()).hexdigest() == digest:
            return path
    return None


def convert_heic_with_sips(src: Path, dest: Path) -> None:
    sips = shutil.which("sips")
    if not sips:
        raise SystemExit(
            "This iPhone photo is HEIC, and this computer cannot turn it into a JPEG. "
            "On a Mac the built-in sips tool does that."
        )
    result = subprocess.run(
        [sips, "-s", "format", "jpeg", str(src), "--out", str(dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not dest.is_file():
        detail = (result.stderr or result.stdout or "").strip()
        raise SystemExit(f"Could not convert {src.name} to JPEG. {detail}")


def commit_photo(src: Path, lot_id: str, convert=convert_heic_with_sips) -> Path | None:
    highlights = _highlights()
    ext = src.suffix.lower()
    work = src
    if ext in {".heic", ".heif"}:
        work = src.with_suffix(".jpg")
        convert(src, work)
        ext = ".jpg"
    elif ext not in highlights.PHOTO_EXTS:
        raise SystemExit(f"Cannot use {src.name} as a part photo.")
    existing = same_bytes(lot_id, work)
    if existing:
        print(f"Already saved as {existing.name}")
        if work != src:
            work.unlink(missing_ok=True)
        src.unlink(missing_ok=True)
        return None
    highlights.PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    dest = highlights.PHOTO_DIR / f"{lot_id}_{highlights.next_photo_index(lot_id)}{ext}"
    work.replace(dest)
    if src != dest and src.exists():
        src.unlink()
    print(f"Saved {dest.name}")
    return dest


def refresh_photo_pages() -> None:
    _highlights().refresh_photo_pages()


def match_lot(query: str, lots: list[dict]) -> tuple[str | None, str]:
    query = query.strip()
    if not query:
        return None, "Type a lot id or a few words from the part name."
    if re.fullmatch(r"\d+", query):
        known = next((lot for lot in lots if str(lot.get("id")) == query), None)
        if known:
            return query, f"Using {query}  {known.get('title', '')}  {known.get('price', '')}".rstrip()
        if lots:
            return None, f"Lot {query} is not on the Parts $10+ list. Check the id and try again."
        return query, f"Using lot {query}."
    needle = query.lower()
    matches = [
        lot
        for lot in lots
        if needle in str(lot.get("title") or "").lower()
        or needle in str(lot.get("item_no") or "").lower()
        or needle in str(lot.get("name") or "").lower()
    ]
    if len(matches) == 1:
        lot = matches[0]
        return str(lot["id"]), f"Using {lot['id']}  {lot.get('title', '')}  {lot.get('price', '')}".rstrip()
    if not matches:
        return None, "No part on the $10+ list matches that. Try the lot id."
    lines = ["More than one part matches:"]
    for lot in matches[:12]:
        lines.append(f"  {lot['id']}  {lot.get('price', '')}  {lot.get('title', '')}".rstrip())
    lines.append("Type the lot id.")
    return None, "\n".join(lines)


def _lot_label(lot_id: str) -> str:
    highlights = _highlights()
    lots = highlights.load_previous(highlights.DATA_PATH)
    known = next((lot for lot in lots if str(lot.get("id")) == lot_id), None)
    if not known:
        return lot_id
    count = len(highlights.photo_files(highlights.PHOTO_DIR, lot_id))
    photos = "1 photo already saved" if count == 1 else f"{count} photos already saved"
    return f"{lot_id}  {known.get('title', '')}  {known.get('price', '')}  ({photos})".rstrip()


async def copy_selected(session, photos: list[RemotePhoto], indexes: list[int], lot_id: str, convert) -> int:
    saved = 0
    for index in indexes:
        photo = photos[index]
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / Path(photo.name).name
            await session.download(photo, src)
            if not src.is_file() or src.stat().st_size <= 0:
                print(f"Could not read {photo.name} from the phone.")
                continue
            # commit_photo moves the file out of the temp directory.
            if commit_photo(src, lot_id, convert):
                saved += 1
                refresh_photo_pages()
    return saved


def _print_photos(photos: list[RemotePhoto]) -> None:
    if not photos:
        print("No camera photos found on the phone.")
        return
    print("Newest photos on the phone:")
    for number, photo in enumerate(photos, start=1):
        when = format_when(photo.modified)
        suffix = f"  {when}" if when else ""
        print(f"  {number}. {photo.name}{suffix}")


async def drive(session, lot: str | None, newest: int | None, pick: str | None, ask, convert) -> int:
    print(f"Connected to {session.label} over USB. Leave the phone unlocked.")
    highlights = _highlights()
    lots = highlights.load_previous(highlights.DATA_PATH)
    saved = 0
    one_shot = newest is not None or pick is not None

    while True:
        lot_id = lot
        if lot_id is None:
            while True:
                query = (await asyncio.to_thread(ask, "Which part? Lot id or a few words from the name: ")).strip()
                chosen, note = match_lot(query, lots)
                print(note)
                if chosen:
                    lot_id = chosen
                    break
        else:
            chosen, note = match_lot(lot_id, lots)
            if chosen is None:
                raise SystemExit(note)
            lot_id = chosen
            print(note)
        print(_lot_label(lot_id))

        photos = await session.list_photos()
        if not photos:
            raise SystemExit(
                "The phone is connected, but there are no pictures in its camera folder. "
                "Take one in the Camera app, then run this again."
            )
        _print_photos(photos)

        if one_shot:
            if newest is not None:
                indexes = list(range(min(newest, len(photos))))
            else:
                try:
                    indexes = parse_indexes(pick or "", len(photos))
                except ValueError as exc:
                    raise SystemExit(str(exc)) from exc
            saved += await copy_selected(session, photos, indexes, lot_id, convert)
            break

        print("Take the picture in the Camera app first.")
        print("Press Enter to copy the newest photo, type a number (or 1,2) for an older one, or q to finish.")
        while True:
            answer = (await asyncio.to_thread(ask, "Copy photo [Enter]: ")).strip()
            if answer.lower() in {"q", "quit", "done", "stop"}:
                break
            try:
                indexes = parse_indexes(answer, len(photos))
            except ValueError as exc:
                print(exc)
                continue
            saved += await copy_selected(session, photos, indexes, lot_id, convert)
            photos = await session.list_photos()
            _print_photos(photos)
        if lot is not None:
            break
        again = (await asyncio.to_thread(ask, "Another part? [y/N] ")).strip().lower()
        if again not in {"y", "yes"}:
            break

    if saved:
        photos_word = "photo" if saved == 1 else "photos"
        print(f"Saved {saved} {photos_word}.")
        print("They are on the Parts $10+ pages in this folder. Commit and push to GitHub main to publish them.")
    else:
        print("No new photos saved.")
    return saved


async def maybe_await(value):
    if asyncio.iscoroutine(value):
        return await value
    return value


async def list_dcim(afc, limit: int = 20) -> list[RemotePhoto]:
    entries = await maybe_await(afc.listdir("/DCIM"))
    folders: dict[str, list[str]] = {}
    for folder in entries:
        if not re.fullmatch(r"\d{3}[A-Za-z]+", folder):
            continue
        try:
            names = await maybe_await(afc.listdir(f"/DCIM/{folder}"))
        except Exception:
            continue
        folders[folder] = list(names)
    chosen = select_camera_files(folders, limit)
    photos = []
    for folder, name in chosen:
        remote = f"/DCIM/{folder}/{name}"
        modified = None
        size = 0
        try:
            info = await maybe_await(afc.stat(remote))
            if isinstance(info, dict):
                modified = info.get("st_mtime") if isinstance(info.get("st_mtime"), datetime) else None
                size = int(info.get("st_size") or 0)
        except Exception:
            pass
        photos.append(RemotePhoto(name=name, remote=remote, modified=modified, size=size))
    return photos


class IphoneSession:
    def __init__(self, afc, label: str):
        self._afc = afc
        self.label = label

    async def list_photos(self) -> list[RemotePhoto]:
        return await list_dcim(self._afc)

    async def download(self, photo: RemotePhoto, dest: Path) -> None:
        try:
            await maybe_await(self._afc.pull(photo.remote, str(dest), progress_bar=False))
        except TypeError:
            await maybe_await(self._afc.pull(photo.remote, str(dest)))


class AndroidSession:
    def __init__(self, serial: str, label: str | None = None):
        self.serial = serial
        self.label = label or f"Android {serial}"

    async def list_photos(self) -> list[RemotePhoto]:
        return await asyncio.to_thread(self._list_photos)

    async def download(self, photo: RemotePhoto, dest: Path) -> None:
        await asyncio.to_thread(self._download, photo, dest)

    def _download(self, photo: RemotePhoto, dest: Path) -> None:
        result = subprocess.run(
            ["adb", "-s", self.serial, "pull", photo.remote, str(dest)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0 or not dest.is_file():
            detail = (result.stderr or result.stdout or "").strip()
            raise SystemExit(f"Could not copy {photo.name} from the Android phone. {detail}")

    def _list_photos(self) -> list[RemotePhoto]:
        listed_dir = ""
        names: list[str] = []
        for remote_dir in ("/sdcard/DCIM/Camera", "/storage/emulated/0/DCIM/Camera", "/sdcard/DCIM"):
            result = subprocess.run(
                ["adb", "-s", self.serial, "shell", "ls", remote_dir],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                continue
            names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            if names:
                listed_dir = remote_dir
                break
        if not listed_dir:
            return []
        chosen = select_camera_files({listed_dir: names}, 20)
        return [RemotePhoto(name=name, remote=f"{listed_dir}/{name}") for _folder, name in chosen]


def adb_device_rows() -> list[tuple[str, str]]:
    if not shutil.which("adb"):
        return []
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        return []
    return parse_adb_devices(result.stdout)


def android_session() -> AndroidSession | None:
    rows = adb_device_rows()
    ready = [serial for serial, state in rows if state == "device"]
    if ready:
        return AndroidSession(ready[0])
    if any(state == "unauthorized" for _serial, state in rows):
        raise PhoneUseError(
            "The Android phone is connected, but USB debugging is not allowed yet. "
            "Unlock the phone, tap Allow, and run this again."
        )
    return None


def ensure_pymobiledevice3() -> None:
    try:
        import pymobiledevice3  # noqa: F401

        return
    except ImportError:
        pass
    print("Installing iPhone USB support. This happens once.")
    attempts = [
        [sys.executable, "-m", "pip", "install", "--user", "pymobiledevice3"],
        [sys.executable, "-m", "pip", "install", "--user", "--break-system-packages", "pymobiledevice3"],
    ]
    installed = False
    for command in attempts:
        result = subprocess.run(command)
        if result.returncode == 0:
            installed = True
            break
    if not installed:
        raise SystemExit(
            "Could not install iPhone USB support. Run this, then try again:\n"
            "  python3 -m pip install --user pymobiledevice3"
        )
    site.addsitedir(site.getusersitepackages())
    importlib.invalidate_caches()
    try:
        import pymobiledevice3  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "iPhone USB support installed, but this Terminal cannot see it yet. "
            "Close Terminal, open it again, and run the usb command once more."
        ) from exc


def _device_name(lockdown) -> str:
    display = getattr(lockdown, "display_name", None)
    if callable(display):
        try:
            display = display()
        except Exception:
            display = None
    if isinstance(display, str) and display.strip():
        return display.strip()
    values = getattr(lockdown, "all_values", None)
    if isinstance(values, dict):
        name = values.get("DeviceName")
        if name:
            return str(name)
    return "iPhone"


async def _lockdown_context():
    from pymobiledevice3.lockdown import create_using_usbmux

    started = create_using_usbmux()
    return await maybe_await(started)


async def _connected_devices():
    from pymobiledevice3.usbmux import list_devices

    devices = list_devices()
    return await maybe_await(devices)


async def _open_iphone_and_copy(lot, newest, pick, ask, convert) -> int:
    context = await _lockdown_context()
    if hasattr(context, "__aenter__"):
        lockdown = await context.__aenter__()

        async def close_lockdown(exc_type, exc, tb):
            await context.__aexit__(exc_type, exc, tb)
    else:
        lockdown = context.__enter__()

        async def close_lockdown(exc_type, exc, tb):
            context.__exit__(exc_type, exc, tb)

    try:
        from pymobiledevice3.services.afc import AfcService

        afc_context = AfcService(lockdown=lockdown)
        afc = await afc_context.__aenter__()
        try:
            session = IphoneSession(afc, _device_name(lockdown))
            return await drive(session, lot, newest, pick, ask, convert)
        finally:
            await afc_context.__aexit__(None, None, None)
    finally:
        await close_lockdown(None, None, None)


async def run_usb(lot: str | None, newest: int | None, pick: str | None, ask=input, convert=convert_heic_with_sips) -> int:
    print("Looking for a phone on USB. Unlock it. If an iPhone asks, tap Trust.")
    try:
        android = android_session()
    except PhoneUseError as exc:
        raise SystemExit(str(exc)) from exc

    library_ready = True
    try:
        import pymobiledevice3  # noqa: F401
    except ImportError:
        library_ready = False

    devices = []
    iphone_error = None
    if library_ready:
        try:
            devices = list(await _connected_devices() or [])
        except Exception as exc:
            iphone_error = exc
    elif android is not None:
        return await drive(android, lot, newest, pick, ask, convert)

    if not devices and not library_ready:
        ensure_pymobiledevice3()
        try:
            devices = list(await _connected_devices() or [])
        except Exception as exc:
            iphone_error = exc

    if devices:
        try:
            return await _open_iphone_and_copy(lot, newest, pick, ask, convert)
        except SystemExit:
            raise
        except Exception as exc:
            raise SystemExit(friendly_iphone_error(exc)) from exc

    if android is not None:
        return await drive(android, lot, newest, pick, ask, convert)
    if iphone_error is not None:
        message = friendly_iphone_error(iphone_error)
        if message.strip() != NO_PHONE_HELP.strip():
            raise SystemExit(message)
    raise SystemExit(NO_PHONE_HELP.strip())


def import_from_usb(lot: str | None, newest: int | None, pick: str | None) -> None:
    if newest is not None and pick:
        raise SystemExit("Pass only one of --newest or --pick.")
    if newest is not None and newest < 1:
        raise SystemExit("--newest must be at least 1.")
    if (newest is not None or pick) and not lot:
        raise SystemExit("Pass --lot with --newest or --pick. Example: --lot 541734691 --newest 1")
    try:
        asyncio.run(run_usb(lot, newest, pick))
    except KeyboardInterrupt:
        print("\nStopped.")
