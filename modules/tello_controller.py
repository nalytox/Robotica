"""Control seguro básico para DJI Tello usando djitellopy."""

from __future__ import annotations

import time
from typing import Optional

import cv2
import os

class TelloController:
    def __init__(self, takeoff: bool = False) -> None:
        try:
            from djitellopy import Tello
        except ImportError as exc:
            raise ImportError(
                "No se pudo importar djitellopy. Instala dependencias con: "
                "pip install -r requirements.txt"
            ) from exc

        self.tello = Tello()
        self.frame_read = None
        self.flying = False
        self.last_rc_time = 0.0
        self.rc_interval_s = 0.05
        self.takeoff_requested = takeoff

    def start(self) -> None:
        print("Conectando con DJI Tello...")
        self.tello.connect()
        print(f"Bateria inicial: {self.safe_get_battery()}%")
        self.tello.streamoff()
        self.tello.streamon()
        self.frame_read = self.tello.get_frame_read()
        time.sleep(2)
        os.makedirs("images", exist_ok=True)

        if self.takeoff_requested:
            print("ATENCION: Se solicitó despegue automatico.")
            confirmation = input("Escribe ARMAR para despegar: ").strip().upper()
            if confirmation == "ARMAR":
                self.tello.takeoff()
                self.flying = True
                time.sleep(2)
            else:
                print("Despegue cancelado. El sistema funcionará solo con video.")

    def read_frame_bgr(self):
        if self.frame_read is None:
            return None
        frame_rgb = self.frame_read.frame
        if frame_rgb is None:
            return None
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        return frame_bgr

    def send_rc_control_(self, lr: int, fb: int, ud: int, yaw: int) -> None:
        now = time.time()
        if now - self.last_rc_time >= self.rc_interval_s:
            self.tello.send_rc_control(lr, fb, ud, yaw)
            self.last_rc_time = now

    def safe_land(self) -> None:
        print("Aterrizaje seguro solicitado...")
        try:
            for _ in range(5):
                self.tello.send_rc_control(0, 0, 0, 0)
                time.sleep(0.05)
            if self.flying:
                self.tello.land()
                self.flying = False
                print("Dron aterrizado correctamente.")
            else:
                print("El dron no estaba en vuelo; no se ejecuta land().")
        except Exception as exc:
            print(f"Fallo land(), se intenta emergencia. Detalle: {exc}")
            try:
                self.tello.emergency()
            except Exception:
                pass

    def emergency(self) -> None:
        print("EMERGENCIA solicitada.")
        try:
            self.tello.emergency()
        finally:
            self.flying = False

    def stop(self) -> None:
        try:
            self.safe_land()
        finally:
            try:
                self.tello.streamoff()
            except Exception:
                pass
            try:
                self.tello.end()
            except Exception:
                pass

    def safe_get_battery(self) -> Optional[int]:
        try:
            return int(self.tello.get_battery())
        except Exception:
            return None

    def safe_get_height(self) -> Optional[int]:
        try:
            return int(self.tello.get_height()+30)
        except Exception:
            return None

    def safe_get_flight_time(self) -> Optional[int]:
        try:
            return int(self.tello.get_flight_time())
        except Exception:
            return None

    def status_text(self) -> str:
        battery = self.safe_get_battery()
        height = self.safe_get_height()
        flight_time = self.safe_get_flight_time()
        return f"Bateria:{battery if battery is not None else 'N/A'}% | Altura:{height if height is not None else 'N/A'}cm | Vuelo:{flight_time if flight_time is not None else 'N/A'}s"
