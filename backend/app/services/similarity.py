from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .scanner import ImageFeatures


@dataclass
class SimilarityConfig:
    overall_similarity: float
    face_similarity: float
    strict_mode: bool


def _hamming_similarity(hash_a: str, hash_b: str) -> float:
    xor_count = sum(ch1 != ch2 for ch1, ch2 in zip(hash_a, hash_b, strict=False))
    return 1.0 - (xor_count / max(len(hash_a), 1))


def _cosine(a: Sequence[float] | None, b: Sequence[float] | None) -> float:
    if not a or not b:
        return 0.0
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def image_similarity(a: ImageFeatures, b: ImageFeatures) -> tuple[float, float, float]:
    hash_sim = _hamming_similarity(a.phash, b.phash)
    semantic_sim = _cosine(a.semantic_embedding, b.semantic_embedding)

    if a.face_embedding and b.face_embedding:
        face_sim = _cosine(a.face_embedding, b.face_embedding)
    else:
        face_sim = 1.0 if a.face_count == b.face_count and a.face_count > 0 else 0.5

    overall = 0.45 * hash_sim + 0.35 * semantic_sim + 0.20 * face_sim
    return overall, face_sim, hash_sim


class _UnionFind:
    def __init__(self, size: int):
        self.parent = list(range(size))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.parent[ry] = rx


def group_similar_images(images: list[ImageFeatures], cfg: SimilarityConfig) -> list[list[ImageFeatures]]:
    if not images:
        return []

    uf = _UnionFind(len(images))

    for i in range(len(images)):
        for j in range(i + 1, len(images)):
            overall, face_sim, hash_sim = image_similarity(images[i], images[j])

            if cfg.strict_mode:
                is_match = hash_sim >= 0.95 or (
                    overall >= cfg.overall_similarity and face_sim >= cfg.face_similarity
                )
            else:
                is_match = overall >= (cfg.overall_similarity * 0.9) and face_sim >= (cfg.face_similarity * 0.8)

            if is_match:
                uf.union(i, j)

    grouped: dict[int, list[ImageFeatures]] = {}
    for idx, image in enumerate(images):
        root = uf.find(idx)
        grouped.setdefault(root, []).append(image)

    return [group for group in grouped.values() if len(group) > 1]
