import asyncio
import os
import tempfile
import unittest
from unittest import mock

from game import Game, world
from game.characters import Hero
from game.storage import FileSaveStorage


def run(coro):
    """Запуск async-метода Game в тестах."""
    return asyncio.run(coro)


class FakeIO:
    def __init__(self, inputs=None):
        self.inputs = list(inputs or [])
        self.out = []

    def ask(self, *a):
        return self.inputs.pop(0) if self.inputs else "0"

    def say(self, text=""):
        self.out.append(str(text))

    def clear(self):
        pass

    def sleep(self, sec=0):
        pass


def make_game(*inputs):
    io = FakeIO(list(inputs))
    g = Game(out=io.say, get_input=io.ask, clear_fn=io.clear, sleep=io.sleep)
    fd, g.save_path = tempfile.mkstemp(suffix=".json", prefix="txtgame_test_")
    os.close(fd)
    return g, io


def make_strong_hero(g, hp=5000):
    g.hero = Hero("Герой", "Воин")
    g.hero.max_hp = hp
    g.hero.hp = hp
    g.hero.attack = (999, 999)
    g.hero.luck = 100
    return g.hero


def cleanup(g):
    if os.path.exists(g.save_path):
        os.remove(g.save_path)


class TestSpawnEnemy(unittest.TestCase):
    def setUp(self):
        self.g, self.io = make_game()
        make_strong_hero(self.g)

    def tearDown(self):
        cleanup(self.g)

    def test_minion_scales_with_diff_and_level(self):
        low = self.g.spawn_enemy(1)
        high = self.g.spawn_enemy(5)
        self.assertLess(low.max_hp, high.max_hp)
        self.assertLess(low.attack[0], high.attack[0])

    def test_boss_stronger_than_minion(self):
        minion = self.g.spawn_enemy(3)
        boss = self.g.spawn_enemy(3, is_boss=True, boss_name="Владыка")
        self.assertGreater(boss.max_hp, minion.max_hp)
        self.assertEqual(boss.name, "Владыка")


class TestBattle(unittest.TestCase):
    def test_battle_win_gives_exp_and_gold(self):
        g, io = make_game("1", "1", "1", "1", "1")
        h = make_strong_hero(g)
        exp_before = h.exp
        gold_before = g.gold
        result = run(g.battle(g.spawn_enemy(1)))
        self.assertTrue(result)
        self.assertGreater(g.gold, gold_before)
        self.assertGreaterEqual(h.exp, exp_before)

    def test_battle_defeat_reloads_from_save(self):
        g, io = make_game("1", "1")
        h = make_strong_hero(g, hp=5000)
        h.hp = 1
        h.attack = (0, 0)
        h.luck = 0
        g.inv["Зелье ХП"] = 0
        result = run(g.battle(g.spawn_enemy(5)))
        self.assertFalse(result)
        self.assertLess(h.hp, 1)
        self.assertGreaterEqual(g.hero.hp, 1)

    def test_potion_heals_in_battle(self):
        g, io = make_game("3", "1", "1", "1", "1", "1")
        h = make_strong_hero(g)
        h.hp = 1
        g.inv["Зелье ХП"] = 1
        with mock.patch.object(g, "drop_loot"):
            run(g.battle(g.spawn_enemy(1)))
        self.assertEqual(g.inv["Зелье ХП"], 0)
        self.assertGreater(h.hp, 1)

    def test_sharpen_bonus_applied(self):
        g, io = make_game("1")
        h = make_strong_hero(g)
        g.inv["Заточка"] = 1
        enemy = g.spawn_enemy(1)
        enemy.max_hp = 99999
        enemy.hp = 99999
        run(g.battle_item(enemy))
        self.assertEqual(h.atk_bonus, 4)
        self.assertEqual(g.inv["Заточка"], 0)

    def test_scroll_deals_damage(self):
        g, io = make_game("2")
        h = make_strong_hero(g)
        g.inv["Свиток силы"] = 1
        enemy = g.spawn_enemy(1)
        hp_before = enemy.hp
        run(g.battle_item(enemy))
        self.assertEqual(enemy.hp, hp_before - 25)

    def test_block_reduces_enemy_damage(self):
        g, io = make_game("2", "1", "1")
        h = make_strong_hero(g)
        h.attack = (999, 999)
        h.max_hp = 1000
        h.hp = 1000
        enemy = g.spawn_enemy(5)
        enemy.luck = 0
        with mock.patch("game.game.random.randint", return_value=20):
            result = run(g.battle(enemy))
        self.assertTrue(result)
        self.assertGreater(h.hp, 800)

    def test_ability_sets_cooldown(self):
        g, io = make_game("4")
        h = make_strong_hero(g)
        h.ability_cd = 0
        enemy = g.spawn_enemy(1)
        run(g.use_ability(enemy))
        self.assertEqual(h.ability_cd, 3)

    def test_ability_used_on_cooldown_does_nothing(self):
        g, io = make_game("4")
        h = make_strong_hero(g)
        enemy = g.spawn_enemy(1)
        h.ability_cd = 2
        hp_before = enemy.hp
        run(g.use_ability(enemy))
        self.assertEqual(enemy.hp, hp_before)
        self.assertEqual(h.ability_cd, 2)


