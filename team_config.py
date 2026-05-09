# ============================================================
# TEAM CONFIGURATION
# Maps team names to their brand colors and logo filenames.
# Add new teams here as needed.
# ============================================================

import os
import re


def hex_to_rgb(hex_str):
    """Convert a hex color string like '#FF0000' or 'FF0000' to an (R, G, B) tuple.
    Returns None if the string is not a valid hex color."""
    if not hex_str:
        return None
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) != 6:
        return None
    try:
        return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
    except ValueError:
        return None

TEAM_CONFIG = {
    # ── Teams with logos ──────────────────────────────────────────────────────
    "1K Huskies": {
        "bar_color": (180, 30, 30),       # Red
        "text_color": (255, 255, 255),
        "logo": "1k_huskies.png",
    },
    "Blood Sweat N Beers": {
        "bar_color": (120, 20, 20),       # Dark red
        "text_color": (255, 255, 255),
        "logo": "blood_sweat_n_beers.png",
    },
    "Canadian Frostbytes": {
        "bar_color": (0, 210, 255),       # Cyan
        "text_color": (0, 0, 0),
        "logo": "canadian_frostbytes.png",
    },
    "Cape Cod Rangers": {
        "bar_color": (34, 80, 30),        # Dark green
        "text_color": (255, 255, 255),
        "logo": "cape_cod_rangers.png",
    },
    "Chemistry Bros": {
        "bar_color": (40, 130, 60),       # Green
        "text_color": (255, 255, 255),
        "logo": "chemistry_bros.png",
    },
    "Cooper Gang HC": {
        "bar_color": (30, 50, 160),       # Dark blue
        "text_color": (255, 255, 255),
        "logo": "cooper_gang_hc.png",
    },
    "Greensboro Hurricanes": {
        "bar_color": (0, 140, 120),       # Teal
        "text_color": (255, 255, 255),
        "logo": "greensboro_hurricanes.png",
    },
    "High Quality Plague": {
        "bar_color": (60, 20, 90),        # Dark purple
        "text_color": (255, 255, 255),
        "logo": "high_quality_plague.png",
    },
    "Hope Skate Park": {
        "bar_color": (100, 110, 120),     # Slate gray
        "text_color": (255, 255, 255),
        "logo": "hope_skate_park.png",
    },
    "II AURA II": {
        "bar_color": (100, 30, 140),      # Purple
        "text_color": (220, 180, 0),      # Gold text
        "logo": "ii_aura_ii.png",
    },
    "Kala Singhs": {
        "bar_color": (20, 40, 120),       # Dark blue
        "text_color": (255, 200, 0),      # Gold text
        "logo": "kala_singhs.png",
    },
    "Kitty Slayers": {
        "bar_color": (50, 50, 50),        # Dark gray
        "text_color": (255, 255, 255),
        "logo": "kitty_slayers.png",
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
    "Montrescotia Buffaloes": {
        "bar_color": (100, 40, 130),      # Purple
        "text_color": (255, 255, 255),
        "logo": "montrescotia_buffaloes.png",
    },
    "North Dakota": {
        "bar_color": (0, 40, 100),        # Dark navy (UND colors)
        "text_color": (255, 255, 255),
        "logo": "north_dakota.png",
    },
    "Oak Gable Goons": {
        "bar_color": (60, 90, 40),        # Forest green
        "text_color": (255, 255, 255),
        "logo": "oak_gable_goons.png",
    },
    "Pioneers": {
        "bar_color": (30, 60, 140),       # Blue
        "text_color": (220, 180, 0),      # Gold text
        "logo": "pioneers.png",
    },
    "Pouch Munchers": {
        "bar_color": (180, 40, 50),       # Crimson red
        "text_color": (255, 255, 255),
        "logo": "pouch_munchers.png",
    },
    "Puckin Around": {
        "bar_color": (200, 100, 20),      # Orange
        "text_color": (255, 255, 255),
        "logo": "puckin_around.png",
    },
    "Reverse HC": {
        "bar_color": (20, 20, 20),        # Black
        "text_color": (255, 255, 255),
        "logo": "reverse_hc.png",
    },
    "Royal Deltz": {
        "bar_color": (80, 20, 140),       # Royal purple
        "text_color": (220, 180, 0),      # Gold text
        "logo": "royal_deltz.png",
    },
    "Sabres on Ice": {
        "bar_color": (135, 180, 210),     # Light blue
        "text_color": (0, 0, 0),
        "logo": "sabres_on_ice.png",
    },
    "Steel City Legion": {
        "bar_color": (30, 100, 200),      # Blue
        "text_color": (255, 255, 255),
        "logo": "steel_city_legion.png",
    },
    "Stratton Oakmont": {
        "bar_color": (10, 30, 80),        # Navy blue
        "text_color": (220, 180, 0),      # Gold text
        "logo": "stratton_oakmont.png",
    },
    "Tombstone": {
        "bar_color": (90, 30, 70),        # Dark purple/maroon
        "text_color": (255, 255, 255),
        "logo": "tombstone.png",
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


# Build a case-insensitive lookup for TEAM_CONFIG
_TEAM_CONFIG_LOWER = {k.lower(): k for k in TEAM_CONFIG}


def _slugify(name):
    """Convert a name to a lowercase slug: 'Cape Cod Rangers' → 'cape_cod_rangers'."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _auto_detect_logo(team_name, logo_dir):
    """Try to find a logo file matching the team name by converting to
    a filename pattern: 'Cape Cod Rangers' → 'cape_cod_rangers.png'.
    Also handles special characters like '&' by trying multiple slug forms
    and scanning the logo directory for case-insensitive matches."""
    if not logo_dir:
        return None

    # Primary slug: strip all non-alphanumeric chars
    slug = _slugify(team_name)
    candidate = slug + ".png"
    path = os.path.join(logo_dir, candidate)
    if os.path.isfile(path):
        return candidate

    # Secondary slug: replace '&' with 'and' before slugifying
    alt_name = team_name.replace("&", "and")
    alt_slug = _slugify(alt_name)
    if alt_slug != slug:
        alt_candidate = alt_slug + ".png"
        if os.path.isfile(os.path.join(logo_dir, alt_candidate)):
            return alt_candidate

    # Directory scan fallback: look for any .png whose slug-form matches
    # This handles filenames like 'blood_sweat_&_beers.png' where the user
    # kept the '&' in the filename.
    try:
        for fname in os.listdir(logo_dir):
            if not fname.lower().endswith(".png"):
                continue
            # Slug the filename (minus extension) and compare to our slug
            base = os.path.splitext(fname)[0]
            file_slug = _slugify(base)
            if file_slug == slug:
                return fname
    except OSError:
        pass

    return None


def get_team_style(team_name, logo_dir=None):
    """Return the style dict for a team, using case-insensitive matching.
    Auto-assigns a unique color to teams not listed in TEAM_CONFIG.
    If logo_dir is provided, attempts auto-detection of logo files."""
    # Exact match first
    if team_name in TEAM_CONFIG:
        style = TEAM_CONFIG[team_name]
        # If logo is set but logo_dir provided, verify the file exists
        if logo_dir and style.get("logo"):
            path = os.path.join(logo_dir, style["logo"])
            if not os.path.isfile(path):
                # Try auto-detect as fallback
                detected = _auto_detect_logo(team_name, logo_dir)
                if detected:
                    style = dict(style)
                    style["logo"] = detected
        return style

    # Case-insensitive match
    lower_name = team_name.lower()
    if lower_name in _TEAM_CONFIG_LOWER:
        canonical = _TEAM_CONFIG_LOWER[lower_name]
        return TEAM_CONFIG[canonical]

    # Unknown team — auto-assign color and try to find logo
    if team_name not in _auto_color_map:
        idx = len(_auto_color_map) % len(_AUTO_COLORS)
        logo = _auto_detect_logo(team_name, logo_dir) if logo_dir else None
        _auto_color_map[team_name] = {
            "bar_color": _AUTO_COLORS[idx],
            "text_color": (255, 255, 255),
            "logo": logo,
        }
    return _auto_color_map[team_name]
