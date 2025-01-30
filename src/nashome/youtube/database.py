from pathlib import Path
import json

from nashome.youtube.constants import STORED_VIDEOS_FILENAME

def read_stored_videos(outdir:Path|str) -> list[str]:
    stored_videos_path = Path(outdir) / STORED_VIDEOS_FILENAME
    if not stored_videos_path.exists():
        return []
    return json.load(open(stored_videos_path, 'r'))

def write_stored_videos(stored_videos:list[str], outpath:Path|str) -> None:
    json.dump(stored_videos, open(outpath, 'w'))