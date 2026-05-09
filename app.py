"""
app.py – EHL Power Rankings Web App
Upload an Excel (.xlsx) schedule file, see the top-10 power rankings, and
download a styled image ready for social media.
"""

import os
import importlib
import importlib.util
import importlib.machinery
import re
import tempfile
import uuid

from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session

from generate_image import generate_rankings_image, DEFAULT_FONT_SIZES
from team_config import get_team_style

# ── Import the ranking engine from the file named "power rankings" ──
_engine_path = os.path.join(os.path.dirname(__file__), "power rankings")
_spec = importlib.util.spec_from_loader(
    "power_rankings_engine",
    importlib.machinery.SourceFileLoader("power_rankings_engine", _engine_path),
)
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)

def _parse_week_number(week_label):
    """Extract the numeric week from a label like 'WEEK 2' or 'Week 10'.

    Looks for digits following the word "week" first; falls back to the first
    number found.  Returns 1 if no number is found.
    """
    m = re.search(r'(?i)week\s*(\d+)', week_label)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)', week_label)
    return int(m.group(1)) if m else 1


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24).hex())

UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "ehl_uploads")
OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "ehl_outputs")
SCHEDULE_CACHE_DIR = os.path.join(tempfile.gettempdir(), "ehl_schedule_cache")
SCHEDULE_CACHE_DIR_REAL = os.path.realpath(SCHEDULE_CACHE_DIR)
LOGO_DIR = os.path.join(os.path.dirname(__file__), "logos")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SCHEDULE_CACHE_DIR, exist_ok=True)


def _collect_font_overrides(form):
    """Extract font size overrides from form data, validating each value."""
    overrides = {}
    for key in DEFAULT_FONT_SIZES:
        raw = form.get(f"font_{key}")
        if raw:
            try:
                val = int(raw)
                if 10 <= val <= 200:
                    overrides[key] = val
            except (ValueError, TypeError):
                pass
    return overrides


def _normalize_hex_color(value):
    """Return normalized #RRGGBB or None for invalid input."""
    if not value:
        return None
    hex_val = value.strip().lstrip("#")
    if re.match(r"^[0-9a-fA-F]{6}$", hex_val):
        return f"#{hex_val.lower()}"
    return None


def _collect_solid_color_overrides(form):
    """Extract solid team color overrides from form data."""
    overrides = {}
    team_names = form.getlist("team_name[]")
    team_colors = form.getlist("team_color[]")
    for name, color in zip(team_names, team_colors):
        name = name.strip()
        normalized = _normalize_hex_color(color)
        if name and normalized:
            overrides[name] = normalized
    return overrides


def _collect_gradient_overrides(form):
    """Extract gradient team color overrides from form data."""
    overrides = {}
    team_names = form.getlist("team_name[]")
    start_colors = form.getlist("team_color_start[]")
    end_colors = form.getlist("team_color_end[]")
    for name, start_color, end_color in zip(team_names, start_colors, end_colors):
        name = name.strip()
        start_hex = _normalize_hex_color(start_color)
        end_hex = _normalize_hex_color(end_color)
        if name and start_hex and end_hex:
            overrides[name] = (start_hex, end_hex)
    return overrides


def _remove_cached_schedule(cache_name):
    """Remove a cached schedule file by basename."""
    resolved = _resolve_cached_schedule_path(cache_name)
    if not resolved:
        return
    if os.path.isfile(resolved):
        os.remove(resolved)


def _cache_schedule_text(csv_text):
    """Persist CSV text in a server-side cache file and return its basename."""
    cache_name = f"{uuid.uuid4().hex}.csv"
    cache_path = os.path.join(SCHEDULE_CACHE_DIR, cache_name)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(csv_text)
    return cache_name


def _load_cached_schedule_text(cache_name):
    """Load CSV text from a server-side cache file by basename."""
    resolved = _resolve_cached_schedule_path(cache_name)
    if not resolved:
        return None
    if not os.path.isfile(resolved):
        return None
    with open(resolved, "r", encoding="utf-8") as f:
        return f.read()


