from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.database import SessionLocal
from app.models import ImageEntry, ScanSession, SimilarityGroup
from app.main import app


def _reset_db() -> None:
    db = SessionLocal()
    try:
        db.query(SimilarityGroup).delete()
        db.query(ImageEntry).delete()
        db.query(ScanSession).delete()
        db.commit()
    finally:
        db.close()


def test_scan_history_decision_and_delete_flow(tmp_path: Path) -> None:
    _reset_db()
    image_dir = tmp_path / "images"
    image_dir.mkdir()

    Image.new("RGB", (200, 200), color=(255, 0, 0)).save(image_dir / "a.jpg")
    Image.new("RGB", (200, 200), color=(254, 0, 0)).save(image_dir / "b.jpg")

    client = TestClient(app)

    scan = client.post(
        "/api/scans",
        json={
            "folder_path": str(image_dir),
            "overall_similarity": 0.75,
            "face_similarity": 0.5,
            "strict_mode": False,
        },
    )
    assert scan.status_code == 200
    detail = scan.json()
    assert detail["groups"]

    session_id = detail["id"]
    histories = client.get("/api/sessions")
    assert histories.status_code == 200
    assert any(item["id"] == session_id for item in histories.json())

    first_group = detail["groups"][0]
    target_image = first_group["images"][0]
    update = client.post(
        f"/api/sessions/{session_id}/decisions",
        json={"decisions": [{"image_id": target_image["id"], "marked_for_delete": True}]},
    )
    assert update.status_code == 200

    delete = client.post(f"/api/sessions/{session_id}/delete-marked")
    assert delete.status_code == 200
    payload = delete.json()
    assert "trash_folder" in payload
