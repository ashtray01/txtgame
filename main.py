import random
import time
import os

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


# ================= ПЕРСОНАЖ =================

class Character:
    def __init__(self, name, hp, attack, luck=10, level=1, is_boss=False):
        self.name = name
        self.level = level
        self.max_hp = hp * (2 if is_boss else 1)
        self.hp = self.max_hp
        self.attack = attack
        self.luck = luck
        self.block = False

    def hit(self):
        dmg = random.randint(*self.attack)
        crit = random.randint(1, 100) <= self.luck
        return dmg * 2 if crit else dmg, crit

    def take(self, dmg):
        self.hp -= dmg


# ================= ГЕРОЙ =================

class Hero(Character):
    def __init__(self, name):
        super().__init__(name, 40, (5, 8), 10)
        self.exp = 0
        self.level = 1
        self.next_exp = 50

    def gain_exp(self, value):
        self.exp += value
        if self.exp >= self.next_exp:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.exp = 0
        self.next_exp = int(self.next_exp * 1.5)
        self.max_hp += 10
        self.hp = self.max_hp
        self.attack = (self.attack[0] + 1, self.attack[1] + 2)
        self.luck += 2
        print(f"\n⭐ УРОВЕНЬ ПОВЫШЕН! Теперь {self.level}")
        input("Enter...")


# ================= ДАННЫЕ МИРА =================

TOWERS = [
    {"name": "Заброшенная башня", "diff": 1, "loot": ["Зелье ХП"]},
    {"name": "Костяная крепость", "diff": 2, "loot": ["Зелье ХП", "Заточка"]},
    {"name": "Кровавая цитадель", "diff": 3, "loot": ["Свиток силы"]},
    {"name": "Адская спираль", "diff": 4, "loot": ["Эликсир жизни"]},
    {"name": "Башня Пустоты", "diff": 5, "loot": ["Реликвия"]}
]

MOBS = {
    1: ["Скелет", "Гнилец"],
    2: ["Орк", "Берсерк"],
    3: ["Демон", "Инквизитор"],
    4: ["Палач", "Архидемон"],
    5: ["Аватар Пустоты"]
}


# ================= ИГРА =================

class Game:
    def __init__(self):
        self.hero = None
        self.inv = {"Зелье ХП": 2}
        self.log = []

    # ---------- КАРТА ----------

    def map_menu(self):
        clear()
        print("🗺 КАРТА МИРА\n")
        for i, t in enumerate(TOWERS, 1):
            print(f"{i}. {t['name']} (сложность {t['diff']})")
        print("\n6. Отдых")
        print("7. Инвентарь")
        print("0. Выход")

        return input("\n>>> ")

    # ---------- ОТДЫХ ----------

    def rest(self):
        clear()
        print("Вы разбили лагерь...")
        time.sleep(1)

        roll = random.randint(1, 100)
        if roll <= 60:
            self.hero.hp = min(self.hero.max_hp, self.hero.hp + 20)
            print("Вы восстановили силы (+20 HP)")
        elif roll <= 85:
            found = random.choice(["Зелье ХП", "Заточка"])
            self.inv[found] = self.inv.get(found, 0) + 1
            print(f"Вы нашли {found}")
        else:
            print("ЗАСАДА!")
            self.battle(self.spawn_enemy(2))

        input("Enter...")

    # ---------- БОЙ ----------

    def spawn_enemy(self, diff):
        name = random.choice(MOBS[diff])
        hp = 20 + diff * 10 + self.hero.level * 3
        atk = (diff * 3, diff * 5)
        return Character(name, hp, atk, luck=5 + diff * 2)

    def battle(self, enemy):
        self.log = [f"⚔ Битва с {enemy.name}"]

        while self.hero.hp > 0 and enemy.hp > 0:
            clear()
            print(f"{self.hero.name} HP {self.hero.hp}/{self.hero.max_hp} | LVL {self.hero.level}")
            print(f"{enemy.name} HP {enemy.hp}/{enemy.max_hp}")
            print("-" * 40)
            for l in self.log[-8:]:
                print(l)
            print("\n1.Атака 2.Блок 3.Зелье")

            cmd = input(">>> ")

            self.hero.block = False
            if cmd == "1":
                dmg, crit = self.hero.hit()
                enemy.take(dmg)
                self.log.append(f"Вы ударили на {dmg}{' КРИТ' if crit else ''}")

            elif cmd == "2":
                self.hero.block = True
                self.log.append("Вы в защите")

            elif cmd == "3" and self.inv.get("Зелье ХП", 0) > 0:
                self.hero.hp = min(self.hero.max_hp, self.hero.hp + 30)
                self.inv["Зелье ХП"] -= 1
                self.log.append("Вы выпили зелье")

            if enemy.hp <= 0:
                break

            dmg, _ = enemy.hit()
            if self.hero.block:
                dmg //= 2
            self.hero.hp -= dmg
            self.log.append(f"{enemy.name} ударил на {dmg}")

        if self.hero.hp <= 0:
            print("💀 Вы погибли")
            exit()

        exp = 20 + enemy.level * 10
        self.hero.gain_exp(exp)
        self.drop_loot()

    # ---------- ЛУТ ----------

    def drop_loot(self):
        if random.randint(1, 100) <= 60:
            item = random.choice(["Зелье ХП", "Заточка"])
            self.inv[item] = self.inv.get(item, 0) + 1
            print(f"Найдено: {item}")
            time.sleep(1)

    # ---------- БАШНЯ ----------

    def enter_tower(self, tower):
        floors = tower["diff"] + 2
        for f in range(1, floors + 1):
            enemy = self.spawn_enemy(tower["diff"])
            self.battle(enemy)

        reward = random.choice(tower["loot"])
        self.inv[reward] = self.inv.get(reward, 0) + 1
        print(f"\n🏆 Башня зачищена! Получено: {reward}")
        input("Enter...")

    # ---------- СТАРТ ----------

    def start(self):
        name = input("Имя героя: ") or "Странник"
        self.hero = Hero(name)

        while True:
            cmd = self.map_menu()
            if cmd == "0":
                break
            elif cmd == "6":
                self.rest()
            elif cmd == "7":
                clear()
                print(self.inv)
                input("Enter...")
            else:
                idx = int(cmd) - 1
                if 0 <= idx < 5:
                    self.enter_tower(TOWERS[idx])


# ================= ЗАПУСК =================

if __name__ == "__main__":
    Game().start()
