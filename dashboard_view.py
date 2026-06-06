import flet as ft
from datetime import datetime
import os
import webbrowser

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
        self.current_dashboard_items = []
        
        self.padding = 10 
        
        def s(size): return int(size * self.scale_factor)
        self.s = s

        self.pdf_lang_dropdown = ft.Dropdown(
            label="Select PDF Language",
            options=[ft.dropdown.Option("English"), ft.dropdown.Option("Urdu (RTL)")],
            value="English", border_radius=8, focused_border_color="#8B5CF6", width=300
        )
        self.pdf_export_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Row([ft.Icon(ft.Icons.PICTURE_AS_PDF, color="#8B5CF6"), ft.Text("Export Daily Report", weight=ft.FontWeight.BOLD)]),
            content=ft.Column([ft.Text("Choose the language and format for your PDF report:"), self.pdf_lang_dropdown], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.pdf_export_dialog)),
                ft.ElevatedButton("Generate PDF", icon=ft.Icons.DOWNLOAD, style=ft.ButtonStyle(color="white", bgcolor="#8B5CF6", shape=ft.RoundedRectangleBorder(radius=8)), on_click=self.execute_dashboard_pdf)
            ]
        )

        self.dash_title = ft.Text(self.t("Global Overview"), size=s(26), weight=ft.FontWeight.W_800, color="#0F172A")
        self.dash_list = ft.Column(spacing=8) 
        self.dash_date = datetime.now()

        self.dash_date_btn = ft.ElevatedButton(
            f"{self.t('Date:')} {self.dash_date.strftime('%d %b %Y')}", 
            icon=ft.Icons.CALENDAR_TODAY, elevation=0, 
            style=ft.ButtonStyle(color="#0F172A", bgcolor="#F1F5F9", shape=ft.RoundedRectangleBorder(radius=8))
        )

        self.dash_date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1), last_date=datetime(2050, 12, 31), 
            current_date=self.dash_date, on_change=self.on_date_change
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
                    ft.IconButton(ft.Icons.RESTORE, on_click=self.reset_date, tooltip=self.t("Reset to Today"), icon_color="#3B82F6", bgcolor="#EFF6FF"),
                    ft.ElevatedButton(self.t("Generate PDF Report"), icon=ft.Icons.PICTURE_AS_PDF, style=ft.ButtonStyle(color="white", bgcolor="#8B5CF6", shape=ft.RoundedRectangleBorder(radius=8)), on_click=self.open_dashboard_pdf_dialog)
                ], wrap=True) 
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)
        )

        self.content = ft.Column([
            ft.Row([self.dash_title], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), 
            ft.Container(height=s(5)), self.filter_container, ft.Container(height=s(5)), self.dash_list
        ], expand=True, scroll=ft.ScrollMode.AUTO)

    def open_dashboard_pdf_dialog(self, e):
        if not self.current_dashboard_items:
            self.page.open(ft.SnackBar(content=ft.Text("No data to export for this date.", color="#FFFFFF"), bgcolor="#EF4444"))
            return
        self.page.open(self.pdf_export_dialog)
        self.page.update()

    def execute_dashboard_pdf(self, e):
        self.page.close(self.pdf_export_dialog)
        is_urdu = self.pdf_lang_dropdown.value == "Urdu (RTL)"
        
        dir_attr = "rtl" if is_urdu else "ltr"
        lang_attr = "ur" if is_urdu else "en"
        
        title_txt = "ڈیلی فیکٹری کی رپورٹ" if is_urdu else "Daily Factory Overview"
        report_date = self.dash_date.strftime('%d %b %Y')
        date_txt = f"تاریخ: <bdi dir='ltr'>{report_date}</bdi>" if is_urdu else f"Activity Date: {report_date}"
        
        def t_pdf(text):
            if not is_urdu: return text
            pdf_dict = {"Started:": "شروع ہوا:", "Completed:": "مکمل ہوا:", "Batch Finalized & Archived": "بیچ مکمل اور محفوظ کر دیا گیا", "Location:": "مقام:", "Qty:": "مقدار:"}
            return pdf_dict.get(text, text)

        # Build Compact HTML Template with Bigger Bold Fonts
        html = f"""<!DOCTYPE html>
        <html dir="{dir_attr}" lang="{lang_attr}">
        <head>
            <meta charset="utf-8">
            <title>{title_txt}</title>
            <style>
                @font-face {{ font-family: 'Jameel Noori'; src: local('Jameel Noori Nastaleeq'), local('Jameel Noori'), url('assets/Jameel Noori.ttf'); }}
                body {{ font-family: 'Jameel Noori', Tahoma, Arial, sans-serif; padding: 20px; color: #1e293b; background: #f8fafc; line-height: 1.2; }}
                .report-box {{ background: white; border: 1px solid #e2e8f0; max-width: 800px; margin: 0 auto; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
                .header {{ background: #2563eb; color: white; padding: 15px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 32px; font-weight: 900; letter-spacing: 0.5px; }}
                .header p {{ margin: 5px 0 0 0; font-size: 18px; font-weight: 900; opacity: 0.95; }}
                .batch-item {{ margin: 10px; border: 2px solid #cbd5e1; border-radius: 6px; overflow: hidden; page-break-inside: avoid; }}
                .b-head {{ background: #f1f5f9; padding: 8px 12px; font-size: 24px; font-weight: 900; color: #0f172a; border-bottom: 2px solid #cbd5e1; display: flex; justify-content: space-between; align-items: center; }}
                .b-loc {{ padding: 6px 12px; font-size: 18px; font-weight: 900; color: #334155; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }}
                .log-list {{ list-style-type: none; padding: 0; margin: 0; }}
                .log-item {{ padding: 6px 12px; border-bottom: 1px dashed #e2e8f0; display: flex; align-items: center; gap: 10px; }}
                .log-item:last-child {{ border-bottom: none; }}
                .time-badge {{ background: #e2e8f0; padding: 3px 8px; border-radius: 4px; font-size: 16px; font-weight: 900; color: #334155; white-space: nowrap; direction: ltr; }}
                .step-text {{ flex-grow: 1; font-weight: 900; color: #0f172a; font-size: 20px; }}
                .qty-text {{ font-size: 18px; color: #059669; font-weight: 900; white-space: nowrap; }}
                
                @media print {{ 
                    @page {{ margin: 5mm; }} 
                    body {{ padding: 0; background: white; }} 
                    .report-box {{ border: none; box-shadow: none; margin: 0; max-width: 100%; }} 
                    .header {{ padding: 12px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }} 
                    .batch-item {{ margin: 6px 0; border: 1.5px solid #94a3b8; }}
                    .log-item {{ padding: 4px 10px; }}
                    .b-head, .b-loc, .time-badge {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                }}
            </style>
        </head>
        <body onload="window.print()">
            <div class="report-box">
                <div class="header">
                    <h1>{title_txt}</h1>
                    <p>{date_txt}</p>
                </div>
        """

        for d_item in self.current_dashboard_items:
            item = d_item["item"]
            loc_str = f"[{d_item['fac']} > {d_item['loc']} > {d_item['sub_name']}]"
            batch_name = str(item.get('name', 'Unknown')).replace("<", "&lt;")
            product_type = str(item.get('type', 'Unknown')).replace("<", "&lt;")
            
            b_title = f"{batch_name} - {product_type}" if is_urdu else f"{product_type} - {batch_name}"
            
            html += f"""
                <div class="batch-item">
                    <div class="b-head"><span>{b_title}</span></div>
                    <div class="b-loc"><strong>{t_pdf("Location:")}</strong> <bdi dir="ltr">{loc_str}</bdi></div>
                    <ul class="log-list">
            """
            
            for log in d_item["valid_logs"]:
                raw_step = log.get('step', '')
                
                # STRICT FILTER: Only meaningful steps
                if not any(x in raw_step for x in ["Started:", "Completed:", "Batch Finalized"]):
                    continue

                dt_obj = parse_date(log['time'])
                time_formatted = dt_obj.strftime("%I:%M %p")
                qty_val = log.get('qty', item.get('quantity', 0))
                
                custom_name = raw_step.replace("<", "&lt;")
                prefix = ""
                if raw_step.startswith("Started:"):
                    prefix = t_pdf("Started:")
                    custom_name = raw_step[8:].strip().replace("<", "&lt;")
                elif raw_step.startswith("Completed:"):
                    prefix = t_pdf("Completed:")
                    custom_name = raw_step[10:].strip().replace("<", "&lt;")
                elif "Batch Finalized" in raw_step:
                    prefix = t_pdf("Batch Finalized & Archived")
                    custom_name = ""
                    
                step_html = f"<span style='color:#64748b; font-weight:900;'>{prefix}</span> {custom_name}".strip()
                
                html += f"""
                        <li class="log-item">
                            <span class="time-badge"><bdi dir="ltr">{time_formatted}</bdi></span>
                            <span class="step-text">{step_html}</span>
                            <span class="qty-text">{t_pdf("Qty:")} <bdi dir="ltr">{qty_val:g}</bdi></span>
                        </li>
                """
            html += "</ul></div>"
            
        html += "</div></body></html>"

        export_dir = os.path.join(os.getcwd(), "Exported_PDFs")
        os.makedirs(export_dir, exist_ok=True)
        lang_suffix = "Urdu" if is_urdu else "English"
        file_path = os.path.join(export_dir, f"Daily_Report_{self.dash_date.strftime('%Y%m%d')}_{lang_suffix}.html")
        
        try:
            with open(file_path, "w", encoding="utf-8") as f: f.write(html)
            if os.name == 'nt': os.startfile(file_path)
            else: webbrowser.open(f"file://{os.path.abspath(file_path)}")
            self.page.open(ft.SnackBar(content=ft.Text("Printable Report Opened!", color="#FFFFFF"), bgcolor="#10B981"))
        except Exception as ex:
            self.page.open(ft.SnackBar(content=ft.Text(f"Export failed: {str(ex)}", color="#FFFFFF"), bgcolor="#EF4444"))

    def update_buttons(self):
        self.dash_date_btn.text = f"{self.t('Date:')} {self.dash_date.strftime('%d %b %Y')}"
        try: self.dash_date_btn.update()
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
        self.current_dashboard_items = dashboard_items
        
        if not dashboard_items:
            self.dash_list.controls.append(ft.Container(padding=20, alignment=ft.alignment.center, content=ft.Text(self.t("No active or completed processes found for this specific date."), color="#64748B", size=s(16))))
            try: self.dash_list.update()
            except: pass
            return
            
        for d_item in dashboard_items:
            item = d_item["item"]; status_type = d_item["status_type"]; valid_logs = d_item["valid_logs"]
            loc_label = self.t("Current") if status_type == "active" else self.t("Final")
            
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
            
            timeline_controls = []
            for i, log in enumerate(valid_logs):
                color = "#0F172A" if i == 0 else "#64748B"
                weight = ft.FontWeight.W_600 if i == 0 else ft.FontWeight.NORMAL
                dt_obj = parse_date(log['time'])
                time_formatted = dt_obj.strftime("%d %b %Y") 
                
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
                qty_str = f"  [{log.get('qty', item.get('quantity', 0)):g} {self.t('units')}]"
                
                text_spans = []
                if translated_prefix:
                    text_spans.append(ft.TextSpan(text=translated_prefix))
                if custom_name:
                    text_spans.append(ft.TextSpan(text=custom_name, style=ft.TextStyle(size=s(19 + 2), weight=ft.FontWeight.W_800)))
                if qty_str:
                    text_spans.append(ft.TextSpan(text=qty_str, style=ft.TextStyle(size=s(19 - 3), color="#64748B")))
                
                timeline_controls.append(
                    ft.Row([
                        ft.Icon(ft.Icons.CIRCLE, size=s(10), color="#CBD5E1"), 
                        ft.Text(spans=text_spans, size=s(19), color=color, weight=weight, expand=True), 
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

            status_chip = ft.Container(
                padding=ft.padding.symmetric(horizontal=s(8), vertical=s(4)), 
                bgcolor=chip_bg, border_radius=12, 
                content=ft.Text(chip_text, size=s(13), color=chip_color, weight=ft.FontWeight.BOLD)
            )
            
            batch_badge = ft.Container(
                padding=ft.padding.symmetric(horizontal=s(10), vertical=s(4)), bgcolor="#EFF6FF", border_radius=6,
                content=ft.Row([ft.Icon(ft.Icons.TAG, size=s(16), color="#2563EB"), ft.Text(f"{self.t('Batch')} {display_tag}", size=s(16), weight=ft.FontWeight.W_900, color="#2563EB")], spacing=s(4), tight=True)
            )

            header_row = ft.Row([
                ft.Text(product_name, size=s(24), weight=ft.FontWeight.W_900, color="#0F172A"),
                batch_badge, ft.Container(expand=True), status_chip
            ], spacing=s(12), alignment=ft.MainAxisAlignment.START)

            dash_card = ft.Container(
                bgcolor="#FFFFFF", border_radius=12, padding=s(16), border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=8, color="#00000005", offset=ft.Offset(0, 2)), 
                content=ft.Row([
                    ft.Container(padding=s(10), bgcolor="#F8FAFC", border_radius=10, content=ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color=icon_color, size=s(24))),
                    ft.Column([header_row, subtitle_col], expand=True, spacing=s(6)),
                ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=s(12))
            )
            self.dash_list.controls.append(dash_card)
        try: self.dash_list.update()
        except: pass