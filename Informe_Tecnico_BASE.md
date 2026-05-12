# Definición técnica del sistema - Medición de velocidad con DJI Tello

## 1. Objetivo del proyecto

El objetivo del sistema es medir la velocidad de desplazamiento de un objeto mediante visión artificial, utilizando la cámara frontal de un DJI Tello como fuente de video y un AprilTag fijo como referencia espacial. El sistema busca reemplazar una medición manual por una solución computacional capaz de detectar el objeto, estimar su desplazamiento y calcular velocidad instantánea y promedio en unidades reales.

## 2. Arquitectura general

El sistema se organiza en los siguientes bloques:

```text
DJI Tello / Webcam
        ↓
Captura de video en tiempo real
        ↓
Detección de AprilTag fijo ──→ Escala espacial cm/pixel
        ↓
Detección de objeto por color
        ↓
Cálculo de desplazamiento entre frames
        ↓
Velocidad instantánea y velocidad promedio
        ↓
Visualización en pantalla + registro CSV
```

A nivel de software, el archivo `main.py` coordina los módulos auxiliares. El módulo `apriltag_detector.py` detecta el marcador fijo y calcula la escala. El módulo `object_tracker.py` identifica el objeto mediante segmentación HSV. El módulo `speed_calculator.py` calcula la velocidad. Finalmente, `tello_controller.py` gestiona la conexión, video, estados internos y acciones de seguridad del dron.

## 3. Funcionalidad implementada

- Conexión con DJI Tello mediante `djitellopy`.
- Captura de video en tiempo real desde Tello, webcam o archivo de video.
- Detección de AprilTag fijo usando `pupil-apriltags`.
- Conversión de pixeles a centímetros usando el tamaño real del AprilTag.
- Detección de objeto por color mediante OpenCV y espacio HSV.
- Cálculo de velocidad instantánea en cm/s y m/s.
- Cálculo de velocidad promedio durante la medición.
- Visualización en pantalla de estados, escala, detección y velocidad.
- Registro opcional de datos en CSV.
- Medidas de seguridad: congelamiento de medición ante pérdida de AprilTag/objeto, aterrizaje seguro, emergencia por teclado y confirmación antes de despegar.

## 4. Librerías utilizadas

### OpenCV
Permite capturar video, procesar imágenes, convertir espacios de color, generar máscaras HSV, encontrar contornos y mostrar resultados en pantalla.

### NumPy
Se utiliza para operaciones numéricas, cálculo de distancias en pixeles y manejo de matrices de imagen.

### pupil-apriltags
Librería empleada para detectar AprilTags en imágenes en escala de grises. Entrega esquinas, centro e ID del marcador detectado.

### djitellopy
Permite comunicarse con el DJI Tello, recibir video, leer estados internos como batería, altura y tiempo de vuelo, además de enviar comandos de control.

## 5. Problemas encontrados o esperados

- Variaciones de iluminación que pueden afectar la detección por color.
- Pérdida temporal del AprilTag por movimiento de cámara o mala orientación.
- Falsos positivos si existen objetos del mismo color en el fondo.
- Latencia WiFi del Tello, lo que puede afectar la suavidad de la medición.
- Cambios de perspectiva cuando el objeto no se mueve sobre el mismo plano de referencia del AprilTag.

## 6. Mejoras futuras

- Incorporar homografía con múltiples AprilTags para corregir mejor la perspectiva.
- Agregar YOLO para detectar clases de objetos sin depender del color.
- Implementar una interfaz gráfica dedicada.
- Suavizar mediciones con filtros de media móvil o Kalman.
- Guardar video procesado para respaldo de la demostración.
- Definir una zona de medición delimitada por más de un marcador fijo.
