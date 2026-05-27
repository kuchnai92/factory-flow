import flet as ft
import database as db

class Sidebar(ft.Container):
    def __init__(self, on_nav_change, on_add_click, on_edit_click, on_delete_click, t, on_lang_change):
        super().__init__()
        self.width = 260 
        self.bgcolor = "#FFFFFF"
        self.padding = ft.padding.all(15)
        self.t = t
        self.on_lang_change = on_lang_change
        
        self.shadow = ft.BoxShadow(blur_radius=20, color="#00000030", offset=ft.Offset(2, 0))
        self.animate_position = ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
        
        self.on_nav_change = on_nav_change
        self.on_add_click = on_add_click
        self.on_edit_click = on_edit_click
        self.on_delete_click = on_delete_click
        
        self.nav_column = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)
        self.content = self.nav_column
        
        self.selected_index = 0
        self.sub_locations = []

    def toggle_language(self, e):
        db.config["language"] = "ur" if e.control.value else "en"
        db.save_data(db.CONFIG_FILE, db.config)
        if self.on_lang_change:
            self.on_lang_change()
        
    def update_locations(self, sub_locations, selected_index):
        self.sub_locations = sub_locations
        self.selected_index = selected_index
        self.render()
        
    def render(self):
        self.nav_column.controls.clear()
        
        self.nav_column.controls.append(
            ft.Container(
                padding=ft.padding.only(bottom=10, left=5, right=5),
                content=ft.Row([
                    ft.Icon(ft.Icons.SPACE_DASHBOARD_ROUNDED, color="#2563EB", size=30),
                    ft.Text("Fru Pro", size=24, weight=ft.FontWeight.W_900, color="#0F172A")
                ])
            )
        )
        self.nav_column.controls.append(ft.Divider(height=1, color="#E2E8F0"))
        self.nav_column.controls.append(ft.Container(height=5))
        
        self.nav_column.controls.append(self.create_item(ft.Icons.DASHBOARD_OUTLINED, self.t("Dashboard"), 0))
        self.nav_column.controls.append(self.create_item(ft.Icons.INVENTORY_2_OUTLINED, self.t("Product Setup"), 1))
        self.nav_column.controls.append(self.create_item(ft.Icons.SETTINGS_OUTLINED, self.t("Settings"), 2))
        
        self.nav_column.controls.append(ft.Container(height=10))
        
        self.nav_column.controls.append(
            ft.Container(
                padding=ft.padding.only(left=10, right=10, bottom=5),
                content=ft.Text(self.t("LOCATIONS"), size=13, weight=ft.FontWeight.BOLD, color="#94A3B8")
            )
        )
        
        for i, loc in enumerate(self.sub_locations):
            actual_index = i + 3
            self.nav_column.controls.append(self.create_item(ft.Icons.FOLDER_OUTLINED, loc, actual_index, is_custom=True))
            
        self.nav_column.controls.append(ft.Container(expand=True)) 
        self.nav_column.controls.append(ft.Divider(height=1, color="#E2E8F0"))

        add_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD, size=22, color="#2563EB"), 
                ft.Text(self.t("New Location"), size=15, color="#2563EB", weight=ft.FontWeight.W_700)
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=14, border_radius=8, bgcolor="#EFF6FF", ink=True,
            on_click=lambda e: self.on_add_click()
        )
        self.nav_column.controls.append(add_btn)

        lang_switch = ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border_radius=8,
            bgcolor="#F8FAFC",
            margin=ft.margin.only(top=5),
            content=ft.Row([
                ft.Icon(ft.Icons.LANGUAGE, color="#64748B", size=22),
                ft.Text(self.t("Urdu (اردو)"), size=15, color="#475569", weight=ft.FontWeight.W_700, expand=True),
                ft.Switch(value=(db.config.get("language") == "ur"), active_color="#2563EB", on_change=self.toggle_language, height=24)
            ])
        )
        self.nav_column.controls.append(lang_switch)

        try:
            self.update()
        except:
            pass
        
    def create_item(self, icon, label, index, is_custom=False):
        is_selected = self.selected_index == index
        
        bg = "#EFF6FF" if is_selected else ft.Colors.TRANSPARENT
        text_color = "#2563EB" if is_selected else "#475569"
        icon_color = "#2563EB" if is_selected else "#94A3B8"
        weight = ft.FontWeight.W_700 if is_selected else ft.FontWeight.W_600
        
        controls = [
            ft.Icon(icon, color=icon_color, size=22),
            ft.Text(label, color=text_color, size=16, weight=weight, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        ]
        
        if is_custom:
            controls.extend([
                ft.IconButton(ft.Icons.EDIT, icon_size=16, icon_color="#60A5FA", padding=0, width=28, height=28, on_click=lambda e: self.on_edit_click(index)),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color="#F87171", padding=0, width=28, height=28, on_click=lambda e: self.on_delete_click(index))
            ])
            
        return ft.Container(
            content=ft.Row(controls, spacing=12),
            bgcolor=bg, padding=ft.padding.symmetric(horizontal=14, vertical=12), border_radius=8, ink=True,
            on_click=lambda e: self.on_nav_change(index)
        )