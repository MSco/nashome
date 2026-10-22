#!/usr/bin/env python
import argparse
import difflib
import io
import math
import re
from pathlib import Path

import requests
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from unidecode import unidecode

SUCCESS = 0
ERROR = 1

FOOTYLOGOS_URL = "https://www.footylogos.com"
SEARCH_INDEX_URL = f"{FOOTYLOGOS_URL}/data/search-index.json"
LOGO_KINDS = ("logo", "national-team")
ASSETS_URL = "https://assets.footylogos.com"
DAZN_LOGO_URL = f"{FOOTYLOGOS_URL}/brands/assets/dazn-logo-white-footylogos.png"
BUNDESLIGA_LOGO_URL = f"{ASSETS_URL}/logos/bundesliga-germany/bundesliga-germany-logo-footylogos.png"
CHAMPIONS_LEAGUE_LOGO_URL = f"{ASSETS_URL}/logos/uefa-champions-league/uefa-champions-league-logo-footylogos.png"
# footylogos uses english names (labels without parenthesized additions), map them to the common german names
GERMAN_NAMES = {
    # germany
    "Bayern Munich": "FC Bayern München",
    "1860 Munich": "TSV 1860 München",
    "FC Nurnberg": "1. FC Nürnberg",
    "Fortuna Koln": "Fortuna Köln",
    "Eimsbutteler TV": "Eimsbütteler TV",
    "Wurzburger Kickers": "Würzburger Kickers",
    # italy
    "AC Milan": "AC Mailand",
    "Inter Milan": "Inter Mailand",
    "Juventus": "Juventus Turin",
    "Torino": "FC Turin",
    "AS Roma": "AS Rom",
    "Lazio": "Lazio Rom",
    "Napoli": "SSC Neapel",
    "Fiorentina": "AC Florenz",
    "Atalanta": "Atalanta Bergamo",
    "Bologna": "FC Bologna",
    "Genoa": "CFC Genua",
    "UC Sampdoria": "Sampdoria Genua",
    # spain
    "Atletico Madrid": "Atlético Madrid",
    "Athletic Club Bilbao": "Athletic Bilbao",
    "Sevilla FC": "FC Sevilla",
    "Real Betis Balompié": "Betis Sevilla",
    "Valencia CF": "FC Valencia",
    "Villarreal CF": "FC Villarreal",
    "RCD Espanyol Barcelona": "Espanyol Barcelona",
    "Deportivo Alaves": "Deportivo Alavés",
    # portugal
    "SL Benfica": "Benfica Lissabon",
    "Sporting CP": "Sporting Lissabon",
    # france
    "Olympique Lyonnais": "Olympique Lyon",
    "Olympique de Marseille": "Olympique Marseille",
    # rest of europe
    "Ajax": "Ajax Amsterdam",
    "Feyenoord": "Feyenoord Rotterdam",
    "Club Brugge": "FC Brügge",
    "Celtic": "Celtic Glasgow",
    "Rangers": "Glasgow Rangers",
    "FC Copenhagen": "FC Kopenhagen",
    "Malmo FF": "Malmö FF",
    "Galatasaray": "Galatasaray Istanbul",
    "Fenerbahçe": "Fenerbahçe Istanbul",
    "Beşiktaş": "Beşiktaş Istanbul",
    "Olympiacos": "Olympiakos Piräus",
    "Panathinaikos": "Panathinaikos Athen",
    "AEK Athens": "AEK Athen",
    "Sparta Praha": "Sparta Prag",
    "Slavia Praha": "Slavia Prag",
    "Legia Warszawa": "Legia Warschau",
    "Ferencvaros TC": "Ferencváros Budapest",
    "GNK Dinamo Zagreb": "Dinamo Zagreb",
    "Red Star Belgrade": "Roter Stern Belgrad",
    "Shakhtar Donetsk": "Schachtar Donezk",
    "Dynamo Kyiv": "Dynamo Kiew",
    "CSKA Moscow": "ZSKA Moskau",
    "Spartak Moscow": "Spartak Moskau",
    "Lokomotiv Moscow": "Lokomotive Moskau",
    "Dynamo Moscow": "Dynamo Moskau",
    "Zenit Saint Petersburg": "Zenit St. Petersburg",
}
DEFAULT_TEMPLATE = Path(__file__).resolve().parents[3] / "data" / "stadium.jpg"
# the template is cropped to this aspect ratio (width / height)
ASPECT_RATIO = 10 / 9
# at least this many matchup cards are placed side by side
MIN_COLUMNS = 2
# layout as fractions of the width and height of the cropped template
MARGIN = 0.04
# header logos grow from LOGO_HEIGHT up to MAX_LOGO_HEIGHT if the cards leave free space
LOGO_HEIGHT = 0.12
MAX_LOGO_HEIGHT = 0.28
# horizontal gap between the header logos as fraction of the logo size
LOGO_GAP = 0.8
MAX_CARD_WIDTH = 0.9
# card content heights as fractions of the card width
CARD_PAD, CARD_LOGO, CARD_GAP, CARD_NAME, CARD_KICKOFF = 0.06, 0.3, 0.045, 0.05, 0.075


