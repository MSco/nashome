import json
from flask import Flask, render_template, request
from nashome.episodes.excel_utils import read_excel_with_colors
from nashome.episodes.episode_utils import parse_episode_to_season_ep, revert_episode_code
import os

EXCEL_FILE = "data/episodes/season_numbering.xlsx"
EVENTS_FILE = "data/episodes/episodes_events.json"

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
    for col_idx, cell in enumerate(row):
        if col_idx == 0:
            new_row.append((str(cell) if cell else "", None, None))
        else:
            ep_num = cell if cell is not None else ""
            new_row.append((str(ep_num), current_season, ep_num))
    processed_data.append(new_row)

# Events laden
with open(EVENTS_FILE, "r", encoding="utf-8") as f:
    EPISODE_EVENTS = json.load(f)

@app.route("/")
def index():
    return render_template("episodes.html", data=processed_data, colors=colors)

@app.route("/get_code/<int:season>/<int:ep>")
def get_code(season, ep):
    try:
        episode_code = revert_episode_code(season, ep)
        value = EPISODE_EVENTS.get(episode_code)
        if value is None:
            return f"Kein Eintrag für {episode_code}", 404
        if isinstance(value, list):
            formatted = "<ul>" + "".join(f"<li>{item}</li>" for item in value) + "</ul>"
        else:
            formatted = str(value)
        return formatted, 200, {"Content-Type": "text/html; charset=utf-8"}
    except Exception as e:
        return f"Fehler: {str(e)}", 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