def _resolve_cached_schedule_path(cache_name):
    """Return a validated cached-schedule path or None."""
    if not cache_name:
        return None
    safe_name = os.path.basename(cache_name)
    path = os.path.join(SCHEDULE_CACHE_DIR, safe_name)
    resolved = os.path.realpath(path)
    try:
        in_cache_dir = os.path.commonpath([resolved, SCHEDULE_CACHE_DIR_REAL]) == SCHEDULE_CACHE_DIR_REAL
    except ValueError:
        return None
    if not in_cache_dir:
        return None
    return resolved


def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _build_team_colors(rankings, solid_overrides=None, gradient_overrides=None):
    """Build color-control data for the results template."""
    solid_overrides = solid_overrides or {}
    gradient_overrides = gradient_overrides or {}

    team_colors = []
    for team, _score, _bd in rankings:
        style = get_team_style(team.name, logo_dir=LOGO_DIR)
        gradient = style.get("bar_gradient") or (style["bar_color"], style["bar_color"])
        start_hex = _rgb_to_hex(gradient[0])
        end_hex = _rgb_to_hex(gradient[1])

        if team.name in solid_overrides:
            solid_hex = solid_overrides[team.name]
            start_hex = solid_hex
            end_hex = solid_hex
        if team.name in gradient_overrides:
            start_hex, end_hex = gradient_overrides[team.name]

        team_colors.append({
            "name": team.name,
            "color_start": start_hex,
            "color_end": end_hex,
        })
    return team_colors


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    # ── Validate upload ─────────────────────────────────────
    if "schedule_file" not in request.files:
        flash("No file uploaded.", "error")
        return redirect(url_for("index"))

    schedule_file = request.files["schedule_file"]
    if schedule_file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("index"))

    fname_lower = schedule_file.filename.lower()
    if not (fname_lower.endswith(".xlsx") or fname_lower.endswith(".csv")):
        flash("Please upload an .xlsx (or .csv) file.", "error")
        return redirect(url_for("index"))

    week_label = request.form.get("week_label", "WEEK 1").strip() or "WEEK 1"
    div_label = request.form.get("div_label", "3'S").strip() or "3'S"

    # Game days per week: how many date-header rows make up one week
    try:
        days_per_week = max(1, int(request.form.get("days_per_week", "1")))
    except (ValueError, TypeError):
        days_per_week = 1

    # ── Collect font size overrides ─────────────────────────
    font_overrides = _collect_font_overrides(request.form)

    # ── Collect team color overrides ────────────────────────
    color_overrides = _collect_solid_color_overrides(request.form)

    # ── Save uploaded file ──────────────────────────────────
    ext = ".xlsx" if fname_lower.endswith(".xlsx") else ".csv"
    saved_filename = f"{uuid.uuid4().hex}{ext}"
    saved_path = os.path.join(UPLOAD_DIR, saved_filename)
    schedule_file.save(saved_path)

    # ── Convert to CSV text ─────────────────────────────────
    try:
        if ext == ".xlsx":
            csv_text = engine.xlsx_to_csv_text(saved_path)
        else:
            with open(saved_path, "r", encoding="utf-8") as f:
                csv_text = f.read()

        week_num = _parse_week_number(week_label)
        rankings_csv = engine.schedule_up_to_week(csv_text, week_num, days_per_week)
        teams = engine.parse_schedule(rankings_csv)
        rankings = engine.calculate_power_scores(teams)

        if not rankings:
            total_teams = len(teams)
            if total_teams > 0:
                flash(
                    f"Found {total_teams} team(s) but none had completed games. "
                    "Make sure the Status/Result column says 'Completed', 'Complete', 'Final', or 'Forfeit'.",
                    "error",
                )
            else:
                flash(
                    "No teams or games found in the file. "
                    "Expected columns include Home Team, Away Team, Home Score, Away Score, and Status "
                    "(plus optional Game#/Time and OT columns). "
                    "Headers are auto-detected and case-insensitive.",
                    "error",
                )
            if os.path.exists(saved_path):
                os.remove(saved_path)
            return redirect(url_for("index"))

    except Exception as exc:
        flash(f"Error processing file: {exc}", "error")
        if os.path.exists(saved_path):
            os.remove(saved_path)
        return redirect(url_for("index"))

    # Store a small server-side cache reference for regeneration.
    session.pop("csv_text", None)
    old_cache_file = session.get("schedule_cache_file")
    session["schedule_cache_file"] = _cache_schedule_text(csv_text)
    _remove_cached_schedule(old_cache_file)
    session["week_label"] = week_label
    session["div_label"] = div_label
    session["days_per_week"] = days_per_week
    if os.path.exists(saved_path):
        os.remove(saved_path)

    # ── Compute movement arrows ─────────────────────────────
    # Use the week number from the user's label (e.g. "WEEK 2" → 2)
    detected_weeks = engine.count_weeks(csv_text, days_per_week)
    movement = engine.compute_movement(csv_text, week_num, days_per_week)

    # Diagnostic: warn user if week detection seems off
    n_date_rows = len(engine._find_date_row_indices(csv_text))
    if week_num > 1 and detected_weeks < week_num:
        flash(
            f"⚠️ Found {n_date_rows} game-day(s) in the schedule "
            f"({detected_weeks} week(s) at {days_per_week} day(s)/week) but you "
            f"selected week {week_num}. Movement arrows need at least {week_num} "
            f"week(s) of data. Check that your file has enough weeks and that "
            f"'Game Days Per Week' is set correctly.",
            "error",
        )

    # ── Generate image ──────────────────────────────────────
    out_filename = f"power_rankings_{uuid.uuid4().hex}.png"
    out_path = os.path.join(OUTPUT_DIR, out_filename)

    # Merge font overrides with defaults for the actual sizes used
    active_font_sizes = dict(DEFAULT_FONT_SIZES)
    active_font_sizes.update(font_overrides)

    generate_rankings_image(
        rankings,
        week_label=week_label,
        division_label=div_label,
        logo_dir=LOGO_DIR,
        output_path=out_path,
        top_n=10,
        color_overrides=color_overrides,
        gradient_overrides=None,
        font_overrides=font_overrides,
        movement=movement,
    )

    # ── Build results table with ALL ranked teams ───────────
    results = []
    for rank, (team, score, _bd) in enumerate(rankings, 1):
        stype, scount = team.current_streak
        streak = f"{stype}{scount}" if scount else "–"
        gd = team.goal_diff
        results.append({
            "rank": rank,
            "name": team.name,
            "record": team.record_str(),
            "points": team.points,
            "gd": f"+{gd}" if gd > 0 else str(gd),
            "score": f"{score:.4f}",
            "streak": streak,
        })

    team_colors = _build_team_colors(rankings, solid_overrides=color_overrides)

    return render_template(
        "results.html",
        results=results,
        image_file=out_filename,
        week_label=week_label,
        div_label=div_label,
        days_per_week=days_per_week,
        total_ranked=len(rankings),
        team_colors=team_colors,
        font_sizes=active_font_sizes,
    )


