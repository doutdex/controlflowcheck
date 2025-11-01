from pathlib import Path
import sys
import os

# Set project root as working dir (two parents up from this file)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(str(ROOT))

import flet as ft


def main(page: ft.Page):
    page.title = "Hola mundo"
    page.padding = 20
    page.bgcolor = "#F5F5F5"
    page.add(
        ft.Container(
            content=ft.Text("Hola mundo", size=36, weight=ft.FontWeight.BOLD),
            alignment=ft.alignment.center,
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
