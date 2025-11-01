import flet as ft

def home_view(page):
    return ft.Column(
        [
            ft.Text("Inicio", size=22, weight="bold"),
            ft.Text("Aplicacion detecttion de rostros en tiempo real."),
        ],
        expand=True
    )
