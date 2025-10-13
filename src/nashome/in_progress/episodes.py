from flask import Flask, render_template_string
from openpyxl import load_workbook
from openpyxl.styles.colors import COLOR_INDEX
import xml.etree.ElementTree as ET

app = Flask(__name__)

EXCEL_FILE = "data/episodes/season_numbering.xlsx"

def hex_to_rgb_tuple(hexstr: str):
    hexstr = hexstr.strip("#")
    if len(hexstr) == 6:
        return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))
    raise ValueError("Ungültiges Hex-Format")

def rgb_tuple_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(
        max(0, min(255, int(round(rgb[0])))),
        max(0, min(255, int(round(rgb[1])))),
        max(0, min(255, int(round(rgb[2]))))
    )

def apply_tint(hex_color: str, tint: float) -> str:
    try:
        rgb = hex_to_rgb_tuple(hex_color)
    except Exception:
        return hex_color
    if tint is None or tint == 0:
        return rgb_tuple_to_hex(rgb)
    out = []
    for comp in rgb:
        if tint < 0:
            val = comp * (1.0 + tint)
        else:
            val = comp * (1.0 - tint) + 255.0 * tint
        out.append(max(0, min(255, val)))
    return rgb_tuple_to_hex(tuple(out))

def parse_theme_colors_from_workbook(wb):
    """Liest tatsächliche Theme-Farben aus dem Workbook."""
    theme_map = {}
    loaded_theme = getattr(wb, "loaded_theme", None)
    if not loaded_theme:
        return theme_map
    try:
        root = ET.fromstring(loaded_theme)
        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        clr_scheme = root.find(".//a:clrScheme", ns)
        if clr_scheme is None:
            return theme_map

        for child in clr_scheme:
            tag_name = child.tag.split("}")[-1]
            srgb = child.find(".//a:srgbClr", ns)
            if srgb is not None and "val" in srgb.attrib:
                theme_map[tag_name] = f"#{srgb.attrib['val']}"
            else:
                sysclr = child.find(".//a:sysClr", ns)
                if sysclr is not None and "lastClr" in sysclr.attrib:
                    theme_map[tag_name] = f"#{sysclr.attrib['lastClr']}"
        print("🎨 Theme-Farben aus Excel:", theme_map)
        return theme_map
    except Exception as e:
        print("⚠️ Fehler beim Parsen des Theme-XML:", e)
        return theme_map

def excel_color_to_hex(wb, color_obj):
    """Konvertiert openpyxl-Farbobjekt in Hex-Farbwert (#RRGGBB)."""
    fallback = "#FFFFFF"
    if color_obj is None:
        return fallback

    rgb_attr = getattr(color_obj, "rgb", None)

    # Manchmal ist color_obj.rgb kein String
    if not isinstance(rgb_attr, str):
        rgb_attr = None

    # direkter RGB/ARGB-Wert
    if rgb_attr:
        rgb_attr = rgb_attr.strip()
        # Entferne Alpha-Kanal, falls vorhanden
        if len(rgb_attr) == 8:
            rgb_attr = rgb_attr[2:]  # AARRGGBB → RRGGBB
        if not rgb_attr.startswith("#"):
            rgb_attr = "#" + rgb_attr
        return rgb_attr.upper()

    # indexed color
    idx = getattr(color_obj, "indexed", None)
    if idx is not None:
        try:
            val = COLOR_INDEX[int(idx)]
            if isinstance(val, str):
                if len(val) == 8:
                    val = val[2:]
                return f"#{val.upper()}"
        except Exception:
            pass

    # theme color
    theme = getattr(color_obj, "theme", None)
    tint = getattr(color_obj, "tint", None)
    if theme is not None:
        if not hasattr(wb, "_theme_color_map_cache"):
            theme_colors = parse_theme_colors_from_workbook(wb)
            ordered_keys = [
                "lt1", "dk1", "lt2", "dk2",
                "accent1", "accent2", "accent3",
                "accent4", "accent5", "accent6"
            ]
            wb._theme_color_map_cache = [
                theme_colors.get(k) for k in ordered_keys
            ]
        theme_list = getattr(wb, "_theme_color_map_cache", [])
        try:
            idx = int(theme)
            if 0 <= idx < len(theme_list):
                base = theme_list[idx]
                if base:
                    if tint:
                        return apply_tint(base, tint)
                    return base
        except Exception:
            pass

    return fallback


