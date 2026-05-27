import flet as ft
import traceback
import os
import json

# --- SAFE IMPORTS ---
INIT_ERROR = None
try:
    from datetime import datetime
    from sidebar import Sidebar
    from top_bar import FactoryHeader
    from settings_view import SettingsView
    from location_view import LocationView, parse_date
    from product_matrix_view import ProductMatrixView
    from dashboard_view import DashboardView 
    import database as db
except Exception as e:
    INIT_ERROR = traceback.format_exc()

# --- PROFESSIONAL URDU DICTIONARY ---
URDU_DICT = {
    "Global Overview": "عالمی جائزہ",
    "Activity Date Filter:": "سرگرمی کی تاریخ کا فلٹر:",
    "Start:": "شروع:",
    "End:": "ختم:",
    "Any": "کوئی نہیں",
    "Clear Dates": "تاریخیں صاف کریں",
    "Username": "صارف نام",
    "Password": "پاس ورڈ",
    "Login": "لاگ ان",
    "Sign in to continue": "جاری رکھنے کے لیے سائن ان کریں",
    "Please enter any username and password.": "صارف نام اور پاس ورڈ درج کریں۔",
    "Factory deleted!": "فیکٹری حذف ہو گئی!",
    "Location deleted!": "مقام حذف ہو گیا!",
    "Factory already exists!": "فیکٹری پہلے سے موجود ہے!",
    "Name cannot be empty!": "نام خالی نہیں ہو سکتا!",
    "Location already exists!": "مقام پہلے سے موجود ہے!",
    "Add a factory first!": "پہلے فیکٹری شامل کریں!",
    "Edit Location": "مقام میں ترمیم کریں",
    "Add New Factory": "نئی فیکٹری شامل کریں",
    "Edit Factory": "فیکٹری میں ترمیم کریں",
    "Add Sidebar Location": "سائیڈ بار مقام شامل کریں",
    "Cancel": "منسوخ کریں",
    "Save": "محفوظ کریں",
    "Delete": "حذف کریں",
    "Confirm Delete": "حذف کرنے کی تصدیق",
    "Are you sure you want to delete this?": "کیا آپ واقعی اسے حذف کرنا چاہتے ہیں؟",
    "No active or completed processes found in this date range.": "اس تاریخ کی حد میں کوئی عمل ملا۔",
    "Current": "موجودہ",
    "Final": "حتمی",
    "In Process": "پروسیس میں",
    "Pending": "زیر التواء",
    "Completed": "مکمل",
    "Database & App Settings": "ڈیٹا بیس اور ایپ کی ترتیبات",
    "Cloud Sync": "کلاؤڈ سنک",
    "Online": "آن لائن",
    "Offline (Database Not Connected)": "آف لائن (ڈیٹا بیس نہیں)",
    "Securely save or load all factory data. Keys are configured directly in the app source code.": "ڈیٹا محفوظ طریقے سے لوڈ یا محفوظ کریں۔",
    "Load Data": "ڈیٹا لوڈ کریں",
    "Backup Data": "ڈیٹا بیک اپ کریں",
    "App Password Settings": "ایپ پاس ورڈ ترتیبات",
    "Update the master password used to log into the application.": "ایپ میں لاگ ان کرنے کے لیے ماسٹر پاس ورڈ اپ ڈیٹ کریں۔",
    "Change App Password": "ایپ پاس ورڈ تبدیل کریں",
    "Product Setup Matrix": "پروڈکٹ سیٹ اپ میٹرکس",
    "Define global routing and processing steps.": "عالمی روٹنگ اور پروسیسنگ کے مراحل کی وضاحت کریں۔",
    "Create Product": "پروڈکٹ بنائیں",
    "New Product Name": "نئے پروڈکٹ کا نام",
    "Edit Name": "نام میں ترمیم کریں",
    "Add routing step": "مرحلہ شامل کریں",
    "Dashboard": "ڈیش بورڈ",
    "Product Setup": "مصنوعات کی ترتیب",
    "Settings": "ترتیبات",
    "LOCATIONS": "مقامات",
    "New Location": "نئی جگہ",
    "Sub-Location Name": "ذیلی مقام کا نام",
    "New Sub-Location": "نیا ذیلی مقام",
    "Add Raw Stock": "خام اسٹاک شامل کریں",
    "Select Product": "پروڈکٹ منتخب کریں",
    "Quantity (e.g., 500)": "مقدار (مثلاً 500)",
    "Import": "درآمد کریں",
    "Start Processing": "پروسیسنگ شروع کریں",
    "Batch Identifier": "بیچ کی شناخت",
    "Quantity to Process": "پروسیس کی مقدار",
    "Launch Batch": "بیچ شروع کریں",
    "Add Routing Step": "راؤٹنگ مرحلہ شامل کریں",
    "Select Process Step": "پروسیس کا مرحلہ منتخب کریں",
    "Or Create New Step": "یا نیا مرحلہ بنائیں",
    "Insert at Position (Optional)": "پوزیشن پر داخل کریں (اختیاری)",
    "Insert Step": "مرحلہ داخل کریں",
    "Complete Batch": "بیچ مکمل کریں",
    "Finish this batch and securely log it into history?": "کیا آپ اس بیچ کو ختم کرکے اسے محفوظ کرنا چاہتے ہیں؟",
    "Yes, Complete": "ہاں، مکمل کریں",
    "Relocate Batch": "بیچ منتقل کریں",
    "1. Destination Factory": "1. منزل کی فیکٹری",
    "2. Destination Room": "2. منزل کا کمرہ",
    "3. Destination Sub-Zone": "3. منزل کا ذیلی زون",
    "Execute Move": "منتقل کریں",
    "Active Matrix": "ایکٹو میٹرکس",
    "Archive & Logs": "آرکائیو اور لاگز",
    "Live Tracking & Logs": "لائیو ٹریکنگ اور لاگز",
    "Import Stock": "اسٹاک درآمد کریں",
    "Log Filter:": "لاگ فلٹر:",
    "Available Stock:": "دستیاب اسٹاک:",
    "Processing:": "پروسیسنگ:",
    "units": "یونٹس",
    "batches": "بیچز",
    "Extract to Batch": "بیچ میں نکالیں",
    "Ready to Archive": "آرکائیو کیلیے تیار",
    "Archive": "آرکائیو کریں",
    "Finish Step": "مرحلہ مکمل کریں",
    "Start Step": "مرحلہ شروع کریں",
    "Batch Finalized & Archived": "بیچ مکمل اور آرکائیو کر دیا گیا",
    "Confirm Action": "عمل کی تصدیق",
    "Urdu (اردو)": "اردو (Urdu)",
    "Split Batch": "بیچ تقسیم کریں",
    "Merge Batch": "بیچ ضم کریں",
    "Select Target Batch": "ہدف بیچ منتخب کریں",
    "Merge": "ضم کریں",
    "Add Quantity": "مقدار شامل کریں",
    "Quantity (+ to add, - to remove)": "مقدار (+ شامل، - کم کرنے کے لیے)",
    "Cannot remove more than batch has!": "بیچ کی موجودہ مقدار سے زیادہ نہیں نکال سکتے!",
    "Add": "شامل کریں",
    "Number of Branches": "شاخوں کی تعداد",
    "Branch Name": "شاخ کا نام",
    "Branch Qty": "مقدار",
    "Invalid name or quantity in branches!": "شاخوں کا نام یا مقدار غلط ہے!",
    "Split total cannot exceed available quantity!": "تقسیم کی کل مقدار دستیاب مقدار سے زیادہ نہیں ہو سکتی!",
    "Split from:": "سے تقسیم کیا گیا:",
    "Confirm Split": "تقسیم کی تصدیق کریں",
    "Qty": "مقدار",
    "Batch Tag": "بیچ ٹیگ",
    "Cancel & Restock": "منسوخ اور ری اسٹاک کریں",
    "Are you sure you want to cancel this batch and return its quantity to stock?": "کیا آپ واقعی اس بیچ کو منسوخ کر کے مقدار واپس اسٹاک میں شامل کرنا چاہتے ہیں؟",
    "Restock": "ری اسٹاک",
    "Batch cancelled and restocked.": "بیچ منسوخ اور اسٹاک واپس کر دیا گیا۔",
    "Batch Group:": "بیچ گروپ:",
    "Available Qty:": "دستیاب مقدار:",
    "Not enough stock! Only ": "اسٹاک ناکافی ہے! صرف ",
    " available.": " دستیاب ہیں۔",
    "No active operations. Extract stock to begin.": "کوئی فعال کام نہیں۔ شروع کرنے کے لئے اسٹاک نکالیں۔",
    "Define a sub-location using the '+' icon above to start managing inventory.": "اسٹاک کے انتظام کے لئے اوپر '+' آئیکن کا استعمال کرتے ہوئے ایک ذیلی مقام کی وضاحت کریں۔",
    "No history matching this date range.": "اس تاریخ کی حد سے ملنے والی کوئی ہسٹری نہیں ہے۔",
    "Zoom In": "بڑا کریں",
    "Zoom Out": "چھوٹا کریں",
    "Old Password": "پرانا پاس ورڈ",
    "New Password": "نیا پاس ورڈ",
    "Confirm Password": "پاس ورڈ کی تصدیق کریں",
    "Fields cannot be empty!": "خانے خالی نہیں ہو سکتے!",
    "Old password is incorrect!": "پرانا پاس ورڈ غلط ہے!",
    "New passwords do not match!": "نئے پاس ورڈ آپس میں نہیں ملتے!",
    "Updated successfully!": "کامیابی سے اپ ڈیٹ ہو گیا!",
    "Incorrect password!": "غلط پاس ورڈ!"
}

