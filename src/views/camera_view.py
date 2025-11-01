import flet as ft
from src.modules.cam.camera_local import start_camera


def camera_view(page: ft.Page) -> ft.Control:
    container = ft.Column(expand=True)
    start_camera(page, container)
    return container
