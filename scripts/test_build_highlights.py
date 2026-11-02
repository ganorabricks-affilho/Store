#!/usr/bin/env python3
"""Logic tests for the Parts $10+ builder. Uses a temporary database and site."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

import build_highlights as highlights


SCHEMA = """
CREATE TABLE store_inventory (
    bl_inventory_id TEXT PRIMARY KEY,
    item_no TEXT NOT NULL DEFAULT '',
    item_name TEXT NOT NULL DEFAULT '',
    color_name TEXT NOT NULL DEFAULT '',
    new_or_used TEXT NOT NULL DEFAULT '',
    quantity INTEGER NOT NULL DEFAULT 0,
    unit_price_milli INTEGER NOT NULL DEFAULT 0,
    description TEXT NOT NULL DEFAULT '',
    remarks TEXT NOT NULL DEFAULT '',
    image_url TEXT NOT NULL DEFAULT '',
    is_retain INTEGER NOT NULL DEFAULT 0,
    is_stock_room INTEGER NOT NULL DEFAULT 0
);
"""


def seed(db_path: Path, rows):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.executemany(
        """
        INSERT INTO store_inventory (
            bl_inventory_id, item_no, item_name, color_name, new_or_used,
            quantity, unit_price_milli, is_retain, is_stock_room
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.db = root / "lotledger.db"
        self.site = root / "docs"
        self.photos = self.site / "assets" / "parts" / "highlights"
        self.photos.mkdir(parents=True)
        (self.photos / "15_1.jpg").write_bytes(b"one")
        (self.photos / "15_2.PNG").write_bytes(b"two")
        (self.photos / "20_1.jpg").write_bytes(b"twenty")
        highlights.SITE = self.site
        highlights.PHOTO_DIR = self.photos
        highlights.DATA_PATH = self.site / "highlights.json"
        highlights.PAGE_DIR = self.site / "highlights"
        seed(
            self.db,
            [
                ("15", "3001", "Brick 2 x 4", "Black", "U", 2, 15000, 0, 0),
                ("9", "3024", "Plate 1 x 1", "Red", "N", 4, 9000, 0, 0),
                ("20", "3069", "Tile 1 x 2", "White", "N", 1, 20000, 0, 0),
                ("7", "3001", "Brick 2 x 4", "Blue", "U", 1, 12000, 1, 0),
                ("8", "3001", "Brick 2 x 4", "Tan", "U", 1, 12000, 0, 1),
            ],
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_build_keeps_only_ten_dollar_for_sale_lots_and_their_photos(self):
        report = highlights.sync(self.db, 10000, False)
        self.assertEqual(report["count"], 2)
        data = highlights.load_previous(highlights.DATA_PATH)
        by_id = {item["id"]: item for item in data}
        self.assertEqual(set(by_id), {"15", "20"})
        self.assertEqual(by_id["15"]["price"], "$15.000")
        self.assertEqual(
            by_id["15"]["photos"],
            ["assets/parts/highlights/15_1.jpg", "assets/parts/highlights/15_2.PNG"],
        )
        self.assertEqual(
            by_id["15"]["bricklink_url"],
            "https://store.bricklink.com/Ganorabricks?p=Ganorabricks&itemID=15#/shop",
        )
        self.assertEqual(by_id["15"]["brickowl_url"], "https://ganorabricks.brickowl.com/")
        page = (highlights.PAGE_DIR / "15.html").read_text()
        self.assertIn("../assets/parts/highlights/15_1.jpg", page)
        self.assertIn("../assets/parts/highlights/15_2.PNG", page)
        listing = (highlights.SITE / "part-highlights.html").read_text()
        self.assertIn('href="highlights/15.html"', listing)
        self.assertIn("See photos (2)", listing)
        self.assertIn("lot 15 · 3001 · Used · qty 2", listing)
        self.assertIn("lot 15 · 3001 · Used · qty 2", page)
        self.assertIn("Black Brick 2 x 4", listing)
        self.assertNotIn("Plate 1 x 1", listing)
        self.assertEqual(by_id["15"]["image_url"], "")
        self.assertIn('src="assets/parts/highlights/15_1.jpg"', listing)

    def test_list_thumbnail_uses_the_database_image_url(self):
        conn = sqlite3.connect(self.db)
        conn.execute(
            "UPDATE store_inventory SET image_url = ? WHERE bl_inventory_id = '15'",
            ("https://img.bricklink.com/ItemImage/PN/11/3001.png",),
        )
        conn.execute(
            "UPDATE store_inventory SET image_url = ? WHERE bl_inventory_id = '20'",
            ("javascript:alert(1)",),
        )
        conn.commit()
        conn.close()
        highlights.sync(self.db, 10000, False)
        listing = (highlights.SITE / "part-highlights.html").read_text()
        self.assertIn(
            'src="https://img.bricklink.com/ItemImage/PN/11/3001.png"',
            listing,
        )
        self.assertIn('referrerpolicy="no-referrer"', listing)
        self.assertNotIn("15_1.jpg", listing)
        self.assertIn('src="assets/parts/highlights/20_1.jpg"', listing)
        self.assertNotIn("javascript:", listing)

    def test_price_update_keeps_photos_and_removal_waits_for_yes(self):
        highlights.sync(self.db, 10000, False)
        conn = sqlite3.connect(self.db)
        conn.execute("UPDATE store_inventory SET unit_price_milli = 18000 WHERE bl_inventory_id = '15'")
        conn.execute("DELETE FROM store_inventory WHERE bl_inventory_id = '20'")
        conn.execute(
            """
            INSERT INTO store_inventory (
                bl_inventory_id, item_no, item_name, color_name, new_or_used,
                quantity, unit_price_milli
            ) VALUES ('30', '4073', 'Plate 1 x 1 Round', 'Yellow', 'U', 1, 11000)
            """
        )
        conn.commit()
        conn.close()

        kept = highlights.sync(self.db, 10000, False)
        self.assertEqual(kept["removed"], 0)
        data = {item["id"]: item for item in highlights.load_previous(highlights.DATA_PATH)}
        self.assertEqual(data["15"]["price"], "$18.000")
        self.assertEqual(len(data["15"]["photos"]), 2)
        self.assertIn("20", data)
        self.assertTrue((self.photos / "20_1.jpg").is_file())
        self.assertIn("30", data)

        deleted = highlights.sync(self.db, 10000, True)
        self.assertEqual(deleted["removed"], 1)
        data = {item["id"]: item for item in highlights.load_previous(highlights.DATA_PATH)}
        self.assertNotIn("20", data)
        self.assertFalse((self.photos / "20_1.jpg").exists())
        self.assertFalse((highlights.PAGE_DIR / "20.html").exists())
        self.assertTrue((self.photos / "15_1.jpg").is_file())

    def test_detail_page_shows_the_description_and_not_the_remarks(self):
        conn = sqlite3.connect(self.db)
        conn.execute(
            """
            UPDATE store_inventory
            SET remarks = 'Closet', description = 'Built and displayed'
            WHERE bl_inventory_id = '15'
            """
        )
        conn.commit()
        conn.close()
        highlights.sync(self.db, 10000, False)
        page = (highlights.PAGE_DIR / "15.html").read_text()
        self.assertIn("Built and displayed", page)
        self.assertNotIn("Closet", page)

    def test_clear_lot_photos_removes_only_that_lots_pictures(self):
        highlights.sync(self.db, 10000, False)
        (self.photos / "99_1.jpg").write_bytes(b"orphan")
        removed = highlights.clear_lot_photos("15")
        self.assertEqual([path.name for path in removed], ["15_1.jpg", "15_2.PNG"])
        self.assertFalse((self.photos / "15_1.jpg").exists())
        self.assertFalse((self.photos / "15_2.PNG").exists())
        self.assertTrue((self.photos / "20_1.jpg").is_file())
        self.assertTrue((self.photos / "99_1.jpg").is_file())
        self.assertTrue((highlights.PAGE_DIR / "15.html").is_file())
        page = (highlights.PAGE_DIR / "15.html").read_text()
        self.assertIn("No photos yet", page)
        self.assertNotIn("15_1.jpg", page)
        listing = (highlights.SITE / "part-highlights.html").read_text()
        self.assertNotIn("15_1.jpg", listing)
        self.assertIn("Black Brick 2 x 4", listing)
        data = {item["id"]: item for item in highlights.load_previous(highlights.DATA_PATH)}
        self.assertEqual(data["15"]["photos"], [])
        self.assertEqual(data["20"]["photos"], ["assets/parts/highlights/20_1.jpg"])

        orphan = highlights.clear_lot_photos("99")
        self.assertEqual([path.name for path in orphan], ["99_1.jpg"])
        self.assertFalse((self.photos / "99_1.jpg").exists())
        with self.assertRaises(SystemExit):
            highlights.clear_lot_photos("lot-15")

    def test_wifi_photo_upload_updates_the_pages(self):
        highlights.sync(self.db, 10000, False)
        dest = highlights.save_lot_photo("15", b"new-photo", "shot.jpg")
        self.assertEqual(dest.name, "15_3.jpg")
        self.assertEqual(dest.read_bytes(), b"new-photo")
        page = (highlights.PAGE_DIR / "15.html").read_text()
        self.assertIn("../assets/parts/highlights/15_3.jpg", page)
        listing = (highlights.SITE / "part-highlights.html").read_text()
        self.assertIn("See photos (3)", listing)
        data = {item["id"]: item for item in highlights.load_previous(highlights.DATA_PATH)}
        self.assertIn("assets/parts/highlights/15_3.jpg", data["15"]["photos"])
        self.assertEqual(data["20"]["photos"], ["assets/parts/highlights/20_1.jpg"])

    def test_upload_list_shows_the_same_thumbnail_as_the_parts_page(self):
        html = highlights.capture_page(
            [
                {
                    "id": "15",
                    "title": "Black Brick 2 x 4",
                    "price": "$15.000",
                    "image_url": "https://img.bricklink.com/ItemImage/PN/11/3001.png",
                    "photos": [],
                },
                {
                    "id": "20",
                    "title": "White Tile",
                    "price": "$20.000",
                    "image_url": "",
                    "photos": ["assets/parts/highlights/20_1.jpg"],
                },
                {
                    "id": "9",
                    "title": "Bad image",
                    "price": "$9.000",
                    "image_url": "javascript:alert(1)",
                    "photos": [],
                },
            ]
        )
        self.assertIn('src="https://img.bricklink.com/ItemImage/PN/11/3001.png"', html)
        self.assertIn('src="/file/20_1.jpg"', html)
        self.assertIn('referrerpolicy="no-referrer"', html)
        self.assertIn(">No photo<", html)
        self.assertNotIn("javascript:", html)


if __name__ == "__main__":
    unittest.main()
