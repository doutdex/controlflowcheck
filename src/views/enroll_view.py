import flet as ft

def enroll_view(page):
    return ft.Column(
        [
            ft.Text("Registro de rostro", size=22, weight="bold"),
            ft.Text("Aquí irá UI para registrar personas"),
        ],
        expand=True
    )
