"""
app.py – EHL Power Rankings Web App
Upload an Excel (.xlsx) schedule file, see the top-10 power rankings, and
download a styled image ready for social media.
"""

import os
import importlib
import importlib.util
import importlib.machinery
import json
import re
import tempfile
import uuid

from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session

from generate_image import generate_rankings_image, DEFAULT_FONT_SIZES
from team_config import get_team_style, hex_to_rgb

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
LOGO_DIR = os.path.join(os.path.dirname(__file__), "logos")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


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
    color_overrides = {}
    team_names = request.form.getlist("team_name[]")
    team_colors = request.form.getlist("team_color[]")
    for name, color in zip(team_names, team_colors):
        name = name.strip()
        color = color.strip()
        if name and color:
            # Ensure color is a valid hex string
            hex_val = color.lstrip("#")
            if re.match(r'^[0-9a-fA-F]{6}$', hex_val):
                color_overrides[name] = f"#{hex_val}"

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

        teams = engine.parse_schedule(csv_text)
        rankings = engine.calculate_power_scores(teams)

        if not rankings:
            total_teams = len(teams)
            if total_teams > 0:
                flash(
                    f"Found {total_teams} team(s) but none had completed games. "
                    "Make sure the Status column (column 8) says 'Completed' or 'Forfeit'.",
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

    # Store CSV text in session for regeneration; remove uploaded file
    session["csv_text"] = csv_text
    session["week_label"] = week_label
    session["div_label"] = div_label
    session["days_per_week"] = days_per_week
    if os.path.exists(saved_path):
        os.remove(saved_path)

    # ── Compute movement arrows ─────────────────────────────
    # Use the week number from the user's label (e.g. "WEEK 2" → 2)
    week_num = _parse_week_number(week_label)
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
        font_overrides=font_overrides,
        movement=movement,
    )

    # ── Build results table with ALL ranked teams ───────────
    results = []
    team_colors = []
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
        # Get current bar color for the color picker
        style = get_team_style(team.name, logo_dir=LOGO_DIR)
        if team.name in color_overrides:
            rgb = hex_to_rgb(color_overrides[team.name])
            if rgb:
                bar_color = color_overrides[team.name]
            else:
                bar_color = "#{:02x}{:02x}{:02x}".format(*style["bar_color"])
        else:
            bar_color = "#{:02x}{:02x}{:02x}".format(*style["bar_color"])
        team_colors.append({
            "name": team.name,
            "color": bar_color,
        })

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
    csv_text = session.get("csv_text")
    week_label = session.get("week_label", "WEEK 1")
    div_label = session.get("div_label", "3'S")
    days_per_week = session.get("days_per_week", 1)

    if not csv_text:
        flash("Session expired. Please upload the schedule again.", "error")
        return redirect(url_for("index"))

    # ── Collect team color overrides ────────────────────────
    color_overrides = {}
    team_names = request.form.getlist("team_name[]")
    team_colors_form = request.form.getlist("team_color[]")
    for name, color in zip(team_names, team_colors_form):
        name = name.strip()
        color = color.strip()
        if name and color:
            hex_val = color.lstrip("#")
            if re.match(r'^[0-9a-fA-F]{6}$', hex_val):
                color_overrides[name] = f"#{hex_val}"

    # ── Collect font size overrides ─────────────────────────
    font_overrides = _collect_font_overrides(request.form)

    # ── Re-run the rankings engine ──────────────────────────
    try:
        teams = engine.parse_schedule(csv_text)
        rankings = engine.calculate_power_scores(teams)
    except Exception as exc:
        flash(f"Error processing schedule: {exc}", "error")
        return redirect(url_for("index"))

    if not rankings:
        flash("No ranked teams found.", "error")
        return redirect(url_for("index"))

    # ── Compute movement arrows ─────────────────────────────
    week_num = _parse_week_number(week_label)
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
        font_overrides=font_overrides,
        movement=movement,
    )

    # ── Build results + team colors ─────────────────────────
    results = []
    team_colors = []
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
        style = get_team_style(team.name, logo_dir=LOGO_DIR)
        if team.name in color_overrides:
            rgb = hex_to_rgb(color_overrides[team.name])
            if rgb:
                bar_color = color_overrides[team.name]
            else:
                bar_color = "#{:02x}{:02x}{:02x}".format(*style["bar_color"])
        else:
            bar_color = "#{:02x}{:02x}{:02x}".format(*style["bar_color"])
        team_colors.append({
            "name": team.name,
            "color": bar_color,
        })

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
