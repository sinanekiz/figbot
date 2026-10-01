"""Rigid homogeneous transforms for FIGBOT frame conversions."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, Sequence

Matrix4 = tuple[tuple[float, float, float, float], ...]


def _as_matrix4(values: Sequence[Sequence[float]]) -> Matrix4:
    if len(values) != 4 or any(len(row) != 4 for row in values):
        raise ValueError("transform must be 4x4")
    matrix = tuple(tuple(float(value) for value in row) for row in values)
    if any(not math.isfinite(value) for row in matrix for value in row):
        raise ValueError("transform values must be finite")
    if any(abs(a - b) > 1e-9 for a, b in zip(matrix[3], (0.0, 0.0, 0.0, 1.0))):
        raise ValueError("last row must be [0,0,0,1]")
    # Rotation validity check: rows must be orthonormal and right-handed.
    rotation = [row[:3] for row in matrix[:3]]
    for i in range(3):
        norm = sum(rotation[i][k] * rotation[i][k] for k in range(3))
        if abs(norm - 1.0) > 1e-6:
            raise ValueError("rotation rows must be unit length")
        for j in range(i + 1, 3):
            dot = sum(rotation[i][k] * rotation[j][k] for k in range(3))
            if abs(dot) > 1e-6:
                raise ValueError("rotation rows must be orthogonal")
    determinant = (
        rotation[0][0] * (rotation[1][1] * rotation[2][2] - rotation[1][2] * rotation[2][1])
        - rotation[0][1] * (rotation[1][0] * rotation[2][2] - rotation[1][2] * rotation[2][0])
        + rotation[0][2] * (rotation[1][0] * rotation[2][1] - rotation[1][1] * rotation[2][0])
    )
    if abs(determinant - 1.0) > 1e-6:
        raise ValueError("rotation must be right-handed with determinant +1")
    return matrix


def load_transform(path: str | Path) -> Matrix4:
    """Load `{\"matrix\": [[...], ...]}` and validate it as a rigid transform."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return _as_matrix4(payload["matrix"])


def apply_transform(matrix: Sequence[Sequence[float]], point: Iterable[float]) -> tuple[float, float, float]:
    transform = _as_matrix4(matrix)
    xyz = tuple(float(value) for value in point)
    if len(xyz) != 3 or any(not math.isfinite(value) for value in xyz):
        raise ValueError("point must contain three finite coordinates")
    vector = (*xyz, 1.0)
    result = tuple(sum(transform[row][column] * vector[column] for column in range(4)) for row in range(3))
    return result  # type: ignore[return-value]


def inverse_transform(matrix: Sequence[Sequence[float]]) -> Matrix4:
    transform = _as_matrix4(matrix)
    rotation_t = tuple(tuple(transform[column][row] for column in range(3)) for row in range(3))
    translation = tuple(transform[row][3] for row in range(3))
    inverse_translation = tuple(-sum(rotation_t[row][k] * translation[k] for k in range(3)) for row in range(3))
    return tuple(
        tuple((*rotation_t[row], inverse_translation[row])) for row in range(3)
    ) + ((0.0, 0.0, 0.0, 1.0),)

