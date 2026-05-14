"""Proyecto: Medición de velocidad con DJI Tello + AprilTag + visión artificial.

Cumple la lógica base solicitada en la tarea:
- Conexión/video con Tello o pruebas con webcam/video.
- Detección de AprilTag fijo para escala espacial.
- Detección de objeto por color.
- Cálculo de velocidad instantánea y promedio.
- Visualización de datos y estados internos.
- Medidas de seguridad: congelar medición ante pérdida, aterrizaje y emergencia por teclado.
"""

from __future__ import annotations

import argparse
import csv
import os
import signal
import sys
import time
from datetime import datetime

import cv2

from modules.apriltag_detector import AprilTagDetector
from modules.object_tracker import ColorObjectTracker
from modules.speed_calculator import SpeedCalculator
from modules.drawing import draw_panel, draw_keyboard_help


source_controller = None
stop_requested = False
WINDOW_NAME = "Tello Speed Measurement"

def parse_args():
    parser = argparse.ArgumentParser(description="Medición de velocidad con DJI Tello, AprilTag y OpenCV")
    parser.add_argument("--source", choices=["tello", "webcam", "video"], default="webcam", help="Fuente de video")
    parser.add_argument("--camera-index", type=int, default=0, help="Índice de webcam para pruebas")
    parser.add_argument("--video", type=str, default="", help="Ruta de video si source=video")
    parser.add_argument("--takeoff", default=True, action="store_true", help="Solicita despegue del Tello con doble confirmación")
    parser.add_argument("--tag-size-cm", type=float, default=16.0, help="Tamaño físico del lado del AprilTag en cm")
    parser.add_argument("--object-color", choices=["red", "green", "blue", "orange", "yellow"], default="red")
    parser.add_argument("--min-area", type=int, default=400, help="Área mínima del objeto detectado en pixeles")
    parser.add_argument("--log", action="store_true", help="Guarda mediciones en logs/velocity_log_*.csv")
    parser.add_argument("--max-dt", type=float, default=1.0, help="Tiempo máximo entre muestras válidas")
    return parser.parse_args()


def build_source(args):
    if args.source == "tello":
        from modules.tello_controller import TelloController
        return TelloController(takeoff=args.takeoff)

    from modules.video_source import OpenCVVideoSource
    if args.source == "webcam":
        return OpenCVVideoSource(args.camera_index)

    if not args.video:
        raise ValueError("Debes indicar --video ruta_del_video.mp4 cuando usas --source video")
    return OpenCVVideoSource(args.video)


def request_stop(*_):
    global stop_requested
    stop_requested = True
    print("\nCtrl+C detectado. Cerrando de forma segura...")


def safe_shutdown(*_):
    global source_controller
    print("Cerrando sistema...")
    try:
        if source_controller is not None:
            source_controller.stop()
    except Exception as exc:
        print(f"Advertencia durante cierre de fuente: {exc}")
    finally:
        source_controller = None
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass


def key_to_rc(key: int, speed: int = 35):
    lr = fb = ud = yaw = 0
    if key == ord("w"):
        fb = speed
    elif key == ord("s"):
        fb = -speed
    elif key == ord("a"):
        lr = -speed
    elif key == ord("d"):
        lr = speed
    elif key == ord("r"):
        ud = speed
    elif key == ord("f"):
        ud = -speed
    elif key == ord("q"):
        yaw = -speed
    elif key == ord("e"):
        yaw = speed
    return lr, fb, ud, yaw


def create_log_writer(enabled: bool):
    if not enabled:
        return None, None
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("logs", f"velocity_log_{timestamp}.csv")
    f = open(path, "w", newline="", encoding="utf-8")
    writer = csv.writer(f)
    writer.writerow([
        "timestamp_s",
        "tag_detected",
        "object_detected",
        "cm_per_px",
        "object_x_px",
        "object_y_px",
        "instant_cm_s",
        "average_cm_s",
        "distance_total_cm",
        "valid",
        "reason",
    ])
    print(f"Log habilitado: {path}")
    return f, writer


