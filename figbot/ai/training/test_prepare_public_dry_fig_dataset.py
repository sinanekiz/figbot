from pathlib import Path

import cv2
import numpy as np

from ai.training.prepare_public_dry_fig_dataset import _approximate_box


def test_approximate_box_finds_central_dry_fig_proxy(tmp_path: Path) -> None:
    image = np.full((256, 256, 3), (80, 220, 120), dtype=np.uint8)
    cv2.circle(image, (128, 128), 68, (35, 60, 85), thickness=-1)
    image_path = tmp_path / "dry_fig.jpg"
    assert cv2.imwrite(str(image_path), image)

    centre_x, centre_y, width, height = _approximate_box(image_path)

    assert abs(centre_x - 0.5) < 0.04
    assert abs(centre_y - 0.5) < 0.04
    assert 0.45 < width < 0.70
    assert 0.45 < height < 0.70
