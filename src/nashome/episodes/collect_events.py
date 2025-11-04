import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time
import os
import argparse
from typing import Dict, List

BASE_URL = "https://www.pokewiki.de"

def get_episode_links():
    url = f"{BASE_URL}/Anime-Episodenliste"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    
    episodes = {}
    # Reihenfolge beibehalten (Historie). 'HZ' für die Horizons Serie ergänzen.
    valid_prefixes = ["EP", "AG", "DP", "BW", "XY", "SM", "PM", "HZ"]  # alle gültigen Präfixe inkl. Horizons
    
    # Jede Episode hat einen Link im Episoden-Div
    for a in soup.select(".episodenliste a"):
        href = a.get("href")
        text = a.get_text(strip=True)
        # Filter für Episoden-Links
        if href and not href.startswith("/Datei:"):
            # Episode-Nummer aus vorherigem div, das z.B. EP001, AG001, etc. enthält
            prev_div = a.find_previous(string=lambda s: s and any(s.startswith(p) for p in valid_prefixes))
            if prev_div:
                ep_num = prev_div.strip()  # komplettes Präfix + Zahl
                episodes[ep_num] = BASE_URL + href
    return episodes

def get_wichtige_ereignisse(ep_url, session: requests.Session):
    r = session.get(ep_url, timeout=20)
    soup = BeautifulSoup(r.content, "html.parser")
    events = []
    # Episodentitel extrahieren und als ersten Eintrag hinzufügen
    title = extract_episode_title(soup)
    if title:
        events.append(title)
    section = soup.find("span", id="Wichtige_Ereignisse")
    if section:
        headline = section.find_parent(["h2","h3"])
        for sibling in headline.find_next_siblings():
            if sibling.name in ["h2","h3"]:
                break
            if sibling.name in ["ul","ol"]:
                for li in sibling.find_all("li"):
                    text = li.get_text(separator=" ", strip=True)
                    events.append(text)
            elif sibling.name == "p":
                text = sibling.get_text(separator=" ", strip=True)
                if text:
                    events.append(text)
    # Sicherstellen, dass zwischen Wörtern Leerzeichen stehen
    events = [e.replace("\xa0", " ") for e in events]
    return events

def extract_episode_title(soup: BeautifulSoup) -> str:
    """Versucht den deutschen Episodentitel zu ermitteln.

    Reihenfolge der Heuristiken:
    1. Infobox (Tabelle) mit einer Zeile, die 'Deutscher Titel' enthält.
    2. Hauptüberschrift (h1) – entfernt dabei führende Episoden-Codes wie EP001, AG001 etc.
    3. Fallback: leerer String
    """
    # 1. Infobox durchsuchen
    infobox = soup.find("table", class_=lambda c: c and "infobox" in c)
    if infobox:
        for row in infobox.find_all("tr"):
            header = row.find(["th","td"])
            if header and "Deutscher Titel" in header.get_text():
                # Nächste Zelle könnte der Titel sein
                cells = row.find_all("td")
                if len(cells) >= 1:
                    candidate = cells[-1].get_text(separator=" ", strip=True)
                    cleaned = clean_title(candidate)
                    if cleaned:
                        return cleaned
    # 2. h1 Titel
    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(separator=" ", strip=True)
        cleaned = clean_title(text)
        if cleaned:
            return cleaned
    return ""

def clean_title(title: str) -> str:
    """Normalisiert den Titel: NBSP -> Space, verschiedene Gedankenstriche vereinheitlichen,
    Episodencode (z.B. EP001) entfernen, trimmen."""
    if not title:
        return ""
    import re
    t = title.replace("\xa0", " ")
    # Episodencode am Anfang entfernen (EP/AG/DP/BW/XY/SM/PM + 3 Ziffern optionaler Zusatz)
    t = re.sub(r'^(EP|AG|DP|BW|XY|SM|PM)\s*0*\d+\s*[-–—:]\s*', '', t, flags=re.IGNORECASE)
    # Mehrfache Spaces
    t = re.sub(r'\s+', ' ', t)
    # Vereinheitliche Bindestriche um zu ' - '
    t = t.replace(' – ', ' - ').replace(' — ', ' - ').replace(' –', ' -').replace('—', '-').replace('–', '-')
    t = re.sub(r'\s*-\s*', ' - ', t)
    return t.strip()

