import json
from flask import Flask, render_template, request
from nashome.episodes.excel_utils import read_excel_with_colors
from nashome.episodes.episode_utils import parse_episode_to_season_ep, revert_episode_code
import os

EXCEL_FILE = "data/episodes/season_numbering.xlsx"
EVENTS_FILE = "data/episodes/episodes_events.json"
MOVIES_FILE = "data/episodes/movie_titles.json"

template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../episodes/templates"))
print("Template folder:", template_folder)
app = Flask(__name__, template_folder=template_folder)

# Excel und Farben laden
raw_data, colors = read_excel_with_colors(EXCEL_FILE)

# Daten für das Template vorbereiten
processed_data = []
current_season = None
for row in raw_data:
    new_row = []
    first_cell = row[0]
    if first_cell:
        current_season = str(first_cell).strip()
    # build row structure
    for col_idx, cell in enumerate(row):
        if col_idx == 0:
            new_row.append((str(cell) if cell else "", None, None))
        else:
            ep_num = cell if cell is not None else ""
            new_row.append((str(ep_num), current_season, ep_num))
    # prüfen ob Zeile (ab Spalte 1) komplett leer ist
    has_episode_content = any(
        (t[0] not in (None, "")) for t in new_row[1:]
    )
    if has_episode_content:
        processed_data.append(new_row)

# Events laden
with open(EVENTS_FILE, "r", encoding="utf-8") as f:
    EPISODE_EVENTS = json.load(f)

# Movie Titel / Inhalte laden (optional)
if os.path.exists(MOVIES_FILE):
    with open(MOVIES_FILE, "r", encoding="utf-8") as f:
        MOVIE_TITLES = json.load(f)
else:
    MOVIE_TITLES = {}

# Helfer um Pink zu erkennen (Fallback, falls exakte Hex nicht bekannt):
def is_pink(hex_color: str) -> bool:
    if not hex_color or not hex_color.startswith("#") or len(hex_color) != 7:
        return False
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
    except ValueError:
        return False
    # Heuristik: starkes Rot, moderates Blau, Grün deutlich geringer als Rot
    return (r > 200) and (b > 150) and (g < r - 30)

# Matrix gleicher Form wie colors für Pink-Flag
pink_flags = []
for row_colors in colors:
    pink_flags.append([is_pink(c.upper()) for c in row_colors])

@app.route("/")
def index():
    return render_template("episodes.html", data=processed_data, colors=colors, pink_flags=pink_flags)

@app.route("/get_code/<int:season>/<int:ep>")
def get_code(season, ep):
    try:
        episode_code = revert_episode_code(season, ep)
        value = EPISODE_EVENTS.get(episode_code)
        if value is None:
            return f"Kein Eintrag für {episode_code}", 404
        if isinstance(value, list):
            if len(value) == 0:
                formatted = f"Keine wichtigen Ereignisse"
            else:
                formatted = "<ul>" + "".join(f"<li>{item}</li>" for item in value) + "</ul>"
        else:
            formatted = str(value)
        return formatted, 200, {"Content-Type": "text/html; charset=utf-8"}
    except Exception as e:
        return f"Fehler: {str(e)}", 400

@app.route("/get_movie/<path:movie_key>")
def get_movie(movie_key):
    # movie_key kann aus der Tabellenzelle stammen; trimmen
    key = f"M{int(movie_key.strip()):02d}"
    print(key)
    if not key:
        return "Kein Movie-Key", 404
    value = MOVIE_TITLES.get(key)
    if value is None:
        return f"Kein Film-Eintrag für {key}", 404
    if isinstance(value, list):
        formatted = "<ul>" + "".join(f"<li>{item}</li>" for item in value) + "</ul>"
    else:
        formatted = str(value)
    return formatted, 200, {"Content-Type": "text/html; charset=utf-8"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
