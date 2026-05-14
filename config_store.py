import json
import os
import tempfile


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "saved_customizations.json")
MIN_FONT_SIZE = 10
MAX_FONT_SIZE = 200
DEFAULT_CONFIG = {
    "font_sizes": {},
    "team_styles": {},
}
_config_cache = None
_config_mtime = None


def _normalize_font_sizes(font_sizes):
    normalized = {}
    if not isinstance(font_sizes, dict):
        return normalized
    for key, value in font_sizes.items():
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            continue
        if MIN_FONT_SIZE <= int_value <= MAX_FONT_SIZE:
            normalized[str(key)] = int_value
    return normalized


def _normalize_text_mode(text_mode):
    value = str(text_mode or "auto").strip().lower()
    return value if value in {"auto", "light", "dark"} else "auto"


def _normalize_team_styles(team_styles):
    normalized = {}
    if not isinstance(team_styles, dict):
        return normalized

    for team_name, style in team_styles.items():
        if not team_name or not isinstance(style, dict):
            continue
        start = style.get("color_start")
        end = style.get("color_end")
        if not (isinstance(start, str) and isinstance(end, str)):
            continue
        normalized[str(team_name)] = {
            "color_start": start,
            "color_end": end,
            "text_mode": _normalize_text_mode(style.get("text_mode")),
        }
    return normalized


def _normalize_config(data):
    if not isinstance(data, dict):
        return dict(DEFAULT_CONFIG)
    return {
        "font_sizes": _normalize_font_sizes(data.get("font_sizes", {})),
        "team_styles": _normalize_team_styles(data.get("team_styles", {})),
    }


def load_saved_customizations():
    global _config_cache, _config_mtime

    try:
        current_mtime = os.path.getmtime(CONFIG_PATH)
    except OSError:
        _config_cache = dict(DEFAULT_CONFIG)
        _config_mtime = None
        return dict(_config_cache)

    if _config_cache is not None and _config_mtime == current_mtime:
        return {
            "font_sizes": dict(_config_cache["font_sizes"]),
            "team_styles": {
                team: dict(style) for team, style in _config_cache["team_styles"].items()
            },
        }

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
    except (OSError, ValueError, TypeError):
        loaded = {}

    _config_cache = _normalize_config(loaded)
    _config_mtime = current_mtime
    return {
        "font_sizes": dict(_config_cache["font_sizes"]),
        "team_styles": {
            team: dict(style) for team, style in _config_cache["team_styles"].items()
        },
    }


def save_saved_customizations(font_sizes=None, team_styles=None):
    current = load_saved_customizations()
    if font_sizes is not None:
        current["font_sizes"] = _normalize_font_sizes(font_sizes)
    if team_styles is not None:
        current["team_styles"].update(_normalize_team_styles(team_styles))

    fd, tmp_path = tempfile.mkstemp(
        prefix="saved-customizations-",
        suffix=".json",
        dir=os.path.dirname(CONFIG_PATH),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, CONFIG_PATH)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise

    global _config_cache, _config_mtime
    _config_cache = _normalize_config(current)
    try:
        _config_mtime = os.path.getmtime(CONFIG_PATH)
    except OSError:
        _config_mtime = None


def get_saved_font_sizes():
    return load_saved_customizations()["font_sizes"]


def get_saved_team_styles():
    return load_saved_customizations()["team_styles"]
