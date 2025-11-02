from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import flet as ft

from src.utils.config import config
from src.utils.system_tray import setup_system_tray, stop_system_tray
from src.views.camera_view import camera_view
from src.views.enroll_view import enroll_view
from src.views.home_view import home_view
from src.views.list_objects import list_objects_view
from src.views.settings_view import settings_view

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def print_config() -> None:
    """Display configuration values in the console."""
    print("\nCONFIGURACION CARGADA")
    print("---------------------")
    for key, value in vars(config).items():
        print(f"{key}: {value}")


def main(page: ft.Page) -> None:
    logging.info("Inicializando interfaz principal Flet.")

    page.title = "ControlFlow Camera"
    page.padding = 0

    page.data = {"config": config}
    page.data["paths"] = {
        "faces": config.detected_faces_dir,
        "models": config.models_dir,
        "logs": config.dir_logs,
    }

    content = ft.Container(expand=True)
    tray_icon_holder: dict[str, Optional[object]] = {"icon": None}
    page.window.prevent_close = True

    def close_dialog() -> None:
        if page.dialog:
            page.dialog.open = False
            page.update()

    def show_window() -> None:
        logging.info("System tray: restaurar ventana principal.")
        page.window.minimized = False
        page.window.visible = True
        try:
            page.window.to_front()
        except Exception:
            logging.debug("window.to_front no disponible en esta plataforma.")
        page.update()

    def hide_window_to_tray(show_notification: bool = True) -> None:
        logging.info("Interceptando cierre/minimizado: manteniendo aplicacion en system tray.")
        page.window.visible = False
        page.window.minimized = True
        if show_notification:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("ControlFlow Camera sigue activo en la bandeja del sistema."),
                duration=3000,
            )
            page.snack_bar.open = True
        page.update()

    def show_about_dialog() -> None:
        logging.info("Mostrando ventana 'Acerca de'.")
        dialog = ft.AlertDialog(
            title=ft.Text("Acerca de ControlFlow Camera"),
            content=ft.Column(
                [
                    ft.Text("Aplicacion multiplataforma para captura y analisis de rostros.", size=14),
                    ft.Text(f"Directorio de rostros: {config.detected_faces_dir}", size=12, color="#666666"),
                    ft.Text("(c) 2025 ControlFlow. Todos los derechos reservados.", size=12, color="#666666"),
                ],
                spacing=8,
                width=360,
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: close_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def exit_application() -> None:
        logging.info("Saliendo de la aplicacion por accion del system tray.")

        tray_icon = tray_icon_holder.get("icon")
        stop_system_tray(tray_icon)  # type: ignore[arg-type]
        tray_icon_holder["icon"] = None

        # liberar handlers que bloquean el cierre
        try:
            page.on_window_event = None
        except Exception:
            pass
        try:
            page.on_disconnect = None
        except Exception:
            pass

        try:
            page.window.prevent_close = False
        except Exception:
            pass

        # asegurarnos que la ventana vuelva a mostrarse para un cierre limpio
        try:
            page.window.visible = True
            page.window.minimized = False
        except Exception:
            pass

        closed = False
        for attr in ("close", "destroy"):
            try:
                getattr(page.window, attr)()
                closed = True
                break
            except Exception as exc:
                logging.debug("No se pudo ejecutar page.window.%s: %s", attr, exc)

        if not closed:
            logging.debug("Ocultando ventana como ultimo recurso.")
            try:
                page.window.visible = False
                page.update()
            except Exception:
                pass

    def change_tab(e: ft.ControlEvent) -> None:
        idx = e.control.selected_index
        match idx:
            case 0:
                content.content = home_view(page)
            case 1:
                content.content = camera_view(page)
            case 2:
                content.content = list_objects_view(page)
            case 3:
                content.content = settings_view(page)
            case 4:
                content.content = enroll_view(page)
        page.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=80,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.HOME, label="Home"),
            ft.NavigationRailDestination(icon=ft.Icons.CAMERA, label="Camara"),
            ft.NavigationRailDestination(icon=ft.Icons.LIST, label="Detecciones"),
            ft.NavigationRailDestination(icon=ft.Icons.SETTINGS, label="Settings"),
        ],
        on_change=change_tab,
    )

    page.add(
        ft.Row(
            [rail, ft.VerticalDivider(width=1), content],
            expand=True,
        )
    )

    print_config()
    content.content = home_view(page)
    page.update()

    def handle_tray_action(message: object) -> None:
        if not isinstance(message, dict) or message.get("source") != "tray":
            return
        action = message.get("action")
        if action == "show":
            show_window()
        elif action == "about":
            show_about_dialog()
        elif action == "exit":
            exit_application()

    page.pubsub.subscribe(handle_tray_action)

    tray_icon = None
    try:
        tray_icon = setup_system_tray(
            on_show=lambda: page.pubsub.send_all({"source": "tray", "action": "show"}),
            on_about=lambda: page.pubsub.send_all({"source": "tray", "action": "about"}),
            on_exit=lambda: page.pubsub.send_all({"source": "tray", "action": "exit"}),
        )
        if tray_icon is None:
            logging.info("System tray no disponible (ver mensajes anteriores).")
    except Exception as exc:
        logging.error("Error arrancando system tray: %s", exc)
        tray_icon = None

    tray_icon_holder["icon"] = tray_icon
    if tray_icon is not None:
        page.window_prevent_close = True

        def on_window_event(e: ft.WindowEvent) -> None:
            logging.debug("Window event recibido: %s", e.type)
            if e.type == ft.WindowEventType.CLOSE:
                hide_window_to_tray(show_notification=True)
            elif e.type in (ft.WindowEventType.MINIMIZE, ft.WindowEventType.HIDE):
                hide_window_to_tray(show_notification=False)

        page.on_window_event = on_window_event
        page.on_disconnect = lambda _: stop_system_tray(tray_icon_holder["icon"])  # type: ignore[arg-type]
        show_window()


def check_config() -> None:
    """Ensure directories from config.json exist and print resolved paths."""
    print("Verificando rutas del config.json...")
    print(f"Proyecto ROOT: {config.ROOT}")
    print(f"detected_faces_dir: {config.detected_faces_dir}")
    print(f"models_dir: {config.models_dir}")
    print(f"logs_dir: {config.dir_logs}")

    dirs = [
        config.detected_faces_dir,
        config.models_dir,
        config.dir_logs,
    ]

    for path in dirs:
        if not path:
            continue

        p = Path(path)
        try:
            p.mkdir(parents=True, exist_ok=True)
            print(f"Directorio OK: {p.resolve()}")
        except Exception as exc:
            print(f"Error creando {p}: {exc}")


if __name__ == "__main__":
    # check_and_install_dependencies()
    # check_config()
    ft.app(target=main)
