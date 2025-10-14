import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import json

BASE_URL = "https://www.pokewiki.de"

def get_episode_links():
    url = f"{BASE_URL}/Anime-Episodenliste"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    
    episodes = {}
    valid_prefixes = ["EP", "AG", "DP", "BW", "XY", "SM", "PM"]  # alle gültigen Präfixe
    
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

def get_wichtige_ereignisse(ep_url):
    r = requests.get(ep_url)
    soup = BeautifulSoup(r.content, "html.parser")
    events = []
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

def main():
    episodes = get_episode_links()
    episode_events = {}
    
    print(f"Gefundene Episoden: {len(episodes)}")
    
    # Multithreading für schnellere Requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_wichtige_ereignisse, url): ep for ep, url in episodes.items()}
        for future in futures:
            ep = futures[future]
            try:
                events = future.result()
                episode_events[ep] = events
            except Exception as e:
                print(f"Fehler bei Episode {ep}: {e}")
    
    # Ergebnisse als JSON speichern
    with open("pokemon_episodes.json", "w", encoding="utf-8") as f:
        json.dump(episode_events, f, ensure_ascii=False, indent=4)
    
    print("Alle Ergebnisse wurden in 'pokemon_episodes.json' gespeichert.")

if __name__ == "__main__":
    main()
