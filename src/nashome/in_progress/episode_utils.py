import re
BLOCKS = [
    ("EP", 1, 82, 1),
    ("EP", 83, 118, 2),
    ("EP", 119, 159, 3),
    ("EP", 160, 211, 4),
    ("EP", 212, 276, 5),
    ("AG", 1, 40, 6),
    ("AG", 41, 92, 7),
    ("AG", 93, 145, 8),
    ("AG", 146, 192, 9),
    ("DP", 1, 52, 10),
    ("DP", 53, 104, 11),
    ("DP", 105, 157, 12),
    ("DP", 158, 191, 13),
    ("BW", 1, 48, 14),
    ("BW", 49, 97, 15),
    ("BW", 98, 142, 16),
    ("XY", 1, 49, 17),
    ("XY", 50, 93, 18),
    ("XY", 94, 140, 19),
    ("SM", 1, 43, 20),
    ("SM", 44, 92, 21),
    ("SM", 93, 146, 22),
    ("PM", 1, 48, 23),
    ("PM", 49, 90, 24),
    ("PM", 91, 147, 25),
]

def parse_episode_to_season_ep(code):
    if not code:
        return None, None
    code = str(code).upper().strip()
    m = re.match(r"([A-Z]+)(\d+)", code)
    if not m:
        return None, None
    prefix, num_str = m.groups()
    num = int(num_str)
    for pfx, start, end, season in BLOCKS:
        if prefix == pfx and start <= num <= end:
            return season, num - start + 1
    return None, None

def revert_episode_code(season: int, new_ep_num: int) -> str:
    for pfx, start, end, blk_season in BLOCKS:
        if blk_season == season:
            ep_num = start + new_ep_num - 1
            if ep_num > end:
                raise ValueError(f"Episodennummer {new_ep_num} überschreitet das Ende der Staffel {season}")
            return f"{pfx}{ep_num:03d}"
    raise ValueError(f"Keine passende Staffel für {season} gefunden.")
