# EHL Power Rankings

Generate styled power-rankings images for the Electric Hockey League.
Upload a schedule file (.xlsx or .csv), and the app produces a downloadable PNG
graphic showing the top 10 teams with logos, rank numbers, team colors, and
week-over-week movement arrows.

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser, upload your schedule file
(.xlsx or .csv), choose the division and week labels, and click **Generate Rankings**.
The results page shows a table and a preview of the image with a download button.

### Command-line usage (no web server)

```bash
python generate_image.py schedule.csv --week "WEEK 3" --div "3'S"
```

This writes `power_rankings.png` to the current directory.

## Schedule Format

The schedule file (.xlsx or .csv) must follow this column layout:

| Col 0 | Col 1 | Col 2 | Col 3 | Col 4 | Col 5 | … | Col 7 |
|-------|-------|-------|-------|-------|-------|---|-------|
| Game # & Time | Home Team | Home Score | OT (or empty) | Away Score | Away Team | … | Status |

- **Status** must be `Completed` or `Forfeit` (rows with other statuses are skipped).
- Date header rows (e.g. `"Monday January 6"`) are ignored automatically.
- For overtime games the row should be: `Game,Home,HomeScore,OT,AwayScore,Away,...,Completed`

## Team Logos

Place PNG logo files in the `logos/` directory. The filename for each team is
configured in `team_config.py`. Placeholder logos are included; replace them
with real logos for production use. An `ehl_logo.png` in the same directory is
used for the header.

## Project Structure

```
├── app.py               # Flask web app (upload schedule → download image)
├── generate_image.py    # Image generator (Pillow)
├── team_config.py       # Team colors and logo filename mapping
├── power rankings       # Ranking engine (schedule parser + scoring + xlsx support)
├── logos/               # Team logo PNGs + ehl_logo.png
├── templates/
│   ├── index.html       # Upload page
│   └── results.html     # Results + image preview page
└── requirements.txt
```