import os
import tempfile
import unittest

from game.storage import FileSaveStorage, SaveStorage


class TestFileSaveStorage(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json", prefix="txtgame_storage_")
        os.close(fd)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_roundtrip(self):
        storage = FileSaveStorage(self.path)
        data = {"name": "Арагорн", "gold": 77, "cleared": [0, 2]}
        storage.save(data)
        self.assertTrue(storage.exists())
        self.assertEqual(storage.load(), data)

    def test_overwrite(self):
        storage = FileSaveStorage(self.path)
        storage.save({"a": 1})
        storage.save({"b": 2})
        self.assertEqual(storage.load(), {"b": 2})

    def test_missing_returns_none(self):
        storage = FileSaveStorage(
            os.path.join(tempfile.gettempdir(), "txtgame_no_such_save_xyz.json")
        )
        self.assertFalse(storage.exists())
        self.assertIsNone(storage.load())

    def test_unicode_survives(self):
        storage = FileSaveStorage(self.path)
        storage.save({"msg": "⚔ Башни Судьбы — «реликвия»"})
        self.assertEqual(storage.load()["msg"], "⚔ Башни Судьбы — «реликвия»")

    def test_base_class_is_abstract(self):
        storage = SaveStorage()
        with self.assertRaises(NotImplementedError):
            storage.save({})
        with self.assertRaises(NotImplementedError):
            storage.load()
        with self.assertRaises(NotImplementedError):
            storage.exists()


if __name__ == "__main__":
    unittest.main()