def main(page: ft.Page):
    BG_COLOR = "#F8FAFC"
    CARD_BG = "#FFFFFF"
    TEXT_MAIN = "#0F172A"
    TEXT_SUB = "#64748B"
    PRIMARY = "#2563EB"

    page.title = "Fru Pro"
    
    # --- ADDED: Properly attaches your logo to the active window frame ---
    try:
        page.window.icon = "assets/Yaseen Brothers.ico" 
    except Exception:
        page.window_icon = "assets/Yaseen Brothers.ico"
        
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    page.bgcolor = BG_COLOR

    page.fonts = {
        "Jameel Noori": "assets/Jameel Noori.ttf"
    }

    if INIT_ERROR:
        page.add(ft.SafeArea(ft.Column([
            ft.Text("IMPORT CRASH!", color=ft.Colors.RED_700, weight=ft.FontWeight.BOLD, size=22),
            ft.Container(padding=10, bgcolor=ft.Colors.GREY_200, content=ft.Text(INIT_ERROR, color=ft.Colors.BLACK, size=11, selectable=True))
        ], scroll=ft.ScrollMode.AUTO, expand=True)))
        page.update()
        return

    try:
        products_config = {}
        factories = []
        factory_sub_locations = {}
        level3_data = {}
        
        STATE_FILE = os.path.join(db.REAL_DATA_DIR, "app_workspace.json")
        loaded_data = {}
        
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f: loaded_data = json.load(f)
            except: pass
            
        if not loaded_data:
            fallback_files = ["data.json", "workspace.json", "factories.json"]
            for fallback in fallback_files:
                fb_path = os.path.join(db.REAL_DATA_DIR, fallback)
                if os.path.exists(fb_path):
                    try:
                        with open(fb_path, "r") as f: 
                            loaded_data = json.load(f)
                            if loaded_data: break
                    except: pass
        
        if loaded_data:
            products_config.update(loaded_data.get("products_config", {}))
            factories.extend(loaded_data.get("factories", []))
            factory_sub_locations.update(loaded_data.get("factory_sub_locations", {}))
            level3_data.update(loaded_data.get("level3_data", {}))
            
            if "is_urdu_mode" in loaded_data:
                db.config["language"] = "ur" if loaded_data["is_urdu_mode"] else "en"
            
            if "tab_scales" in loaded_data:
                db.config["tab_scales"] = loaded_data["tab_scales"]
            else:
                db.config["tab_scales"] = {"0": 1.0, "1": 1.0, "2": 1.0, "loc": 1.0}
        
        active_factory_index = 0
        current_nav_index = 0
        is_logged_in = False

        def save_db():
            data_to_save = {
                "products_config": products_config, 
                "factories": factories, 
                "factory_sub_locations": factory_sub_locations, 
                "level3_data": level3_data,
                "is_urdu_mode": (db.config.get("language") == "ur"),
                "tab_scales": db.config.get("tab_scales", {"0": 1.0, "1": 1.0, "2": 1.0, "loc": 1.0})
            }
            try:
                with open(STATE_FILE, "w") as f: json.dump(data_to_save, f, indent=4)
            except: pass

        def setup_app():
            nonlocal is_logged_in
            page.controls.clear()
            page.overlay.clear()
            
            is_urdu = (db.config.get("language") == "ur")
            page.rtl = is_urdu

            page.theme = ft.Theme(font_family="Jameel Noori")

            tab_scales = db.config.get("tab_scales", {"0": 1.0, "1": 1.0, "2": 1.0, "loc": 1.0})
            
            def get_scale_key():
                if current_nav_index == 0: return "0"
                if current_nav_index == 1: return "1"
                if current_nav_index == 2: return "2"
                return "loc"

            def get_scale(key):
                return tab_scales.get(key, 1.0)
                
            scale_dash = get_scale("0")
            def s_dash(size): return int(size * scale_dash)

            def t(text):
                if is_urdu: return URDU_DICT.get(text, text)
                return text

            def show_snack(msg, is_error=False):
                page.open(ft.SnackBar(content=ft.Text(msg, color="#FFFFFF", weight=ft.FontWeight.W_500, size=14), bgcolor="#EF4444" if is_error else "#10B981", behavior=ft.SnackBarBehavior.FLOATING, margin=20, shape=ft.RoundedRectangleBorder(radius=8)))

            def action_push_to_db(e): show_snack(t("Pushing local data to Cloud Database..."), False)
            def action_pull_from_db(e): show_snack(t("Pulling data from Cloud Database..."), False)

            def close_dialog(e=None): page.close(main_dialog)
            
            def process_dialog(e):
                val = text_input.value.strip()
                if not val: show_snack(t("Name cannot be empty!"), True); return
                nonlocal active_factory_index
                current_factory = factories[active_factory_index] if factories else None

                if dialog_mode == "add_factory":
                    if val in factories: show_snack(t("Factory already exists!"), True); return
                    factories.append(val); factory_sub_locations[val] = []; active_factory_index = len(factories) - 1
                    show_snack(t("Factory added!"))
                elif dialog_mode == "add_loc":
                    if val in factory_sub_locations[current_factory]: show_snack(t("Location already exists!"), True); return
                    factory_sub_locations[current_factory].append(val); show_snack(t("Location added!"))
                elif dialog_mode == "edit_factory":
                    if val != current_factory and val in factories: show_snack(t("Name already exists!"), True); return
                    factories[active_factory_index] = val
                    factory_sub_locations[val] = factory_sub_locations.pop(current_factory)
                    
                    keys_to_update = [k for k in level3_data.keys() if k.startswith(f"{current_factory}::")]
                    for old_key in keys_to_update:
                        new_key = old_key.replace(f"{current_factory}::", f"{val}::", 1)
                        level3_data[new_key] = level3_data.pop(old_key)
                        
                    show_snack(t("Updated successfully!"))
                elif dialog_mode == "edit_loc":
                    old_val = factory_sub_locations[current_factory][target_edit_index]
                    if val != old_val and val in factory_sub_locations[current_factory]: show_snack(t("Name already exists!"), True); return
                    factory_sub_locations[current_factory][target_edit_index] = val
                    
                    old_key = f"{current_factory}::{old_val}"
                    new_key = f"{current_factory}::{val}"
                    if old_key in level3_data:
                        level3_data[new_key] = level3_data.pop(old_key)
                        
                    show_snack(t("Updated successfully!"))

                close_dialog(); save_db(); refresh_ui()

            text_input = ft.TextField(autofocus=True, border_radius=8, border_color="#CBD5E1", focused_border_color=PRIMARY, cursor_color=PRIMARY, on_submit=process_dialog)
            dialog_mode = ""; target_edit_index = 0 

            main_dialog = ft.AlertDialog(shape=ft.RoundedRectangleBorder(radius=12), title=ft.Text("", weight=ft.FontWeight.BOLD, color=TEXT_MAIN, size=18), content=text_input, actions=[ft.TextButton(t("Cancel"), on_click=close_dialog, style=ft.ButtonStyle(color=TEXT_SUB)), ft.ElevatedButton(t("Save"), on_click=process_dialog, style=ft.ButtonStyle(color="#FFFFFF", bgcolor=PRIMARY, shape=ft.RoundedRectangleBorder(radius=8)))])
            def open_dialog(mode, title, default_val=""): nonlocal dialog_mode; dialog_mode = mode; main_dialog.title.value = title; text_input.value = default_val; page.open(main_dialog)

            def confirm_delete_active_factory(e):
                def execute(e):
                    page.close(dlg)
                    nonlocal active_factory_index, current_nav_index
                    factory_to_delete = factories[active_factory_index]
                    factories.pop(active_factory_index); del factory_sub_locations[factory_to_delete]
                    
                    keys_to_delete = [k for k in level3_data.keys() if k.startswith(f"{factory_to_delete}::")]
                    for k in keys_to_delete: del level3_data[k]
                        
                    active_factory_index = 0; current_nav_index = 0
                    show_snack(t("Factory deleted!")); save_db(); refresh_ui()
                dlg = ft.AlertDialog(title=ft.Text(t("Confirm Delete"), weight=ft.FontWeight.BOLD, size=18), content=ft.Text(t("Are you sure you want to delete this?"), size=14), actions=[ft.TextButton(t("Cancel"), on_click=lambda e: page.close(dlg)), ft.ElevatedButton(t("Delete"), on_click=execute, style=ft.ButtonStyle(color="white", bgcolor="#EF4444", shape=ft.RoundedRectangleBorder(radius=8)))])
                page.open(dlg)

            def confirm_delete_sidebar_loc(index):
                def execute(e):
                    page.close(dlg)
                    nonlocal current_nav_index; sub_loc_index = index - 3
                    
                    factory = factories[active_factory_index]
                    room_to_delete = factory_sub_locations[factory][sub_loc_index]
                    
                    key_to_delete = f"{factory}::{room_to_delete}"
                    if key_to_delete in level3_data: del level3_data[key_to_delete]
                        
                    factory_sub_locations[factory].pop(sub_loc_index)
                    if current_nav_index == index: current_nav_index = 0 
                    show_snack(t("Location deleted!")); save_db(); refresh_ui()
                dlg = ft.AlertDialog(title=ft.Text(t("Confirm Delete"), weight=ft.FontWeight.BOLD, size=18), content=ft.Text(t("Are you sure you want to delete this?"), size=14), actions=[ft.TextButton(t("Cancel"), on_click=lambda e: page.close(dlg)), ft.ElevatedButton(t("Delete"), on_click=execute, style=ft.ButtonStyle(color="white", bgcolor="#EF4444", shape=ft.RoundedRectangleBorder(radius=8)))])
                page.open(dlg)

            def edit_sidebar_loc(index): nonlocal target_edit_index; target_edit_index = index - 3; open_dialog("edit_loc", t("Edit Location"), factory_sub_locations[factories[active_factory_index]][target_edit_index])
            def get_current_l3_context(): return factories[active_factory_index], factory_sub_locations[factories[active_factory_index]][current_nav_index - 3]
            
            location_view = LocationView(page, products_config, get_current_l3_context, factories, factory_sub_locations, level3_data, save_db, t, get_scale("loc"))
            if hasattr(location_view, 'overlay_controls'):
                for ctrl in location_view.overlay_controls: page.overlay.append(ctrl)

            def on_language_toggled(): 
                save_db()
                setup_app()

            dashboard_view = DashboardView(page, level3_data, t, get_scale("0"))
            product_matrix_view = ProductMatrixView(page, products_config, save_db, t)
            settings_view = SettingsView(page, save_db, action_push_to_db, action_pull_from_db, t)

            def toggle_sidebar(show: bool):
                if show:
                    if is_urdu:
                        sidebar.right = 0
                        sidebar.left = None
                    else:
                        sidebar.left = 0
                        sidebar.right = None
                    sidebar_overlay.visible = True
                else:
                    if is_urdu:
                        sidebar.right = -280
                        sidebar.left = None
                    else:
                        sidebar.left = -280
                        sidebar.right = None
                    sidebar_overlay.visible = False
                page.update()

            def on_top_tab_change(index): 
                nonlocal active_factory_index, current_nav_index
                active_factory_index = index; current_nav_index = 0
                refresh_ui()

            def on_nav_change(index):
                nonlocal current_nav_index
                if not factories: show_snack(t("Add a factory first!"), True); return
                current_nav_index = index
                if page.width and page.width < 768: toggle_sidebar(False)
                refresh_ui()

            header = FactoryHeader(on_tab_change=on_top_tab_change, on_add_click=lambda e: open_dialog("add_factory", t("Add New Factory")), on_edit_click=lambda e: open_dialog("edit_factory", t("Edit Factory"), factories[active_factory_index] if factories else ""), on_delete_click=confirm_delete_active_factory, on_menu_click=lambda e: toggle_sidebar(True))
            sidebar = Sidebar(on_nav_change=on_nav_change, on_add_click=lambda: open_dialog("add_loc", t("Add Sidebar Location")) if factories else show_snack(t("Add a factory first!"), True), on_edit_click=edit_sidebar_loc, on_delete_click=confirm_delete_sidebar_loc, t=t, on_lang_change=on_language_toggled)
            
            if is_urdu:
                sidebar.right = 0
                sidebar.left = None
            else:
                sidebar.left = 0
                sidebar.right = None
            sidebar.top = 0
            sidebar.bottom = 0
            
            content_margin = ft.margin.only(right=260) if is_urdu else ft.margin.only(left=260)
            content_area = ft.Container(margin=content_margin, expand=True, content=ft.Column(expand=True, spacing=0, controls=[header, ft.Container(expand=True, content=ft.Stack([dashboard_view, product_matrix_view, settings_view, location_view]))]))

            def zoom_in(e):
                k = get_scale_key()
                tab_scales[k] = min(2.0, tab_scales.get(k, 1.0) + 0.1)
                save_db(); setup_app()

            def zoom_out(e):
                k = get_scale_key()
                tab_scales[k] = max(0.6, tab_scales.get(k, 1.0) - 0.1)
                save_db(); setup_app()

            def manual_zoom(e):
                try:
                    val = int(e.control.value.replace('%', '').strip())
                    k = get_scale_key()
                    tab_scales[k] = max(0.6, min(2.0, val / 100.0))
                    save_db()
                    setup_app()
                except ValueError:
                    refresh_ui() 

            zoom_input = ft.TextField(
                value=f"{int(get_scale(get_scale_key()) * 100)}",
                width=55,
                height=35,
                text_align=ft.TextAlign.CENTER,
                content_padding=ft.padding.all(0),
                border=ft.InputBorder.NONE,
                color="#FFFFFF",
                cursor_color="#FFFFFF",
                text_size=15,
                text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                suffix_text="%",
                suffix_style=ft.TextStyle(color="#94A3B8", weight=ft.FontWeight.BOLD, size=15),
                on_submit=manual_zoom,
                on_blur=manual_zoom
            )

            zoom_widget = ft.Container(
                content=ft.Row([
                    ft.IconButton(ft.Icons.REMOVE, on_click=zoom_out, icon_color="#FFFFFF", icon_size=18, tooltip=t("Zoom Out")),
                    zoom_input,
                    ft.IconButton(ft.Icons.ADD, on_click=zoom_in, icon_color="#FFFFFF", icon_size=18, tooltip=t("Zoom In"))
                ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor="#0F172A",
                border_radius=30,
                padding=ft.padding.symmetric(horizontal=5, vertical=0),
                shadow=ft.BoxShadow(blur_radius=10, color="#00000040", offset=ft.Offset(0, 4)),
                right=20 if not is_urdu else None,
                left=20 if is_urdu else None,
                bottom=20,
            )

            sidebar_overlay = ft.Container(bgcolor="#80000000", expand=True, visible=False, on_click=lambda e: toggle_sidebar(False))
            root_stack = ft.Stack(controls=[content_area, sidebar_overlay, sidebar, zoom_widget], expand=True)
            main_app_view = ft.Container(content=root_stack, expand=True, visible=False)

            def page_resize(e):
                pw = page.width
                if pw is None: pw = 400 
                if pw < 768:
                    content_area.margin = ft.margin.all(0); header.set_menu_visible(True)
                    if not sidebar_overlay.visible:
                        if is_urdu:
                            sidebar.right = -280
                            sidebar.left = None
                        else:
                            sidebar.left = -280
                            sidebar.right = None
                else:
                    content_area.margin = ft.margin.only(right=260) if is_urdu else ft.margin.only(left=260)
                    header.set_menu_visible(False)
                    if is_urdu:
                        sidebar.right = 0
                        sidebar.left = None
                    else:
                        sidebar.left = 0
                        sidebar.right = None
                    sidebar_overlay.visible = False
                page.update()
            page.on_resized = page_resize

            def refresh_ui():
                nonlocal active_factory_index
                if not factories:
                    header.update_tabs([], 0); sidebar.update_locations([], 0)
                    dashboard_view.visible = True; product_matrix_view.visible = False; settings_view.visible = False; location_view.visible = False; page.update(); return

                if active_factory_index >= len(factories):
                    active_factory_index = 0

                current_factory = factories[active_factory_index]
                header.update_tabs(factories, active_factory_index); sidebar.update_locations(factory_sub_locations[current_factory], current_nav_index)
                
                dashboard_view.visible = False; product_matrix_view.visible = False; settings_view.visible = False; location_view.visible = False

                if current_nav_index == 0: 
                    dashboard_view.render()
                    dashboard_view.visible = True
                    zoom_widget.visible = False 
                elif current_nav_index == 1: 
                    product_matrix_view.visible = True
                    zoom_widget.visible = False 
                elif current_nav_index == 2: 
                    settings_view.visible = True
                    zoom_widget.visible = False 
                else: 
                    location_view.update_context()
                    location_view.visible = True
                    zoom_widget.visible = True
                
                zoom_input.value = f"{int(get_scale(get_scale_key()) * 100)}"
                page.update()

            def do_login(e):
                user_val = login_username.value.strip() if login_username.value else ""
                pass_val = login_password.value.strip() if login_password.value else ""
                
                if user_val and pass_val:
                    stored_hash = db.config.get("admins", {}).get("default", db.hash_val("123"))
                    if db.hash_val(pass_val) == stored_hash:
                        nonlocal is_logged_in
                        is_logged_in = True
                        login_view.visible = False
                        main_app_view.visible = True
                        page_resize(None)
                        refresh_ui()
                    else:
                        show_snack(t("Incorrect password!"), True)
                else:
                    show_snack(t("Please enter any username and password."), True)

            login_username = ft.TextField(label=t("Username"), prefix_icon=ft.Icons.PERSON, border_radius=8, width=300, on_submit=do_login)
            login_password = ft.TextField(label=t("Password"), prefix_icon=ft.Icons.LOCK, password=True, can_reveal_password=True, border_radius=8, width=300, on_submit=do_login)
            login_btn = ft.ElevatedButton(t("Login"), on_click=do_login, width=300, style=ft.ButtonStyle(color="#FFFFFF", bgcolor=PRIMARY, shape=ft.RoundedRectangleBorder(radius=8), padding=15))

            login_view = ft.Container(
                expand=True, alignment=ft.alignment.center, bgcolor=BG_COLOR,
                content=ft.Container(
                    padding=40, bgcolor=CARD_BG, border_radius=12, shadow=ft.BoxShadow(blur_radius=15, color="#00000015", offset=ft.Offset(0, 4)),
                    content=ft.Column(
                        tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.FACTORY_ROUNDED, size=50, color=PRIMARY),
                            ft.Text("Fru Pro", size=28, weight=ft.FontWeight.W_800, color=TEXT_MAIN),
                            ft.Container(margin=ft.margin.only(bottom=20), content=ft.Text(t("Sign in to continue"), size=14, color=TEXT_SUB)),
                            login_username, login_password, ft.Container(height=10), login_btn
                        ]
                    )
                )
            )

            page.add(login_view, main_app_view)
            
            if is_logged_in:
                login_view.visible = False
                main_app_view.visible = True
                page.update() 
                refresh_ui()
                page_resize(None)
            else:
                page.update()

        setup_app()

    except Exception as e:
        error_msg = traceback.format_exc()
        try: page.clean()
        except: pass
        page.add(ft.SafeArea(ft.Column([
            ft.Text("APP CRASHED!", color=ft.Colors.RED_700, weight=ft.FontWeight.BOLD, size=22),
            ft.Text(f"Error: {str(e)}", color=ft.Colors.BLACK, size=14, weight=ft.FontWeight.BOLD),
            ft.Container(padding=10, bgcolor=ft.Colors.GREY_200, border_radius=8, expand=True, content=ft.Text(error_msg, color=ft.Colors.BLACK, size=11, selectable=True))
        ], scroll=ft.ScrollMode.AUTO, expand=True)))
        page.update()

ft.app(target=main)