from __future__ import annotations

from collections import defaultdict
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import ImageEntry, ScanSession, SimilarityGroup
from .schemas import (
    BatchDecisionUpdate,
    DeleteMarkedResponse,
    ScanConfig,
    SessionDetail,
    SessionSummary,
    SimilarityGroupResult,
    ImageResult,
)
from .services.deletion import safe_delete
from .services.recommendations import recommend_keep_delete
from .services.scanner import discover_images, extract_features
from .services.similarity import SimilarityConfig, group_similar_images

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PhotoMorph Deduplicator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/scans", response_model=SessionDetail)
def start_scan(config: ScanConfig, db: Session = Depends(get_db)) -> SessionDetail:
    try:
        file_paths = discover_images(config.folder_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    features = extract_features(file_paths)
    groups = group_similar_images(
        features,
        SimilarityConfig(
            overall_similarity=config.overall_similarity,
            face_similarity=config.face_similarity,
            strict_mode=config.strict_mode,
        ),
    )

    session = ScanSession(
        folder_path=config.folder_path,
        config=config.model_dump(),
        total_images=len(features),
    )
    db.add(session)
    db.flush()

    image_by_path: dict[str, ImageEntry] = {}
    for feature in features:
        image = ImageEntry(
            session_id=session.id,
            group_index=None,
            file_path=feature.file_path,
            phash=feature.phash,
            width=feature.width,
            height=feature.height,
            sharpness=feature.sharpness,
            exposure=feature.exposure,
            face_count=feature.face_count,
            expression_score=feature.expression_score,
            semantic_embedding=feature.semantic_embedding,
            face_embedding=feature.face_embedding,
            recommended_delete=False,
            user_marked_delete=False,
        )
        db.add(image)
        db.flush()
        image_by_path[feature.file_path] = image

    for group_index, feature_group in enumerate(groups, start=1):
        keep_file, delete_files = recommend_keep_delete(feature_group)
        keep_image_id = image_by_path[keep_file].id if keep_file else None

        group_row = SimilarityGroup(
            session_id=session.id,
            group_index=group_index,
            keep_image_id=keep_image_id,
        )
        db.add(group_row)

        for feature in feature_group:
            row = image_by_path[feature.file_path]
            row.group_index = group_index
            row.recommended_delete = feature.file_path in delete_files
            row.user_marked_delete = row.recommended_delete

    db.commit()
    db.refresh(session)

    return _session_detail(db, session.id)


@app.get("/api/sessions", response_model=list[SessionSummary])
def list_sessions(db: Session = Depends(get_db)) -> list[SessionSummary]:
    sessions = db.query(ScanSession).order_by(ScanSession.created_at.desc()).all()
    return [
        SessionSummary(
            id=s.id,
            folder_path=s.folder_path,
            created_at=s.created_at,
            total_images=s.total_images,
            group_count=len(s.groups),
        )
        for s in sessions
    ]


@app.get("/api/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: int, db: Session = Depends(get_db)) -> SessionDetail:
    return _session_detail(db, session_id)


@app.post("/api/sessions/{session_id}/decisions", response_model=SessionDetail)
def update_decisions(session_id: int, payload: BatchDecisionUpdate, db: Session = Depends(get_db)) -> SessionDetail:
    session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    ids = {item.image_id for item in payload.decisions}
    images = (
        db.query(ImageEntry)
        .filter(ImageEntry.session_id == session_id, ImageEntry.id.in_(ids))
        .all()
    )
    image_map = {img.id: img for img in images}

    for decision in payload.decisions:
        image = image_map.get(decision.image_id)
        if image:
            image.user_marked_delete = decision.marked_for_delete

    db.commit()
    return _session_detail(db, session_id)


@app.post("/api/sessions/{session_id}/delete-marked", response_model=DeleteMarkedResponse)
def delete_marked(session_id: int, db: Session = Depends(get_db)) -> DeleteMarkedResponse:
    session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    marked = (
        db.query(ImageEntry)
        .filter(ImageEntry.session_id == session_id, ImageEntry.user_marked_delete.is_(True))
        .all()
    )
    paths = [img.file_path for img in marked]
    moved, trash_folder = safe_delete(paths, session.folder_path)

    return DeleteMarkedResponse(moved=moved, trash_folder=trash_folder)


def _session_detail(db: Session, session_id: int) -> SessionDetail:
    session = db.query(ScanSession).filter(ScanSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    group_rows = db.query(SimilarityGroup).filter(SimilarityGroup.session_id == session_id).all()
    images = db.query(ImageEntry).filter(ImageEntry.session_id == session_id).all()
    group_buckets: dict[int, list[ImageEntry]] = defaultdict(list)
    for image in images:
        if image.group_index is not None:
            group_buckets[image.group_index].append(image)

    similarity_groups: list[SimilarityGroupResult] = []
    for group in sorted(group_rows, key=lambda g: g.group_index):
        members = group_buckets[group.group_index]
        unique_members = {m.id: m for m in members}.values()
        similarity_groups.append(
            SimilarityGroupResult(
                group_id=group.group_index,
                keep_image_id=group.keep_image_id,
                images=[ImageResult.model_validate(m) for m in unique_members],
            )
        )

    return SessionDetail(
        id=session.id,
        folder_path=session.folder_path,
        created_at=session.created_at,
        total_images=session.total_images,
        config=session.config,
        groups=similarity_groups,
    )
