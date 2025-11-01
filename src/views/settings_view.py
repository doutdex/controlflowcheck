import flet as ft

def settings_view(page):
    return ft.Column(
        [
            ft.Text("Configuración", size=22, weight="bold"),
            ft.Text("Ajustes del sistema / rutas / log"),
        ],
        expand=True
    )
