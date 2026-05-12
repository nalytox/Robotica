# Proyecto Tello: Medición de velocidad con AprilTag

Sistema base para medir la velocidad de un objeto en movimiento usando video del DJI Tello o webcam, un AprilTag fijo como referencia espacial y seguimiento por color con OpenCV.

## Estructura

```text
proyecto_tello_velocidad/
├── main.py
├── requirements.txt
├── Instruction.txt
├── Informe_Tecnico_BASE.md
├── logs/
└── modules/
    ├── apriltag_detector.py
    ├── object_tracker.py
    ├── speed_calculator.py
    ├── tello_controller.py
    ├── video_source.py
    └── drawing.py
```

## Ejecución rápida con webcam

```bash
python main.py --source webcam --tag-size-cm 16 --object-color red --log
```

## Ejecución con Tello

```bash
python main.py --source tello --tag-size-cm 16 --object-color red --log
```

## Ejecución con Tello y despegue

```bash
python main.py --source tello --takeoff --tag-size-cm 16 --object-color red --log
```

El programa solicitará escribir `ARMAR` antes de despegar.
