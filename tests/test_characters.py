import unittest
from unittest import mock

from game.characters import Character, Hero
from game import world


class TestCharacter(unittest.TestCase):
    def test_hit_damage_range(self):
        c = Character("Скелет", 30, (5, 5), luck=0, level=1)
        dmg, crit = c.hit()
        self.assertEqual(dmg, 5)
        self.assertFalse(crit)

    def test_hit_crit_doubles(self):
        c = Character("Скелет", 30, (10, 10), luck=100, level=1)
        dmg, crit = c.hit()
        self.assertEqual(dmg, 20)
        self.assertTrue(crit)

    def test_take_reduces_hp(self):
        c = Character("Скелет", 30, (1, 1))
        c.take(10)
        self.assertEqual(c.hp, 20)


class TestHero(unittest.TestCase):
    def test_all_classes_constructible(self):
        for cls in world.CLASSES:
            h = Hero("Герой", cls)
            self.assertGreater(h.max_hp, 0)
            self.assertGreater(h.attack[1], h.attack[0])

    def test_warrior_stats(self):
        h = Hero("Герой", "Воин")
        self.assertEqual(h.max_hp, 60)
        self.assertEqual(h.attack, (5, 10))
        self.assertEqual(h.luck, 5)

    def test_mage_stats(self):
        h = Hero("Герой", "Маг")
        self.assertEqual(h.max_hp, 35)
        self.assertEqual(h.attack, (8, 13))
        self.assertEqual(h.luck, 8)

    def test_level_up_at_threshold(self):
        h = Hero("Герой", "Воин")
        leveled = h.gain_exp(50)
        self.assertTrue(leveled)
        self.assertEqual(h.level, 2)
        self.assertEqual(h.exp, 0)

    def test_exp_overflow_is_carried(self):
        h = Hero("Герой", "Воин")
        h.gain_exp(60)
        self.assertEqual(h.level, 2)
        self.assertEqual(h.exp, 10)

    def test_multi_level_up(self):
        h = Hero("Герой", "Воин")
        h.gain_exp(200)
        self.assertEqual(h.level, 3)

    def test_level_up_stats(self):
        h = Hero("Герой", "Воин")
        hp_before = h.max_hp
        atk_before = h.attack
        h.gain_exp(50)
        self.assertEqual(h.max_hp, hp_before + 10)
        self.assertEqual(h.attack, (atk_before[0] + 1, atk_before[1] + 2))
        self.assertEqual(h.luck, 7)
        self.assertEqual(h.hp, h.max_hp)

    def test_attack_total_includes_bonus(self):
        h = Hero("Герой", "Маг")
        h.atk_bonus = 4
        self.assertEqual(h.attack_total, (12, 17))

    def test_reset_battle(self):
        h = Hero("Герой", "Маг")
        h.block = True
        h.atk_bonus = 4
        h.reset_battle()
        self.assertFalse(h.block)
        self.assertEqual(h.atk_bonus, 0)


if __name__ == "__main__":
    unittest.main()