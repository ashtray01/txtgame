import pathlib
import re
import unittest

SRC = pathlib.Path(__file__).resolve().parents[1]
BROWSER_IMPORTS = (
    r"\bimport\s+js\b",
    r"\bimport\s+pyscript\b",
    r"\bimport\s+polyscript\b",
    r"\bimport\s+micropip\b",
    r"\bimport\s+pyodide\b",
    r"\bfrom\s+js\b",
)


class TestCliHasNoBrowserImports(unittest.TestCase):
    def assert_no_browser_imports(self, text, label):
        for pattern in BROWSER_IMPORTS:
            self.assertIsNone(re.search(pattern, text), f"{label}: найден {pattern}")

    def test_game_sources_have_no_browser_imports(self):
        for py in sorted((SRC / "game").glob("*.py")):
            self.assert_no_browser_imports(py.read_text(encoding="utf-8"), py.name)

    def test_main_has_no_browser_imports(self):
        self.assert_no_browser_imports((SRC / "main.py").read_text(encoding="utf-8"), "main.py")


if __name__ == "__main__":
    unittest.main()
