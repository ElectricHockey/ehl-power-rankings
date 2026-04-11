# ============================================================
# TEAM CONFIGURATION
# Maps team names to their brand colors and logo filenames.
# Add new teams here as needed.
# ============================================================

TEAM_CONFIG = {
    "Cape Cod Rangers": {
        "bar_color": (34, 80, 30),       # Dark green
        "text_color": (255, 255, 255),
        "logo": "cape_cod_rangers.png",
    },
    "Sabres on Ice": {
        "bar_color": (135, 180, 210),     # Light blue
        "text_color": (0, 0, 0),
        "logo": "sabres_on_ice.png",
    },
    "Hope Skate Park": {
        "bar_color": (100, 110, 120),     # Slate gray
        "text_color": (255, 255, 255),
        "logo": "hope_skate_park.png",
    },
    "Montrescotia Buffaloes": {
        "bar_color": (100, 40, 130),      # Purple
        "text_color": (255, 255, 255),
        "logo": "montrescotia_buffaloes.png",
    },
    "Canadian Frostbytes": {
        "bar_color": (0, 210, 255),       # Cyan
        "text_color": (0, 0, 0),
        "logo": "canadian_frostbytes.png",
    },
    "Tombstone": {
        "bar_color": (90, 30, 70),        # Dark purple/maroon
        "text_color": (255, 255, 255),
        "logo": "tombstone.png",
    },
    "Steel City Legion": {
        "bar_color": (30, 100, 200),      # Blue
        "text_color": (255, 255, 255),
        "logo": "steel_city_legion.png",
    },
    "Pouch Munchers": {
        "bar_color": (180, 40, 50),       # Crimson red
        "text_color": (255, 255, 255),
        "logo": "pouch_munchers.png",
    },
    "MN Blues": {
        "bar_color": (20, 30, 120),       # Navy blue
        "text_color": (255, 255, 255),
        "logo": "mn_blues.png",
    },
    "Minnesota Wild": {
        "bar_color": (20, 70, 30),        # Dark green
        "text_color": (255, 255, 255),
        "logo": "minnesota_wild.png",
    },
}

# Default style for teams not in the config
DEFAULT_TEAM_STYLE = {
    "bar_color": (80, 80, 80),
    "text_color": (255, 255, 255),
    "logo": None,
}

# Pool of distinct bar colors used for teams not in TEAM_CONFIG.
# Each unknown team gets a unique color from this list (cycling if needed).
_AUTO_COLORS = [
    (180, 60, 30),    # Burnt orange
    (50, 140, 80),    # Forest green
    (160, 30, 120),   # Magenta
    (40, 120, 160),   # Teal
    (200, 160, 30),   # Gold
    (100, 50, 150),   # Violet
    (30, 90, 60),     # Dark teal
    (170, 80, 80),    # Dusty rose
    (60, 60, 140),    # Slate blue
    (130, 100, 40),   # Olive
    (90, 160, 160),   # Aqua
    (140, 40, 70),    # Raspberry
    (70, 110, 50),    # Moss
    (110, 70, 130),   # Lavender
    (180, 120, 60),   # Copper
    (50, 80, 130),    # Steel
    (160, 100, 100),  # Mauve
    (80, 140, 100),   # Sage
    (120, 60, 60),    # Brick
    (60, 100, 120),   # Cadet
]
_auto_color_map = {}


def get_team_style(team_name):
    """Return the style dict for a team, auto-assigning a unique color
    to teams not listed in TEAM_CONFIG."""
    if team_name in TEAM_CONFIG:
        return TEAM_CONFIG[team_name]

    if team_name not in _auto_color_map:
        idx = len(_auto_color_map) % len(_AUTO_COLORS)
        _auto_color_map[team_name] = {
            "bar_color": _AUTO_COLORS[idx],
            "text_color": (255, 255, 255),
            "logo": None,
        }
    return _auto_color_map[team_name]
