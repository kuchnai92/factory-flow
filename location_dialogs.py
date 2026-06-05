import flet as ft
from datetime import datetime

TEXT_MAIN = "#0F172A"
TEXT_SUB = "#64748B"
PRIMARY = "#2563EB"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
BORDER = "#E2E8F0"

class LocationDialogsMixin:
    def setup_dialogs(self):
        s = self.s
        dlg_shape = ft.RoundedRectangleBorder(radius=12)

        def get_btn_style(bg, fg):
            return ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8), 
                bgcolor=bg, 
                color=fg,
                text_style=ft.TextStyle(font_family="Jameel Noori")
            )

        ts_base = ft.TextStyle(font_family="Jameel Noori", color=TEXT_MAIN)
        ts_large = ft.TextStyle(font_family="Jameel Noori", size=s(18), weight=ft.FontWeight.BOLD, color=TEXT_MAIN)

        self.step_date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1), 
            last_date=datetime(2050, 12, 31),
            on_change=self.execute_edit_step_date
        )
        self.step_date_picker_data = None

        # --- NEW STEP QTY EDIT DIALOG ---
        self.edit_step_qty_input = ft.TextField(label=self.t("New Quantity"), border_radius=8, focused_border_color=PRIMARY, autofocus=False, text_style=ts_base, on_submit=self.execute_edit_step_qty)
        self.edit_step_qty_data = None
        self.edit_step_qty_dialog = ft.AlertDialog(
            shape=dlg_shape, 
            title=ft.Text(self.t("Edit Step Quantity"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), 
            content=self.edit_step_qty_input,
            actions=[
                ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.edit_step_qty_dialog), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), 
                ft.ElevatedButton(self.t("Save"), on_click=self.execute_edit_step_qty, style=get_btn_style(PRIMARY, "#FFFFFF"))
            ]
        )

        self.l3_name_input = ft.TextField(label=self.t("Sub-Location Name"), autofocus=False, border_radius=8, focused_border_color=PRIMARY, on_submit=self.save_l3_tab, text_style=ts_base)
        self.l3_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text(self.t("New Sub-Location"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), content=self.l3_name_input, actions=[ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.l3_dialog), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), ft.ElevatedButton(self.t("Save"), on_click=self.save_l3_tab, style=get_btn_style(PRIMARY, "#FFFFFF"))])

        self.l3_target_edit_name = ""
        self.l3_edit_name_input = ft.TextField(label=self.t("Sub-Location Name"), autofocus=False, border_radius=8, focused_border_color=PRIMARY, on_submit=self.save_edit_l3_tab, text_style=ts_base)
        self.l3_edit_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text(self.t("Edit Location"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), content=self.l3_edit_name_input, actions=[ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.l3_edit_dialog), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), ft.ElevatedButton(self.t("Save"), on_click=self.save_edit_l3_tab, style=get_btn_style(PRIMARY, "#FFFFFF"))])

        self.l3_target_delete_name = ""
        self.delete_l3_btn_confirm = ft.ElevatedButton(self.t("Delete"), on_click=self.execute_delete_l3, style=get_btn_style("#EF4444", "white"))
        self.delete_l3_confirm_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text(self.t("Confirm Delete"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), content=ft.Text(self.t("Are you sure you want to delete this?"), size=s(14), font_family="Jameel Noori"), actions=[ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.delete_l3_confirm_dialog), style=ft.ButtonStyle(text_style=ts_base)), self.delete_l3_btn_confirm])
        
        self.process_batch_input = ft.TextField(label=self.t("Batch Identifier"), border_radius=8, focused_border_color=PRIMARY, read_only=True, text_style=ts_base)
        self.process_qty_input = ft.TextField(label=self.t("Quantity to Process"), border_radius=8, focused_border_color=PRIMARY, on_submit=self.execute_process, autofocus=False, text_style=ts_base)
        self.process_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text(self.t("Start Processing"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), content=ft.Column([self.process_batch_input, self.process_qty_input], tight=True), actions=[ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.process_dialog), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), ft.ElevatedButton(self.t("Launch Batch"), on_click=self.execute_process, style=get_btn_style(PRIMARY, "#FFFFFF"))])
        
        self.confirm_text = ft.Text("", size=s(14), font_family="Jameel Noori")
        self.confirm_btn = ft.ElevatedButton("Yes", on_click=self.execute_step, style=get_btn_style(PRIMARY, "#FFFFFF"))
        self.confirm_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text(self.t("Confirm Action"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), content=self.confirm_text, actions=[ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.confirm_dialog), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), self.confirm_btn])
        
        self.swap_confirm_btn = ft.ElevatedButton(self.t("Yes, Swap"), on_click=self.execute_step_swap, style=get_btn_style(PRIMARY, "#FFFFFF"))
        self.swap_confirm_text = ft.Text("", size=s(14), font_family="Jameel Noori")
        self.swap_dialog = ft.AlertDialog(
            shape=dlg_shape, 
            title=ft.Text(self.t("Confirm Swap"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), 
            content=self.swap_confirm_text, 
            actions=[
                ft.TextButton(self.t("Cancel"), on_click=lambda e: (setattr(self, 'pending_step_swap', None), self.page.close(self.swap_dialog)), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), 
                self.swap_confirm_btn
            ]
        )

        self.delete_type_data = None
        self.delete_step_btn = ft.ElevatedButton(self.t("Delete"), on_click=self.execute_delete_step, style=get_btn_style("#EF4444", "white"))
        self.delete_confirm_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text(self.t("Confirm Delete"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), content=ft.Text(self.t("Are you sure you want to delete this?"), size=s(14), font_family="Jameel Noori"), actions=[ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.delete_confirm_dialog), style=ft.ButtonStyle(text_style=ts_base)), self.delete_step_btn])

        self.cancel_to_stock_qty_input = ft.TextField(label=self.t("Quantity to Return"), border_radius=8, focused_border_color=WARNING, autofocus=False, text_style=ts_base)
        self.cancel_to_stock_dialog = ft.AlertDialog(
            shape=dlg_shape, 
            title=ft.Text(self.t("Return to Stock"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), 
            content=ft.Column([ft.Text(self.t("Enter quantity to return from batch to raw stock."), font_family="Jameel Noori"), self.cancel_to_stock_qty_input], tight=True),
            actions=[ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.cancel_to_stock_dialog), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), ft.ElevatedButton(self.t("Confirm"), on_click=self.execute_cancel_to_stock, style=get_btn_style(WARNING, "#FFFFFF"))]
        )

        self.step_dropdown = ft.Dropdown(label=self.t("Select Process Step"), border_radius=8, focused_border_color=PRIMARY, text_size=s(18), text_style=ts_large, color=TEXT_MAIN)
        self.custom_step_input = ft.TextField(label=self.t("Create New Step"), border_radius=8, focused_border_color=PRIMARY, visible=False, on_submit=self.execute_custom_step, text_size=s(18), text_style=ts_large)
        self.custom_step_pos_input = ft.TextField(label=self.t("Insert at Position (Optional)"), value="", border_radius=8, focused_border_color=PRIMARY, on_submit=self.execute_custom_step, text_size=s(18), text_style=ts_large)
        self.mode_toggle_btn = ft.TextButton(self.t("Create New"), on_click=self.toggle_step_mode, style=ft.ButtonStyle(color=PRIMARY, text_style=ts_base))

        self.step_dialog = ft.AlertDialog(
            shape=dlg_shape, 
            title=ft.Text(self.t("Add Routing Step"), weight=ft.FontWeight.BOLD, size=s(21), font_family="Jameel Noori"), 
            content=ft.Column([self.step_dropdown, self.custom_step_input, self.custom_step_pos_input], tight=True), 
            actions=[
                ft.Row([
                    self.mode_toggle_btn,
                    ft.Container(expand=True),
                    ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.step_dialog), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), 
                    ft.ElevatedButton(self.t("Insert Step"), on_click=self.execute_custom_step, style=get_btn_style(TEXT_MAIN, "#FFFFFF"))
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]
        )
        
        self.complete_btn = ft.ElevatedButton(self.t("Yes, Complete"), on_click=self.execute_complete_batch, style=get_btn_style(SUCCESS, "#FFFFFF"))
        self.complete_batch_text = ft.Text(self.t("Finish this batch and securely log it into history?"), size=s(14), font_family="Jameel Noori")
        self.complete_batch_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text(self.t("Complete Batch"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), content=self.complete_batch_text, actions=[ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.complete_batch_dialog), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), self.complete_btn])
        
        self.move_confirm_btn = ft.ElevatedButton(self.t("Execute Move"), on_click=self.execute_move, style=get_btn_style(WARNING, "#FFFFFF"))
        self.move_fac_dd = ft.Dropdown(label=self.t("1. Destination Factory"), on_change=self.on_move_fac_change, border_radius=8, focused_border_color=WARNING, text_size=s(18), text_style=ts_large, color=TEXT_MAIN)
        self.move_loc_dd = ft.Dropdown(label=self.t("2. Destination Room"), on_change=self.on_move_loc_change, border_radius=8, focused_border_color=WARNING, text_size=s(18), text_style=ts_large, color=TEXT_MAIN)
        self.move_sub_dd = ft.Dropdown(label=self.t("3. Destination Sub-Zone"), border_radius=8, focused_border_color=WARNING, text_size=s(18), text_style=ts_large, color=TEXT_MAIN)
        self.move_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text(self.t("Relocate Batch"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), content=ft.Column([self.move_fac_dd, self.move_loc_dd, self.move_sub_dd], tight=True), actions=[ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.move_dialog), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), self.move_confirm_btn])

        self.split_confirm_btn = ft.ElevatedButton(self.t("Confirm Split"), on_click=self.execute_split, style=get_btn_style(WARNING, "#FFFFFF"))
        self.split_avail_qty_label = ft.Text(weight=ft.FontWeight.W_600, color=PRIMARY, size=s(14), font_family="Jameel Noori")
        self.split_num_input = ft.TextField(label=self.t("Number of Branches"), value="1", border_radius=8, focused_border_color=WARNING, on_change=self.build_split_fields, on_submit=self.execute_split, text_style=ts_base)
        self.split_fields_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=200)
        self.split_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text(self.t("Split Batch"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), content=ft.Column([self.split_avail_qty_label, self.split_num_input, self.split_fields_container], tight=True), actions=[ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.split_dialog), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), self.split_confirm_btn])

        self.merge_confirm_btn = ft.ElevatedButton(self.t("Merge"), on_click=self.execute_merge, style=get_btn_style(PRIMARY, "#FFFFFF"))
        self.merge_dd = ft.Dropdown(label=self.t("Select Target Batch"), border_radius=8, focused_border_color=PRIMARY, text_size=s(18), text_style=ts_large, color=TEXT_MAIN)
        self.merge_dialog = ft.AlertDialog(shape=dlg_shape, title=ft.Text(self.t("Merge Batch"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), content=self.merge_dd, actions=[ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.merge_dialog), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), self.merge_confirm_btn])

        self.add_qty_input = ft.TextField(label=self.t("Quantity (+ to add, - to remove)"), border_radius=8, focused_border_color=PRIMARY, on_submit=self.execute_add_qty, text_style=ts_base)
        self.free_stock_checkbox = ft.Checkbox(label=self.t("Free Stock (Do not affect raw stock)"), value=False, label_position=ft.LabelPosition.RIGHT)
        self.add_qty_dialog = ft.AlertDialog(
            shape=dlg_shape, 
            title=ft.Text(self.t("Add Quantity"), weight=ft.FontWeight.BOLD, size=s(18), font_family="Jameel Noori"), 
            content=ft.Column([self.add_qty_input, self.free_stock_checkbox], tight=True), 
            actions=[ft.TextButton(self.t("Cancel"), on_click=lambda e: self.page.close(self.add_qty_dialog), style=ft.ButtonStyle(color=TEXT_SUB, text_style=ts_base)), ft.ElevatedButton(self.t("Submit"), on_click=self.execute_add_qty, style=get_btn_style(SUCCESS, "#FFFFFF"))]
        )

    # --- OPEN STEP DATE PICKER LOGIC ---
    def open_step_date_picker(self, item_id, log_idx, current_dt_obj):
        self.step_date_picker_data = {"item_id": item_id, "log_idx": log_idx}
        self.step_date_picker.current_date = current_dt_obj
        if self.step_date_picker not in self.page.overlay:
            self.page.overlay.append(self.step_date_picker)
            self.page.update()
        if hasattr(self.page, "open"):
            self.page.open(self.step_date_picker)
        else:
            self.step_date_picker.pick_date()

    # --- OPEN STEP QTY EDIT LOGIC ---
    def open_edit_step_qty(self, item_id, log_idx, current_qty):
        self.edit_step_qty_data = {"item_id": item_id, "log_idx": log_idx}
        self.edit_step_qty_input.value = f"{current_qty:g}"
        self.page.open(self.edit_step_qty_dialog)
        self.page.update()
        try: self.edit_step_qty_input.focus()
        except: pass

    def open_add_l3_dialog(self, e): 
        self.l3_name_input.value = ""
        self.page.open(self.l3_dialog)
        self.page.update()
        try: self.l3_name_input.focus()
        except: pass

    def on_edit_l3_click(self, e):
        data_ctx = self.get_current_data()
        if data_ctx["tabs"]:
            name = data_ctx["tabs"][data_ctx["active_tab"]]
            self.open_edit_l3_dialog(name)

    def open_edit_l3_dialog(self, name):
        self.l3_target_edit_name = name
        self.l3_edit_name_input.value = name
        self.page.open(self.l3_edit_dialog)
        self.page.update()
        try: self.l3_edit_name_input.focus()
        except: pass

    def on_delete_l3_click(self, e):
        data_ctx = self.get_current_data()
        if data_ctx["tabs"]:
            name = data_ctx["tabs"][data_ctx["active_tab"]]
            self.confirm_delete_l3(name)

    def confirm_delete_l3(self, name):
        self.l3_target_delete_name = name
        self.page.open(self.delete_l3_confirm_dialog)
        self.page.update()
        try: self.delete_l3_btn_confirm.focus()
        except: pass

    def open_process_dialog(self, product_name):
        self.current_process_product = product_name
        self.process_batch_input.value = self.get_unique_batch_name(product_name)
        self.process_qty_input.value = ""
        self.page.open(self.process_dialog)
        self.page.update()
        try: self.process_qty_input.focus()
        except: pass

    def build_split_fields(self, e=None):
        self.split_fields_container.controls.clear()
        try: num = int(self.split_num_input.value)
        except: num = 0
        if num > 15: num = 15 
        
        item = self.get_item_by_id(self.current_action_item)
        if not item: return
        base_name = item['name'].split('.')[0]
        
        existing_names = self.get_all_batch_names_for_product(item["type"])
        max_suf = 1
        for name in existing_names:
            if name.startswith(base_name + "."):
                try:
                    suf = int(name.split(".")[-1])
                    if suf > max_suf: max_suf = suf
                except: pass
        
        for i in range(num):
            max_suf += 1
            name_f = ft.TextField(label=self.t("Branch Name"), value=f"{base_name}.{max_suf}", expand=True, border_radius=8, focused_border_color=WARNING, read_only=True, text_style=ft.TextStyle(font_family="Jameel Noori", color=TEXT_MAIN))
            qty_f = ft.TextField(label=self.t("Branch Qty"), width=90, border_radius=8, focused_border_color=WARNING, on_submit=self.execute_split, text_style=ft.TextStyle(font_family="Jameel Noori", color=TEXT_MAIN))
            self.split_fields_container.controls.append(ft.Row([name_f, qty_f]))
        if self.page: self.page.update()

    def open_split(self, item_id):
        self.current_action_item = item_id; item = self.get_item_by_id(item_id)
        self.split_avail_qty_label.value = f"{self.t('Available Qty:')} {item['quantity']:g}"
        self.split_num_input.value = "1"
        self.build_split_fields()
        self.page.open(self.split_dialog)
        self.page.update()
        try: self.split_num_input.focus()
        except: pass

    def open_merge(self, item_id):
        self.current_action_item = item_id; item = self.get_item_by_id(item_id)
        active_items_list = self.get_current_data()["data"][self.get_current_data()["tabs"][self.get_current_data()["active_tab"]]]["active"]
        
        valid_targets = [b["name"] for b in active_items_list if b["type"] == item["type"] and b["id"] != item_id]
        if not valid_targets: self.show_snackbar(self.t("No valid targets to merge into!"), True); return
        
        bold_option_style = ft.TextStyle(font_family="Jameel Noori", weight=ft.FontWeight.BOLD, size=self.s(18), color=TEXT_MAIN)
        self.merge_dd.options = [ft.dropdown.Option(key=n, text=n, text_style=bold_option_style) for n in valid_targets]
        
        self.merge_dd.value = None
        self.page.open(self.merge_dialog)
        self.page.update()
        try: self.merge_confirm_btn.focus()
        except: pass

    def open_add_qty(self, item_id):
        self.current_action_item = item_id
        self.add_qty_input.value = ""
        self.free_stock_checkbox.value = False 
        self.page.open(self.add_qty_dialog)
        self.page.update()
        try: self.add_qty_input.focus()
        except: pass

    def open_cancel_to_stock_dialog(self, item_id):
        self.current_action_item = item_id
        item = self.get_item_by_id(item_id)
        self.cancel_to_stock_qty_input.value = f"{item['quantity']:g}"
        self.page.open(self.cancel_to_stock_dialog)
        self.page.update()
        try: self.cancel_to_stock_qty_input.focus()
        except: pass

    def open_confirm_step(self, item_id):
        self.current_action_item = item_id; item = self.get_item_by_id(item_id)
        if item["step_idx"] < len(item["steps"]):
            self.is_finishing_batch = False; step_name = item["steps"][item["step_idx"]]
            if not item.get("is_processing", False):
                self.confirm_text.value = f"Commence step '{step_name}'?"
                self.confirm_btn.text = self.t("Start Step")
                self.confirm_btn.style.bgcolor = PRIMARY
            else:
                self.confirm_text.value = f"Log '{step_name}' as fully completed?"
                self.confirm_btn.text = self.t("Yes, Complete")
                self.confirm_btn.style.bgcolor = "#0D9488" 
            
            self.page.open(self.confirm_dialog)
            self.page.update()
            try: self.confirm_btn.focus()
            except: pass

    def toggle_step_mode(self, e):
        is_custom = not self.custom_step_input.visible
        self.custom_step_input.visible = is_custom
        self.step_dropdown.visible = not is_custom
        self.mode_toggle_btn.text = self.t("Select Existing") if is_custom else self.t("Create New")
        
        self.page.update()
        if is_custom:
            try: self.custom_step_input.focus()
            except: pass
        else:
            try: self.step_dropdown.focus()
            except: pass

    def open_custom_step(self, item_id): 
        self.current_action_item = item_id
        item = self.get_item_by_id(item_id)
        ptype = item["type"]
        default_steps = self.products_config.get(ptype, {}).get("steps", [])
        
        unique_steps = []
        for st in default_steps:
            if st not in unique_steps:
                unique_steps.append(st)
        
        self.step_dropdown.options.clear()
        
        bold_option_style = ft.TextStyle(font_family="Jameel Noori", weight=ft.FontWeight.BOLD, size=self.s(18), color=TEXT_MAIN)
        
        if not unique_steps:
            self.step_dropdown.options.append(ft.dropdown.Option(
                key=self.t("No steps defined"), 
                text=self.t("No steps defined"),
                text_style=bold_option_style
            ))
            self.step_dropdown.value = self.t("No steps defined")
            self.step_dropdown.disabled = True
        else:
            for st in unique_steps:
                self.step_dropdown.options.append(ft.dropdown.Option(
                    key=st,
                    text=st,
                    text_style=bold_option_style
                ))
            self.step_dropdown.value = None
            self.step_dropdown.disabled = False
        
        self.custom_step_input.visible = False
        self.step_dropdown.visible = True
        self.mode_toggle_btn.text = self.t("Create New")
        
        self.custom_step_input.value = ""
        self.custom_step_pos_input.value = ""
        
        self.page.open(self.step_dialog)
        self.page.update()
        try: self.step_dropdown.focus()
        except: pass

    def open_complete_batch(self, item_id): 
        self.current_action_item = item_id
        self.page.open(self.complete_batch_dialog)
        self.page.update()
        try: self.complete_btn.focus()
        except: pass

    def open_move_dialog(self, item_id):
        self.current_action_item = item_id
        
        bold_option_style = ft.TextStyle(font_family="Jameel Noori", weight=ft.FontWeight.BOLD, size=self.s(18), color=TEXT_MAIN)
        self.move_fac_dd.options = [ft.dropdown.Option(key=f, text=f, text_style=bold_option_style) for f in self.factories]
        
        curr_fac, curr_loc = self.get_context(); self.move_fac_dd.value = curr_fac; self.on_move_fac_change(None); self.move_loc_dd.value = curr_loc; self.on_move_loc_change(None) 
        if self.get_current_data()["tabs"]: self.move_sub_dd.value = self.get_current_data()["tabs"][self.get_current_data()["active_tab"]]
        
        self.page.open(self.move_dialog)
        self.page.update()
        try: self.move_confirm_btn.focus()
        except: pass

    def on_move_fac_change(self, e):
        bold_option_style = ft.TextStyle(font_family="Jameel Noori", weight=ft.FontWeight.BOLD, size=self.s(18), color=TEXT_MAIN)
        fac = self.move_fac_dd.value
        self.move_loc_dd.options = [ft.dropdown.Option(key=l, text=l, text_style=bold_option_style) for l in self.factory_sub_locations[fac]] if fac and fac in self.factory_sub_locations else []
        self.move_loc_dd.value = None; self.move_sub_dd.options = []; self.move_sub_dd.value = None
        if e: self.page.update()

    def on_move_loc_change(self, e):
        bold_option_style = ft.TextStyle(font_family="Jameel Noori", weight=ft.FontWeight.BOLD, size=self.s(18), color=TEXT_MAIN)
        fac, loc = self.move_fac_dd.value, self.move_loc_dd.value
        key = f"{fac}::{loc}"
        if fac and loc and key in self.level3_data and self.level3_data[key]["tabs"]: 
            self.move_sub_dd.options = [ft.dropdown.Option(key=t, text=t, text_style=bold_option_style) for t in self.level3_data[key]["tabs"]]
        else: 
            self.move_sub_dd.options = []
        self.move_sub_dd.value = None
        if e: self.page.update()

    def confirm_delete_specific_step(self, item_id, step_idx):
        self.delete_type_data = {"id": item_id, "idx": step_idx}
        self.page.open(self.delete_confirm_dialog)
        self.page.update()
        try: self.delete_step_btn.focus()
        except: pass