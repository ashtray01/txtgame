import json
import os


class SaveStorage:
    """Интерфейс хранилища сохранений.

    Класс должен реализовывать три метода:
      save(data)   — записать словарь данных;
      load()       — вернуть словарь или None, если данных нет;
      exists()     — True, если сохранение существует.

    CLI-версия (FileSaveStorage) пишет в локальный файл,
    браузерная — в localStorage (см. web/browser_main.py).
    """

    def save(self, data):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def exists(self):
        raise NotImplementedError


class FileSaveStorage(SaveStorage):
    def __init__(self, path):
        self.path = path

    def save(self, data):
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)

    def load(self):
        if not self.exists():
            return None
        with open(self.path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def exists(self):
        return os.path.exists(self.path)
