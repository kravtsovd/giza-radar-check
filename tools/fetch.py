"""Download the public Capella scenes and verify each byte count and SHA-256."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from urllib.request import urlopen

MANIFEST = Path(__file__).resolve().parents[1] / "data/scenes.json"


def verify(path, spec):
    if path.stat().st_size != spec["bytes"]:
        raise ValueError(f"Wrong size: {path}")
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != spec["sha256"]:
            raise ValueError(f"Wrong SHA-256: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    for scene in json.loads(MANIFEST.read_text()):
        for spec in scene["files"]:
            path = args.directory / spec["name"]
            if args.metadata_only and path.suffix != ".json":
                continue
            if path.exists() or args.verify_only:
                verify(path, spec)
            else:
                temp = path.with_suffix(path.suffix + ".part")
                with urlopen(spec["url"], timeout=120) as src, temp.open("wb") as dst:
                    shutil.copyfileobj(src, dst, length=4 * 1024 * 1024)
                verify(temp, spec)
                temp.replace(path)
            print(f"Verified {path.name}")


if __name__ == "__main__":
    main()
