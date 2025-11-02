

import flet as ft


 
def settings_view(page):
    sby = ft.SnackBar(ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_300))
    sbn = ft.SnackBar(ft.Icon(ft.Icons.CANCEL, color=ft.Colors.PINK_700))
    dlg = ft.AlertDialog(
        title=ft.Text("Hello"),
        content=ft.Text("You are notified!"),
        alignment=ft.alignment.center,
        on_dismiss=lambda e: print("Dialog dismissed!"),
        title_padding=ft.padding.all(25)
    )
 
    
    return ft.Column(
        [
            ft.Text("Configuración", size=22, weight="bold"),
            ft.Text("Ajustes del sistema / rutas / log"),
            ft.ElevatedButton("Open dialog", on_click=lambda e: page.open(dlg)),
            ft.IconButton(
                    icon=ft.Icons.CHECK_CIRCLE,
                    icon_color=ft.Colors.GREEN_300,
                    icon_size=40,
                    tooltip="Yep",
                     on_click=lambda e: page.open(dlg)
                ),
            ft.IconButton(
                icon=ft.Icons.CANCEL,
                icon_color=ft.Colors.PINK_700,
                icon_size=40,
                tooltip="Nope",
                on_click=lambda e: page.open(sbn),
            ),
            ft.Card(
                content=ft.Container(
                content=ft.Column(
                    [
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.ALBUM),
                            title=ft.Text("The Enchanted Nightingale"),
                            subtitle=ft.Text(
                                "Music by Julie Gable. Lyrics by Sidney Stein."
                            ),
                            bgcolor=ft.Colors.GREY_400,
                        ),
                        ft.Row(
                            [ft.TextButton("Buy tickets"), ft.TextButton("Listen")],
                            alignment=ft.MainAxisAlignment.END,
                        ), 
                        ft.Row(
                            [ft.TextButton("Buy 2222"), ft.TextButton("Cgeck")],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ]
                ),
                width=400,
                padding=10,
            ),
            shadow_color=ft.Colors.ON_SURFACE_VARIANT,
        )
        ],
        expand=True
    )