def build_session() -> requests.Session:
    """Erstellt eine Requests-Session mit Retry-Strategie (inkl. Backoff)."""
    session = requests.Session()
    retries = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1.2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; EpisodeScraper/1.0; +https://www.example.com/bot)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return session

def load_existing(path: str) -> Dict[str, List[str]]:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warnung: Konnte bestehende Datei nicht laden ({e}), starte neu.")
    return {}

def save_json(path: str, data: Dict[str, List[str]]):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(tmp_path, path)

def main():
    parser = argparse.ArgumentParser(description="Scrape wichtige Ereignisse aus Pokémon Episoden (Pokéwiki)")
    parser.add_argument("--output", "-o", default="pokemon_episodes.json", help="Zieldatei für JSON (default: pokemon_episodes.json)")
    resume_group = parser.add_mutually_exclusive_group()
    resume_group.add_argument("--resume", dest="resume", action="store_true", help="Vorhandene Ergebnisse laden und fehlende Episoden ergänzen (Default)")
    resume_group.add_argument("--no-resume", dest="resume", action="store_false", help="Vorhandene Ergebnisse ignorieren und komplett neu sammeln")
    parser.set_defaults(resume=True)
    parser.add_argument("--workers", type=int, default=8, help="Anzahl paralleler Worker (Default 8)")
    parser.add_argument("--save-interval", type=int, default=20, help="Alle X neue Episoden Zwischenstand speichern (Default 20)")
    args = parser.parse_args()

    out_file = args.output
    episodes = get_episode_links()
    total = len(episodes)
    print(f"Gefundene Episoden: {total}")

    if args.resume:
        episode_events = load_existing(out_file)
        already = len(episode_events)
        if already:
            print(f"Resume aktiv: {already} Episoden bereits vorhanden – überspringe diese.")
    else:
        episode_events = {}
        print("Resume deaktiviert: beginne vollständigen Neuaufbau.")

    # Filter: nur Episoden ohne gespeicherte Events
    remaining_items = {ep: url for ep, url in episodes.items() if ep not in episode_events}
    print(f"Verbleibend zu laden: {len(remaining_items)}")

    if not remaining_items:
        print("Nichts zu tun – alle Episoden bereits vorhanden.")
        return

    session = build_session()

    start_time = time.time()
    errors = {}

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {executor.submit(fetch_with_retry, ep, url, session): ep for ep, url in remaining_items.items()}
        for i, future in enumerate(as_completed(future_map), 1):
            ep = future_map[future]
            try:
                events = future.result()
                episode_events[ep] = events
            except Exception as e:
                errors[ep] = str(e)
                print(f"Fehler bei Episode {ep}: {e}")
            # Inkrementell speichern
            if i % args.save_interval == 0:
                save_json(out_file, episode_events)
                elapsed = time.time() - start_time
                print(f"Progress: {i}/{len(remaining_items)} neu, Gesamt {len(episode_events)}/{total} | {elapsed:.1f}s")
        # finaler Save
        save_json(out_file, episode_events)

    print(f"Alle Ergebnisse wurden in '{out_file}' gespeichert. Gesamt: {len(episode_events)} Episoden.")
    if errors:
        print(f"Episoden mit Fehlern ({len(errors)}): {', '.join(sorted(errors.keys()))}")

def fetch_with_retry(ep: str, url: str, session: requests.Session) -> List[str]:
    """Ruft Ereignisse ab; zusätzliche Retry-Schicht für nicht-statusbezogene Fehler (z.B. SSL)."""
    attempts = 0
    last_exc = None
    while attempts < 5:
        try:
            return get_wichtige_ereignisse(url, session)
        except Exception as e:
            last_exc = e
            attempts += 1
            sleep_time = 1.5 * attempts
            print(f"Retry {attempts}/5 für {ep} in {sleep_time:.1f}s wegen: {e}")
            time.sleep(sleep_time)
    raise last_exc

if __name__ == "__main__":
    main()
