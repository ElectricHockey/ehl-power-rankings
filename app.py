"""
app.py – EHL Power Rankings Web App
Upload a CSV schedule file, see the top-10 power rankings, and download
a styled image ready for social media.
"""

import os
import importlib
import importlib.util
import importlib.machinery
import tempfile
import uuid

from flask import Flask, render_template, request, send_file, redirect, url_for, flash

from generate_image import generate_rankings_image

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
            flash("No completed games found in the CSV. Check the file format.", "error")
            return redirect(url_for("index"))

    except Exception as exc:
        flash(f"Error processing CSV: {exc}", "error")
        return redirect(url_for("index"))
    finally:
        # Clean up the uploaded CSV
        if os.path.exists(csv_path):
            os.remove(csv_path)

    # ── Generate image ──────────────────────────────────────
    out_filename = f"power_rankings_{uuid.uuid4().hex}.png"
    out_path = os.path.join(OUTPUT_DIR, out_filename)

    generate_rankings_image(
        rankings,
        week_label=week_label,
        division_label=div_label,
        logo_dir=LOGO_DIR,
        output_path=out_path,
    )

    # ── Build a simple results table for the template ───────
    results = []
    for rank, (team, score, _bd) in enumerate(rankings[:10], 1):
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

    return render_template(
        "results.html",
        results=results,
        image_file=out_filename,
        week_label=week_label,
        div_label=div_label,
    )


@app.route("/download/<filename>")
def download(filename):
    """Serve the generated image for download."""
    safe_name = os.path.basename(filename)
    path = os.path.join(OUTPUT_DIR, safe_name)
    if not os.path.isfile(path):
        flash("Image not found. Please generate rankings again.", "error")
        return redirect(url_for("index"))
    return send_file(
        path,
        mimetype="image/png",
        as_attachment=True,
        download_name="ehl_power_rankings.png",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
