from __future__ import annotations

from .scanner import ImageFeatures


def _normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def quality_score(image: ImageFeatures, max_resolution: float, max_sharpness: float) -> float:
    resolution = image.width * image.height
    resolution_score = resolution / max(max_resolution, 1.0)
    sharpness_score = image.sharpness / max(max_sharpness, 1.0)
    exposure_score = 1.0 - abs(image.exposure - 0.5) * 2.0

    expression_weight = image.expression_score if image.face_count > 0 else 0.6

    return (
        0.35 * resolution_score
        + 0.30 * sharpness_score
        + 0.20 * max(0.0, exposure_score)
        + 0.15 * expression_weight
    )


def recommend_keep_delete(group: list[ImageFeatures]) -> tuple[str, set[str]]:
    if not group:
        return "", set()

    max_resolution = max(float(img.width * img.height) for img in group)
    max_sharpness = max(float(img.sharpness) for img in group)

    scored = sorted(
        (
            (
                quality_score(img, max_resolution=max_resolution, max_sharpness=max_sharpness),
                img.file_path,
            )
            for img in group
        ),
        reverse=True,
    )

    keep_file = scored[0][1]
    delete_files = {path for _, path in scored[1:]}
    return keep_file, delete_files
