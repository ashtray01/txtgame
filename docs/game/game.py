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

    # (остальные методы опущены в этой минимальной копии)
