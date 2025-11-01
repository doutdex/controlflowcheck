import os
from pathlib import Path
from datetime import datetime
import base64
import cv2
import flet as ft


def list_objects_view(page: ft.Page):
    # --- Obtener paths desde page.data/config ---
    cfg = page.data.get("config")
    images_dir = cfg.detected_faces_dir if cfg else Path("detected_faces")

    images_dir = Path(images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)

    # --- UI Components ---
    title = ft.Text("📸 Historial de detecciones", size=20, weight="bold")
    subtitle = ft.Text(f"📁 {images_dir}", size=12, color="#888")
    total_label = ft.Text("0", size=14, weight="w600")
    grid = ft.GridView(
        expand=True,
        runs_count=4,
        max_extent=180,
        child_aspect_ratio=0.8,
        spacing=10,
        run_spacing=10,
        padding=10,
    )

    # --- Helpers ---
    def encode_img(path: Path, max_side=400):
        img = cv2.imread(str(path))
        if img is None:
            return None

        h, w = img.shape[:2]
        scale = min(1.0, max_side / max(h, w))
        if scale != 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)))

        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            return None

        return base64.b64encode(buf).decode()

    # --- Full image modal + delete confirmation ---
    def open_fullscreen(path: Path):
        b64 = encode_img(path, 1200)
        if not b64:
            return

        dialog_ref = {"dlg": None}
        confirm_ref = {"dlg": None}

        def close_dialog():
            if dialog_ref["dlg"]:
                dialog_ref["dlg"].open = False
                page.update()

        def close_confirm():
            if confirm_ref["dlg"]:
                confirm_ref["dlg"].open = False
                page.update()

        def delete_file():
            try:
                path.unlink()
            except Exception as e:
                print(f"Error eliminando archivo: {e}")
            close_confirm()
            close_dialog()
            refresh()

        def confirm_delete():
            cdlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Eliminar imagen"),
                content=ft.Text(f"¿Seguro que deseas eliminar\n{path.name}?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: close_confirm()),
                    ft.TextButton(
                        "Eliminar",
                        style=ft.ButtonStyle(color="white", bgcolor="red"),
                        on_click=lambda e: delete_file()
                    ),
                ],
            )
            confirm_ref["dlg"] = cdlg
            page.dialog = cdlg
            cdlg.open = True
            page.update()

        img = ft.Image(src_base64=b64, width=900, height=700, fit=ft.ImageFit.CONTAIN)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(path.name, size=14),
            content=ft.Column(
                controls=[img],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            actions=[
                ft.TextButton("Eliminar", on_click=lambda e: confirm_delete()),
                ft.TextButton("Cerrar", on_click=lambda e: close_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        dialog_ref["dlg"] = dlg
        page.dialog = dlg
        dlg.open = True
        page.update()

    # --- Load files and refresh grid ---
    def refresh(e=None):
        if not images_dir.exists():
            grid.controls = [ft.Text("📌 No hay imágenes registradas", color="#aaa")]
            total_label.value = "0"
            page.update()
            return

        files = sorted(
            [p for p in images_dir.iterdir() if p.suffix.lower() in [".jpg", ".jpeg", ".png"]],
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        total_label.value = str(len(files))
        cards = []

        for path in files:
            b64 = encode_img(path)
            if not b64:
                continue

            ts = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

            thumb = ft.Image(
                src_base64=b64,
                width=150,
                height=150,
                fit=ft.ImageFit.COVER
            )

            card = ft.Container(
                bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.BLACK),
                border_radius=8,
                padding=6,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.START,
                    controls=[
                        ft.GestureDetector(
                            content=thumb,
                            on_tap=lambda e, p=path: open_fullscreen(p)
                        ),
                        ft.Text(ts, size=10, color="#666"),
                        ft.Container(
                            padding=4,
                            content=ft.ElevatedButton(
                                "Abrir",
                                icon=ft.Icons.ZOOM_IN,
                                on_click=lambda e, p=path: open_fullscreen(p),
                                height=30,
                            )
                        )
                    ]
                )
            )
            cards.append(card)

        grid.controls = cards
        page.update()

    # Cargar al inicio
    refresh()

    return ft.Column(
        expand=True,
        controls=[
            title,
            subtitle,
            ft.Row([
                ft.Text("Total archivos:", size=14),
                total_label,
                ft.IconButton(icon=ft.Icons.REFRESH, on_click=refresh)
            ]),
            ft.Divider(),
            grid
        ],
    )