@app.route("/download/<filename>")
def download(filename):
    """Serve the generated image for download or preview."""
    safe_name = os.path.basename(filename)
    # Only allow expected filename pattern (hex UUID + .png)
    if not safe_name.startswith("power_rankings_") or not safe_name.endswith(".png"):
        flash("Invalid file request.", "error")
        return redirect(url_for("index"))
    path = os.path.join(OUTPUT_DIR, safe_name)
    resolved = os.path.realpath(path)
    if not resolved.startswith(os.path.realpath(OUTPUT_DIR)):
        flash("Invalid file request.", "error")
        return redirect(url_for("index"))
    if not os.path.isfile(resolved):
        flash("Image not found. Please generate rankings again.", "error")
        return redirect(url_for("index"))
    # If ?preview=1, serve inline (for <img> tags); otherwise attachment
    if request.args.get("preview"):
        return send_file(resolved, mimetype="image/png")
    return send_file(
        resolved,
        mimetype="image/png",
        as_attachment=True,
        download_name="ehl_power_rankings.png",
    )


@app.route("/regenerate", methods=["POST"])
def regenerate():
    """Re-generate the image using the previously uploaded schedule with new overrides."""
    csv_text = _load_cached_schedule_text(session.get("schedule_cache_file"))
    if not csv_text:
        csv_text = session.get("csv_text")
        if csv_text:
            session["schedule_cache_file"] = _cache_schedule_text(csv_text)
            session.pop("csv_text", None)
    week_label = session.get("week_label", "WEEK 1")
    div_label = session.get("div_label", "3'S")
    days_per_week = session.get("days_per_week", 1)

    if not csv_text:
        flash("Session expired. Please upload the schedule again.", "error")
        return redirect(url_for("index"))

    # ── Collect team color overrides ────────────────────────
    color_overrides = _collect_solid_color_overrides(request.form)
    gradient_overrides = _collect_gradient_overrides(request.form)

    # ── Collect font size overrides ─────────────────────────
    font_overrides = _collect_font_overrides(request.form)

    # ── Re-run the rankings engine ──────────────────────────
    try:
        week_num = _parse_week_number(week_label)
        rankings_csv = engine.schedule_up_to_week(csv_text, week_num, days_per_week)
        teams = engine.parse_schedule(rankings_csv)
        rankings = engine.calculate_power_scores(teams)
    except Exception as exc:
        flash(f"Error processing schedule: {exc}", "error")
        return redirect(url_for("index"))

    if not rankings:
        flash("No ranked teams found.", "error")
        return redirect(url_for("index"))

    # ── Compute movement arrows ─────────────────────────────
    detected_weeks = engine.count_weeks(csv_text, days_per_week)
    movement = engine.compute_movement(csv_text, week_num, days_per_week)

    n_date_rows = len(engine._find_date_row_indices(csv_text))
    if week_num > 1 and detected_weeks < week_num:
        flash(
            f"⚠️ Found {n_date_rows} game-day(s) in the schedule "
            f"({detected_weeks} week(s) at {days_per_week} day(s)/week) but you "
            f"selected week {week_num}. Movement arrows need at least {week_num} "
            f"week(s) of data. Check that your file has enough weeks and that "
            f"'Game Days Per Week' is set correctly.",
            "error",
        )

    # ── Generate new image ──────────────────────────────────
    out_filename = f"power_rankings_{uuid.uuid4().hex}.png"
    out_path = os.path.join(OUTPUT_DIR, out_filename)

    active_font_sizes = dict(DEFAULT_FONT_SIZES)
    active_font_sizes.update(font_overrides)

    generate_rankings_image(
        rankings,
        week_label=week_label,
        division_label=div_label,
        logo_dir=LOGO_DIR,
        output_path=out_path,
        top_n=10,
        color_overrides=color_overrides,
        gradient_overrides=gradient_overrides,
        font_overrides=font_overrides,
        movement=movement,
    )

    # ── Build results + team colors ─────────────────────────
    results = []
    for rank, (team, score, _bd) in enumerate(rankings, 1):
        stype, scount = team.current_streak
        streak = f"{stype}{scount}" if scount else "–"
        gd = team.goal_diff
        results.append({
            "rank": rank,
            "name": team.name,
            "record": team.record_str(),
            "points": team.points,
            "gd": f"+{gd}" if gd > 0 else str(gd),
            "score": f"{score:.4f}",
            "streak": streak,
        })

    team_colors = _build_team_colors(
        rankings,
        solid_overrides=color_overrides,
        gradient_overrides=gradient_overrides,
    )

    return render_template(
        "results.html",
        results=results,
        image_file=out_filename,
        week_label=week_label,
        div_label=div_label,
        days_per_week=days_per_week,
        total_ranked=len(rankings),
        team_colors=team_colors,
        font_sizes=active_font_sizes,
    )


if __name__ == "__main__":
    app.run(debug=False, port=5000)