def main() -> int:
    # argument parsing
    parser = argparse.ArgumentParser(description="Create a football stadium image showing the crests of the given clubs as matchups.\n"
                                                 "Crests are taken from https://www.footylogos.com", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('clubs', type=str, nargs='+', help="Club names (even number). Consecutive clubs are paired, e.g. 'Bayern München' 'Borussia Dortmund'")
    parser.add_argument('-o', '--output', type=Path, default=Path("stadium.png"), help="Output image file (default: stadium.png)")
    parser.add_argument('-s', '--subtitle', type=str, default="Alle Spiele. Live. Auf DAZN.", help="Subtitle shown at the top between the logos (default: '%(default)s', '' for none)")
    parser.add_argument('-d', '--date', type=str, default="", help="Optional date shown above the subtitle, e.g. 25.10.")
    parser.add_argument('-k', '--kickoff', type=str, nargs='+', default=[], help="Kickoff times, either one for all matchups or one per matchup, e.g. 15:30 17:30")
    parser.add_argument('-cl', '--champions-league', action='store_true', help="Show the Champions League logo instead of the Bundesliga logo")
    parser.add_argument('-t', '--template', type=Path, default=DEFAULT_TEMPLATE, help=f"Stadium background image (default: {DEFAULT_TEMPLATE})")
    args = parser.parse_args()

    if len(args.clubs) % 2 != 0:
        parser.error(f"the number of clubs must be even, got {len(args.clubs)}")
    if len(args.kickoff) not in (0, 1, len(args.clubs) // 2):
        parser.error(f"expected 1 or {len(args.clubs) // 2} kickoff times, got {len(args.kickoff)}")

    kickoffs = args.kickoff * (len(args.clubs) // 2) if len(args.kickoff) == 1 else args.kickoff
    return create_stadium(args.clubs, args.output, args.template, args.date, args.subtitle, kickoffs, args.champions_league)


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; nashome-create-stadium/1.0)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    })
    return session


def _normalize(name: str) -> str:
    name = unidecode(name).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", name).split())


def _german_name(label: str) -> str:
    label = re.sub(r"\s*\(.*?\)", "", label).strip()
    return GERMAN_NAMES.get(label, label)


def _load_logo_index(session: requests.Session) -> dict[str, dict]:
    """Return a mapping of normalized club names and slugs to footylogos search index entries."""
    r = session.get(SEARCH_INDEX_URL, timeout=30)
    r.raise_for_status()
    index = {}
    for entry in r.json():
        if entry.get("kind") not in LOGO_KINDS or not entry.get("href", "").startswith("/logos/"):
            continue
        slug = entry["href"].removeprefix("/logos/")
        index.setdefault(_normalize(entry["label"]), entry)
        index.setdefault(_normalize(_german_name(entry["label"])), entry)
        index.setdefault(_normalize(slug), entry)
    return index


def _find_club(name: str, index: dict[str, dict]) -> dict | None:
    query = _normalize(name)
    if query in index:
        return index[query]

    # query contained as whole words in a club name, prefer the shortest name
    contained = [key for key in index if f" {query} " in f" {key} "]
    if contained:
        return index[min(contained, key=len)]

    matches = difflib.get_close_matches(query, index.keys(), n=1, cutoff=0.6)
    return index[matches[0]] if matches else None


def _fetch_logo(entry: dict, session: requests.Session) -> Image.Image:
    """Download the primary PNG crest of a club."""
    candidates = []
    preview = entry.get("preview", "")
    if preview.endswith("-320.webp"):
        candidates.append(preview.replace("/previews/", "/logos/").removesuffix("-320.webp") + ".png")

    # fallback: scan the logo page for the primary png
    slug = entry["href"].removeprefix("/logos/")
    try:
        page = session.get(FOOTYLOGOS_URL + entry["href"], timeout=20).text
        candidates += re.findall(rf"https://assets\.footylogos\.com/logos/(?:{slug}/)?{slug}-logo-footylogos\.png", page)
    except requests.RequestException:
        pass

    for url in candidates:
        logo = _download_image(url, session)
        if logo is not None:
            return logo
    raise ValueError(f"No logo found for {entry['label']}")


