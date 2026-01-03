import random
import time
import os

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def health_bar(current, max_hp, length=20):
    filled = int(current / max_hp * length) if max_hp > 0 else 0
    bar = '█' * filled + ' ' * (length - filled)
    return f"[{bar}] {current}/{max_hp}"

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
    def __init__(self, name, class_name):
        if class_name == "Воин":
            hp = 50
            attack = (5, 10)
            luck = 5
        elif class_name == "Маг":
            hp = 30
            attack = (7, 12)
            luck = 10
        elif class_name == "Разбойник":
            hp = 40
            attack = (4, 8)
            luck = 20
        else:
            hp = 40
            attack = (5, 8)
            luck = 10

        super().__init__(name, hp, attack, luck, level=1)
        self.class_name = class_name
        self.exp = 0
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
        self.cleared_towers = set()  # индексы зачищенных башен (0..4)

    # ---------- КАРТА ----------

    def map_menu(self):
        clear()
        print("🗺 КАРТА МИРА\n")
        for i, t in enumerate(TOWERS, 1):
            if (i-1) in self.cleared_towers:
                status = "ЗАЧИЩЕНА"
            else:
                status = f"сложность {t['diff']}"
            print(f"{i}. {t['name']} ({status})")
        print("\n6. Отдых")
        print("7. Инвентарь и персонаж")
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
        level = diff
        return Character(name, hp, atk, luck=5 + diff * 2, level=level)

    def battle(self, enemy):
        self.log = [f"⚔ Битва с {enemy.name}"]

        while self.hero.hp > 0 and enemy.hp > 0:
            clear()
            print(f"{self.hero.name} LVL {self.hero.level} {health_bar(self.hero.hp, self.hero.max_hp)}")
            print(f"{enemy.name} LVL {enemy.level} {health_bar(enemy.hp, enemy.max_hp)}")
            print("-" * 40)
            for l in self.log[-8:]:
                print(l)
            potions = self.inv.get("Зелье ХП", 0)
            print(f"\n1. Атака  2. Блок  3. Зелье ({potions})")

            cmd = input(">>> ")

            self.hero.block = False
            if cmd == "1":
                dmg, crit = self.hero.hit()
                enemy.take(dmg)
                self.log.append(f"Вы ударили на {dmg}{' КРИТ' if crit else ''}")

            elif cmd == "2":
                self.hero.block = True
                self.log.append("Вы в защите")

            elif cmd == "3" and potions > 0:
                self.hero.hp = min(self.hero.max_hp, self.hero.hp + 30)
                self.inv["Зелье ХП"] -= 1
                self.log.append("Вы выпили зелье")

            if enemy.hp <= 0:
                break

            dmg, crit = enemy.hit()
            if self.hero.block:
                dmg //= 2
            self.hero.take(dmg)
            self.log.append(f"{enemy.name} ударил на {dmg}{' КРИТ' if crit else ''}")

        if self.hero.hp <= 0:
            print("💀 Вы погибли")
            input("Enter...")
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

    def enter_tower(self, tower_idx):
        tower = TOWERS[tower_idx]
        
        if tower_idx in self.cleared_towers:
            print(f"\n{ tower['name'] } уже зачищена.")
            input("Enter...")
            return

        floors = tower["diff"] + 2
        print(f"\nВы входите в {tower['name']}... этажей: {floors}\n")
        time.sleep(1.2)

        for f in range(1, floors + 1):
            clear()
            print(f"Этаж {f}/{floors}")
            enemy = self.spawn_enemy(tower["diff"])
            self.battle(enemy)

        reward = random.choice(tower["loot"])
        self.inv[reward] = self.inv.get(reward, 0) + 1
        self.cleared_towers.add(tower_idx)

        print(f"\n🏆 Башня зачищена! Получено: {reward}")
        input("Enter...")

    # ---------- ПЕРСОНАЖ И ИНВЕНТАРЬ ----------

    def show_character(self):
        clear()
        print(f"Персонаж: {self.hero.name} ({self.hero.class_name})")
        print(f"Уровень: {self.hero.level}")
        print(f"HP: {health_bar(self.hero.hp, self.hero.max_hp)}")
        print(f"Атака: {self.hero.attack[0]}-{self.hero.attack[1]}")
        print(f"Удача: {self.hero.luck}%")
        print(f"EXP: {self.hero.exp}/{self.hero.next_exp}")
        print("\nИнвентарь:")
        for item, count in self.inv.items():
            print(f"• {item}: {count}")
        input("\nEnter...")

    # ---------- СТАРТ ----------

    def start(self):
        name = input("Имя героя: ") or "Странник"
        print("\nВыберите класс:")
        print("1. Воин (высокое HP, средняя атака, низкая удача)")
        print("2. Маг (низкое HP, высокая атака, средняя удача)")
        print("3. Разбойник (среднее HP, средняя атака, высокая удача)")
        cmd = input(">>> ")
        if cmd == "1":
            class_name = "Воин"
        elif cmd == "2":
            class_name = "Маг"
        elif cmd == "3":
            class_name = "Разбойник"
        else:
            class_name = "Воин"
        self.hero = Hero(name, class_name)

        while True:
            cmd = self.map_menu()
            if cmd == "0":
                break
            elif cmd == "6":
                self.rest()
            elif cmd == "7":
                self.show_character()
            else:
                try:
                    idx = int(cmd) - 1
                    if 0 <= idx < len(TOWERS):
                        self.enter_tower(idx)
                except ValueError:
                    pass


# ================= ЗАПУСК =================

if __name__ == "__main__":
    Game().start()