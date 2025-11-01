import asyncio
from pathlib import Path
import cv2
import base64
import logging
from datetime import datetime
import flet as ft
from typing import List
from utils.config import config


class HistoryTab:
    def __init__(self, page: ft.Page, images_dir=None):
        self.page = page
        self.images_dir: Path = self._resolve_images_dir(images_dir)
        self.path_text = ft.Text(self._path_message(), size=12, color="#616161")
        self.count_label = ft.Text("Imágenes registradas:", size=13, color="#424242")
        self.count_value = ft.Text("0", size=16, weight=ft.FontWeight.W_600, color="#212121")
        self.count_row = ft.Row(
            controls=[self.count_label, self.count_value],
            spacing=6,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )
        self.refresh_button = ft.FilledTonalButton("Actualizar historial", on_click=lambda e: self.refresh(e))
        self.header_row = ft.Row(
            controls=[self.count_row, self.refresh_button],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.grid = ft.GridView(
            expand=True,
            runs_count=5,
            max_extent=180,
            child_aspect_ratio=0.8,
            spacing=10,
            run_spacing=10,
            padding=10,
        )
        self.dialog = None
        self.confirm = None
        self.pending_refresh = False
        self._auto_refresh_interval = 10
        self._auto_refresh_task = None
        logging.basicConfig(level=logging.INFO)
        logging.info(f"HistoryTab initialized, images_dir={self.images_dir}")
        self._start_auto_refresh()

    def _resolve_images_dir(self, images_dir) -> Path:
        """Return an absolute path for the images directory."""
        configured = images_dir if images_dir is not None else getattr(config, "detected_faces_dir", "")
        if not configured:
            configured = "detected_faces"
        candidate = Path(configured).expanduser()
        if str(candidate) in (".", ""):
            candidate = Path("detected_faces")
        if candidate.is_absolute():
            return candidate.resolve()
        project_root = Path(__file__).resolve().parent.parent
        return (project_root / candidate).resolve()

    def _path_message(self) -> str:
        base_message = f"Mostrando imagenes desde: {self.images_dir}"
        if not self.images_dir.exists():
            return f"{base_message} (directorio no encontrado)"
        return base_message

    def _encode_image(self, path: Path, max_side: int = 600) -> str:
        img = cv2.imread(str(path))
        if img is None:
            logging.error(f"HistoryTab: failed to read image: {path}")
            return ""
        h, w = img.shape[:2]
        scale = min(1.0, max_side / max(w, h))
        if scale != 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)))
        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            logging.error(f"HistoryTab: failed to encode image: {path}")
            return ""
        return base64.b64encode(buf).decode("utf-8")

    def _list_images(self) -> List[Path]:
        if not self.images_dir.exists() or not self.images_dir.is_dir():
            logging.warning(f"HistoryTab: images_dir does not exist: {self.images_dir}")
            return []
        try:
            files = [p for p in self.images_dir.iterdir() if p.suffix.lower() in ('.jpg', '.jpeg', '.png')]
        except Exception as e:
            logging.error(f"HistoryTab: failed to list directory {self.images_dir}: {e}")
            return []
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        logging.info(f"HistoryTab: found {len(files)} image files in {self.images_dir}")
        return files

    def _open_image_dialog(self, path: Path):
        b64 = self._encode_image(path, max_side=1000)
        if not b64:
            return
        large_img = ft.Image(src_base64=b64, fit=ft.ImageFit.CONTAIN, width=800, height=600)
        timestamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        filename = path.name

        def on_delete(e):
            self._show_confirm_delete(path)

        self.dialog = ft.AlertDialog(
            title=ft.Text(filename),
            content=ft.Column([ft.Text(f"Detectado: {timestamp}", size=12), large_img], spacing=10),
            actions=[
                ft.TextButton("Eliminar", on_click=on_delete),
                ft.TextButton("Cerrar", on_click=lambda e: self._close_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = self.dialog
        self.dialog.open = True
        try:
            self.page.update()
        except Exception:
            # page may not be ready, mark pending
            self.pending_refresh = True

    def _show_confirm_delete(self, path: Path):
        def confirm_delete(e):
            try:
                path.unlink()
            except Exception as ex:
                print(f"Error deleting file: {ex}")
            self._close_confirm()
            self._close_dialog()
            self.refresh()

        def cancel_delete(e):
            self._close_confirm()

        self.confirm = ft.AlertDialog(
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text("¿Desea eliminar esta imagen?"),
            actions=[
                ft.TextButton("Sí, eliminar", on_click=confirm_delete, bgcolor="#ff5252", color="white"),
                ft.TextButton("Cancelar", on_click=cancel_delete)
            ],
        )
        self.page.dialog = self.confirm
        self.confirm.open = True
        self.page.update()

    def _close_dialog(self):
        if self.dialog:
            self.dialog.open = False
            self.page.update()
            self.dialog = None

    def _close_confirm(self):
        if self.confirm:
            self.confirm.open = False
            self.page.update()
            self.confirm = None

    def refresh(self, _e=None):
        """Rebuild thumbnail grid from detected_faces directory (most recent first)."""
        try:
            self.path_text.value = self._path_message()
            files = self._list_images()
            logging.info(f"HistoryTab.refresh: total images={len(files)}")
            self.count_value.value = str(len(files))
            cards = []
            if not files:
                cards.append(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("No hay rostros guardados", color="#9E9E9E"),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=20,
                        alignment=ft.alignment.center,
                    )
                )
            else:
                for path in files:
                    b64 = self._encode_image(path, max_side=300)
                    if not b64:
                        logging.info(f"HistoryTab.refresh: skipping file (encode failed): {path}")
                        continue
                    ts = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    thumb = ft.Image(src_base64=b64, width=150, height=150, fit=ft.ImageFit.COVER)
                    card = ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Container(content=thumb, on_click=lambda e, p=path: self._open_image_dialog(p)),
                                    ft.Text(ts, size=11, color="#424242"),
                                    ft.Row(
                                        controls=[
                                            ft.TextButton("Abrir", on_click=lambda e, p=path: self._open_image_dialog(p)),
                                            ft.TextButton("Eliminar", on_click=lambda e, p=path: self._show_confirm_delete(p)),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                ],
                                spacing=6,
                            ),
                            padding=6,
                        ),
                        elevation=1,
                    )
                    cards.append(card)
            self.grid.controls = cards

            # Try updating grid and page; if grid not yet attached to page, defer
            try:
                self.path_text.update()
                self.count_value.update()
                self.grid.update()
                self.header_row.update()
                self.page.update()
                self.pending_refresh = False
            except Exception as ex:
                logging.info(f"HistoryTab.refresh: page not ready yet, deferring update: {ex}")
                self.pending_refresh = True

        except Exception as e:
            logging.error(f"HistoryTab.refresh error: {e}")

    def try_deferred_refresh(self):
        if self.pending_refresh:
            try:
                self.path_text.update()
                self.count_value.update()
                self.grid.update()
                self.header_row.update()
                self.page.update()
                self.pending_refresh = False
            except Exception:
                pass

    def tab(self) -> ft.Tab:
        content_column = ft.Column(
            [self.path_text, self.header_row, self.grid],
            spacing=10,
            expand=True,
        )
        container = ft.Container(
            content=content_column,
            padding=10,
            border_radius=8,
            bgcolor="#FFFFFF",
            expand=True
        )
        return ft.Tab(text="Historial de rostros", icon=None, content=container)

    def _start_auto_refresh(self):
        if self._auto_refresh_task is None:
            try:
                self._auto_refresh_task = self.page.run_task(self._auto_refresh_loop)
            except Exception as e:
                logging.debug(f"HistoryTab: unable to start auto-refresh task: {e}")

    async def _auto_refresh_loop(self):
        while True:
            try:
                await asyncio.sleep(self._auto_refresh_interval)
                self.refresh()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logging.debug(f"HistoryTab: auto-refresh stopped: {e}")
                break
