import asyncio
import json
import sys
import time

sys.path.insert(0, "/")

from js import document, localStorage

from game import Game
from game.storage import SaveStorage

SAVE_KEY = "txtgame_save_v1"


class BrowserSaveStorage(SaveStorage):
    """Сохранение игры в localStorage браузера."""

    def __init__(self, key=SAVE_KEY):
        self.key = key
        self.memory = {}

    def save(self, data):
        text = json.dumps(data, ensure_ascii=False)
        try:
            localStorage.setItem(self.key, text)
        except Exception:
            self.memory[self.key] = text
            print("! Сохранение временное: localStorage недоступен, прогресс может потеряться.")

    def load(self):
        try:
            raw = localStorage.getItem(self.key)
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
            return localStorage.getItem(self.key) is not None
        except Exception:
            return self.key in self.memory


def browser_clear():
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def print_flush(*args, **kwargs):
    kwargs.setdefault("flush", True)
    print(*args, **kwargs)


async def browser_input(prompt_text):
    """Асинхронный ввод через HTML-элемент <input> + кнопку.

    input() в PyScript работает только в worker-режиме (который требует
    cross-origin isolation). В основном потоке используем HTML-ввод.
    """
    print(str(prompt_text), end="", flush=True)
    bar = document.getElementById("input-bar")
    inp = document.getElementById("game-input")
    btn = document.getElementById("game-input-btn")
    bar.classList.remove("hidden")
    inp.disabled = False
    btn.disabled = False
    inp.value = ""
    inp.focus()

    loop = asyncio.get_event_loop()
    future = loop.create_future()

    def submit(*_):
        value = str(inp.value)
        inp.disabled = True
        btn.disabled = True
        bar.classList.add("hidden")
        if not future.done():
            future.set_result(value)

    btn.onclick = submit

    def on_key(event):
        if event.key == "Enter":
            submit()

    inp.onkeydown = on_key

    value = await future
    return value


async def main():
    game = Game(
        out=print_flush,
        get_input=browser_input,
        clear_fn=browser_clear,
        sleep=time.sleep,
        storage=BrowserSaveStorage(),
    )
    await game.start()


# Планируем игру в существующем event loop PyScript (top-level await
# несовместим с py_compile, а ensure_future работает в асинхронном контексте).
_TASK = asyncio.ensure_future(main())