class TestTower(unittest.TestCase):
    def test_enter_tower_clears_and_gives_relic(self):
        g, io = make_game("", "1", "1", "1", "1", "", "")
        make_strong_hero(g)
        run(g.enter_tower(0))
        self.assertIn(0, g.cleared)
        self.assertIn(world.TOWERS[0]["relic"], g.inv)

    def test_cleared_tower_rejected(self):
        g, io = make_game("")
        make_strong_hero(g)
        g.cleared = {0}
        run(g.enter_tower(0))
        self.assertEqual(g.cleared, {0})


class TestRest(unittest.TestCase):
    def test_rest_consumes_supplies(self):
        g, io = make_game("")
        h = make_strong_hero(g)
        h.hp = 1
        g.inv["Припасы"] = 3
        with mock.patch("game.game.random.randint", return_value=50):
            run(g.rest())
        self.assertEqual(g.inv["Припасы"], 2)

    def test_rest_no_supplies(self):
        g, io = make_game("")
        make_strong_hero(g)
        g.inv["Припасы"] = 0
        run(g.rest())
        self.assertEqual(g.inv["Припасы"], 0)


class TestShop(unittest.TestCase):
    def test_buy_item(self):
        g, io = make_game("1", "", "0")
        make_strong_hero(g)
        g.gold = 100
        g.inv["Зелье ХП"] = 2
        run(g.shop())
        self.assertEqual(g.gold, 85)
        self.assertEqual(g.inv["Зелье ХП"], 3)

    def test_buy_upgrade(self):
        g, io = make_game("6", "", "0")
        h = make_strong_hero(g)
        h.attack = (5, 10)
        g.gold = 200
        run(g.shop())
        self.assertEqual(g.gold, 150)
        self.assertEqual(h.attack, (7, 12))
        self.assertEqual(g.upgrades["Клинок"], 1)

    def test_buy_without_gold(self):
        g, io = make_game("1", "", "0")
        make_strong_hero(g)
        g.gold = 0
        run(g.shop())
        self.assertEqual(g.gold, 0)


class TestSaveLoad(unittest.TestCase):
    def tearDown(self):
        if os.path.exists(self.g.save_path):
            os.remove(self.g.save_path)

    def test_roundtrip(self):
        g, io = make_game()
        h = make_strong_hero(g)
        h.name = "Арагорн"
        h.class_name = "Маг"
        g.gold = 77
        g.inv["Заточка"] = 5
        g.cleared = {0, 2}
        g.upgrades["Доспех"] = 2
        g.save()

        g2, io2 = make_game()
        g2.save_path = g.save_path
        self.g = g2
        self.assertTrue(g2.load())
        self.assertEqual(g2.hero.name, "Арагорн")
        self.assertEqual(g2.hero.class_name, "Маг")
        self.assertEqual(g2.gold, 77)
        self.assertEqual(g2.inv["Заточка"], 5)
        self.assertEqual(g2.cleared, {0, 2})
        self.assertEqual(g2.upgrades["Доспех"], 2)
        self.assertEqual(g2.hero.attack, (999, 999))

    def test_load_missing_file(self):
        g, io = make_game()
        self.g = g
        g.save_path = os.path.join(tempfile.gettempdir(), "nonexistent_xyz.json")
        self.assertFalse(g.load())

    def test_default_storage_is_file_storage(self):
        g, io = make_game()
        self.g = g
        self.assertIsInstance(g.storage, FileSaveStorage)
        self.assertEqual(g.storage.path, g.save_path)

    def test_custom_storage_injected(self):
        class FakeStorage(FileSaveStorage):
            def __init__(self):
                self.data = None
                self.saved = 0
                self.loaded = 0

            def save(self, data):
                self.data = data
                self.saved += 1

            def load(self):
                self.loaded += 1
                return self.data

            def exists(self):
                return self.data is not None

        g, io = make_game()
        self.g = g
        g.storage = FakeStorage()
        make_strong_hero(g)
        g.gold = 42
        g.save()
        self.assertEqual(g.storage.saved, 1)
        self.assertEqual(g.storage.data["gold"], 42)

        g2, io2 = make_game()
        self.g = g2
        g2.storage = g.storage
        self.assertTrue(g2.load())
        self.assertEqual(g2.gold, 42)
        self.assertEqual(g2.storage.loaded, 1)

    def test_save_without_hero_does_nothing(self):
        g, io = make_game()
        self.g = g
        g.save()
        with open(g.save_path, encoding="utf-8") as f:
            self.assertEqual(f.read(), "")


class TestVictory(unittest.TestCase):
    def test_victory_raises_exit_on_quit(self):
        g, io = make_game("0")
        make_strong_hero(g)
        g.cleared = set(range(len(world.TOWERS)))
        with self.assertRaises(SystemExit):
            run(g.victory())


class TestElixir(unittest.TestCase):
    def test_elixir_increases_max_hp(self):
        g, io = make_game("1", "")
        h = make_strong_hero(g, hp=100)
        g.inv["Эликсир жизни"] = 1
        run(g.show_character())
        self.assertEqual(h.max_hp, 120)
        self.assertEqual(g.inv["Эликсир жизни"], 0)


if __name__ == "__main__":
    unittest.main()