def main():

    os.makedirs("images", exist_ok=True)
    os.makedirs("images_processed", exist_ok=True)
    frame_count = 0
    global source_controller
    args = parse_args()

    signal.signal(signal.SIGINT, request_stop)

    source_controller = build_source(args)
    tag_detector = AprilTagDetector(tag_size_cm=args.tag_size_cm)
    object_tracker = ColorObjectTracker(color_name=args.object_color, min_area=args.min_area)
    speed_calculator = SpeedCalculator(max_dt_s=args.max_dt)

    log_file, log_writer = create_log_writer(args.log)

    print("Iniciando fuente de video...")
    flying = source_controller.start()
    print("Sistema iniciado. Presiona ESC para salir.")

    try:
        if flying==True:
            tiempo_inicial = time.time()
        while not stop_requested:
            frame = source_controller.read_frame_bgr()
            cv2.imwrite(f"images/frame_{frame_count}.png", frame)
            if frame is None:
                print("No hay más frames o se perdió la señal de video.")
                break

            now = time.time()
            tag = tag_detector.detect(frame)
            obj = object_tracker.detect(frame)

            if tag is None:
                speed_result = speed_calculator.freeze("Sin AprilTag: medicion congelada")
            elif obj is None:
                speed_result = speed_calculator.freeze("Sin objeto: medicion congelada")
            else:
                speed_result = speed_calculator.update(obj.center, now, tag.cm_per_px)

            AprilTagDetector.draw(frame, tag)
            ColorObjectTracker.draw(frame, obj)

            cm_per_px = tag.cm_per_px if tag else 0.0
            obj_x = obj.center[0] if obj else -1
            obj_y = obj.center[1] if obj else -1
            if flying==False:
                tiempo_vuelo = 0
            elif flying==True:
                tiempo_vuelo = int(time.time()-tiempo_inicial)
            panel_lines = [
                f"Vel. inst.: {speed_result.instant_cm_s:.2f} cm/s  ({speed_result.instant_cm_s / 100:.3f} m/s)",
                f"Vel. prom.: {speed_result.average_cm_s:.2f} cm/s  ({speed_result.average_cm_s / 100:.3f} m/s)",
                f"Distancia acumulada: {speed_result.distance_total_cm:.2f} cm | Muestras: {speed_result.samples}",
                f"Estado medicion: {'VALIDA' if speed_result.valid else 'CONGELADA'} | {speed_result.reason}",
                source_controller.status_text(time_flight=tiempo_vuelo),
            ]
            draw_panel(frame, panel_lines)
            draw_keyboard_help(frame)

            if log_writer is not None:
                log_writer.writerow([
                    f"{now:.6f}",
                    tag is not None,
                    obj is not None,
                    f"{cm_per_px:.8f}",
                    obj_x,
                    obj_y,
                    f"{speed_result.instant_cm_s:.6f}",
                    f"{speed_result.average_cm_s:.6f}",
                    f"{speed_result.distance_total_cm:.6f}",
                    speed_result.valid,
                    speed_result.reason,
                ])

            cv2.imwrite(f"images_processed/frame_{frame_count}.png", frame)
            frame_count += 1
            cv2.imshow(WINDOW_NAME, frame)

            # Controles de seguridad y operación
            try:
                if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    print("Ventana cerrada por el usuario.")
                    break
            except cv2.error:
                break

            key = cv2.waitKey(1) & 0xFF

            # Controles de seguridad y operación
            if key in (27, ord("p")):  # ESC o P
                print("Salida solicitada por teclado.")
                break
            if key == ord("l"):
                source_controller.safe_land()
                break
            if key == ord("x"):
                source_controller.emergency()
                break
            if key == ord("t"):
                speed_calculator.reset()
                print("Medición reiniciada.")

            lr, fb, ud, yaw = key_to_rc(key)
            source_controller.send_rc_control_(lr, fb, ud, yaw)

    finally:
        if log_file is not None:
            log_file.close()
        safe_shutdown()


if __name__ == "__main__":
    main()
