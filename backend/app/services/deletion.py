from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
import shutil


def safe_delete(paths: list[str], base_folder: str) -> tuple[list[str], str]:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    trash_folder = Path(base_folder) / ".photomorph_trash" / stamp
    trash_folder.mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    for source in paths:
        src = Path(source)
        if not src.exists():
            continue
        target = trash_folder / src.name
        suffix = 1
        while target.exists():
            target = trash_folder / f"{src.stem}_{suffix}{src.suffix}"
            suffix += 1
        shutil.move(str(src), str(target))
        moved.append(str(src))

    return moved, str(trash_folder)
