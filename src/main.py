import flet as ft
import platform

# Detecta si está corriendo en escritorio
USE_LOCAL_CAMERA = platform.system() in ("Windows", "Linux", "Darwin")

def main(page: ft.Page):
    page.title = "Cámara OpenCV multiplataforma"
    page.padding = 10

    if USE_LOCAL_CAMERA:
        from camera_local import start_camera
        start_camera(page)
    else:
        from camera_remote import upload_image
        upload_image(page)

ft.app(target=main)
