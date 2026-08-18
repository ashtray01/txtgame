import unittest

from game import art, world


class TestArtCoverage(unittest.TestCase):
    def test_every_mob_has_art(self):
        for mobs in world.MOBS.values():
            for name in mobs:
                self.assertTrue(art.get_enemy(name).strip(), f"нет арта для моба: {name}")

    def test_every_boss_has_art(self):
        for tower in world.TOWERS:
            self.assertTrue(art.get_enemy(tower["boss"]).strip(), f"нет арта для босса: {tower['boss']}")

    def test_every_class_has_hero_art(self):
        for cls in world.CLASSES:
            self.assertTrue(art.get_hero(cls).strip(), f"нет арта героя: {cls}")

    def test_every_relic_has_art(self):
        for tower in world.TOWERS:
            self.assertTrue(art.get_relic(tower["relic"]).strip(), f"нет арта реликвии: {tower['relic']}")

    def test_extra_scenes_exist(self):
        for name in ("CAMP", "SHOPKEEPER", "DEATH", "VICTORY"):
            self.assertTrue(art.get_extra(name).strip(), f"нет арта сцены: {name}")


class TestArtFallback(unittest.TestCase):
    def test_unknown_enemy_returns_empty(self):
        self.assertEqual(art.get_enemy("Нет такого моба"), "")

    def test_unknown_hero_returns_empty(self):
        self.assertEqual(art.get_hero("Нет такого класса"), "")

    def test_unknown_relic_returns_empty(self):
        self.assertEqual(art.get_relic("Нет такой реликвии"), "")

    def test_unknown_scene_returns_empty(self):
        self.assertEqual(art.get("Нет такой сцены"), "")
        self.assertEqual(art.get_extra("Нет такой сцены"), "")


if __name__ == "__main__":
    unittest.main()