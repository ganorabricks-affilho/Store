#!/usr/bin/env python3
"""Tests for copying part photos from a USB-connected phone."""

import asyncio
import json
import subprocess
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import build_highlights as highlights
import phone_usb


def lot(lot_id, title, item_no="3001"):
    return {
        "id": lot_id,
        "item_no": item_no,
        "name": title,
        "title": title,
        "condition": "Used",
        "qty": 1,
        "price_milli": 15000,
        "price": "$15.000",
        "bricklink_url": f"https://store.bricklink.com/Ganorabricks?p=Ganorabricks&itemID={lot_id}#/shop",
        "brickowl_url": "https://ganorabricks.brickowl.com/",
        "photos": [],
        "photo_page": f"highlights/{lot_id}.html",
    }


class FakeAfc:
    def __init__(self, tree, stats=None, stat_errors=()):
        self.tree = tree
        self.stats = stats or {}
        self.stat_errors = set(stat_errors)

    async def listdir(self, path):
        return list(self.tree[path])

    async def stat(self, path):
        if path in self.stat_errors:
            raise FileNotFoundError(path)
        return dict(self.stats.get(path, {}))


class FakePhone:
    def __init__(self, files):
        self.files = files
        self.label = "Test iPhone"
        self.listing = [
            phone_usb.RemotePhoto(Path(remote).name, remote) for remote in files
        ]

    async def list_photos(self):
        return list(self.listing)

    async def download(self, photo, dest):
        dest.write_bytes(self.files[photo.remote])


class GrowingPhone:
    def __init__(self):
        self.label = "Test iPhone"
        self.calls = 0

    async def list_photos(self):
        self.calls += 1
        photos = [phone_usb.RemotePhoto("IMG_1.jpg", "/DCIM/100APPLE/IMG_1.jpg")]
        if self.calls > 1:
            photos.insert(0, phone_usb.RemotePhoto("IMG_2.jpg", "/DCIM/100APPLE/IMG_2.jpg"))
        return photos

    async def download(self, photo, dest):
        dest.write_bytes(photo.remote.encode())


def answers_for(*replies):
    pending = list(replies)

    def ask(_prompt):
        if not pending:
            raise AssertionError("prompted more times than expected")
        return pending.pop(0)

    return ask


def jpeg_convert(src, dest):
    dest.write_bytes(b"jpeg:" + src.read_bytes())


class PhoneSelectionTests(unittest.TestCase):
    def test_newest_camera_file_comes_from_the_highest_folder(self):
        chosen = phone_usb.select_camera_files(
            {
                "100APPLE": ["IMG_9999.JPG", "IMG_0001.JPG", "IMG_0001.AAE"],
                "101APPLE": ["IMG_0002.HEIC", "IMG_E0002.HEIC"],
            },
            limit=3,
        )
        self.assertEqual(
            chosen,
            [
                ("101APPLE", "IMG_E0002.HEIC"),
                ("101APPLE", "IMG_0002.HEIC"),
                ("100APPLE", "IMG_9999.JPG"),
            ],
        )

    def test_parse_indexes_and_adb_devices(self):
        self.assertEqual(phone_usb.parse_indexes("", 4), [0])
        self.assertEqual(phone_usb.parse_indexes("2, 2, 4", 4), [1, 3])
        self.assertEqual(phone_usb.parse_indexes("all", 2), [0, 1])
        with self.assertRaises(ValueError):
            phone_usb.parse_indexes("9", 2)
        rows = phone_usb.parse_adb_devices("List of devices attached\nABC123\tdevice\n")
        self.assertEqual(rows, [("ABC123", "device")])
        self.assertIn("Unlock", phone_usb.friendly_iphone_error(type("PasswordRequiredError", (Exception,), {})()))

    def test_dcim_listing_keeps_dates_and_skips_a_bad_stat(self):
        taken = datetime(2026, 11, 1, 18, 4)
        afc = FakeAfc(
            {"/DCIM": ["100APPLE", "MISC"], "DCIM/100APPLE": []},
            {},
        )
        afc.tree["/DCIM/100APPLE"] = ["IMG_4.HEIC", "notes.txt"]
        afc.stats["/DCIM/100APPLE/IMG_4.HEIC"] = {"st_mtime": taken, "st_size": 12}
        photos = asyncio.run(phone_usb.list_dcim(afc))
        self.assertEqual([photo.name for photo in photos], ["IMG_4.HEIC"])
        self.assertEqual(photos[0].modified, taken)
        self.assertEqual(photos[0].remote, "/DCIM/100APPLE/IMG_4.HEIC")

    def test_android_list_uses_the_folder_that_actually_exists(self):
        def fake_run(cmd, **_kwargs):
            remote = cmd[-1]
            result = subprocess.CompletedProcess(cmd, 1, "", "missing")
            if remote == "/storage/emulated/0/DCIM/Camera":
                result = subprocess.CompletedProcess(cmd, 0, "IMG_2.jpg\nnotes.txt\nIMG_10.jpg\n", "")
            return result

        original = phone_usb.subprocess.run
        phone_usb.subprocess.run = fake_run
        try:
            photos = phone_usb.AndroidSession("serial")._list_photos()
        finally:
            phone_usb.subprocess.run = original
        self.assertEqual(
            [photo.remote for photo in photos],
            [
                "/storage/emulated/0/DCIM/Camera/IMG_10.jpg",
                "/storage/emulated/0/DCIM/Camera/IMG_2.jpg",
            ],
        )


class UsbCopyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.photos = root / "docs" / "assets" / "parts" / "highlights"
        self.photos.mkdir(parents=True)
        highlights.SITE = root / "docs"
        highlights.PHOTO_DIR = self.photos
        highlights.DATA_PATH = highlights.SITE / "highlights.json"
        highlights.PAGE_DIR = highlights.SITE / "highlights"
        highlights.DATA_PATH.write_text(
            json.dumps({"min_milli": 10000, "items": [lot("15", "Red Brick"), lot("20", "Black Brick")]})
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_enter_copies_the_newest_then_a_newer_shot(self):
        saved = asyncio.run(
            phone_usb.drive(
                GrowingPhone(),
                None,
                None,
                None,
                answers_for("red", "", "", "q", "n"),
                jpeg_convert,
            )
        )
        self.assertEqual(saved, 2)
        self.assertEqual((self.photos / "15_1.jpg").read_bytes(), b"/DCIM/100APPLE/IMG_1.jpg")
        self.assertEqual((self.photos / "15_2.jpg").read_bytes(), b"/DCIM/100APPLE/IMG_2.jpg")
        page = (highlights.PAGE_DIR / "15.html").read_text()
        self.assertIn("../assets/parts/highlights/15_1.jpg", page)
        self.assertIn("../assets/parts/highlights/15_2.jpg", page)
        listing = (highlights.SITE / "part-highlights.html").read_text()
        self.assertIn("See photos (2)", listing)

    def test_same_photo_is_not_saved_twice_and_heic_becomes_jpeg(self):
        phone = FakePhone({"/DCIM/100APPLE/IMG_9.HEIC": b"heic-bytes"})
        saved = asyncio.run(
            phone_usb.drive(
                phone,
                "15",
                None,
                None,
                answers_for("", "", "q"),
                jpeg_convert,
            )
        )
        self.assertEqual(saved, 1)
        saved_files = list(self.photos.iterdir())
        self.assertEqual([path.name for path in saved_files], ["15_1.jpg"])
        self.assertEqual(saved_files[0].read_bytes(), b"jpeg:heic-bytes")

    def test_newest_flag_copies_without_prompts(self):
        phone = FakePhone(
            {
                "/DCIM/101APPLE/IMG_3.jpg": b"new",
                "/DCIM/100APPLE/IMG_2.jpg": b"old",
            }
        )
        saved = asyncio.run(
            phone_usb.drive(phone, "20", 2, None, answers_for(), jpeg_convert)
        )
        self.assertEqual(saved, 2)
        names = sorted(path.name for path in self.photos.iterdir())
        self.assertEqual(names, ["20_1.jpg", "20_2.jpg"])

    def test_unknown_lot_and_bad_cli_flags_stop(self):
        phone = FakePhone({"/DCIM/100APPLE/IMG_1.jpg": b"x"})
        with self.assertRaises(SystemExit):
            asyncio.run(phone_usb.drive(phone, "999", 1, None, answers_for(), jpeg_convert))
        with self.assertRaises(SystemExit):
            phone_usb.import_from_usb(None, 1, None)
        with self.assertRaises(SystemExit):
            phone_usb.import_from_usb("15", 1, "1")
        self.assertEqual(list(self.photos.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
