import base64
import cv2
import flet as ft
import numpy as np


def upload_image(page: ft.Page):
    page.title = "Capturar o subir foto"
    page.padding = 10

    txt = ft.Text("Selecciona o captura una imagen para deteccion facial:")
    img_view = ft.Image(
        width=800, height=600, fit=ft.ImageFit.CONTAIN,
        src="https://via.placeholder.com/800x600?text=Sin+imagen"
    )

    picker = ft.FilePicker(on_result=lambda e: on_file_picked(e))
    page.overlay.append(picker)

    # Captura desde camara (solo movil / web)
    camera_btn = ft.FilledButton(
        "Capturar foto",
        on_click=lambda e: picker.pick_files(
            allow_multiple=False,
            capture="camera"  # fuerza cámara del móvil
        ),
    )

    # Subir desde galeria
    upload_btn = ft.FilledButton(
        "Subir desde galeria",
        on_click=lambda e: picker.pick_files(allow_multiple=False)
    )

    def on_file_picked(e):
        if not e.files:
            txt.value = "No se selecciono ningun archivo"
            page.update()
            return

        try:
            file = e.files[0]
            with open(file.path, "rb") as f:
                data = f.read()

            npimg = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
            
            if frame is None:
                txt.value = "No se pudo cargar la imagen"
                page.update()
                return

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ok, buf = cv2.imencode(".jpg", frame)
            if ok:
                img_view.src_base64 = base64.b64encode(buf).decode("utf-8")
                txt.value = f"{len(faces)} rostro(s) detectado(s)"
                page.update()
            else:
                txt.value = "Error al procesar la imagen"
                page.update()

        except Exception as ex:
            txt.value = f"Error: {str(ex)}"
            page.update()

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    page.add(
        txt,
        ft.Row([camera_btn, upload_btn], alignment=ft.MainAxisAlignment.CENTER),
        img_view
    )
