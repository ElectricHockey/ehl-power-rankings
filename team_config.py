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


def get_team_style(team_name):
    """Return the style dict for a team, falling back to defaults."""
    return TEAM_CONFIG.get(team_name, DEFAULT_TEAM_STYLE)
