
from pathlib import Path
import sys
import os

# Set project root as working dir (two parents up from src/main.py)
ROOT = Path(__file__).resolve().parents[1]
# ensure imports can find project packages
sys.path.insert(0, str(ROOT))
# run from project root so relative assets work
os.chdir(str(ROOT))

from src.utils.requirements_checker import check_and_install_dependencies

if __name__ == "__main__":
    # Check and install dependencies
    check_and_install_dependencies()
    
    import flet as ft
    import platform

    # Detecta si está corriendo en escritorio
    USE_LOCAL_CAMERA = platform.system() in ("Windows", "Linux", "Darwin")

    def main(page: ft.Page):
        page.title = "Cámara OpenCV multiplataforma"
        page.padding = 10
        # ensure Flet assets point to project assets folder
        try:
            page.assets_dir = str(ROOT / "assets")
        except Exception:
            pass

        if USE_LOCAL_CAMERA:
            from camera_local import start_camera
            start_camera(page)
            
        else:
            from camera_remote import upload_image
            upload_image(page)

    ft.app(target=main)
