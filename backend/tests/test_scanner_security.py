from pathlib import Path

import pytest

from app.services.scanner import discover_images


def test_discover_images_rejects_outside_allowed_root(tmp_path: Path, monkeypatch) -> None:
    inside = tmp_path / "inside"
    outside = tmp_path.parent / "outside"
    inside.mkdir(exist_ok=True)
    outside.mkdir(exist_ok=True)

    monkeypatch.setenv("PHOTOMORPH_SCAN_ROOT", str(inside))

    with pytest.raises(ValueError):
        discover_images(str(outside))
