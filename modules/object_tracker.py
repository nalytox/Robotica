"""Seguimiento simple de objeto por color y contorno.

La idea es usar un objeto de color fuerte: rojo, verde, azul u naranja.
Para el laboratorio es más defendible que un modelo pesado, porque se puede explicar
con HSV, máscara binaria, morfología y contornos.
"""

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np


@dataclass
class ObjectDetection:
    center: tuple[int, int]
    bbox: tuple[int, int, int, int]
    area: float
    color_name: str


class ColorObjectTracker:
    HSV_RANGES = {
        "red": [((0, 90, 70), (10, 255, 255)), ((170, 90, 70), (180, 255, 255))],
        "green": [((35, 60, 50), (85, 255, 255))],
        "blue": [((90, 60, 50), (130, 255, 255))],
        "orange": [((10, 80, 80), (25, 255, 255))],
        "yellow": [((20, 70, 70), (35, 255, 255))],
    }

    def __init__(self, color_name: str = "red", min_area: int = 400) -> None:
        if color_name not in self.HSV_RANGES:
            valid = ", ".join(self.HSV_RANGES.keys())
            raise ValueError(f"Color '{color_name}' no soportado. Usa uno de: {valid}")
        self.color_name = color_name
        self.min_area = min_area

    def detect(self, frame_bgr: np.ndarray) -> Optional[ObjectDetection]:
        blurred = cv2.GaussianBlur(frame_bgr, (7, 7), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in self.HSV_RANGES[self.color_name]:
            lower_np = np.array(lower, dtype=np.uint8)
            upper_np = np.array(upper, dtype=np.uint8)
            mask_total = cv2.bitwise_or(mask_total, cv2.inRange(hsv, lower_np, upper_np))

        kernel = np.ones((5, 5), np.uint8)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour)
        if area < self.min_area:
            return None

        x, y, w, h = cv2.boundingRect(contour)
        cx = x + w // 2
        cy = y + h // 2
        return ObjectDetection(center=(cx, cy), bbox=(x, y, w, h), area=float(area), color_name=self.color_name)

    @staticmethod
    def draw(frame_bgr: np.ndarray, detection: Optional[ObjectDetection]) -> None:
        if detection is None:
            cv2.putText(
                frame_bgr,
                "Objeto: NO DETECTADO",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )
            return

        x, y, w, h = detection.bbox
        cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 255, 255), 2)
        cv2.circle(frame_bgr, detection.center, 5, (255, 0, 255), -1)
        text = f"Objeto {detection.color_name} | area:{detection.area:.0f} | x:{detection.center[0]}, y:{detection.center[1]}"
        cv2.putText(
            frame_bgr,
            text,
            (x, max(20, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2,
        )
