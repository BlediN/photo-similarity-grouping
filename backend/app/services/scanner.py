from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image
import imagehash
import cv2

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


@dataclass
class ImageFeatures:
    file_path: str
    phash: str
    width: int
    height: int
    sharpness: float
    exposure: float
    face_count: int
    expression_score: float
    semantic_embedding: list[float]
    face_embedding: list[float] | None


def discover_images(folder_path: str) -> list[str]:
    root = Path(folder_path)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid folder path: {folder_path}")

    files = [
        str(path)
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files)


def _normalize(vec: np.ndarray) -> list[float]:
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec.tolist()
    return (vec / norm).tolist()


def _semantic_embedding(image_bgr: np.ndarray) -> list[float]:
    # Lightweight fallback embedding (composition + background color + edges).
    small = cv2.resize(image_bgr, (64, 64), interpolation=cv2.INTER_AREA)
    hist = cv2.calcHist([small], [0, 1, 2], None, [4, 4, 4], [0, 256, 0, 256, 0, 256]).flatten()

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    edge_density = np.array([edges.mean() / 255.0], dtype=np.float32)

    thirds = []
    h, w = gray.shape
    for i in range(3):
        y0 = int(i * h / 3)
        y1 = int((i + 1) * h / 3)
        thirds.append(gray[y0:y1, :].mean() / 255.0)

    embedding = np.concatenate([hist.astype(np.float32), edge_density, np.array(thirds, dtype=np.float32)])
    return _normalize(embedding)


def _face_features(image_bgr: np.ndarray) -> tuple[int, float, list[float] | None]:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(32, 32))

    face_count = len(faces)
    if face_count == 0:
        return 0, 0.0, None

    expression_score = 0.0
    smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_smile.xml")
    embeddings: list[np.ndarray] = []

    for (x, y, w, h) in faces:
        face_roi = gray[y : y + h, x : x + w]
        smiles = smile_cascade.detectMultiScale(face_roi, scaleFactor=1.7, minNeighbors=22)
        expression_score += 1.0 if len(smiles) > 0 else 0.5

        resized = cv2.resize(face_roi, (32, 32), interpolation=cv2.INTER_AREA)
        embeddings.append(resized.flatten().astype(np.float32))

    merged = np.mean(np.vstack(embeddings), axis=0)
    return face_count, expression_score / face_count, _normalize(merged)


def extract_features(file_paths: Iterable[str]) -> list[ImageFeatures]:
    features: list[ImageFeatures] = []

    for file_path in file_paths:
        image = Image.open(file_path).convert("RGB")
        width, height = image.size
        phash = str(imagehash.phash(image))

        image_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        exposure = float(gray.mean() / 255.0)

        face_count, expression_score, face_embedding = _face_features(image_bgr)
        semantic_embedding = _semantic_embedding(image_bgr)

        features.append(
            ImageFeatures(
                file_path=file_path,
                phash=phash,
                width=width,
                height=height,
                sharpness=sharpness,
                exposure=exposure,
                face_count=face_count,
                expression_score=expression_score,
                semantic_embedding=semantic_embedding,
                face_embedding=face_embedding,
            )
        )

    return features
