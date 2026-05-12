"""Cálculo de velocidad instantánea y promedio."""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class SpeedResult:
    instant_cm_s: float
    average_cm_s: float
    distance_total_cm: float
    samples: int
    valid: bool
    reason: str = "OK"


class SpeedCalculator:
    def __init__(self, max_dt_s: float = 1.0) -> None:
        self.max_dt_s = max_dt_s
        self.reset()

    def reset(self) -> None:
        self.prev_center: Optional[tuple[int, int]] = None
        self.prev_time: Optional[float] = None
        self.start_time: Optional[float] = None
        self.distance_total_cm = 0.0
        self.samples = 0
        self.last_result = SpeedResult(0.0, 0.0, 0.0, 0, False, "Sin muestras")

    def update(self, center_px: tuple[int, int], timestamp_s: float, cm_per_px: float) -> SpeedResult:
        if self.prev_center is None or self.prev_time is None:
            self.prev_center = center_px
            self.prev_time = timestamp_s
            self.start_time = timestamp_s
            self.samples = 1
            self.last_result = SpeedResult(0.0, 0.0, 0.0, self.samples, True, "Primera muestra")
            return self.last_result

        dt = timestamp_s - self.prev_time
        if dt <= 0:
            self.last_result = SpeedResult(0.0, self.last_result.average_cm_s, self.distance_total_cm, self.samples, False, "dt invalido")
            return self.last_result

        if dt > self.max_dt_s:
            # Si hubo un salto muy grande de tiempo, no se suma como movimiento válido.
            self.prev_center = center_px
            self.prev_time = timestamp_s
            self.last_result = SpeedResult(0.0, self.last_result.average_cm_s, self.distance_total_cm, self.samples, False, "Salto temporal")
            return self.last_result

        dx_px = center_px[0] - self.prev_center[0]
        dy_px = center_px[1] - self.prev_center[1]
        dist_px = math.sqrt(dx_px**2 + dy_px**2)
        dist_cm = dist_px * cm_per_px
        instant_cm_s = dist_cm / dt

        self.distance_total_cm += dist_cm
        self.samples += 1
        elapsed = max(timestamp_s - (self.start_time or timestamp_s), 1e-6)
        average_cm_s = self.distance_total_cm / elapsed

        self.prev_center = center_px
        self.prev_time = timestamp_s
        self.last_result = SpeedResult(
            instant_cm_s=instant_cm_s,
            average_cm_s=average_cm_s,
            distance_total_cm=self.distance_total_cm,
            samples=self.samples,
            valid=True,
            reason="OK",
        )
        return self.last_result

    def freeze(self, reason: str) -> SpeedResult:
        self.last_result.valid = False
        self.last_result.reason = reason
        return self.last_result
