import random


class Character:
    def __init__(self, name, hp, attack, luck=10, level=1):
        self.name = name
        self.level = level
        self.max_hp = hp
        self.hp = self.max_hp
        self.attack = attack
        self.luck = luck
        self.block = False
        # счётчик ходов без крита: гарантирует крит, если удача долго молчит
        self.hits_since_crit = 0

    def hit(self):
        dmg = random.randint(*self.attack)
        # Крит гарантирован на 10-й удар без него (страховка от "вечного невезения")
        if self.hits_since_crit >= 9:
            self.hits_since_crit = 0
            return dmg * 2, True
        crit = random.randint(1, 100) <= self.luck
        if crit:
            self.hits_since_crit = 0
            return dmg * 2, True
        self.hits_since_crit += 1
        return dmg, False

    def take(self, dmg):
        self.hp -= dmg


class Hero(Character):
    def __init__(self, name, class_name):
        from .world import CLASSES

        data = CLASSES[class_name]
        super().__init__(name, data["hp"], data["attack"], luck=data["luck"], level=1)
        self.class_name = class_name
        self.exp = 0
        self.next_exp = 50
        self.atk_bonus = 0
        self.ability_cd = 0

    @property
    def attack_total(self):
        return (self.attack[0] + self.atk_bonus, self.attack[1] + self.atk_bonus)

    def hit(self):
        dmg = random.randint(*self.attack_total)
        if self.hits_since_crit >= 9:
            self.hits_since_crit = 0
            return dmg * 2, True
        crit = random.randint(1, 100) <= self.luck
        if crit:
            self.hits_since_crit = 0
            return dmg * 2, True
        self.hits_since_crit += 1
        return dmg, False

    def gain_exp(self, value):
        self.exp += value
        leveled = False
        while self.exp >= self.next_exp:
            self.exp -= self.next_exp
            self.next_exp = int(self.next_exp * 1.5)
            self.level += 1
            self.max_hp += 10
            self.hp = self.max_hp
            self.attack = (self.attack[0] + 1, self.attack[1] + 2)
            self.luck += 2
            leveled = True
        return leveled

    def reset_battle(self):
        self.block = False
        self.atk_bonus = 0
        # способность снова доступна в начале каждого боя
        self.ability_cd = 0
        self.hits_since_crit = 0