from pathlib import Path
import json

from nashome.utils.constants import STORED_VIDEOS_FILENAME

def read_stored_videos(outdir:Path|str) -> list[str]:
    stored_videos_path = Path(outdir) / STORED_VIDEOS_FILENAME
    if not stored_videos_path.exists():
        return []
    return json.load(open(stored_videos_path, 'r'))

def write_stored_videos(stored_videos:list[str], outpath:Path|str) -> None:
    parent_dir = Path(outpath).parent
    if not parent_dir.exists():
        parent_dir.mkdir(parents=True, exist_ok=True)
    json.dump(stored_videos, open(outpath, 'w'))