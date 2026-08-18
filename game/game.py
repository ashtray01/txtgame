import json
import os
import random
import time

from . import art
from .characters import Character, Hero
from .storage import FileSaveStorage
from .world import (
    CLASSES,
    ELIXIR_HP,
    LOOT,
    MOBS,
    POTION_HEAL,
    SHOP,
    TOWERS,
    UPGRADES,
)


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def health_bar(current, max_hp, length=20):
    filled = int(current / max_hp * length) if max_hp > 0 else 0
    bar = '█' * filled + ' ' * (length - filled)
    return f"[{bar}] {current}/{max_hp}"


class Game:
    def __init__(self, out=print, get_input=input, clear_fn=clear, sleep=time.sleep,
                 storage=None):
        """storage: объект с методами save/load/exists (см. game.storage)."""
        self.out = out
        self.get_input = get_input
        self.clear_fn = clear_fn
        self.sleep = sleep
        self.hero = None
        self.inv = {"Зелье ХП": 2, "Припасы": 3}
        self.gold = 0
        self.cleared = set()
        self.upgrades = {"Клинок": 0, "Доспех": 0, "Талисман": 0}
        self.log = []
        self.save_path = "savegame.json"
        self._storage = storage

    @property
    def storage(self):
        if self._storage is None:
            self._storage = FileSaveStorage(self.save_path)
        return self._storage

    @storage.setter
    def storage(self, value):
        self._storage = value

    # ---------- вывод ----------

    def say(self, text=""):
        self.out(text)

    async def ask(self, prompt=">>> "):
        result = self.get_input(prompt)
        if hasattr(result, "__await__"):
            result = await result
        return str(result).strip()

    def scene(self, name, header=""):
        self.clear_fn()
        self.say(art.get(name))
        if header:
            self.say(header)

    def scene_art(self, text, header=""):
        self.clear_fn()
        self.say(text)
        if header:
            self.say(header)

    def wait(self, sec=0.6):
        self.sleep(sec)

    # ---------- враги ----------

    def spawn_enemy(self, diff, is_boss=False, boss_name=None):
        level = self.hero.level if self.hero else 1
        if is_boss:
            name = boss_name or "Владыка"
            hp = 30 + diff * 12 + level * 4
            atk = (diff * 3 + level // 2, diff * 4 + level // 2)
            luck = 5 + diff * 2
        else:
            name = random.choice(MOBS[diff])
            hp = 15 + diff * 8 + level * 3
            atk = (diff * 2 + level // 2, diff * 3 + level // 2)
            luck = 3 + diff * 2
        return Character(name, hp, atk, luck, level=diff)

    # ---------- бой ----------

    async def battle(self, enemy, is_boss=False):
        self.hero.reset_battle()
        self.log = [f"⚔ Битва с {enemy.name}" + (" (БОСС)" if is_boss else "")]
        self.save()

        while self.hero.hp > 0 and enemy.hp > 0:
            self.scene_art(art.get_enemy(enemy.name) or art.get("BATTLE_BOSS" if is_boss else "BATTLE"))
            self.say(f"{self.hero.name} LVL {self.hero.level} {health_bar(self.hero.hp, self.hero.max_hp)}")
            self.say(f"{enemy.name} LVL {enemy.level} {health_bar(enemy.hp, enemy.max_hp)}")
            self.say("-" * 42)
            for line in self.log[-8:]:
                self.say(line)
            potions = self.inv.get("Зелье ХП", 0)
            sharp = self.inv.get("Заточка", 0)
            scroll = self.inv.get("Свиток силы", 0)
            ab = CLASSES[self.hero.class_name]
            ab_status = f"{self.hero.ability_cd} хода" if self.hero.ability_cd > 0 else "готово"
            self.say("")
            self.say(f"1. Атака  2. Блок  3. Зелье ({potions})")
            self.say(f"4. {ab['ability']} ({ab_status})  5. Предмет (Зат {sharp}/Свит {scroll})")

            cmd = await self.ask(">>> ")
            self.hero.block = False
            acted = True

            if cmd == "1":
                dmg, crit = self.hero.hit()
                enemy.take(dmg)
                self.log.append(f"Вы ударили на {dmg}{' КРИТ' if crit else ''}")
            elif cmd == "2":
                self.hero.block = True
                self.log.append("Вы в защите (-70% урона)")
            elif cmd == "3" and potions > 0:
                self.hero.hp = min(self.hero.max_hp, self.hero.hp + POTION_HEAL)
                self.inv["Зелье ХП"] -= 1
                self.log.append(f"Вы выпили зелье (+{POTION_HEAL} HP)")
            elif cmd == "4":
                await self.use_ability(enemy)
            elif cmd == "5":
                await self.battle_item(enemy)
            else:
                acted = False
                self.log.append("Вы замешкались...")

            if enemy.hp <= 0:
                break

            dmg, crit = enemy.hit()
            if self.hero.block:
                dmg = int(dmg * 0.3)
            self.hero.take(dmg)
            self.log.append(f"{enemy.name} ударил на {dmg}{' КРИТ' if crit else ''}")

            if acted and self.hero.ability_cd > 0:
                self.hero.ability_cd -= 1

        if self.hero.hp <= 0:
            return await self.defeat()

        exp = (10 + enemy.level * 8) if not is_boss else (25 + enemy.level * 15)
        gold = (4 + enemy.level * 4) if not is_boss else (15 + enemy.level * 10)
        self.gold += gold
        self.say(f"✨ Победа! +{exp} EXP, +{gold} золота")
        self.wait()
        self.drop_loot(enemy, is_boss)
        leveled = self.hero.gain_exp(exp)
        if leveled:
            self.scene("LEVEL_UP")
            self.say(f"⭐ УРОВЕНЬ ПОВЫШЕН! Теперь {self.hero.level}")
            await self.ask("Enter...")
        self.save()
        return True

    async def use_ability(self, enemy):
        cls = self.hero.class_name
        if self.hero.ability_cd > 0:
            self.log.append("Способность ещё не готова!")
            return
        if cls == "Воин":
            dmg, crit = self.hero.hit()
            dmg = int(dmg * 1.5)
            enemy.take(dmg)
            self.log.append(f"ЯРОСТНЫЙ УДАР на {dmg}{' КРИТ' if crit else ''}")
        elif cls == "Маг":
            dmg = 12 + self.hero.level * 2
            enemy.take(dmg)
            self.log.append(f"ОГНЕННЫЙ ШАР на {dmg}")
        elif cls == "Разбойник":
            dmg = random.randint(*self.hero.attack_total) * 2
            enemy.take(dmg)
            self.log.append(f"УДАР В СПИНУ на {dmg} (КРИТ)")
        self.hero.ability_cd = 3

    async def battle_item(self, enemy):
        sharp = self.inv.get("Заточка", 0)
        scroll = self.inv.get("Свиток силы", 0)
        self.say(f"Предметы: 1. Заточка ({sharp}) +4 ATK  2. Свиток силы ({scroll}) 25 урона  0. Назад")
        cmd = await self.ask(">>> ")
        if cmd == "1" and sharp > 0:
            self.inv["Заточка"] -= 1
            self.hero.atk_bonus += 4
            self.log.append("Клинок заточен! +4 к атаке")
        elif cmd == "2" and scroll > 0:
            self.inv["Свиток силы"] -= 1
            enemy.take(25)
            self.log.append("Свиток силы вспыхнул на 25 урона!")
        else:
            self.log.append("Вы убрали предмет обратно")

    def drop_loot(self, enemy, is_boss=False):
        if not is_boss and random.randint(1, 100) > 60:
            return
        item = random.choice(LOOT)
        self.inv[item] = self.inv.get(item, 0) + 1
        self.say(f"Найдено: {item}")
        self.wait(1.0)

    # ---------- поражение ----------

    async def defeat(self):
        self.scene_art(art.get_extra("DEATH"), "💀 Вы погибли...")
        if self.storage.exists():
            ans = await self.ask("Восстановиться из последнего сохранения? (1 да / 0 выйти) ")
            if ans == "1" and self.load():
                self.say("Сохранение загружено, путь продолжается.")
                await self.ask("Enter...")
                return False
        self.say("Игра окончена. Приходите снова!")
        raise SystemExit

    # ---------- башня ----------

    async def enter_tower(self, idx):
        tower = TOWERS[idx]
        if idx in self.cleared:
            self.scene("MAP")
            self.say(f"{tower['name']} уже зачищена.")
            await self.ask("Enter...")
            return
        self.scene(f"TOWER_{idx + 1}", f"🏰 {tower['name']}  —  сложность {tower['diff']}")
        floors = tower["diff"] + 2
        self.say(f"Этажей: {floors}. Впереди чудовища и босс — {tower['boss']}.")
        await self.ask("Войти? (Enter)")
        for f in range(1, floors + 1):
            self.scene("TOWER_INNER")
            self.say(f"Этаж {f}/{floors}")
            is_boss = f == floors
            if is_boss:
                enemy = self.spawn_enemy(tower["diff"], is_boss=True, boss_name=tower["boss"])
            else:
                enemy = self.spawn_enemy(tower["diff"])
            if not await self.battle(enemy, is_boss):
                return
        self.inv[tower["relic"]] = self.inv.get(tower["relic"], 0) + 1
        self.cleared.add(idx)
        self.save()
        self.scene_art(art.get_relic(tower["relic"]) or art.get("REWARD"))
        self.say(f"🏆 Башня зачищена! Получена реликвия: {tower['relic']}")
        await self.ask("Enter...")
        if len(self.cleared) == len(TOWERS):
            await self.victory()

    async def victory(self):
        self.scene_art(art.get_extra("VICTORY") or art.get("VICTORY"), "👑 ВЫ СОБРАЛИ ВСЕ ПЯТЬ РЕЛИКВИЙ!")
        self.say("Древнее зло повержено. Мир спасён. Слава герою!")
        ans = await self.ask("1. Новая игра  0. Выход: ")
        if ans == "1":
            await self.new_game()
        else:
            raise SystemExit

    # ---------- отдых ----------

    async def rest(self):
        self.scene_art(art.get_extra("CAMP"))
        supplies = self.inv.get("Припасы", 0)
        if supplies <= 0:
            self.say("Нет припасов, чтобы разбить лагерь.")
            self.say("Купите их в лавке или найдите в бою.")
            await self.ask("Enter...")
            return
        self.inv["Припасы"] -= 1
        self.say("Вы разбили лагерь и разожгли костёр...")
        self.wait(1.2)
        roll = random.randint(1, 100)
        if roll <= 55:
            heal = min(self.hero.max_hp - self.hero.hp, 25)
            self.hero.hp += heal
            self.say(f"Вы отдохнули и восстановили силы (+{heal} HP)")
        elif roll <= 85:
            found = random.choice(["Зелье ХП", "Заточка", "Припасы"])
            self.inv[found] = self.inv.get(found, 0) + 1
            self.say(f"Среди вещей вы нашли: {found}")
        else:
            self.say("ЗАСАДА! Из темноты выходят враги!")
            self.wait()
            await self.battle(self.spawn_enemy(2))
        await self.ask("Enter...")

    # ---------- магазин ----------

    async def shop(self):
        while True:
            self.scene_art(art.get_extra("SHOPKEEPER"), "🏪 Лавка странствующего торговца")
            self.say(f"Золото: {self.gold}")
            self.say("")
            self.say("Товары:")
            for i, (item, cost) in enumerate(SHOP, 1):
                self.say(f"{i}. {item} — {cost} зол.")
            self.say("")
            self.say("Улучшения:")
            for i, name in enumerate(UPGRADES, len(SHOP) + 1):
                data = UPGRADES[name]
                cost = int(data["cost"] * data["mult"] ** self.upgrades[name])
                self.say(f"{i}. {name} ({data['effect']}) — {cost} зол. [ур. {self.upgrades[name]}]")
            self.say("")
            self.say("0. Выйти из лавки")
            cmd = await self.ask(">>> ")
            if cmd == "0":
                self.save()
                return
            try:
                n = int(cmd)
            except ValueError:
                continue
            if 1 <= n <= len(SHOP):
                item, cost = SHOP[n - 1]
                self.buy(item, cost)
            elif len(SHOP) + 1 <= n <= len(SHOP) + len(UPGRADES):
                name = list(UPGRADES)[n - len(SHOP) - 1]
                self.buy_upgrade(name)
            await self.ask("Enter...")

    def buy(self, item, cost):
        if self.gold < cost:
            self.say("Недостаточно золота!")
            return
        self.gold -= cost
        self.inv[item] = self.inv.get(item, 0) + 1
        self.say(f"Куплено: {item}")

    def buy_upgrade(self, name):
        data = UPGRADES[name]
        cost = int(data["cost"] * data["mult"] ** self.upgrades[name])
        if self.gold < cost:
            self.say("Недостаточно золота!")
            return
        self.gold -= cost
        self.upgrades[name] += 1
        if name == "Клинок":
            self.hero.attack = (self.hero.attack[0] + 2, self.hero.attack[1] + 2)
        elif name == "Доспех":
            self.hero.max_hp += 15
            self.hero.hp += 15
        elif name == "Талисман":
            self.hero.luck += 3
        self.say(f"Улучшено: {name} {data['effect']}")

    # ---------- персонаж ----------

    async def show_character(self):
        while True:
            self.scene_art(art.get_hero(self.hero.class_name) or art.get("CHARACTER"))
            h = self.hero
            self.say(f"{h.name} — {h.class_name}")
            self.say(f"Уровень: {h.level}   EXP: {h.exp}/{h.next_exp}")
            self.say(f"HP: {health_bar(h.hp, h.max_hp)}")
            self.say(f"Атака: {h.attack_total[0]}-{h.attack_total[1]}")
            self.say(f"Удача: {h.luck}%")
            self.say(f"Золото: {self.gold}")
            self.say(f"Зачищено башен: {len(self.cleared)}/{len(TOWERS)}")
            self.say("")
            self.say("Инвентарь:")
            for item, count in sorted(self.inv.items()):
                self.say(f"• {item}: {count}")
            self.say("")
            self.say("1. Использовать Эликсир жизни  0. Назад")
            cmd = await self.ask(">>> ")
            if cmd == "0":
                return
            if cmd == "1" and self.inv.get("Эликсир жизни", 0) > 0:
                self.inv["Эликсир жизни"] -= 1
                h.max_hp += ELIXIR_HP
                h.hp = min(h.max_hp, h.hp + ELIXIR_HP)
                self.say(f"Эликсир наполняет силой! +{ELIXIR_HP} к макс. HP")
                await self.ask("Enter...")

    # ---------- карта ----------

    async def map_menu(self):
        self.scene("MAP", "🗺 КАРТА МИРА")
        for i, t in enumerate(TOWERS, 1):
            if (i - 1) in self.cleared:
                status = "ЗАЧИЩЕНА"
            else:
                status = f"сложность {t['diff']}"
            self.say(f"{i}. {t['name']} ({status})")
        self.say("")
        supplies = self.inv.get("Припасы", 0)
        self.say(f"6. Отдых (припасы: {supplies})")
        self.say("7. Персонаж и инвентарь")
        self.say("8. Лавка торговца")
        self.say("0. Выход")
        return await self.ask(">>> ")

    # ---------- старт ----------

    async def new_game(self):
        name = (await self.ask("Имя героя: ")) or "Странник"
        self.scene("MAP")
        self.say("Выберите класс:")
        for i, c in enumerate(CLASSES, 1):
            data = CLASSES[c]
            self.say(f"{i}. {c} — {data['desc']} | {data['ability']}: {data['ability_desc']}")
        cmd = await self.ask(">>> ")
        names = list(CLASSES)
        try:
            class_name = names[int(cmd) - 1]
        except (ValueError, IndexError):
            class_name = "Воин"
        self.hero = Hero(name, class_name)
        self.inv = {"Зелье ХП": 2, "Припасы": 3}
        self.gold = 0
        self.cleared = set()
        self.upgrades = {"Клинок": 0, "Доспех": 0, "Талисман": 0}
        self.save()

    def save(self):
        if not self.hero:
            return
        data = {
            "name": self.hero.name,
            "class_name": self.hero.class_name,
            "level": self.hero.level,
            "exp": self.hero.exp,
            "next_exp": self.hero.next_exp,
            "hp": self.hero.hp,
            "max_hp": self.hero.max_hp,
            "attack": self.hero.attack,
            "luck": self.hero.luck,
            "inv": self.inv,
            "gold": self.gold,
            "cleared": sorted(self.cleared),
            "upgrades": self.upgrades,
        }
        self.storage.save(data)

    def load(self):
        if not self.storage.exists():
            return False
        try:
            data = self.storage.load()
            self.hero = Hero(data["name"], data["class_name"])
            self.hero.level = data["level"]
            self.hero.exp = data["exp"]
            self.hero.next_exp = data["next_exp"]
            self.hero.hp = data["hp"]
            self.hero.max_hp = data["max_hp"]
            self.hero.attack = tuple(data["attack"])
            self.hero.luck = data["luck"]
            self.inv = data["inv"]
            self.gold = data["gold"]
            self.cleared = set(data["cleared"])
            self.upgrades = data["upgrades"]
            return True
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            return False

    async def start(self):
        if self.storage.exists():
            self.scene("TITLE", "🏰 БАШНИ СУДЬБЫ")
            self.say("Найдено сохранение.")
            ans = await self.ask("1. Продолжить  2. Новая игра  0. Выход: ")
            if ans == "0":
                return
            if ans == "1" and self.load():
                self.say("Загружено!")
                await self.ask("Enter...")
            else:
                await self.new_game()
        else:
            self.scene("TITLE", "🏰 БАШНИ СУДЬБЫ")
            await self.ask("Нажмите Enter, чтобы начать...")
            await self.new_game()

        while True:
            cmd = await self.map_menu()
            if cmd == "0":
                self.save()
                self.say("До встречи, странник!")
                break
            elif cmd == "6":
                await self.rest()
            elif cmd == "7":
                await self.show_character()
            elif cmd == "8":
                await self.shop()
            else:
                try:
                    idx = int(cmd) - 1
                    if 0 <= idx < len(TOWERS):
                        await self.enter_tower(idx)
                except ValueError:
                    pass