def get_cell_color(wb, cell):
    """Bestimmt die tatsächlich sichtbare Farbe einer Zelle."""
    fill = cell.fill
    if not fill:
        return "#FFFFFF"

    color = None

    # Nur "solid" pattern wirklich einfärben, Rest = weiß
    if fill.patternType == "solid":
        color = excel_color_to_hex(wb, fill.fgColor)
    else:
        color = excel_color_to_hex(wb, fill.bgColor)

    # Ungültige oder transparente Farben als weiß behandeln
    if (
        color in (None, "", "#000000", "#00000000", "#FF000000")
        or "None" in str(color)
        or color.upper().startswith("#00") and color.upper() not in ("#00FFFF", "#00FF00", "#0000FF")
    ):
        color = "#FFFFFF"

    # Debug-Ausgabe nur für Nicht-Weiß
    if color != "#FFFFFF":
        print(f"Zelle {cell.coordinate}: pattern={fill.patternType}, "
              f"fg={getattr(fill.fgColor, 'rgb', None)}, "
              f"bg={getattr(fill.bgColor, 'rgb', None)}, → {color}")

    return color


def read_excel_with_colors(filename, sheet_name=None, start_row=2, end_row=28):
    wb = load_workbook(filename, data_only=True)
    ws = wb[sheet_name] if sheet_name else wb.active

    data, colors = [], []
    for row in ws.iter_rows(min_row=start_row, max_row=end_row):
        row_data, row_colors = [], []
        for cell in row:
            row_data.append(cell.value)
            row_colors.append(get_cell_color(wb, cell))
        data.append(row_data)
        colors.append(row_colors)
    return data, colors


# Daten einlesen
data, colors = read_excel_with_colors(EXCEL_FILE)

# HTML-Template mit angepasster Darstellung

html_template = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Season Numbering Tabelle</title>
<style>
/* Desktop bleibt wie bisher */
table {
    border-collapse: collapse;
    width: 100%;
}
td {
    border: 1px solid #999;
    padding: 2px;
    text-align: center;
    font-size: 11px;
}

/* Mobile-Layout */
@media (max-width: 600px) {
    table, thead, tbody, th, td, tr {
        display: block;
    }

    tr {
        margin-bottom: 8px; /* Abstand zwischen den „Karten“ */
        border: 1px solid #999; /* Linie um die gesamte „Karte" */
        border-radius: 4px;
        padding: 4px;
    }

    td {
        display: flex;
        justify-content: space-between;
        padding: 4px;
        border: none; /* einzelne Zelllinien entfernen */
        border-bottom: 1px solid #ddd; /* Linie zwischen Werten */
    }

    td:last-child {
        border-bottom: none; /* letzte Zelle ohne Linie */
    }

    td::before {
        content: attr(data-label);
        font-weight: bold;
    }
}
</style>

<script>
function showPopup() { alert("Hallo"); }
</script>
</head>
<body>
<h2>Season Numbering Übersicht</h2>
<table>
{% for r in range(data|length) %}
        {% set row_data = data[r] %}
        {% set row_colors = colors[r] %}

        {# Erste Zeile: Spalten A & B + erste 16 ab Spalte C (Index 2–17) #}
        <tr>
            {% for c in range(0,2) %}
                <td class="{{ 'col-b' if c == 1 else 'small' }}"
                        style="background-color: {{ row_colors[c] }};"
                        onclick="showPopup()">
                    {{ row_data[c] if row_data[c] is not none else "" }}
                </td>
            {% endfor %}
            {% set end_index = 18 if row_data|length > 18 else row_data|length %}
            {% for c in range(2, end_index) %}
                <td class="small"
                        style="background-color: {{ row_colors[c] }};"
                        onclick="showPopup()">
                    {{ row_data[c] if row_data[c] is not none else "" }}
                </td>
            {% endfor %}
        </tr>

        {# Weitere Blöcke ab Spalte 18 in 16er-Chunks #}
        {% for start in range(18, row_data|length, 16) %}
            <tr>
                <td></td>
                <td></td>
                {% for c in range(start, start + 16) %}
                    {% if c < row_data|length %}
                        <td class="small"
                                style="background-color: {{ row_colors[c] }};"
                                onclick="showPopup()">
                            {{ row_data[c] if row_data[c] is not none else "" }}
                        </td>
                    {% endif %}
                {% endfor %}
            </tr>
        {% endfor %}

{% endfor %}
</table>
</body>
</html>
"""




@app.route("/")
def index():
    return render_template_string(html_template, data=data, colors=colors)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
