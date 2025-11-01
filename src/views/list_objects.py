import os
from pathlib import Path
from datetime import datetime
import base64
import cv2
import flet as ft


def list_objects_view(page: ft.Page):

    cfg = page.data.get("config")
    images_dir = Path(cfg.detected_faces_dir if cfg else "detected_faces")
    images_dir.mkdir(parents=True, exist_ok=True)

    title = ft.Text("📸 Historial de detecciones", size=20, weight="bold")
    subtitle = ft.Text(f"📁 {images_dir}", size=12, color="#888")
    total_label = ft.Text("0", size=14, weight="w600")

    grid = ft.GridView(
        expand=True,
        runs_count=4,
        max_extent=180,
        spacing=10,
        run_spacing=10,
        padding=10
    )

    # ---- Helpers ----
    def encode_img(path: Path, max_side=500):
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

    def close_dialog(dialog):
        dialog.open = False
        page.update()

    def delete_file(path: Path, dialog):
        try:
            path.unlink()
        except Exception as e:
            print(f"Error eliminando archivo: {e}")
        close_dialog(dialog)
        refresh()

    def open_confirm(path: Path, parent_dialog):
        confirm = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar imagen"),
            content=ft.Text(f"¿Seguro que deseas eliminar?\n{path.name}"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: close_dialog(confirm)),
                ft.FilledButton(
                    "Eliminar",
                    bgcolor="red",
                    color="white",
                    on_click=lambda e: delete_file(path, parent_dialog),
                ),
            ],
        )
        page.dialog = confirm
        confirm.open = True
        page.update()

    def open_fullscreen(path: Path):
        b64 = encode_img(path, 1200)
        if not b64:
            return

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(path.name, size=14),
            content=ft.Image(
                src_base64=b64,
                width=900,
                height=700,
                fit=ft.ImageFit.CONTAIN
            ),
            actions=[
                ft.TextButton("Eliminar", on_click=lambda e: open_confirm(path, dlg)),
                ft.TextButton("Cerrar", on_click=lambda e: close_dialog(dlg)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dlg
        dlg.open = True
        page.update()

    # ---- Refresh grid ----
    def refresh(e=None):
        if not images_dir.exists():
            grid.controls = [ft.Text("📌 No hay imágenes registradas", color="#aaa")]
            total_label.value = "0"
            page.update()
            return

        files = sorted(
            (p for p in images_dir.iterdir() if p.suffix.lower() in [".jpg", ".jpeg", ".png"]),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
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
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                border_radius=8,
                padding=6,
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.GestureDetector(
                            content=thumb,
                            on_tap=lambda e, p=path: open_fullscreen(p)
                        ),
                        ft.Text(ts, size=10, color="#666"),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.ZOOM_IN,
                                    tooltip="Ver",
                                    on_click=lambda e, p=path: open_fullscreen(p)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Eliminar",
                                    icon_color="red",
                                    on_click=lambda e, p=path: open_confirm(p, None)
                                ),
                            ],
                        )
                    ]
                )
            )
            cards.append(card)

        grid.controls = cards
        page.update()

    refresh()

    return ft.Column(
        expand=True,
        controls=[
            title,
            subtitle,
            ft.Row([
                ft.Text("Total archivos:", size=14),
                total_label,
                ft.IconButton(icon=ft.Icons.REFRESH, on_click=refresh),
            ]),
            ft.Divider(),
            grid,
        ],
    )
