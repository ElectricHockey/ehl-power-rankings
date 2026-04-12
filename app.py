"""
app.py – EHL Power Rankings Web App
Upload a CSV schedule file, see the top-10 power rankings, and download
a styled image ready for social media.
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

from generate_image import generate_rankings_image
from team_config import get_team_style, hex_to_rgb

# ── Import the ranking engine from the file named "power rankings" ──
_engine_path = os.path.join(os.path.dirname(__file__), "power rankings")
_spec = importlib.util.spec_from_loader(
    "power_rankings_engine",
    importlib.machinery.SourceFileLoader("power_rankings_engine", _engine_path),
)
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24).hex())

UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "ehl_uploads")
OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "ehl_outputs")
LOGO_DIR = os.path.join(os.path.dirname(__file__), "logos")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    # ── Validate upload ─────────────────────────────────────
    if "csv_file" not in request.files:
        flash("No file uploaded.", "error")
        return redirect(url_for("index"))

    csv_file = request.files["csv_file"]
    if csv_file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("index"))

    if not csv_file.filename.lower().endswith(".csv"):
        flash("Please upload a .csv file.", "error")
        return redirect(url_for("index"))

    week_label = request.form.get("week_label", "WEEK 1").strip() or "WEEK 1"
    div_label = request.form.get("div_label", "3'S").strip() or "3'S"

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

    # ── Save uploaded CSV ───────────────────────────────────
    csv_filename = f"{uuid.uuid4().hex}.csv"
    csv_path = os.path.join(UPLOAD_DIR, csv_filename)
    csv_file.save(csv_path)

    # ── Run the rankings engine ─────────────────────────────
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
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
                    "No teams or games found in the CSV. "
                    "Expected columns: Game#, Home, HomeScore, AwayScore, Away, …, …, Status. "
                    "Rows must start with a number (game #).",
                    "error",
                )
            if os.path.exists(csv_path):
                os.remove(csv_path)
            return redirect(url_for("index"))

    except Exception as exc:
        flash(f"Error processing CSV: {exc}", "error")
        if os.path.exists(csv_path):
            os.remove(csv_path)
        return redirect(url_for("index"))

    # Keep the CSV so the user can regenerate with different colors
    session["csv_path"] = csv_path
    session["week_label"] = week_label
    session["div_label"] = div_label

    # ── Generate image ──────────────────────────────────────
    out_filename = f"power_rankings_{uuid.uuid4().hex}.png"
    out_path = os.path.join(OUTPUT_DIR, out_filename)

    generate_rankings_image(
        rankings,
        week_label=week_label,
        division_label=div_label,
        logo_dir=LOGO_DIR,
        output_path=out_path,
        top_n=10,
        color_overrides=color_overrides,
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
        total_ranked=len(rankings),
        team_colors=team_colors,
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
    """Re-generate the image using the previously uploaded CSV with new color overrides."""
    csv_path = session.get("csv_path")
    week_label = session.get("week_label", "WEEK 1")
    div_label = session.get("div_label", "3'S")

    if not csv_path or not os.path.isfile(csv_path):
        flash("Session expired. Please upload the CSV again.", "error")
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

    # ── Re-run the rankings engine ──────────────────────────
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_text = f.read()
        teams = engine.parse_schedule(csv_text)
        rankings = engine.calculate_power_scores(teams)
    except Exception as exc:
        flash(f"Error processing CSV: {exc}", "error")
        return redirect(url_for("index"))

    if not rankings:
        flash("No ranked teams found.", "error")
        return redirect(url_for("index"))

    # ── Generate new image ──────────────────────────────────
    out_filename = f"power_rankings_{uuid.uuid4().hex}.png"
    out_path = os.path.join(OUTPUT_DIR, out_filename)

    generate_rankings_image(
        rankings,
        week_label=week_label,
        division_label=div_label,
        logo_dir=LOGO_DIR,
        output_path=out_path,
        top_n=10,
        color_overrides=color_overrides,
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
        total_ranked=len(rankings),
        team_colors=team_colors,
    )


if __name__ == "__main__":
    app.run(debug=False, port=5000)
