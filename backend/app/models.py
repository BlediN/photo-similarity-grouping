from datetime import datetime, UTC
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class ScanSession(Base):
    __tablename__ = "scan_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    folder_path: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    status: Mapped[str] = mapped_column(String, default="completed")
    total_images: Mapped[int] = mapped_column(Integer, default=0)
    config: Mapped[dict] = mapped_column(JSON)

    images: Mapped[list["ImageEntry"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    groups: Mapped[list["SimilarityGroup"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class ImageEntry(Base):
    __tablename__ = "image_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("scan_sessions.id", ondelete="CASCADE"))
    group_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_path: Mapped[str] = mapped_column(String, unique=False, index=True)
    phash: Mapped[str] = mapped_column(String)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    sharpness: Mapped[float] = mapped_column(Float)
    exposure: Mapped[float] = mapped_column(Float)
    face_count: Mapped[int] = mapped_column(Integer, default=0)
    expression_score: Mapped[float] = mapped_column(Float, default=0.0)
    semantic_embedding: Mapped[list[float]] = mapped_column(JSON)
    face_embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    recommended_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    user_marked_delete: Mapped[bool] = mapped_column(Boolean, default=False)

    session: Mapped["ScanSession"] = relationship(back_populates="images")


class SimilarityGroup(Base):
    __tablename__ = "similarity_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("scan_sessions.id", ondelete="CASCADE"))
    group_index: Mapped[int] = mapped_column(Integer)
    keep_image_id: Mapped[int | None] = mapped_column(ForeignKey("image_entries.id"), nullable=True)

    session: Mapped["ScanSession"] = relationship(back_populates="groups")
