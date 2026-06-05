import flet as ft
import copy
import os
from datetime import datetime

def parse_date(date_str):
    try: return datetime.strptime(date_str, "%Y-%m-%d %I:%M %p")
    except ValueError:
        try: return datetime.strptime(date_str, "%I:%M %p, %d %b")
        except: return datetime.now()

class ArchiveLogView(ft.Container):
    def __init__(self, page: ft.Page, t, scale_factor: float, revert_cb=None):
        super().__init__()
        self.page = page
        self.t = t
        self.scale_factor = scale_factor
        self.tab_data = {}
        self.view_mode = "archive" 
        self.expand = True
        self.revert_cb = revert_cb
        self.filtered_items = []
        
        def s(size): return int(size * self.scale_factor)
        self.s = s
        
        self.expanded_groups = set()
        self.search_query = ""
        
        self.revert_target_name = ""
        self.revert_confirm_btn = ft.ElevatedButton(
            self.t("Yes, Revert"), 
            on_click=self.execute_revert, 
            style=ft.ButtonStyle(color="#FFFFFF", bgcolor="#F59E0B", shape=ft.RoundedRectangleBorder(radius=8))
        )
        self.revert_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Text(self.t("Confirm Revert"), weight=ft.FontWeight.BOLD, size=s(18)),
            content=ft.Text(self.t("Are you sure you want to revert this batch back to the active matrix?"), size=s(14)),
            actions=[
                ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.revert_dialog), style=ft.ButtonStyle(color="#64748B")),
                self.revert_confirm_btn
            ]
        )
        
        self.export_selected_ids = set()
        self.export_list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=400)
        
        self.export_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Row([
                ft.Icon(ft.Icons.PICTURE_AS_PDF, color="#8B5CF6", size=28),
                ft.Text(self.t("Export PDF"), weight=ft.FontWeight.BOLD, size=s(22))
            ], spacing=10),
            content=ft.Container(
                width=600,
                content=ft.Column([
                    ft.Text(self.t("Select specific batches or click Select All to generate a combined PDF report."), size=s(14), color="#64748B"),
                    ft.Container(height=5),
                    ft.Row([
                        ft.ElevatedButton("Select All", on_click=self.select_all_export, style=ft.ButtonStyle(color="#2563EB", bgcolor="#EFF6FF")),
                        ft.ElevatedButton("Deselect All", on_click=self.deselect_all_export, style=ft.ButtonStyle(color="#64748B", bgcolor="#F1F5F9"))
                    ]),
                    ft.Divider(height=20, color="#E2E8F0"),
                    self.export_list_col
                ], tight=True)
            ),
            actions=[
                ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.export_dialog), style=ft.ButtonStyle(color="#64748B")),
                ft.ElevatedButton(self.t("Generate PDF"), icon=ft.Icons.DOWNLOAD, on_click=self.execute_pdf_export, style=ft.ButtonStyle(color="white", bgcolor="#8B5CF6", shape=ft.RoundedRectangleBorder(radius=8)))
            ]
        )

        current_date_val = datetime.now()
        self.start_date = None
        self.end_date = None
        self.start_picker = ft.DatePicker(first_date=datetime(2020, 1, 1), last_date=datetime(2050, 12, 31), current_date=current_date_val, on_change=self.on_start_change)
        self.end_picker = ft.DatePicker(first_date=datetime(2020, 1, 1), last_date=datetime(2050, 12, 31), current_date=current_date_val, on_change=self.on_end_change)
        
        if self.start_picker not in self.page.overlay:
            self.page.overlay.extend([self.start_picker, self.end_picker])

        self.search_input = ft.TextField(
            hint_text=self.t("Live Search..."), 
            prefix_icon=ft.Icons.SEARCH, 
            border_radius=8, 
            focused_border_color="#2563EB", 
            height=s(40), 
            width=s(200), 
            content_padding=ft.padding.symmetric(horizontal=10, vertical=0), 
            text_size=s(13), 
            on_change=self.on_search_change
        )

        self.start_btn = ft.ElevatedButton(f"{self.t('Start:')} {self.t('Any')}", on_click=self.open_start_date, icon=ft.Icons.CALENDAR_TODAY, style=ft.ButtonStyle(color="#0F172A", bgcolor="#F8FAFC", shape=ft.RoundedRectangleBorder(radius=8)), elevation=0)
        self.end_btn = ft.ElevatedButton(f"{self.t('End:')} {self.t('Any')}", on_click=self.open_end_date, icon=ft.Icons.CALENDAR_TODAY, style=ft.ButtonStyle(color="#0F172A", bgcolor="#F8FAFC", shape=ft.RoundedRectangleBorder(radius=8)), elevation=0)
        self.filter_title = ft.Text(self.t("Archive Filter:"), color="#64748B", weight=ft.FontWeight.W_600, size=s(15))

        self.filter_container = ft.Container(
            padding=15, bgcolor="#FFFFFF", border_radius=12, border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=10, color="#00000005", offset=ft.Offset(0, 2)), 
            content=ft.Row([
                ft.Row([ft.Icon(ft.Icons.FILTER_ALT, color="#64748B", size=s(20)), self.filter_title]), 
                ft.Row([
                    self.search_input, 
                    self.start_btn, 
                    self.end_btn, 
                    ft.IconButton(ft.Icons.CLOSE, on_click=self.clear_filters, tooltip=self.t("Clear Filters"), icon_color="#EF4444", bgcolor="#FEF2F2"),
                    ft.ElevatedButton("Export PDF", icon=ft.Icons.PICTURE_AS_PDF, style=ft.ButtonStyle(color="white", bgcolor="#8B5CF6", shape=ft.RoundedRectangleBorder(radius=8)), on_click=self.open_export_dialog)
                ], wrap=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)
        )

        self.list_container = ft.Column(spacing=15, expand=True, scroll=ft.ScrollMode.AUTO)
        
        self.content = ft.Column([
            self.filter_container, 
            self.list_container
        ], expand=True)

    def open_export_dialog(self, e):
        self.export_selected_ids.clear()
        self.render_export_list()
        self.page.open(self.export_dialog)
        self.page.update()

    def select_all_export(self, e):
        for wrapper in self.filtered_items:
            self.export_selected_ids.add(wrapper["data"].get("id", "Unknown"))
        self.render_export_list()

    def deselect_all_export(self, e):
        self.export_selected_ids.clear()
        self.render_export_list()

    def toggle_export_batch(self, e, batch_id, force_state=None):
        is_checked = force_state if force_state is not None else e.control.value
        if is_checked: self.export_selected_ids.add(batch_id)
        else: self.export_selected_ids.discard(batch_id)
        self.render_export_list()

    def render_export_list(self):
        self.export_list_col.controls.clear()
        
        def sort_key(wrapper):
            return (0 if wrapper["data"].get("id") in self.export_selected_ids else 1, wrapper["data"].get("name", ""))
            
        sorted_items = sorted(self.filtered_items, key=sort_key)

        for wrapper in sorted_items:
            item = wrapper["data"]
            item_id = item.get("id", "Unknown")
            is_checked = item_id in self.export_selected_ids
            status_txt = wrapper["status"]
            status_color = "#10B981" if status_txt == "Completed" else "#2563EB"
            
            creation_date = "Unknown Date"
            if item.get("timeline") and len(item["timeline"]) > 0:
                creation_date = item["timeline"][0].get("time", "Unknown Date")

            batch_name = item.get('name', 'Unknown')
            qty = item.get('quantity', 0)

            card = ft.Container(
                padding=ft.padding.symmetric(horizontal=15, vertical=12),
                bgcolor="#F8FAFC" if not is_checked else "#EFF6FF",
                border_radius=8,
                border=ft.border.all(1, "#CBD5E1" if not is_checked else "#2563EB"),
                ink=True,
                on_click=lambda e, i=item_id, c=not is_checked: self.toggle_export_batch(e, i, force_state=c),
                content=ft.Row([
                    ft.Checkbox(value=is_checked, on_change=lambda e, i=item_id: self.toggle_export_batch(e, i), active_color="#2563EB"),
                    ft.Column([
                        ft.Text(f"{batch_name}", weight=ft.FontWeight.W_800, size=self.s(17), color="#0F172A", font_family="Jameel Noori"),
                        ft.Row([
                            ft.Icon(ft.Icons.CALENDAR_TODAY, size=13, color="#64748B"),
                            ft.Text(f"Created: {creation_date}", size=self.s(13), color="#64748B"),
                            ft.Text("•", size=self.s(13), color="#64748B"),
                            ft.Text(f"{qty:g} units", size=self.s(13), color="#64748B", weight=ft.FontWeight.W_600)
                        ], spacing=6)
                    ], expand=True, spacing=4),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor=f"{status_color}20", border_radius=12,
                        content=ft.Text(status_txt, size=self.s(13), color=status_color, weight=ft.FontWeight.W_800)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )
            self.export_list_col.controls.append(card)
            
        if not self.export_list_col.controls:
            self.export_list_col.controls.append(ft.Container(padding=20, alignment=ft.alignment.center, content=ft.Text("No batches match current filter.", color="#64748B", italic=True)))
            
        self.page.update()

    def execute_pdf_export(self, e):
        # --- DYNAMIC IMPORT FIX ---
        try:
            from fpdf import FPDF
        except ImportError:
            self.page.open(ft.SnackBar(content=ft.Text("Please install fpdf2: pip install fpdf2", color="#FFFFFF"), bgcolor="#EF4444"))
            return
            
        if not self.export_selected_ids:
            self.page.open(ft.SnackBar(content=ft.Text("Please select at least one batch.", color="#FFFFFF"), bgcolor="#EF4444"))
            return

        pdf = FPDF()
        pdf.add_page()
        
        font_path = "assets/Jameel Noori.ttf"
        has_unicode_font = False
        if os.path.exists(font_path):
            try:
                pdf.add_font("JameelNoori", "", font_path)
                has_unicode_font = True
            except: pass
                
        font_name = "JameelNoori" if has_unicode_font else "Helvetica"
        
        def safe_txt(txt):
            if has_unicode_font: return str(txt)
            return str(txt).encode('latin-1', 'replace').decode('latin-1')

        pdf.set_font(font_name, size=18)
        pdf.cell(200, 10, txt=f"Filtered Batch Report - {self.view_mode.title()}", ln=True, align='C')
        pdf.cell(200, 10, txt="---------------------------------------------------------", ln=True, align='C')

        for wrapper in self.filtered_items:
            item = wrapper["data"]
            if item.get("id", "Unknown") in self.export_selected_ids:
                pdf.set_font(font_name, size=14)
                pdf.cell(200, 10, txt=safe_txt(f"Batch: {item.get('name', 'Unknown')} ({item.get('type', '')}) - {wrapper['status']}"), ln=True)
                pdf.set_font(font_name, size=12)
                
                for log in item.get("timeline", []):
                    pdf.cell(200, 8, txt=safe_txt(f"   [{log.get('time', '')}] {log.get('step', '')} (Qty: {log.get('qty', item.get('quantity', 0))})"), ln=True)
                
                pdf.cell(200, 5, txt="", ln=True)

        file_path = os.path.join(os.path.expanduser("~"), "Desktop", f"Batch_Report_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        
        try:
            pdf.output(file_path)
            self.page.close(self.export_dialog)
            self.page.open(ft.SnackBar(content=ft.Text(f"PDF saved to Desktop: {os.path.basename(file_path)}", color="#FFFFFF"), bgcolor="#10B981"))
        except Exception as ex:
            self.page.open(ft.SnackBar(content=ft.Text(f"PDF generation failed: {str(ex)}", color="#FFFFFF"), bgcolor="#EF4444"))

    def open_revert_dialog(self, batch_name):
        self.revert_target_name = batch_name
        self.page.open(self.revert_dialog)
        self.page.update()

    def execute_revert(self, e):
        if self.revert_target_name and self.revert_cb:
            self.revert_cb(self.revert_target_name)
        self.page.close(self.revert_dialog)
        self.revert_target_name = ""
        self.page.update()

    def open_start_date(self, e):
        if hasattr(self.page, "open"): self.page.open(self.start_picker)
        else: self.start_picker.pick_date()

    def open_end_date(self, e):
        if hasattr(self.page, "open"): self.page.open(self.end_picker)
        else: self.end_picker.pick_date()

    def update_data(self, new_tab_data, view_mode="archive"):
        self.tab_data = new_tab_data
        self.view_mode = view_mode
        self.filter_title.value = self.t("Live Filter:") if self.view_mode == "live" else self.t("Archive Filter:")
        try: self.filter_title.update()
        except: pass
        self.render()

    def update_button_texts(self):
        self.start_btn.text = f"{self.t('Start:')} {self.start_date.strftime('%d %b %Y') if self.start_date else self.t('Any')}"
        self.end_btn.text = f"{self.t('End:')} {self.end_date.strftime('%d %b %Y') if self.end_date else self.t('Any')}"
        try:
            self.start_btn.update()
            self.end_btn.update()
        except: pass

    def on_start_change(self, e): 
        self.start_date = self.start_picker.value
        self.update_button_texts()
        self.render()

    def on_end_change(self, e): 
        self.end_date = self.end_picker.value
        self.update_button_texts()
        self.render()

    def on_search_change(self, e): 
        self.search_query = self.search_input.value.strip().lower()
        self.render()
    
    def clear_filters(self, e): 
        self.start_date = None
        self.end_date = None
        self.start_picker.value = None
        self.end_picker.value = None
        self.search_query = ""
        self.search_input.value = ""
        self.update_button_texts()
        try: self.search_input.update()
        except: pass
        self.render()
    
    def toggle_group(self, e, key_val, is_active):
        if not is_active:
            if e.data == "true": self.expanded_groups.add(key_val)
            else: self.expanded_groups.discard(key_val)

    def render(self):
        self.list_container.controls.clear()
        s = self.s
        
        all_items = []
        if self.view_mode == "archive":
            for item in self.tab_data.get("history", []):
                all_items.append({"data": item, "status": "Completed"})
        else: 
            for item in self.tab_data.get("active", []):
                all_items.append({"data": item, "status": "Active"})
            
        filtered_items = []
        for wrapper in all_items:
            item = wrapper["data"]
            
            if item.get("entry_type") == "Stock": continue
            
            if self.search_query:
                match = False
                search_str = self.search_query
                if search_str in item.get("name", "").lower() or search_str in item.get("type", "").lower() or search_str in item.get("action", "").lower():
                    match = True
                else:
                    for log in item.get("timeline", []):
                        if search_str in log.get("step", "").lower():
                            match = True
                            break
                if not match: continue
            
            dt_str = item.get("date") or item.get("date_completed")
            if not dt_str and "timeline" in item and item["timeline"]: dt_str = item["timeline"][-1]["time"]
            dt = parse_date(dt_str)
            if self.start_date and dt.date() < self.start_date.date(): continue
            if self.end_date and dt.date() > self.end_date.date(): continue
            filtered_items.append(wrapper)

        if not filtered_items:
            self.list_container.controls.append(ft.Container(padding=40, alignment=ft.alignment.center, content=ft.Text(self.t("No tracking logs match the current filters."), color="#64748B", size=s(16))))
            try: self.list_container.update() 
            except: pass
            return

        for wrapper in filtered_items:
            item = wrapper["data"]
            
            step_font_size = 22 if self.view_mode == "archive" else 21
            date_font_size = 17 if self.view_mode == "archive" else 16

            logs_ui = []
            for log in item.get("timeline", []):
                raw_step = log["step"]
                
                if "Started:" in raw_step or "Completed:" in raw_step or "Batch Finalized" in raw_step:
                    dt_obj = parse_date(log['time'])
                    time_formatted = dt_obj.strftime("%d %b %Y")
                    
                    prefix = ""
                    custom_name = raw_step

                    if raw_step.startswith("Started:"):
                        prefix = "Started:"
                        custom_name = raw_step[8:].strip()
                    elif raw_step.startswith("Completed:"):
                        prefix = "Completed:"
                        custom_name = raw_step[10:].strip()
                    elif "Batch Finalized" in raw_step:
                        prefix = "Batch Finalized & Archived"
                        custom_name = ""

                    translated_prefix = self.t(prefix) + " " if prefix else ""
                    qty_str = f"  [{log['qty']:g} {self.t('units')}]" if 'qty' in log else ""
                    
                    text_spans = []
                    if translated_prefix:
                        text_spans.append(ft.TextSpan(text=translated_prefix))
                    if custom_name:
                        text_spans.append(ft.TextSpan(text=custom_name, style=ft.TextStyle(size=s(step_font_size + 2), weight=ft.FontWeight.W_800)))
                    if qty_str:
                        text_spans.append(ft.TextSpan(text=qty_str, style=ft.TextStyle(size=s(step_font_size - 3), color="#64748B")))
                    
                    logs_ui.append(
                        ft.Row([
                            ft.Icon(ft.Icons.CIRCLE, size=s(10), color="#CBD5E1"), 
                            ft.Text(spans=text_spans, size=s(step_font_size), color="#0F172A", expand=True), 
                            ft.Text(time_formatted, size=s(date_font_size), color="#94A3B8")
                        ])
                    )

            is_active = (wrapper["status"] == "Active")
            status_color = "#2563EB" if is_active else "#10B981"
            status_text = "Live / In-Process" if is_active else "Archived / Complete"
            status_bg = "#EFF6FF" if is_active else "#F0FDF4"
            icon_type = ft.Icons.TRACK_CHANGES if is_active else ft.Icons.ARCHIVE_OUTLINED
            
            status_badge = ft.Container(padding=ft.padding.symmetric(horizontal=12, vertical=6), bgcolor=status_bg, border_radius=16, content=ft.Text(status_text, color=status_color, size=s(14), weight=ft.FontWeight.BOLD))

            revert_btn = ft.Container()
            if not is_active and self.revert_cb and "name" in item:
                revert_btn = ft.IconButton(
                    icon=ft.Icons.UNDO, 
                    icon_color="#FFFFFF",
                    bgcolor="#F59E0B",
                    tooltip=self.t("Revert back to Active"),
                    width=36, height=36, icon_size=20,
                    on_click=lambda e, n=item["name"]: self.open_revert_dialog(n) 
                )

            latest_time_str = ""
            if item.get('timeline'):
                dt_latest = parse_date(item['timeline'][-1]['time'])
                latest_time_str = dt_latest.strftime("%d %b %Y") 

            if logs_ui:
                controls_to_add = [ft.Divider(height=1, color="#E2E8F0"), ft.Container(padding=ft.padding.symmetric(horizontal=20, vertical=15), bgcolor="#F8FAFC", content=ft.Column(logs_ui, spacing=8))]
            else:
                controls_to_add = [ft.Divider(height=1, color="#E2E8F0"), ft.Container(padding=20, alignment=ft.alignment.center, content=ft.Text(self.t("No routing steps logged yet"), italic=True, color="#94A3B8", size=s(16)))]

            self.list_container.controls.append(
                ft.Container(
                    bgcolor="#FFFFFF", border_radius=12, border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=10, color="#00000008", offset=ft.Offset(0, 4)), 
                    content=ft.ExpansionTile(
                        title=ft.Column([
                            ft.Row([
                                ft.Text(f"{item.get('type', '')} - {item.get('name', '')}", weight=ft.FontWeight.W_800, color="#0F172A", size=s(18)), 
                                status_badge,
                                revert_btn
                            ], spacing=15), 
                        ], spacing=2), 
                        subtitle=ft.Text(f"{self.t('Total Tracked Qty:')} {item.get('quantity', 0):g} | {self.t('Latest update:')} {latest_time_str}", size=s(14), color="#64748B"), 
                        leading=ft.Container(padding=12, bgcolor=status_bg, border_radius=10, content=ft.Icon(icon_type, color=status_color, size=28)), 
                        controls_padding=0, 
                        controls=controls_to_add
                    )
                )
            )
        try: self.list_container.update()
        except: pass