def _download_image(url: str, session: requests.Session) -> Image.Image | None:
    r = session.get(url, timeout=20)
    if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    return None


def _whiten_dark(logo: Image.Image, threshold: int = 100) -> Image.Image:
    """Turn dark parts of a logo (e.g. black lettering) white so that it is readable on a dark background."""
    r, g, b, a = logo.split()
    dark = ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda v: 255 if v < threshold else 0)
    white = Image.new("RGB", logo.size, (255, 255, 255))
    rgb = Image.composite(white, logo.convert("RGB"), dark)
    rgb.putalpha(a)
    return rgb


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSansCondensed-Bold.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def _fit_font(draw: ImageDraw.ImageDraw, text: str, size: int, max_width: float) -> ImageFont.ImageFont:
    """Return the largest font not bigger than size in which text fits into max_width."""
    font = _font(size)
    while font.size > 8 and draw.textlength(text, font=font) > max_width:
        font = _font(font.size - 1)
    return font


def _draw_spaced_text(draw: ImageDraw.ImageDraw, center: tuple[float, float], text: str, font: ImageFont.ImageFont,
                      spacing: float, fill: tuple) -> None:
    """Draw horizontally centered text with additional letter spacing."""
    width = sum(draw.textlength(c, font=font) for c in text) + spacing * (len(text) - 1)
    x = center[0] - width / 2
    for c in text:
        draw.text((x, center[1]), c, font=font, fill=fill, anchor="lm")
        x += draw.textlength(c, font=font) + spacing


def _crop_aspect(img: Image.Image, aspect: float) -> Image.Image:
    """Crop the center of an image to the given aspect ratio (width / height)."""
    width, height = min(img.width, round(img.height * aspect)), min(img.height, round(img.width / aspect))
    left, top = (img.width - width) // 2, (img.height - height) // 2
    return img.crop((left, top, left + width, top + height))


