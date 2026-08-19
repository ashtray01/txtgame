from .ascii_art_pack import ENEMIES, HEROES, RELICS, SCENES_EXTRA

SCENES = {
    "TITLE": """
   _____  __   __   _____    _____    _____    _____   _____
  |_   _| \\ \/ /  / ____|  / ____|  |  __ \\  / ____| / ____|
    | |    \\ V /  | |  __  | |  __  | |__) | | (___  | (___
    | |     > <   | | |_ | | | |_ | |  _  /   \\___ \  \\___ \
   _| |_   / . \\  | |__| | | |__| | | | \\ \\  ____) | ____) |
  |_____| /_/ \\_\\  \\_____|  \\_____| |_|  \\_\\|_____/ |_____/

              << БАШНИ СУДЬБЫ >>
       пять башен. пять реликвий. одна судьба.
""",
}

SCENES.update(SCENES_EXTRA)


def get(name):
    return SCENES.get(name, "")


def get_enemy(name):
    return ENEMIES.get(name, "")


def get_hero(class_name):
    return HEROES.get(class_name, "")


def get_relic(name):
    return RELICS.get(name, "")


def get_extra(name):
    return SCENES_EXTRA.get(name, "")
