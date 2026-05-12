"""Funciones auxiliares de visualización."""

import cv2


def draw_panel(frame, lines, origin=(20, 95), line_height=24):
    x, y = origin
    max_width = 0
    for line in lines:
        (w, _), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.58, 2)
        max_width = max(max_width, w)

    panel_h = line_height * len(lines) + 12
    cv2.rectangle(frame, (x - 8, y - 20), (x + max_width + 12, y + panel_h), (0, 0, 0), -1)

    for idx, line in enumerate(lines):
        yy = y + idx * line_height
        cv2.putText(frame, line, (x, yy), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2)


def draw_keyboard_help(frame):
    text = "Controles: ESC salir | L aterrizar | X emergencia | T reset | WASD mover | Q/E yaw | R/F subir/bajar"
    h = frame.shape[0]
    cv2.rectangle(frame, (0, h - 35), (frame.shape[1], h), (0, 0, 0), -1)
    cv2.putText(frame, text, (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
