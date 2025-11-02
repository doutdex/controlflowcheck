import logging
import threading
from pathlib import Path
from typing import Callable, Optional

try:
    import pystray  # type: ignore
    from PIL import Image, ImageDraw  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    pystray = None  # type: ignore
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore


def _create_fallback_image() -> Optional["Image.Image"]:
    if Image is None or ImageDraw is None:
        return None

    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, size - 8, size - 8), fill="#1976D2")
    draw.rectangle((size // 2 - 6, size // 2 - 16, size // 2 + 6, size // 2 + 16), fill="#FFFFFF")
    return image


def _load_icon_from_assets() -> Optional["Image.Image"]:
    if Image is None:
        return None

    try:
        assets_dir = Path(__file__).resolve().parents[2] / "assets"
        icon_path = assets_dir / "icon.png"
        if icon_path.exists():
            return Image.open(icon_path).resize((64, 64))
    except Exception as exc:  # pragma: no cover - best effort logging
        logging.debug("System tray: unable to load icon from assets: %s", exc)
    return None


def _resolve_icon_image() -> Optional["Image.Image"]:
    icon = _load_icon_from_assets()
    if icon:
        logging.info("System tray: loaded icon from assets.")
        return icon
    logging.info("System tray: using generated fallback icon.")
    return _create_fallback_image()


def setup_system_tray(
    *,
    on_show: Callable[[], None],
    on_about: Callable[[], None],
    on_exit: Callable[[], None],
) -> Optional["pystray.Icon"]:
    """Create and start a system tray icon in a background thread.

    Callbacks are executed via the page pubsub (UI thread) by the caller.
    """
    try:
        if pystray is None or Image is None:
            logging.warning(
                "System tray disabled: install optional dependencies with 'pip install pystray pillow'"
            )
            return None

        icon_image = _resolve_icon_image()
        if icon_image is None:
            logging.warning("System tray disabled: could not prepare tray icon image")
            return None

        menu = pystray.Menu(
            pystray.MenuItem(
                "Mostrar ventana",
                lambda icon, item: on_show(),
                default=True,
            ),
            pystray.MenuItem("Acerca de...", lambda icon, item: on_about()),
            pystray.MenuItem("Salir", lambda icon, item: on_exit()),
        )

        tray_icon = pystray.Icon(
            "controlflow_camera",
            icon_image,
            "ControlFlow Camera",
            menu,
        )

        thread = threading.Thread(target=tray_icon.run, daemon=True)
        thread.start()
        logging.info("System tray icon created and background thread started.")
        return tray_icon
    except Exception as exc:  # pragma: no cover - defensive logging
        logging.error("System tray: failed to initialize icon: %s", exc)
        return None


def stop_system_tray(icon: Optional["pystray.Icon"]) -> None:
    if icon is None:
        return
    try:
        icon.stop()
        logging.info("System tray icon stopped")
    except Exception as exc:  # pragma: no cover - defensive
        logging.debug("System tray: error stopping icon: %s", exc)
