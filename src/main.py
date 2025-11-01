if __name__ == "__main__":
  #  check_and_install_dependencies()
   # check_config()

    import flet as ft
    import platform
    from src.utils.config import config  # config singleton


    USE_LOCAL_CAMERA = platform.system() in ("Windows", "Linux", "Darwin")

    # ✅ Import views
    from src.views.camera_view import camera_view
    from src.views.settings_view import settings_view
    from src.views.list_objects import list_objects_view
    from src.views.enroll_view import enroll_view
    from src.views.home_view import home_view
    
    def print_config():
        print("\n🛠️  CONFIGURACIÓN CARGADA")
        print("---------------------------")

        for key, value in vars(config).items():
            print(f"{key}: {value}")


    def main(page: ft.Page):
        page.title = "ControlFlow Camera"
        page.padding = 0

        # ✅ store config global here
        page.data = {"config": config}

        # ✅ store resolved paths for views
        page.data["paths"] = {
            "faces": config.detected_faces_dir,
            "models": config.models_dir,
            "logs": config.dir_logs
        }

        content = ft.Container(expand=True)

        def change_tab(e):
            idx = e.control.selected_index

            match idx:
                case 0: content.content = home_view(page)
                case 1: content.content = camera_view(page)
                case 2: content.content = list_objects_view(page)
                case 3: content.content = settings_view(page)
                case 4: content.content = enroll_view(page)

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

        # ✅ load home on start
        print_config()
        content.content = home_view(page)
        page.update()

    ft.app(target=main)

    def check_config():
        """Ensure directories from config.json exist and print resolved paths."""
        print("🔧 Verificando rutas del config.json...")

        print(f"📂 Proyecto ROOT: {config.ROOT}")
        print(f"📸 detected_faces_dir: {config.detected_faces_dir}")
        print(f"🧠 models_dir: {config.models_dir}")
        print(f"📝 logs_dir: {config.dir_logs}")

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
                print(f"✅ Directorio OK: {p.resolve()}")
            except Exception as e:
                print(f"❌ Error creando {p}: {e}")

    
# from pathlib import Path
# import sys
# import os

# # Set project root
# ROOT = Path(__file__).resolve().parents[1]
# sys.path.insert(0, str(ROOT))
# os.chdir(str(ROOT))

# from src.utils.requirements_checker import check_and_install_dependencies

# if __name__ == "__main__":
#     check_and_install_dependencies()

#     import flet as ft
#     import platform

#     USE_LOCAL_CAMERA = platform.system() in ("Windows", "Linux", "Darwin")

#     # ✅ Import views as components
#     from src.views.camera_view import camera_view
#     from src.views.settings_view import settings_view
#     from src.views.list_objects import list_objects_view
#     from src.views.enroll_view import enroll_view
#     from src.views.home_view import home_view

#     def main(page: ft.Page):
#         page.title = "ControlFlow Camera"
#         page.padding = 0

#         # container where view changes
#         content = ft.Container(expand=True)

#         # ✅ callback for NavigationRail
#         def change_tab(e):
#             idx = e.control.selected_index

#             if idx == 0:
#                 content.content = home_view(page)
#             elif idx == 1:
#                 content.content = camera_view(page)
#             elif idx == 2:
#                 content.content = list_objects_view(page)
#             elif idx == 3:
#                 content.content = settings_view(page)

#             page.update()

#         # ✅ NavigationRail menu
#         rail = ft.NavigationRail(
#             selected_index=0,
#             label_type=ft.NavigationRailLabelType.ALL,
#             min_width=80,
#             destinations=[
#                 ft.NavigationRailDestination(icon=ft.Icons.HOME, label="Home"),
#                 ft.NavigationRailDestination(icon=ft.Icons.CAMERA, label="Camara En Vivo"),
#                 ft.NavigationRailDestination(icon=ft.Icons.LIST, label="Listar Detecciones"),
#                 ft.NavigationRailDestination(icon=ft.Icons.SETTINGS, label="Settings")
#             ],
#             on_change=change_tab,
#         )

#         # ✅ Layout
#         page.add(
#             ft.Row(
#                 [
#                     rail,
#                     ft.VerticalDivider(width=1),
#                     content,
#                 ],
#                 expand=True,
#             )
#         )

#         # load first view
#         content.content = home_view(page)
#         page.update()

#     ft.app(target=main)


# from pathlib import Path
# import sys
# import os

# # Set project root as working dir (two parents up from src/main.py)
# ROOT = Path(__file__).resolve().parents[1]
# # ensure imports can find project packages
# sys.path.insert(0, str(ROOT))
# # run from project root so relative assets work
# os.chdir(str(ROOT))

# from src.utils.requirements_checker import check_and_install_dependencies

# if __name__ == "__main__":
#     # Check and install dependencies
#     check_and_install_dependencies()
    
#     import flet as ft
#     import platform

#     # Detecta si está corriendo en escritorio
#     USE_LOCAL_CAMERA = platform.system() in ("Windows", "Linux", "Darwin")

#     def main(page: ft.Page):
#         page.title = "Cámara OpenCV multiplataforma"
#         page.padding = 10
#         # ensure Flet assets point to project assets folder
#         try:
#             page.assets_dir = str(ROOT / "assets")
#         except Exception:
#             pass

#         if USE_LOCAL_CAMERA:
#             from camera_local import start_camera
#             start_camera(page)
            
#         else:
#             from camera_remote import upload_image
#             upload_image(page)

#     ft.app(target=main)
