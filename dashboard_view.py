import flet as ft
from datetime import datetime

def parse_date(date_str):
    try: return datetime.strptime(date_str, "%Y-%m-%d %I:%M %p")
    except ValueError:
        try: return datetime.strptime(date_str, "%I:%M %p, %d %b")
        except: return datetime.now()

class DashboardView(ft.Container):
    def __init__(self, page: ft.Page, level3_data: dict, t, scale: float):
        super().__init__()
        self.page = page
        self.level3_data = level3_data
        self.t = t
        self.scale_factor = scale
        self.expand = True
        self.visible = False
        
        self.padding = 10 
        
        def s(size): return int(size * self.scale_factor)
        self.s = s

        self.dash_title = ft.Text(self.t("Global Overview"), size=s(26), weight=ft.FontWeight.W_800, color="#0F172A")
        
        self.dash_list = ft.Column(spacing=8) 

        self.dash_date = datetime.now()

        self.dash_date_btn = ft.ElevatedButton(
            f"{self.t('Date:')} {self.dash_date.strftime('%d %b %Y')}", 
            icon=ft.Icons.CALENDAR_TODAY, 
            elevation=0, 
            style=ft.ButtonStyle(color="#0F172A", bgcolor="#F1F5F9", shape=ft.RoundedRectangleBorder(radius=8))
        )

        self.dash_date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1), 
            last_date=datetime(2050, 12, 31), 
            current_date=self.dash_date, 
            on_change=self.on_date_change
        )
        
        if self.dash_date_picker not in self.page.overlay:
            self.page.overlay.append(self.dash_date_picker)

        self.dash_date_btn.on_click = lambda _: self.page.open(self.dash_date_picker) if hasattr(self.page, "open") else self.dash_date_picker.pick_date()

        self.filter_container = ft.Container(
            padding=s(10), bgcolor="#FFFFFF", border_radius=12, border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=10, color="#00000005", offset=ft.Offset(0, 2)), 
            content=ft.Row([
                ft.Row([ft.Icon(ft.Icons.FILTER_ALT, color="#64748B", size=s(20)), ft.Text(self.t("Activity Date Filter:"), color="#64748B", weight=ft.FontWeight.W_600, size=s(15))]),
                ft.Row([
                    self.dash_date_btn,
                    ft.IconButton(ft.Icons.RESTORE, on_click=self.reset_date, tooltip=self.t("Reset to Today"), icon_color="#3B82F6", bgcolor="#EFF6FF")
                ], wrap=True) 
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)
        )

        self.content = ft.Column([
            ft.Row([self.dash_title], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), 
            ft.Container(height=s(5)),
            self.filter_container, 
            ft.Container(height=s(5)), 
            self.dash_list
        ], expand=True, scroll=ft.ScrollMode.AUTO)

    def update_buttons(self):
        self.dash_date_btn.text = f"{self.t('Date:')} {self.dash_date.strftime('%d %b %Y')}"
        try:
            self.dash_date_btn.update()
        except: pass

    def on_date_change(self, e): 
        if self.dash_date_picker.value:
            self.dash_date = self.dash_date_picker.value
            self.update_buttons()
            self.render()

    def reset_date(self, e): 
        self.dash_date = datetime.now()
        self.dash_date_picker.value = self.dash_date
        self.update_buttons()
        self.render()

    def render(self):
        self.dash_list.controls.clear()
        s = self.s
        dashboard_items = []
        
        for key, loc_data in self.level3_data.items():
            fac, loc = key.split("::")
            for sub_name, tab_data in loc_data["data"].items():
                for status_type, item_list in [("active", tab_data.get("active", [])), ("completed", tab_data.get("history", []))]:
                    for item in item_list:
                        if status_type == "completed" and item.get("entry_type") != "Batch": continue
                        valid_logs = []
                        for log in item.get("timeline", []):
                            step_text = log.get("step", "")
                            if "Started:" not in step_text and "Completed:" not in step_text and "Batch Finalized" not in step_text:
                                continue

                            log_time = parse_date(log["time"])
                            if self.dash_date and log_time.date() != self.dash_date.date(): continue
                            
                            valid_logs.append(log)
                            
                        if not valid_logs: continue 
                        valid_logs.reverse()
                        latest_time = parse_date(valid_logs[0]["time"])
                        dashboard_items.append({"item": item, "fac": fac, "loc": loc, "sub_name": sub_name, "status_type": status_type, "valid_logs": valid_logs, "latest_time": latest_time})
        
        dashboard_items.sort(key=lambda x: x["latest_time"], reverse=True)
        
        if not dashboard_items:
            self.dash_list.controls.append(ft.Container(padding=20, alignment=ft.alignment.center, content=ft.Text(self.t("No active or completed processes found for this specific date."), color="#64748B", size=s(16))))
            try: self.dash_list.update()
            except: pass
            return
            
        for d_item in dashboard_items:
            item = d_item["item"]; status_type = d_item["status_type"]; valid_logs = d_item["valid_logs"]
            loc_label = self.t("Current") if status_type == "active" else self.t("Final")
            
            timeline_controls = []
            for i, log in enumerate(valid_logs):
                color = "#0F172A" if i == 0 else "#64748B"
                weight = ft.FontWeight.W_600 if i == 0 else ft.FontWeight.NORMAL
                dt_obj = parse_date(log['time'])
                
                time_formatted = dt_obj.strftime("%d %b %Y") 
                
                # --- NEW TEXT ISOLATION LOGIC ---
                raw_step = log.get('step', '')
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
                
                step_font_size = 19
                
                text_spans = []
                if translated_prefix:
                    text_spans.append(ft.TextSpan(text=translated_prefix))
                if custom_name:
                    # ONLY THE CUSTOM STEP NAME IS INCREASED AND BOLDED
                    text_spans.append(ft.TextSpan(text=custom_name, style=ft.TextStyle(size=s(step_font_size + 2), weight=ft.FontWeight.W_800)))
                if qty_str:
                    text_spans.append(ft.TextSpan(text=qty_str, style=ft.TextStyle(size=s(step_font_size - 3), color="#64748B")))
                
                timeline_controls.append(
                    ft.Row([
                        ft.Icon(ft.Icons.CIRCLE, size=s(10), color="#CBD5E1"), 
                        ft.Text(spans=text_spans, size=s(step_font_size), color=color, weight=weight, expand=True), 
                        ft.Text(time_formatted, size=s(14), color="#94A3B8")
                    ], spacing=s(8))
                )
                
            subtitle_col = ft.Column([
                ft.Container(height=s(4)), 
                ft.Row([
                    ft.Icon(ft.Icons.LOCATION_ON, size=s(16), color="#94A3B8"), 
                    ft.Text(f"{loc_label}: {d_item['fac']} → {d_item['loc']} → {d_item['sub_name']}", size=s(16), color="#64748B", weight=ft.FontWeight.W_600, expand=True)
                ], spacing=s(6)), 
                ft.Container(padding=ft.padding.only(left=s(6), top=s(4)), content=ft.Column(timeline_controls, spacing=s(4)))
            ], spacing=0)

            product_name = item.get('type', 'Unknown')
            display_tag = str(item.get('name', '')).replace("Batch ", "")

            if status_type == "active":
                icon_color = "#2563EB"
                chip_bg = "#FEF3C7" if item.get("is_processing") else "#DBEAFE"
                chip_color = "#D97706" if item.get("is_processing") else "#2563EB"
                chip_text = self.t("In Process") if item.get("is_processing") else self.t("Pending")
            else:
                icon_color = "#10B981"
                chip_bg = "#D1FAE5"
                chip_color = "#059669"
                chip_text = self.t("Completed")

            status_chip = ft.Container(padding=ft.padding.symmetric(horizontal=s(8), vertical=s(4)), bgcolor=chip_bg, border_radius=12, content=ft.Text(chip_text, size=s(13), color=chip_color, weight=ft.FontWeight.BOLD))
            
            batch_badge = ft.Container(
                padding=ft.padding.symmetric(horizontal=s(10), vertical=s(4)),
                bgcolor="#EFF6FF",
                border_radius=6,
                content=ft.Row([
                    ft.Icon(ft.Icons.TAG, size=s(16), color="#2563EB"),
                    ft.Text(f"{self.t('Batch')} {display_tag}", size=s(16), weight=ft.FontWeight.W_900, color="#2563EB")
                ], spacing=s(4), tight=True)
            )

            product_title = ft.Text(product_name, size=s(24), weight=ft.FontWeight.W_900, color="#0F172A")

            header_row = ft.Row([
                product_title,
                batch_badge,
                ft.Container(expand=True), 
                status_chip
            ], spacing=s(12), alignment=ft.MainAxisAlignment.START)

            dash_card = ft.Container(
                bgcolor="#FFFFFF", border_radius=12, padding=s(16), border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=8, color="#00000005", offset=ft.Offset(0, 2)), 
                content=ft.Row([
                    ft.Container(padding=s(10), bgcolor="#F8FAFC", border_radius=10, content=ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color=icon_color, size=s(24))),
                    ft.Column([
                        header_row,
                        subtitle_col
                    ], expand=True, spacing=s(6)),
                ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=s(12))
            )
            self.dash_list.controls.append(dash_card)
        try: self.dash_list.update()
        except: pass