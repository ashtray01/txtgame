import json
import sys
import time

sys.path.insert(0, "/")

from polyscript import xworker

from game import Game
from game.storage import SaveStorage

SAVE_KEY = "txtgame_save_v1"


class BrowserSaveStorage(SaveStorage):
    def __init__(self, key=SAVE_KEY):
        self.key = key
        self.memory = {}

    def save(self, data):
        text = json.dumps(data, ensure_ascii=False)
        try:
            xworker.sync.localStorage.setItem(self.key, text)
        except Exception:
            self.memory[self.key] = text
            print("! Сохранение временное: localStorage недоступен, прогресс может потеряться.")

    def load(self):
        try:
            raw = xworker.sync.localStorage.getItem(self.key)
        except Exception:
            raw = self.memory.get(self.key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return None

    def exists(self):
        try:
            return xworker.sync.localStorage.getItem(self.key) is not None
        except Exception:
            return self.key in self.memory


def browser_clear():
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def print_flush(*args, **kwargs):
    kwargs.setdefault("flush", True)
    print(*args, **kwargs)


Game(out=print_flush, get_input=input, clear_fn=browser_clear,
     sleep=time.sleep, storage=BrowserSaveStorage()).start()
