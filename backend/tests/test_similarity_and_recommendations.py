from app.services.recommendations import recommend_keep_delete
from app.services.scanner import ImageFeatures
from app.services.similarity import SimilarityConfig, group_similar_images


def make_image(path: str, phash: str, sharpness: float, width: int = 1000, height: int = 800) -> ImageFeatures:
    return ImageFeatures(
        file_path=path,
        phash=phash,
        width=width,
        height=height,
        sharpness=sharpness,
        exposure=0.5,
        face_count=1,
        expression_score=0.8,
        semantic_embedding=[1.0, 0.0, 0.0],
        face_embedding=[1.0, 0.0, 0.0],
    )


def test_groups_similar_images_with_thresholds() -> None:
    a = make_image("a.jpg", "aaaaaaaaaaaaaaaa", 100)
    b = make_image("b.jpg", "aaaaaaaaaaaaaaab", 110)
    c = make_image("c.jpg", "ffffffffffffffff", 95)
    c.semantic_embedding = [0.0, 1.0, 0.0]
    c.face_embedding = [0.0, 1.0, 0.0]

    groups = group_similar_images(
        [a, b, c],
        SimilarityConfig(overall_similarity=0.8, face_similarity=0.7, strict_mode=False),
    )

    assert len(groups) == 1
    assert sorted(img.file_path for img in groups[0]) == ["a.jpg", "b.jpg"]


def test_recommend_keep_delete_picks_best_quality() -> None:
    best = make_image("best.jpg", "aaaaaaaaaaaaaaaa", 350, width=4000, height=3000)
    blurred = make_image("blurred.jpg", "aaaaaaaaaaaaaaab", 10, width=4000, height=3000)
    small = make_image("small.jpg", "aaaaaaaaaaaaaaac", 200, width=800, height=600)

    keep, delete = recommend_keep_delete([best, blurred, small])

    assert keep == "best.jpg"
    assert delete == {"blurred.jpg", "small.jpg"}
