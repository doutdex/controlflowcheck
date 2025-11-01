import flet as ft
import cv2
import base64
import numpy as np
from datetime import datetime
from pathlib import Path
import logging
import threading
import time
import traceback
import subprocess
import sys
from face_storage import FaceStorage
from typing import Optional
from history_tab import HistoryTab
from utils.config import config

def start_camera(page: ft.Page):
    # Global components
    global img, status, info, faces_grid, running, cap, face_cascade, face_storage
    
    # Initialize components
    img = ft.Image(
        width=800,
        height=600,
        fit=ft.ImageFit.CONTAIN,
        src="https://via.placeholder.com/800x600?text=C%C3%A1mara+no+iniciada"
    )
    
    status = ft.Text("Listo para iniciar", size=14)
    info = ft.Text("", size=12)
    
    # Initialize faces grid and other state
    faces_grid = ft.GridView(expand=True, runs_count=5, max_extent=150, child_aspect_ratio=0.8, spacing=10, run_spacing=10, padding=20)
    running = {"flag": False}
    cap = {"obj": None}
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    face_storage = FaceStorage()
    history = HistoryTab(page, images_dir=config.detected_faces_dir)

    # --- MOVER/DEFINIR las funciones antes de construir la UI ---
    def frame_to_b64(frame: np.ndarray) -> Optional[str]:
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            return None
        return base64.b64encode(buf).decode("utf-8")

    def update_faces_grid():
        # delega a HistoryTab
        history.refresh()

    def loop():
        try:
            while running["flag"]:
                ret, frame = cap["obj"].read()
                if not ret:
                    status.value = "⚠️ No se pudo leer frame de la cámara"
                    page.update()
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                frame_with_faces = frame.copy()
                
                for face_coords in faces:
                    x, y, w, h = face_coords
                    face_img, embedding, quality_message = face_storage.face_recognizer.process_face(frame, face_coords)
                    
                    if face_img is not None and embedding is not None:
                        cv2.rectangle(frame_with_faces, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(frame_with_faces, "OK", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        if face_storage.save_face(frame, face_coords):
                            info.value = f"✅ Nueva cara detectada y guardada"
                            update_faces_grid()
                        else:
                            info.value = f"👁️ Rostro detectado: {quality_message}"
                    else:
                        cv2.rectangle(frame_with_faces, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        cv2.putText(frame_with_faces, quality_message or "Error", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        info.value = f"⚠️ Rostro rechazado: {quality_message}"
                    page.update()

                frame_with_faces = cv2.resize(frame_with_faces, (800, 600))
                frame_with_faces = cv2.cvtColor(frame_with_faces, cv2.COLOR_BGR2RGB)
                b64 = frame_to_b64(frame_with_faces)
                if b64:
                    img.src_base64 = b64
                    page.update()

                time.sleep(0.03)
        except Exception as e:
            logging.error(f"Error in camera loop: {e}")
            status.value = f"⚠️ Error: {str(e)}"
            page.update()
        finally:
            if cap["obj"]:
                cap["obj"].release()
                cap["obj"] = None
                running["flag"] = False
                status.value = "⏹ Cámara detenida"
                page.update()

    def start(e):
        try:
            if running["flag"]:
                return
            c = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not c.isOpened():
                status.value = "❌ No se pudo abrir la cámara"
                page.update()
                return
            cap["obj"] = c
            running["flag"] = True
            status.value = "✅ Cámara activa"
            page.update()
            import threading
            threading.Thread(target=loop, daemon=True).start()
        except Exception as ex:
            status.value = f"❌ Error: {str(ex)}"
            page.update()

    def stop(e):
        if running["flag"]:
            running["flag"] = False
            if cap["obj"]:
                cap["obj"].release()
                cap["obj"] = None
            status.value = "⏹ Cámara detenida"
            page.update()
        else:
            status.value = "⚠️ La cámara ya está detenida"
            page.update()

    def open_hello_page(_e):
        """Launch the standalone Hola Mundo page."""
        try:
            script_path = (Path(__file__).resolve().parent / "hello_page.py").resolve()
            if not script_path.exists():
                logging.error("Hola Mundo page not found: %s", script_path)
                return
            python_exec = sys.executable or "python"
            subprocess.Popen([python_exec, str(script_path)])
            logging.info("Launching Hola Mundo page at %s", script_path)
        except Exception as ex:
            logging.error(f"Failed to launch Hola Mundo page: {ex}")

    def on_tabs_change(e: ft.ControlEvent):
        """Log the images directory when the history tab is selected."""
        try:
            selected = e.control.selected_index
        except AttributeError:
            selected = None
        if selected == 1:
            logging.info("Historial de rostros buscara en: %s", history.images_dir.resolve())
    # --- FIN de funciones ---

    # ahora construir la UI (usar start/stop ya definidos)
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        on_change=on_tabs_change,
        tabs=[
            ft.Tab(
                text="Cámara en vivo",
                icon=None,
                content=ft.Column([
                    ft.Row(
                        [
                            ft.FilledButton("Iniciar", icon=None, on_click=start),
                            ft.OutlinedButton("Detener", icon=None, on_click=stop),
                            ft.FilledTonalButton("Actualizar historial", icon=None, on_click=lambda _: update_faces_grid()),
                            ft.TextButton("Hola Mundo", on_click=open_hello_page),
                        ],
                        spacing=10
                    ),
                    status,
                    info,
                    img,
                ])
            ),
            history.tab(),
        ]
    )

    page.add(tabs)
    # cargar historial inicial
    update_faces_grid()
    history.try_deferred_refresh()
