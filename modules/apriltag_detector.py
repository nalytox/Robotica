"""Detector de AprilTags para referencia espacial.

Usa pupil-apriltags para detectar marcadores tag36h11 en la imagen.
El tamaño físico conocido del AprilTag permite convertir pixeles a centímetros.
"""

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np


@dataclass
class TagDetection:
    tag_id: int
    center: tuple[int, int]
    corners: np.ndarray
    size_px: float
    cm_per_px: float


class AprilTagDetector:
    def __init__(self, tag_size_cm: float = 16.0, family: str = "tag36h11") -> None:
        try:
            from pupil_apriltags import Detector
        except ImportError as exc:
            raise ImportError(
                "No se pudo importar pupil_apriltags. Instala dependencias con: "
                "pip install -r requirements.txt"
            ) from exc

        if tag_size_cm <= 0:
            raise ValueError("tag_size_cm debe ser mayor que 0")

        self.tag_size_cm = tag_size_cm
        self.detector = Detector(
            families=family,
            nthreads=2,
            quad_decimate=1.0,
            quad_sigma=0.0,
            refine_edges=1,
            decode_sharpening=0.25,
            debug=0,
        )

    def detect(self, frame_bgr: np.ndarray) -> Optional[TagDetection]:
        """Detecta el AprilTag de mayor tamaño visible.

        Retorna None si no se detecta ningún marcador.
        """
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        results = self.detector.detect(gray)

        if not results:
            return None

        best = max(results, key=lambda r: self._tag_size_px(r.corners))
        size_px = self._tag_size_px(best.corners)
        if size_px <= 0:
            return None

        cx, cy = int(best.center[0]), int(best.center[1])
        return TagDetection(
            tag_id=int(best.tag_id),
            center=(cx, cy),
            corners=best.corners.astype(int),
            size_px=float(size_px),
            cm_per_px=float(self.tag_size_cm / size_px),
        )

    @staticmethod
    def _tag_size_px(corners: np.ndarray) -> float:
        width_1 = np.linalg.norm(corners[0] - corners[1])
        width_2 = np.linalg.norm(corners[2] - corners[3])
        height_1 = np.linalg.norm(corners[1] - corners[2])
        height_2 = np.linalg.norm(corners[3] - corners[0])
        return float((width_1 + width_2 + height_1 + height_2) / 4.0)

    @staticmethod
    def draw(frame_bgr: np.ndarray, detection: Optional[TagDetection]) -> None:
        if detection is None:
            cv2.putText(
                frame_bgr,
                "AprilTag: NO DETECTADO",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )
            return

        corners = detection.corners
        for i in range(4):
            pt1 = tuple(corners[i])
            pt2 = tuple(corners[(i + 1) % 4])
            cv2.line(frame_bgr, pt1, pt2, (0, 255, 0), 2)

        cv2.circle(frame_bgr, detection.center, 5, (0, 0, 255), -1)
        text = (
            f"AprilTag ID:{detection.tag_id} | "
            f"{detection.size_px:.1f}px | {detection.cm_per_px:.4f} cm/px"
        )
        cv2.putText(
            frame_bgr,
            text,
            (detection.center[0] + 10, detection.center[1] + 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 0, 0),
            2,
        )
