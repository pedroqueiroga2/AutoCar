from pathlib import Path

def list_mp4(folder: str):
    p = Path(folder)
    return [str(x.resolve()) for x in p.glob("*.mp4") if x.is_file()]