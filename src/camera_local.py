import flet as ft
import cv2, base64, threading, time, traceback


def start_camera(page: ft.Page):
    page.title = "Cámara local (PC)"
    page.window_width = 900
    page.window_height = 700
    page.padding = 10

    # Estado inicial
    status = ft.Text("Listo para iniciar", size=14)
    info = ft.Text("", size=12)

    # Imagen inicial (placeholder para evitar warning)
    img = ft.Image(
        width=800,
        height=600,
        fit=ft.ImageFit.CONTAIN,
        src="https://via.placeholder.com/800x600?text=C%C3%A1mara+no+iniciada"
    )

    # Detector de rostros
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    running = {"flag": False}
    cap = {"obj": None}

    # --- Función auxiliar: convierte frame a base64 ---
    def frame_to_b64(frame):
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            return None
        return base64.b64encode(buf).decode("utf-8")

    # --- Bucle principal de captura ---
    def loop():
        try:
            while running["flag"]:
                ret, frame = cap["obj"].read()
                if not ret:
                    status.value = "⚠️ No se pudo leer frame de la cámara"
                    page.update()
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                frame = cv2.resize(frame, (800, 600))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                b64 = frame_to_b64(frame)
                if b64:
                    img.src_base64 = b64
                    info.value = f"Rostros detectados: {len(faces)}"
                    page.update()
                else:
                    status.value = "⚠️ Falló la codificación del frame"
                    page.update()

                time.sleep(0.03)
        except Exception:
            traceback.print_exc()
            status.value = "❌ Error interno en el bucle de cámara"
            page.update()
        finally:
            if cap["obj"]:
                cap["obj"].release()
                cap["obj"] = None
                running["flag"] = False
                status.value = "⏹ Cámara detenida"
                page.update()

    # --- Iniciar cámara ---
    def start(e):
        try:
            if running["flag"]:
                status.value = "⚠️ Cámara ya en ejecución"
                page.update()
                return

            c = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not c.isOpened():
                status.value = "❌ No se pudo abrir la cámara (ocupada o inexistente)"
                page.update()
                return

            cap["obj"] = c
            running["flag"] = True
            status.value = "✅ Cámara activa"
            page.update()

            threading.Thread(target=loop, daemon=True).start()
        except Exception as ex:
            traceback.print_exc()
            status.value = f"❌ Error al iniciar cámara: {ex}"
            page.update()

    # --- Detener cámara ---
    def stop(e):
        if running["flag"]:
            running["flag"] = False
            status.value = "⏹ Deteniendo cámara..."
            page.update()
        else:
            status.value = "⚠️ Cámara ya detenida"
            page.update()

    # --- Layout ---
    page.add(
        ft.Row(
            [
                ft.FilledButton("Iniciar", icon=ft.Icons.PLAY_ARROW, on_click=start),
                ft.OutlinedButton("Detener", icon=ft.Icons.STOP, on_click=stop),
            ],
            spacing=10
        ),
        status,
        info,
        img,
    )