def _darken_background(img: Image.Image) -> Image.Image:
    """Blur and darken the template, stronger at the top, so that header and cards stand out."""
    img = img.filter(ImageFilter.GaussianBlur(max(1, img.width // 1600)))
    overlay = Image.new("RGBA", img.size)
    draw = ImageDraw.Draw(overlay)
    for y in range(img.height):
        t = y / max(img.height - 1, 1)
        draw.line([(0, y), (img.width, y)], fill=(5, 5, 15, int(140 - 100 * t)))
    return Image.alpha_composite(img, overlay)


def _paste_logo(img: Image.Image, logo: Image.Image, center: tuple[int, int], size: int) -> None:
    logo = logo.copy()
    logo.thumbnail((size, size), Image.LANCZOS)
    x, y = center[0] - logo.width // 2, center[1] - logo.height // 2
    # drop shadow
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    alpha = logo.getchannel("A").point(lambda a: a * 0.6)
    offset = max(3, size // 25)
    shadow.paste((0, 0, 0, 255), (x + offset, y + offset), alpha)
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(offset)))
    img.alpha_composite(logo, (x, y))


def _subtitle_font(draw: ImageDraw.ImageDraw, text: str, size: int, max_width: float) -> ImageFont.ImageFont:
    # letter spacing adds about a quarter of the font size per character
    font = _font(size)
    while font.size > 8 and draw.textlength(text, font=font) + font.size * 0.25 * len(text) > max_width:
        font = _font(font.size - 1)
    return font


def _draw_date(draw: ImageDraw.ImageDraw, cx: float, y: float, date_text: str, font: ImageFont.ImageFont, render: bool) -> float:
    """Draw the date with its visible top at y and return its visible height."""
    bbox = draw.textbbox((cx, 0), date_text, font=font, anchor="mt")
    if render:
        draw.text((cx, y - bbox[1]), date_text, font=font, fill=(255, 255, 255), anchor="mt",
                  stroke_width=max(1, font.size // 40), stroke_fill=(255, 255, 255))
    return bbox[3] - bbox[1]


def _draw_header(img: Image.Image, size: int, date_text: str, subtitle: str, left_logo: Image.Image, right_logo: Image.Image,
                 render: bool = True) -> float:
    """Draw the logos with the given size side by side at the top, date and subtitle below, and return the header height.

    With render=False, nothing is drawn and only the height is computed.
    """
    draw = ImageDraw.Draw(img)
    top, margin, cx = img.height * MARGIN, img.width * MARGIN, img.width / 2
    if render:
        gap = size * LOGO_GAP
        for logo, x in ((left_logo, cx - gap / 2 - size / 2), (right_logo, cx + gap / 2 + size / 2)):
            _paste_logo(img, logo.crop(logo.getbbox()), (int(x), int(top + size / 2)), size)
        draw.line([(cx, top + size * 0.1), (cx, top + size * 0.9)], fill=(255, 255, 255), width=max(1, size // 60))

    y = top + size
    max_width = img.width - 2 * margin
    if date_text:
        y += size * 0.12
        y += _draw_date(draw, cx, y, date_text, _fit_font(draw, date_text, int(size * 0.42), max_width), render)
    text = subtitle.upper()
    if text:
        sub_font = _subtitle_font(draw, text, int(size * 0.15), max_width)
        y += sub_font.size * 0.7
        if render:
            _draw_spaced_text(draw, (cx, y + sub_font.size / 2), text, sub_font, sub_font.size * 0.25, (230, 230, 235))
        y += sub_font.size
    return y - top


def _card_aspect(with_kickoff: bool) -> float:
    height = 2 * CARD_PAD + CARD_LOGO + CARD_GAP + CARD_NAME
    if with_kickoff:
        height += CARD_GAP * 1.5 + CARD_KICKOFF
    return 1 / height


def _card_layout(n: int, w: float, h: float, gap: float, aspect: float, max_w: float) -> tuple[int, float, float]:
    """Return (columns, card width, card height) maximizing the card size for n cards in a w x h area."""
    best = (1, 0.0, 0.0)
    for cols in range(min(n, MIN_COLUMNS), n + 1):
        rows = math.ceil(n / cols)
        card_w = min((w - gap * (cols - 1)) / cols, (h - gap * (rows - 1)) / rows * aspect, max_w)
        if card_w > best[1]:
            best = (cols, card_w, card_w / aspect)
    return best


def _draw_card(img: Image.Image, pair: list[tuple[str, Image.Image]], kickoff: str | None, x0: float, y0: float, cw: float, ch: float) -> None:
    card = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([x0, y0, x0 + cw, y0 + ch], radius=cw * 0.04, fill=(10, 12, 25, 150),
                                           outline=(255, 255, 255, 110), width=max(1, int(cw / 250)))
    img.alpha_composite(card)

    draw = ImageDraw.Draw(img)
    logo_size = int(cw * CARD_LOGO)
    logo_y = y0 + cw * CARD_PAD + logo_size / 2
    name_y = logo_y + logo_size / 2 + cw * (CARD_GAP + CARD_NAME / 2)
    for (name, logo), x in zip(pair, (x0 + cw * 0.25, x0 + cw * 0.75)):
        _paste_logo(img, logo, (int(x), int(logo_y)), logo_size)
        name = name.upper()
        name_font = _fit_font(draw, name, int(cw * CARD_NAME), cw * 0.44)
        draw.text((x, name_y), name, font=name_font, fill=(255, 255, 255), anchor="mm")
    draw.text((x0 + cw / 2, logo_y), "VS.", font=_font(int(cw * 0.06)), fill=(255, 255, 255), anchor="mm")
    if kickoff:
        # separator line centered between the names and the kickoff time
        names_bottom = name_y + cw * CARD_NAME / 2
        kickoff_top = y0 + ch - cw * (CARD_PAD + CARD_KICKOFF * 0.75)
        line_y = (names_bottom + kickoff_top) / 2
        draw.line([(x0 + cw * CARD_PAD, line_y), (x0 + cw * (1 - CARD_PAD), line_y)], fill=(255, 255, 255), width=max(1, int(cw / 300)))
        draw.text((x0 + cw / 2, y0 + ch - cw * CARD_PAD), f"{kickoff} Uhr", font=_font(int(cw * CARD_KICKOFF)), fill=(255, 255, 255), anchor="ms")


def _cards_area(img: Image.Image, header_height: float) -> tuple[float, float, float, float]:
    """Return (left, top, right, bottom) of the area below a header with the given height."""
    margin_x, margin_y = img.width * MARGIN, img.height * MARGIN
    return margin_x, 2 * margin_y + header_height, img.width - margin_x, img.height - margin_y


def _layout(img: Image.Image, n_pairs: int, with_kickoff: bool, header: callable) -> tuple[int, float, tuple[int, float, float]]:
    """Return the header logo size, the header height and the card layout (columns, card width, card height).

    header(size) returns the header height for a logo size. Space the cards cannot use enlarges the header.
    """
    gap = img.width * 0.015
    aspect = _card_aspect(with_kickoff)
    max_card_width = img.height * MAX_CARD_WIDTH

    def cards(header_height: float) -> tuple[tuple[int, float, float], float]:
        left, top, right, bottom = _cards_area(img, header_height)
        layout = _card_layout(n_pairs, right - left, bottom - top, gap, aspect, max_card_width)
        rows = math.ceil(n_pairs / layout[0])
        return layout, (bottom - top) - (rows * layout[2] + (rows - 1) * gap)

    size = img.height * LOGO_HEIGHT
    height = header(int(size))
    _, free = cards(height)
    # the header height grows about linearly with the logo size; also keep both logos within the width
    size = int(min(size * (height + free) / height, img.height * MAX_LOGO_HEIGHT, img.width * 0.75 / (2 + LOGO_GAP)))
    height = header(size)
    return size, height, cards(height)[0]


def _draw_matchups(img: Image.Image, logos: list[tuple[str, Image.Image]], kickoffs: list[str], header_height: float,
                   layout: tuple[int, float, float]) -> None:
    left, top, right, bottom = _cards_area(img, header_height)
    pairs = [logos[i:i + 2] for i in range(0, len(logos), 2)]
    gap = img.width * 0.015
    cols, cw, ch = layout
    rows = math.ceil(len(pairs) / cols)
    # center the grid vertically in the available area
    grid_top = top + (bottom - top - rows * ch - (rows - 1) * gap) / 2

    for idx, pair in enumerate(pairs):
        row, col = divmod(idx, cols)
        # center the last row if it is not full
        cols_in_row = min(cols, len(pairs) - row * cols)
        row_width = cols_in_row * cw + (cols_in_row - 1) * gap
        x0 = (left + right - row_width) / 2 + col * (cw + gap)
        y0 = grid_top + row * (ch + gap)
        _draw_card(img, pair, kickoffs[idx] if kickoffs else None, x0, y0, cw, ch)


def create_stadium(clubs: list[str], output: Path, template: Path, date_text: str, subtitle: str, kickoffs: list[str],
                   champions_league: bool) -> int:
    if not template.is_file():
        print(f"Error: template {template} not found")
        return ERROR

    session = _build_session()
    try:
        index = _load_logo_index(session)
    except Exception as e:
        print(f"Error loading footylogos search index: {e}")
        return ERROR

    logos = []
    for club in clubs:
        entry = _find_club(club, index)
        if entry is None:
            suggestions = difflib.get_close_matches(_normalize(club), index.keys(), n=5, cutoff=0.4)
            print(f"Error: club '{club}' not found on footylogos.com" + (f", did you mean: {', '.join(suggestions)}?" if suggestions else ""))
            return ERROR
        name = _german_name(entry["label"])
        print(f"{club} -> {name} ({FOOTYLOGOS_URL}{entry['href']})")
        try:
            logos.append((name, _fetch_logo(entry, session)))
        except Exception as e:
            print(f"Error fetching logo of {club}: {e}")
            return ERROR

    competition_url = CHAMPIONS_LEAGUE_LOGO_URL if champions_league else BUNDESLIGA_LOGO_URL
    try:
        dazn_logo = _download_image(DAZN_LOGO_URL, session)
        competition_logo = _download_image(competition_url, session)
    except requests.RequestException as e:
        print(f"Error fetching header logos: {e}")
        return ERROR
    if dazn_logo is None or competition_logo is None:
        print(f"Error: could not download {DAZN_LOGO_URL if dazn_logo is None else competition_url}")
        return ERROR

    img = _darken_background(_crop_aspect(Image.open(template).convert("RGBA"), ASPECT_RATIO))
    competition_logo = _whiten_dark(competition_logo)

    def header(size: int, render: bool = False) -> float:
        return _draw_header(img, size, date_text, subtitle, dazn_logo, competition_logo, render)

    header_size, header_height, layout = _layout(img, len(logos) // 2, bool(kickoffs), header)
    header(header_size, render=True)
    _draw_matchups(img, logos, kickoffs, header_height, layout)

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() in (".jpg", ".jpeg"):
        img = img.convert("RGB")
    img.save(output)
    print(f"Wrote stadium image to {output}")
    return SUCCESS


if __name__ == "__main__":
    main()
