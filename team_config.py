# ============================================================
# TEAM CONFIGURATION
# Maps team names to their brand colors and logo filenames.
# Add new teams here as needed.
# ============================================================

import os
import re
from PIL import Image

# Logo palette extraction tuning constants
LOGO_SAMPLE_SIZE = 48
ALPHA_VISIBILITY_THRESHOLD = 40
LOGO_PALETTE_SIZE = 6
MIN_COLOR_DISTANCE = 50
DARK_COLOR_BLEND_RATIO = 0.30
LIGHT_COLOR_BLEND_RATIO = 0.25


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
_logo_style_cache = {}


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


def _clamp_channel(val):
    return max(0, min(255, int(round(val))))


def _mix_rgb(c1, c2, t):
    """Linear blend c1 -> c2 by t in [0,1]."""
    return (
        _clamp_channel(c1[0] + (c2[0] - c1[0]) * t),
        _clamp_channel(c1[1] + (c2[1] - c1[1]) * t),
        _clamp_channel(c1[2] + (c2[2] - c1[2]) * t),
    )


def _color_distance(c1, c2):
    return (
        (c1[0] - c2[0]) ** 2 +
        (c1[1] - c2[1]) ** 2 +
        (c1[2] - c2[2]) ** 2
    ) ** 0.5


def _relative_luminance(rgb):
    """Approximate luminance for contrast checks."""
    r, g, b = rgb
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def _contrast_text_color(bg_rgb):
    """Return black or white based on background luminance."""
    return (0, 0, 0) if _relative_luminance(bg_rgb) >= 0.6 else (255, 255, 255)


def _extract_logo_gradient_style(logo_path):
    """Extract primary/secondary colors from a logo for bar gradient styling."""
    cached = _logo_style_cache.get(logo_path)
    if cached is not None:
        return cached

    try:
        img = Image.open(logo_path).convert("RGBA")
        img.thumbnail((LOGO_SAMPLE_SIZE, LOGO_SAMPLE_SIZE), Image.Resampling.LANCZOS)

        # Keep only visible-ish pixels to avoid transparent padding bias.
        visible = []
        for r, g, b, a in img.getdata():
            if a >= ALPHA_VISIBILITY_THRESHOLD:
                visible.append((r, g, b))

        if not visible:
            _logo_style_cache[logo_path] = None
            return None

        # Reduce to representative palette; keeps dominant logo colors.
        palette_img = Image.new("RGB", (len(visible), 1))
        palette_img.putdata(visible)
        pal = palette_img.quantize(colors=LOGO_PALETTE_SIZE, method=Image.Quantize.MEDIANCUT)
        rgb_pal = pal.convert("RGB")
        counts = rgb_pal.getcolors(maxcolors=256) or []
        if not counts:
            _logo_style_cache[logo_path] = None
            return None
        counts.sort(key=lambda x: x[0], reverse=True)
        colors = [c for _n, c in counts]

        primary = colors[0]
        secondary = None
        for c in colors[1:]:
            if _color_distance(primary, c) >= MIN_COLOR_DISTANCE:
                secondary = c
                break
        if secondary is None:
            # Create a subtle two-tone gradient if logo is mostly one color.
            lum = _relative_luminance(primary)
            if lum < 0.5:
                secondary = _mix_rgb(primary, (255, 255, 255), DARK_COLOR_BLEND_RATIO)
            else:
                secondary = _mix_rgb(primary, (0, 0, 0), LIGHT_COLOR_BLEND_RATIO)

        mid = _mix_rgb(primary, secondary, 0.5)
        style = {
            "bar_color": primary,
            "bar_gradient": (primary, secondary),
            "text_color": _contrast_text_color(mid),
        }
        _logo_style_cache[logo_path] = style
        return style
    except Exception:
        _logo_style_cache[logo_path] = None
        return None


def _apply_logo_colors(team_name, style, logo_dir):
    """Attach detected logo + logo-derived colors when available."""
    out = dict(style)

    logo_file = out.get("logo")
    if logo_dir and (not logo_file):
        logo_file = _auto_detect_logo(team_name, logo_dir)
    if logo_file:
        out["logo"] = logo_file
    if not logo_dir or not logo_file:
        return out

    logo_path = os.path.join(logo_dir, logo_file)
    if not os.path.isfile(logo_path):
        return out

    derived = _extract_logo_gradient_style(logo_path)
    if not derived:
        return out
    out.update(derived)
    return out


def get_team_style(team_name, logo_dir=None):
    """Return the style dict for a team, using case-insensitive matching.
    Auto-assigns a unique color to teams not listed in TEAM_CONFIG.
    If logo_dir is provided, attempts auto-detection of logo files."""
    # Exact match first
    if team_name in TEAM_CONFIG:
        return _apply_logo_colors(team_name, TEAM_CONFIG[team_name], logo_dir)

    # Case-insensitive match
    lower_name = team_name.lower()
    if lower_name in _TEAM_CONFIG_LOWER:
        canonical = _TEAM_CONFIG_LOWER[lower_name]
        return _apply_logo_colors(team_name, TEAM_CONFIG[canonical], logo_dir)

    # Unknown team — auto-assign color and try to find logo
    if team_name not in _auto_color_map:
        idx = len(_auto_color_map) % len(_AUTO_COLORS)
        base_style = {
            "bar_color": _AUTO_COLORS[idx],
            "text_color": (255, 255, 255),
            "logo": _auto_detect_logo(team_name, logo_dir) if logo_dir else None,
        }
        _auto_color_map[team_name] = _apply_logo_colors(team_name, base_style, logo_dir)
    return _auto_color_map[team_name]
