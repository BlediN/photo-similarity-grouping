from datetime import datetime
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class ScanConfig(BaseModel):
    folder_path: str
    overall_similarity: float = Field(default=0.85, ge=0.0, le=1.0)
    face_similarity: float = Field(default=0.8, ge=0.0, le=1.0)
    strict_mode: bool = False


class ImageDecisionUpdate(BaseModel):
    image_id: int
    marked_for_delete: bool


class BatchDecisionUpdate(BaseModel):
    decisions: list[ImageDecisionUpdate]


class DeleteMarkedResponse(BaseModel):
    moved: list[str]
    trash_folder: str


class ImageResult(BaseModel):
    id: int
    file_path: str
    recommended_delete: bool
    user_marked_delete: bool
    width: int
    height: int
    sharpness: float
    exposure: float
    face_count: int
    expression_score: float

    model_config = ConfigDict(from_attributes=True)


class SimilarityGroupResult(BaseModel):
    group_id: int
    keep_image_id: int | None
    images: list[ImageResult]


class SessionSummary(BaseModel):
    id: int
    folder_path: str
    created_at: datetime
    total_images: int
    group_count: int


class SessionDetail(BaseModel):
    id: int
    folder_path: str
    created_at: datetime
    total_images: int
    config: dict
    groups: list[SimilarityGroupResult]
