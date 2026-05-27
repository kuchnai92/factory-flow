import flet as ft
import database as db

class SettingsView(ft.Container):
    def __init__(self, page: ft.Page, save_cb, push_cb, pull_cb, t):
        super().__init__()
        self.page = page
        self.save_cb = save_cb
        self.push_cb = push_cb
        self.pull_cb = pull_cb
        self.t = t
        
        self.expand = True
        self.padding = 20
        self.visible = False

        self.title = ft.Text(self.t("Database & App Settings"), size=28, weight=ft.FontWeight.W_800, color="#0F172A")
        
        self.btn_push = ft.ElevatedButton(self.t("Save to Database"), icon=ft.Icons.CLOUD_UPLOAD, style=ft.ButtonStyle(color="#FFFFFF", bgcolor="#10B981", shape=ft.RoundedRectangleBorder(radius=8), padding=15), height=50, on_click=self.push_cb)
        self.btn_pull = ft.ElevatedButton(self.t("Load from Database"), icon=ft.Icons.CLOUD_DOWNLOAD, style=ft.ButtonStyle(color="#FFFFFF", bgcolor="#0F172A", shape=ft.RoundedRectangleBorder(radius=8), padding=15), height=50, on_click=self.pull_cb)

        self.cloud_card = ft.Container(
            bgcolor="#FFFFFF", border_radius=12, padding=25, border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=15, color="#0000000A", offset=ft.Offset(0, 4)),
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.CLOUD_SYNC, color="#0F172A", size=24), ft.Text(self.t("Cloud Sync"), size=22, weight=ft.FontWeight.BOLD, color="#0F172A")]),
                ft.Container(height=10),
                ft.Row([ft.Icon(ft.Icons.FIBER_MANUAL_RECORD, color="#EF4444", size=14), ft.Text(self.t("Offline (Database Not Connected)"), color="#EF4444", weight=ft.FontWeight.BOLD, size=15)]),
                ft.Text(self.t("Securely save or load all factory data. Keys are configured directly in the app source code."), color="#64748B", size=15),
                ft.Container(height=15),
                ft.Row([self.btn_push, self.btn_pull], wrap=True, spacing=15)
            ])
        )

        # --- RESTORED: Old, New, and Confirm Password Logic ---
        self.old_pass_input = ft.TextField(label=self.t("Old Password"), password=True, can_reveal_password=True, border_radius=8, focused_border_color="#2563EB")
        self.new_pass_input = ft.TextField(label=self.t("New Password"), password=True, can_reveal_password=True, border_radius=8, focused_border_color="#2563EB")
        self.confirm_pass_input = ft.TextField(label=self.t("Confirm Password"), password=True, can_reveal_password=True, border_radius=8, focused_border_color="#2563EB")

        self.pass_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Text(self.t("Change App Password"), weight=ft.FontWeight.BOLD),
            content=ft.Column([self.old_pass_input, self.new_pass_input, self.confirm_pass_input], tight=True),
            actions=[
                ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.pass_dialog), style=ft.ButtonStyle(color="#64748B")),
                ft.ElevatedButton(self.t("Save"), on_click=self.change_password, style=ft.ButtonStyle(color="white", bgcolor="#2563EB", shape=ft.RoundedRectangleBorder(radius=8)))
            ]
        )

        self.btn_change_pass = ft.ElevatedButton(self.t("Change App Password"), icon=ft.Icons.LOCK, style=ft.ButtonStyle(color="#FFFFFF", bgcolor="#0F172A", shape=ft.RoundedRectangleBorder(radius=8), padding=15), height=50, on_click=lambda e: self.open_pass_dialog())

        self.auth_card = ft.Container(
            bgcolor="#FFFFFF", border_radius=12, padding=25, border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=15, color="#0000000A", offset=ft.Offset(0, 4)),
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.SETTINGS, color="#0F172A", size=24), ft.Text(self.t("App Password Settings"), size=22, weight=ft.FontWeight.BOLD, color="#0F172A")]),
                ft.Container(height=10),
                ft.Text(self.t("Update the master password used to log into the application."), color="#64748B", size=15),
                ft.Container(height=15),
                self.btn_change_pass
            ])
        )

        self.settings_wrapper = ft.Container(
            expand=True,
            content=ft.Column([
                self.title,
                ft.Container(height=20),
                self.cloud_card,
                ft.Container(height=10),
                self.auth_card
            ])
        )

        self.content = ft.Column([
            self.settings_wrapper
        ], expand=True, scroll=ft.ScrollMode.AUTO)

    def open_pass_dialog(self):
        self.old_pass_input.value = ""
        self.new_pass_input.value = ""
        self.confirm_pass_input.value = ""
        self.page.open(self.pass_dialog)
        self.page.update()
        
    def change_password(self, e):
        old_p = self.old_pass_input.value.strip()
        new_p = self.new_pass_input.value.strip()
        conf_p = self.confirm_pass_input.value.strip()
        
        if not old_p or not new_p or not conf_p:
            self.page.open(ft.SnackBar(content=ft.Text(self.t("Fields cannot be empty!"), color="#FFFFFF"), bgcolor="#EF4444"))
            return
            
        if db.hash_val(old_p) != db.config["admins"]["default"]:
            self.page.open(ft.SnackBar(content=ft.Text(self.t("Old password is incorrect!"), color="#FFFFFF"), bgcolor="#EF4444"))
            return
            
        if new_p != conf_p:
            self.page.open(ft.SnackBar(content=ft.Text(self.t("New passwords do not match!"), color="#FFFFFF"), bgcolor="#EF4444"))
            return
            
        db.config["admins"]["default"] = db.hash_val(new_p)
        db.save_data(db.CONFIG_FILE, db.config)
        self.page.close(self.pass_dialog)
        self.page.open(ft.SnackBar(content=ft.Text(self.t("Updated successfully!"), color="#FFFFFF"), bgcolor="#10B981"))