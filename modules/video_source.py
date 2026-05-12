"""Fuentes de video para pruebas con webcam o archivo."""

import cv2


class OpenCVVideoSource:
    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la fuente de video: {source}")

    def start(self) -> None:
        pass

    def read_frame_bgr(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def status_text(self) -> str:
        return "Fuente: Webcam/Video | Bateria:N/A | Altura:N/A | Vuelo:N/A"

    def send_rc_control(self, lr: int, fb: int, ud: int, yaw: int) -> None:
        pass

    def safe_land(self) -> None:
        pass

    def emergency(self) -> None:
        pass

    def stop(self) -> None:
        self.cap.release()
