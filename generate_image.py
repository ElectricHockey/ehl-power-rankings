"""
generate_image.py
Generates a styled EHL Power Rankings image (PNG) from ranking data.
Output matches the reference design: black background, colored team bars,
rank numbers, team logos, and an EHL header.
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

from team_config import get_team_style, hex_to_rgb

# ── Layout constants ────────────────────────────────────────
IMG_WIDTH = 1080
ROW_HEIGHT = 120
HEADER_HEIGHT = 240
TOP_PADDING = 10
BOTTOM_PADDING = 20
RANK_BOX_W = 100
BAR_LEFT = RANK_BOX_W + 6
BAR_RIGHT = IMG_WIDTH - 60
LOGO_SIZE = 90
MOVEMENT_X = IMG_WIDTH - 35

BG_COLOR = (0, 0, 0)
RANK_BG = (200, 20, 20)
RANK_TEXT_COLOR = (255, 255, 255)
TITLE_COLOR = (255, 215, 0)
SUBTITLE_COLOR = (255, 215, 0)
MOVEMENT_COLOR = (255, 255, 255)
MOVE_UP_COLOR = (0, 200, 0)
MOVE_DOWN_COLOR = (220, 30, 30)

FONT_DIR = "/usr/share/fonts/truetype"

# Bundled fonts directory (shipped with the repo so fonts always work)
_BUNDLED_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def _load_font(name, size):
    """Load a font, checking the bundled fonts/ dir first, then system paths."""
    candidates = [
        os.path.join(_BUNDLED_FONT_DIR, name),
        os.path.join(FONT_DIR, "lato", name),
        os.path.join(FONT_DIR, "dejavu", name),
        os.path.join(FONT_DIR, "liberation", name),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _load_team_logo(logo_dir, filename, size):
    """Load and resize a team logo. Returns None if missing."""
    if not filename:
        return None
    path = os.path.join(logo_dir, filename)
    if not os.path.isfile(path):
        return None
    img = Image.open(path).convert("RGBA")
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    return img


def _load_ehl_logo(logo_dir, size):
    """Load the EHL header logo from logo_dir/ehl_logo.png."""
    path = os.path.join(logo_dir, "ehl_logo.png")
    if not os.path.isfile(path):
        return None
    img = Image.open(path).convert("RGBA")
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    return img


def _draw_rounded_rect(draw, xy, radius, fill):
    """Draw a rectangle with rounded corners."""
    x0, y0, x1, y1 = xy
    r = min(radius, (x1 - x0) // 2, (y1 - y0) // 2)
    draw.rounded_rectangle(xy, radius=r, fill=fill)


# Default font sizes – can be overridden via font_overrides parameter
DEFAULT_FONT_SIZES = {
    "title": 84,
    "subtitle": 52,
    "team": 48,
    "rank": 54,
}

# Default font files (edit these in code to change typefaces independently)
DEFAULT_FONT_FILES = {
    "title": "Lato-Black.ttf",
    "subtitle": "Lato-BoldItalic.ttf",
    "team": "Lato-Heavy.ttf",
    "rank": "Lato-Black.ttf",
    "movement": "Lato-Bold.ttf",
}

# Per-text placement offsets (edit these in code for independent positioning)
TEXT_POSITION_OFFSETS = {
    "title_x": 0,
    "title_y": 0,
    "subtitle_x": 0,
    "subtitle_y": 0,
    "team_x": 0,
    "team_y": 0,
}


def generate_rankings_image(
    ranked_teams,
    week_label="WEEK 1",
    division_label="3'S",
    logo_dir="logos",
    output_path="power_rankings.png",
    top_n=10,
    color_overrides=None,
    font_overrides=None,
    movement=None,
):
    """
    Generate the power rankings image.

    Parameters
    ----------
    ranked_teams : list of (team, score, breakdown)
        Output from calculate_power_scores(), sorted best→worst.
    week_label : str
        e.g. "WEEK 1"
    division_label : str
        e.g. "3'S" or "6'S"
    logo_dir : str
        Directory containing team logo PNGs and ehl_logo.png.
    output_path : str
        Where to save the resulting image.
    top_n : int
        How many teams to show in the image (default 10).
    color_overrides : dict or None
        Optional {team_name: "#RRGGBB"} to override bar colors.
    font_overrides : dict or None
        Optional {"title": int, "subtitle": int, "team": int, "rank": int}
        to override default font sizes (in pt).
    movement : dict or None
        Optional {team_name: int} where positive = moved up, negative = down,
        0 = unchanged, None = new team.  Omit for no arrows.

    Note
    ----
    To change typefaces and placement in code, edit DEFAULT_FONT_FILES and
    TEXT_POSITION_OFFSETS near the top of this file.
    """
    if color_overrides is None:
        color_overrides = {}
    if movement is None:
        movement = {}

    # Merge user font sizes with defaults
    font_sizes = dict(DEFAULT_FONT_SIZES)
    if font_overrides:
        for key in DEFAULT_FONT_SIZES:
            if key in font_overrides:
                val = font_overrides[key]
                if isinstance(val, int) and 10 <= val <= 200:
                    font_sizes[key] = val

    teams_to_show = ranked_teams[:top_n]
    num_rows = len(teams_to_show)
    img_height = HEADER_HEIGHT + TOP_PADDING + num_rows * ROW_HEIGHT + BOTTOM_PADDING

    img = Image.new("RGB", (IMG_WIDTH, img_height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # ── Fonts ───────────────────────────────────────────────
    font_title = _load_font(DEFAULT_FONT_FILES["title"], font_sizes["title"])
    font_subtitle = _load_font(DEFAULT_FONT_FILES["subtitle"], font_sizes["subtitle"])
    font_rank = _load_font(DEFAULT_FONT_FILES["rank"], font_sizes["rank"])
    font_team = _load_font(DEFAULT_FONT_FILES["team"], font_sizes["team"])
    font_move = _load_font(DEFAULT_FONT_FILES["movement"], 32)

    # ── Header ──────────────────────────────────────────────
    # NOTE: PIL textbbox((0,0), text) returns (x0, y0, x1, y1) where y0 is
    # a positive offset (font ascent above baseline). To truly center text
    # we must subtract these origin offsets from the draw position.
    ehl_logo = _load_ehl_logo(logo_dir, 130)
    if ehl_logo:
        logo_y_center = (HEADER_HEIGHT - ehl_logo.height) // 2
        img.paste(ehl_logo, (20, logo_y_center), ehl_logo)
        img.paste(ehl_logo, (IMG_WIDTH - 20 - ehl_logo.width, logo_y_center), ehl_logo)

    title_text = "POWER RANKINGS"
    bbox = draw.textbbox((0, 0), title_text, font=font_title)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    # Center the title in the top portion of the header (account for bbox origin)
    title_x = (IMG_WIDTH - tw) // 2 - bbox[0]
    title_y = (HEADER_HEIGHT // 2 - th) // 2 - bbox[1]
    title_x += TEXT_POSITION_OFFSETS["title_x"]
    title_y += TEXT_POSITION_OFFSETS["title_y"]
    draw.text((title_x, title_y), title_text, fill=TITLE_COLOR, font=font_title)

    sub_text = f"{division_label} {week_label}"
    bbox = draw.textbbox((0, 0), sub_text, font=font_subtitle)
    sw = bbox[2] - bbox[0]
    sh = bbox[3] - bbox[1]
    # Center the subtitle in the bottom portion of the header (account for bbox origin)
    sub_x = (IMG_WIDTH - sw) // 2 - bbox[0]
    sub_y = HEADER_HEIGHT // 2 + (HEADER_HEIGHT // 2 - sh) // 2 - bbox[1]
    sub_x += TEXT_POSITION_OFFSETS["subtitle_x"]
    sub_y += TEXT_POSITION_OFFSETS["subtitle_y"]
    draw.text((sub_x, sub_y), sub_text, fill=SUBTITLE_COLOR, font=font_subtitle)

    # ── Team rows ───────────────────────────────────────────
    y_start = HEADER_HEIGHT + TOP_PADDING
    for idx, (team, score, _bd) in enumerate(teams_to_show):
        rank = idx + 1
        y = y_start + idx * ROW_HEIGHT

        style = get_team_style(team.name, logo_dir=logo_dir)

        # Apply user-specified hex color override if provided
        if team.name in color_overrides:
            rgb = hex_to_rgb(color_overrides[team.name])
            if rgb:
                style = dict(style)  # copy to avoid mutating config
                style["bar_color"] = rgb

        # Rank box (red rounded rectangle)
        rank_x0, rank_y0 = 10, y + 5
        rank_x1, rank_y1 = RANK_BOX_W, y + ROW_HEIGHT - 5
        box_h = rank_y1 - rank_y0
        box_w = rank_x1 - rank_x0
        _draw_rounded_rect(draw, (rank_x0, rank_y0, rank_x1, rank_y1), 14, RANK_BG)
        rank_str = str(rank)
        rb = draw.textbbox((0, 0), rank_str, font=font_rank)
        rw = rb[2] - rb[0]
        rh = rb[3] - rb[1]
        draw.text(
            (rank_x0 + (box_w - rw) // 2 - rb[0],
             rank_y0 + (box_h - rh) // 2 - rb[1]),
            rank_str,
            fill=RANK_TEXT_COLOR,
            font=font_rank,
        )

        # Team bar (colored rounded rectangle)
        bar_x0, bar_y0 = BAR_LEFT, y + 5
        bar_x1, bar_y1 = BAR_RIGHT, y + ROW_HEIGHT - 5
        bar_h = bar_y1 - bar_y0
        _draw_rounded_rect(draw, (bar_x0, bar_y0, bar_x1, bar_y1), 14, style["bar_color"])

        # Team logo (drawn first so we know the exact reserved space)
        logo_img = _load_team_logo(logo_dir, style.get("logo"), LOGO_SIZE)
        logo_x = bar_x1 - LOGO_SIZE - 10
        if logo_img:
            logo_y = bar_y0 + (bar_h - LOGO_SIZE) // 2
            img.paste(logo_img, (logo_x, logo_y), logo_img)

        # Team name text – must fit between bar left edge and logo area
        name_upper = team.name.upper()
        text_left = bar_x0 + 12
        text_right = logo_x - 8  # leave gap before logo
        text_area_w = text_right - text_left

        # Use the requested font, but auto-shrink if the name is too wide
        actual_font = font_team
        nb = draw.textbbox((0, 0), name_upper, font=actual_font)
        nw = nb[2] - nb[0]
        nh = nb[3] - nb[1]
        if nw > text_area_w:
            # Shrink font until text fits
            shrunk_size = font_sizes["team"]
            while nw > text_area_w and shrunk_size > 16:
                shrunk_size -= 2
                actual_font = _load_font(DEFAULT_FONT_FILES["team"], shrunk_size)
                nb = draw.textbbox((0, 0), name_upper, font=actual_font)
                nw = nb[2] - nb[0]
                nh = nb[3] - nb[1]

        text_x = text_left + (text_area_w - nw) // 2 - nb[0]
        text_y = bar_y0 + (bar_h - nh) // 2 - nb[1]
        text_x += TEXT_POSITION_OFFSETS["team_x"]
        text_y += TEXT_POSITION_OFFSETS["team_y"]
        draw.text((text_x, text_y), name_upper, fill=style["text_color"], font=actual_font)

        # Movement indicator: drawn arrow + number, or "–" for no change
        move_val = movement.get(team.name, 0)
        margin_cx = BAR_RIGHT + (IMG_WIDTH - BAR_RIGHT) // 2  # center x of margin
        row_cy = y + ROW_HEIGHT // 2  # center y of this row

        if move_val is None or move_val == 0:
            # No movement — draw a dash
            move_text = "–"
            mb = draw.textbbox((0, 0), move_text, font=font_move)
            mw, mh = mb[2] - mb[0], mb[3] - mb[1]
            draw.text(
                (margin_cx - mw // 2 - mb[0], row_cy - mh // 2 - mb[1]),
                move_text, fill=MOVEMENT_COLOR, font=font_move,
            )
        else:
            # Draw a polygon arrow (up or down) + the number
            num_text = str(abs(move_val))
            nb = draw.textbbox((0, 0), num_text, font=font_move)
            nw, nh = nb[2] - nb[0], nb[3] - nb[1]

            arrow_h = 14   # arrow triangle height
            arrow_w = 16   # arrow triangle base width
            gap = 2        # space between arrow and number
            total_h = arrow_h + gap + nh
            top_y = row_cy - total_h // 2

            if move_val > 0:
                # Green up arrow ▲
                arrow_color = MOVE_UP_COLOR
                arrow_tip = (margin_cx, top_y)
                arrow_bl = (margin_cx - arrow_w // 2, top_y + arrow_h)
                arrow_br = (margin_cx + arrow_w // 2, top_y + arrow_h)
                draw.polygon([arrow_tip, arrow_bl, arrow_br], fill=arrow_color)
                # Number below arrow
                num_x = margin_cx - nw // 2 - nb[0]
                num_y = top_y + arrow_h + gap - nb[1]
                draw.text((num_x, num_y), num_text, fill=arrow_color, font=font_move)
            else:
                # Red down arrow ▼
                arrow_color = MOVE_DOWN_COLOR
                # Number on top, arrow below
                num_x = margin_cx - nw // 2 - nb[0]
                num_y = top_y - nb[1]
                draw.text((num_x, num_y), num_text, fill=arrow_color, font=font_move)
                arrow_top_y = top_y + nh + gap
                arrow_tl = (margin_cx - arrow_w // 2, arrow_top_y)
                arrow_tr = (margin_cx + arrow_w // 2, arrow_top_y)
                arrow_tip = (margin_cx, arrow_top_y + arrow_h)
                draw.polygon([arrow_tl, arrow_tr, arrow_tip], fill=arrow_color)

    img.save(output_path, "PNG")
    return output_path


# ── Standalone usage ────────────────────────────────────────
if __name__ == "__main__":
    import sys

    # Allow importing the rankings engine that lives in the oddly-named file
    sys.path.insert(0, os.path.dirname(__file__))

    # The existing engine lives in the file called "power rankings" (no .py)
    import importlib.util
    import types

    engine_path = os.path.join(os.path.dirname(__file__), "power rankings")
    spec = importlib.util.spec_from_loader(
        "power_rankings",
        importlib.machinery.SourceFileLoader("power_rankings", engine_path),
    )
    pr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pr)

    if len(sys.argv) < 2:
        print("Usage: python generate_image.py <schedule.csv> [--week 'WEEK 1'] [--div '3S']")
        sys.exit(1)

    csv_path = sys.argv[1]
    week_label = "WEEK 1"
    div_label = "3'S"
    for i, arg in enumerate(sys.argv):
        if arg == "--week" and i + 1 < len(sys.argv):
            week_label = sys.argv[i + 1]
        if arg == "--div" and i + 1 < len(sys.argv):
            div_label = sys.argv[i + 1]

    with open(csv_path, "r", encoding="utf-8") as f:
        csv_text = f.read()

    teams = pr.parse_schedule(csv_text)
    rankings = pr.calculate_power_scores(teams)

    out = generate_rankings_image(
        rankings,
        week_label=week_label,
        division_label=div_label,
    )
    print(f"✅ Power rankings image saved to: {out}")
