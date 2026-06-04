import flet as ft
from datetime import datetime
from archive_view import ArchiveLogView
from location_actions import LocationActionsMixin, parse_qty
from location_dialogs import LocationDialogsMixin

CARD_BG = "#FFFFFF"
TEXT_MAIN = "#0F172A"
TEXT_SUB = "#64748B"
PRIMARY = "#2563EB"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
BORDER = "#E2E8F0"

def parse_date(date_str):
    try: return datetime.strptime(date_str, "%Y-%m-%d %I:%M %p")
    except ValueError:
        try: return datetime.strptime(date_str, "%I:%M %p, %d %b")
        except: return datetime.now() 

class LocationView(ft.Container, LocationActionsMixin, LocationDialogsMixin):
    def __init__(self, page: ft.Page, products_config: dict, get_context_cb, factories: list, factory_sub_locations: dict, level3_data: dict, save_cb, t, scale):
        super().__init__()
        self.page = page
        self.products_config = products_config
        self.get_context = get_context_cb 
        self.factories = factories
        self.factory_sub_locations = factory_sub_locations
        
        self.level3_data = level3_data 
        self.save_cb = save_cb 
        self.t = t
        self.scale_factor = scale
        
        self.expand = True
        self.padding = 10 
        self.visible = False

        self.current_action_item = None 
        self.current_process_product = None 
        self.active_product_filter = None
        self.pending_step_swap = None 

        def s(size): return int(size * self.scale_factor)
        self.s = s

        self.l3_tabs = ft.Tabs(selected_index=0, on_change=self.on_l3_tab_change, animation_duration=300, expand=True)
        self.edit_l3_btn = ft.IconButton(icon=ft.Icons.EDIT, icon_color="#60A5FA", tooltip=self.t("Edit Location"), on_click=self.on_edit_l3_click)
        self.delete_l3_btn = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="#F87171", tooltip=self.t("Delete Location"), on_click=self.on_delete_l3_click)
        self.add_l3_btn = ft.IconButton(icon=ft.Icons.ADD_BOX, icon_color=PRIMARY, tooltip=self.t("New Sub-Location"), on_click=self.open_add_l3_dialog)
        
        self.setup_dialogs()
        
        self.view_mode_tabs = ft.Tabs(selected_index=0, on_change=self.on_view_mode_change, animation_duration=300)
        self.list_container = ft.Column(spacing=8) 

        self.main_wrapper = ft.Container(
            expand=True,
            content=ft.Column([
                ft.Container(padding=ft.padding.symmetric(horizontal=10, vertical=5), bgcolor=CARD_BG, border_radius=12, border=ft.border.all(1, BORDER), shadow=ft.BoxShadow(blur_radius=8, color="#00000005", offset=ft.Offset(0, 2)), content=ft.Row([self.l3_tabs, self.edit_l3_btn, self.delete_l3_btn, self.add_l3_btn], alignment=ft.MainAxisAlignment.START)),
                ft.Row([self.view_mode_tabs], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
                self.list_container
            ], spacing=5)
        )

        self.content = ft.Column([
            self.main_wrapper
        ], expand=True, scroll=ft.ScrollMode.AUTO)

        self.archive_view = ArchiveLogView(self.page, self.t, self.scale_factor, self.revert_archived_batch)

    def show_snackbar(self, msg, is_error=False): 
        self.page.open(ft.SnackBar(content=ft.Text(msg, color="#FFFFFF", weight=ft.FontWeight.W_500, size=self.s(14)), bgcolor="#EF4444" if is_error else "#10B981", behavior=ft.SnackBarBehavior.FLOATING, margin=20, shape=ft.RoundedRectangleBorder(radius=8)))

    def get_current_data(self):
        factory, loc = self.get_context(); key = f"{factory}::{loc}"
        if key not in self.level3_data: self.level3_data[key] = {"tabs": [], "active_tab": 0, "data": {}}
        for tab_val, tab_data in self.level3_data[key]["data"].items():
            if "stock" not in tab_data: tab_data["stock"] = {}
        return self.level3_data[key]

    def get_item_by_id(self, item_id, return_list=False):
        data_ctx = self.get_current_data()
        if not data_ctx["tabs"]: return None
        active_items = data_ctx["data"][data_ctx["tabs"][data_ctx["active_tab"]]]["active"]
        for item in active_items:
            if item["id"] == item_id: return (item, active_items) if return_list else item
        return None

    def get_all_batch_names_for_product(self, ptype):
        names = set()
        for loc_data in self.level3_data.values():
            for tab_data in loc_data["data"].values():
                for item in tab_data.get("active", []):
                    if item.get("type") == ptype: 
                        names.add(item.get("name"))
                        names.add(item.get("name").split(".")[0]) 
                for item in tab_data.get("history", []):
                    if item.get("entry_type") == "Batch" and item.get("type") == ptype: 
                        names.add(item.get("name"))
                        names.add(item.get("name").split(".")[0]) 
        return names

    def get_unique_batch_name(self, ptype):
        existing = self.get_all_batch_names_for_product(ptype)
        max_num = 0
        for name in existing:
            if name.startswith("Batch "):
                try:
                    num = int(name.replace("Batch ", "").split(".")[0])
                    if num > max_num: max_num = num
                except: pass
        return f"Batch {max_num + 1}"

    def update_context(self): self.render()

    def on_l3_tab_change(self, e): 
        data_ctx = self.get_current_data()
        data_ctx["active_tab"] = self.l3_tabs.selected_index
        self.view_mode_tabs.selected_index = 0
        self.render()

    def set_filter(self, product_type):
        self.active_product_filter = product_type
        self.render_lists(None)

    def on_view_mode_change(self, e):
        self.render_lists(None) 
        self.page.update() 
        
    def open_batch_details(self, item_id):
        item = self.get_item_by_id(item_id)
        if not item: return
        
        s = self.s
        details_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        
        max_steps = len(item["steps"])
        step_idx = item["step_idx"]
        is_processing = item.get("is_processing", False)
        
        for idx, s_name in enumerate(item["steps"]):
            step_time_str = ""
            if idx < step_idx:
                icon, color = ft.Icons.CHECK_CIRCLE, SUCCESS
                for log in reversed(item["timeline"]):
                    if (log.get("idx") == idx and log["step"].startswith("Completed:")) or (log.get("idx") is None and log["step"] == f"Completed: {s_name}"): 
                        dt_obj = parse_date(log['time'])
                        step_time_str = f"{dt_obj.strftime('%d %b %Y, %I:%M %p')} • {log.get('qty', item['quantity']):g} units"
                        break
            elif idx == step_idx and is_processing:
                icon, color = ft.Icons.MOTION_PHOTOS_ON, WARNING
                for log in reversed(item["timeline"]):
                    if (log.get("idx") == idx and log["step"].startswith("Started:")) or (log.get("idx") is None and log["step"] == f"Started: {s_name}"): 
                        dt_obj = parse_date(log['time'])
                        step_time_str = f"{dt_obj.strftime('%d %b %Y, %I:%M %p')} • {log.get('qty', item['quantity']):g} units"
                        break
            elif idx == step_idx and not is_processing:
                icon, color = ft.Icons.RADIO_BUTTON_UNCHECKED, PRIMARY
                step_time_str = "Pending (Next)"
            else:
                icon, color = ft.Icons.RADIO_BUTTON_UNCHECKED, "#CBD5E1"
                step_time_str = "Pending"
                
            details_col.controls.append(
                ft.Container(
                    padding=10, bgcolor="#F8FAFC", border_radius=8, border=ft.border.all(1, "#E2E8F0"),
                    content=ft.Row([
                        ft.Icon(icon, color=color, size=24),
                        ft.Column([
                            ft.Text(f"{idx + 1}. {s_name}", size=s(16), weight=ft.FontWeight.BOLD, color=TEXT_MAIN),
                            ft.Text(step_time_str, size=s(13), color=TEXT_SUB)
                        ], spacing=2, expand=True)
                    ])
                )
            )

        dlg = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Row([
                ft.Icon(ft.Icons.RECEIPT_LONG, color=PRIMARY),
                ft.Text(f"Full Details: {item['name']}", weight=ft.FontWeight.BOLD, size=s(18))
            ]),
            content=ft.Container(
                width=450, height=500,
                content=details_col
            ),
            actions=[
                ft.ElevatedButton("Close", on_click=lambda e: self.page.close(dlg), style=ft.ButtonStyle(bgcolor=PRIMARY, color="white", shape=ft.RoundedRectangleBorder(radius=8)))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.open(dlg)
        self.page.update()

    def render(self):
        data_ctx = self.get_current_data()
        
        new_tabs = []
        for t_name in data_ctx["tabs"]:
            active_count = len(data_ctx["data"][t_name].get("active", []))
            tab_text = f"{t_name} ({active_count})" if active_count > 0 else t_name
            new_tab = ft.Tab(
                tab_content=ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    content=ft.Text(tab_text, size=self.s(17), weight=ft.FontWeight.W_800)
                )
            )
            new_tab.data = t_name 
            new_tabs.append(new_tab)
            
        current_l3_names = [getattr(t, 'data', t.text) for t in self.l3_tabs.tabs]
        
        if current_l3_names != data_ctx["tabs"]:
            self.l3_tabs.tabs = new_tabs
        else:
            for i, t_name in enumerate(data_ctx["tabs"]):
                active_count = len(data_ctx["data"][t_name].get("active", []))
                tab_text = f"{t_name} ({active_count})" if active_count > 0 else t_name
                self.l3_tabs.tabs[i].tab_content = ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    content=ft.Text(tab_text, size=self.s(17), weight=ft.FontWeight.W_800)
                )
                self.l3_tabs.tabs[i].data = t_name
                
        self.l3_tabs.selected_index = data_ctx["active_tab"] if data_ctx["tabs"] else 0
        
        has_tabs = len(data_ctx["tabs"]) > 0
        self.view_mode_tabs.visible = has_tabs
        
        self.edit_l3_btn.visible = has_tabs
        self.delete_l3_btn.visible = has_tabs
        
        if not has_tabs:
            self.list_container.controls = [ft.Container(padding=40, alignment=ft.alignment.center, content=ft.Text(self.t("Define a sub-location using the '+' icon above to start managing inventory."), color=TEXT_SUB, size=self.s(15)))]
        else:
            active_tab_name = data_ctx["tabs"][data_ctx["active_tab"]]
            has_history = len(data_ctx["data"][active_tab_name].get("history", [])) > 0
            has_active = len(data_ctx["data"][active_tab_name].get("active", [])) > 0
            
            new_view_tab_names = [self.t("Active Matrix")]
            if has_active or has_history:
                new_view_tab_names.append(self.t("Live Tracking"))
                new_view_tab_names.append(self.t("Archive & Logs"))
                
            current_view_tab_names = [t.text for t in self.view_mode_tabs.tabs]
            if current_view_tab_names != new_view_tab_names: 
                self.view_mode_tabs.tabs = [ft.Tab(text=n) for n in new_view_tab_names]
                
            if self.view_mode_tabs.selected_index >= len(self.view_mode_tabs.tabs): 
                self.view_mode_tabs.selected_index = 0
            self.render_lists(None)
            
        if self.page: self.update()
        self.save_cb() 

    def render_lists(self, e):
        self.list_container.controls.clear()
        data_ctx = self.get_current_data()
        tab_data = data_ctx["data"][data_ctx["tabs"][data_ctx["active_tab"]]]
        s = self.s
        
        if not self.view_mode_tabs.tabs: return
            
        selected_tab_text = self.view_mode_tabs.tabs[self.view_mode_tabs.selected_index].text

        if selected_tab_text == self.t("Live Tracking"):
            self.archive_view.update_data(tab_data, "live")
            self.list_container.controls.append(self.archive_view)
            if self.page: self.update()
            return
        elif selected_tab_text == self.t("Archive & Logs"):
            self.archive_view.update_data(tab_data, "archive")
            self.list_container.controls.append(self.archive_view)
            if self.page: self.update()
            return
        
        def make_input(val, lbl, width, on_blur_cb, read_only=False): 
            return ft.TextField(
                value=val, label=lbl, height=s(46), content_padding=ft.padding.symmetric(horizontal=10, vertical=10), 
                text_size=s(18), 
                label_style=ft.TextStyle(weight=ft.FontWeight.W_800, color=TEXT_MAIN, size=s(14)), 
                width=width, expand=(width is None), border_radius=8, border_color="#E2E8F0", focused_border_color=PRIMARY, 
                on_blur=on_blur_cb, on_submit=on_blur_cb, read_only=read_only
            )

        grouped_products = set(self.products_config.keys())
        for item in tab_data["active"]: grouped_products.add(item["type"])
        if not grouped_products:
            self.list_container.controls.append(ft.Container(padding=40, alignment=ft.alignment.center, content=ft.Text(self.t("No active operations. Extract stock to begin."), color=TEXT_SUB, size=s(15))))
            if self.page: self.update(); return

        product_batch_counts = {p: len([b for b in tab_data["active"] if b["type"] == p]) for p in grouped_products}
        sorted_products = sorted(list(grouped_products), key=lambda p: (-product_batch_counts[p], p))

        if self.active_product_filter not in sorted_products:
            self.active_product_filter = sorted_products[0]

        selector_row = ft.Row(scroll=ft.ScrollMode.ADAPTIVE, spacing=12)
        for ptype in sorted_products:
            batch_count = product_batch_counts[ptype] 
            is_selected = (self.active_product_filter == ptype)
            
            bg_c = PRIMARY if is_selected else CARD_BG
            text_c = "#FFFFFF" if is_selected else TEXT_MAIN
            border_c = PRIMARY if is_selected else BORDER

            card = ft.Container(
                content=ft.Row([
                    ft.Text(ptype, size=s(18), weight=ft.FontWeight.W_800, color=text_c),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor="#3B82F6" if is_selected else "#E2E8F0",
                        border_radius=14,
                        content=ft.Text(f"{batch_count}", size=s(14), color="#FFFFFF" if is_selected else "#475569", weight=ft.FontWeight.W_900)
                    )
                ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=bg_c, border_radius=30, padding=ft.padding.symmetric(horizontal=20, vertical=12),
                border=ft.border.all(1, border_c), shadow=ft.BoxShadow(blur_radius=8, color="#00000005", offset=ft.Offset(0, 2)),
                on_click=lambda e, p=ptype: self.set_filter(p), ink=True
            )
            selector_row.controls.append(card)
        
        self.list_container.controls.append(ft.Container(content=selector_row, padding=ft.padding.only(bottom=5)))

        ptype = self.active_product_filter
        if ptype:
            curr_stock = self.products_config.get(ptype, {}).get("stock", 0)
            p_items = [b for b in tab_data["active"] if b["type"] == ptype]
            
            batch_row = ft.ResponsiveRow(columns=12, spacing=12, run_spacing=12)
            
            grouped_batches = {}
            for item in p_items:
                base = item["name"].split(".")[0]
                if base not in grouped_batches: grouped_batches[base] = []
                grouped_batches[base].append(item)
                
            def get_order_idx(b_name):
                for i, itm in enumerate(tab_data["active"]):
                    if itm["name"].split(".")[0] == b_name:
                        return i
                return 0
                
            sorted_base_names = sorted(grouped_batches.keys(), key=get_order_idx)

            for base_name in sorted_base_names:
                g_items = grouped_batches[base_name]
                built_cards = []

                for item in g_items: 
                    display_tag = item["name"].replace("Batch ", "")
                    
                    batch_display = ft.Container(
                        height=s(46),
                        padding=ft.padding.symmetric(horizontal=12, vertical=0),
                        bgcolor="#EFF6FF",
                        border_radius=8,
                        alignment=ft.alignment.center,
                        on_click=lambda e, i=item["id"]: self.open_batch_details(i),
                        ink=True,
                        tooltip=self.t("Click to view full step history"),
                        content=ft.Row([
                            ft.Icon(ft.Icons.TAG, size=s(20), color=PRIMARY),
                            ft.Text(f"{self.t('Batch')} {display_tag}", size=s(20), weight=ft.FontWeight.W_900, color=PRIMARY)
                        ], spacing=6)
                    )

                    qty_field = make_input(f"{item['quantity']:g}", self.t("Qty"), s(80), lambda e, i=item["id"]: None, read_only=True)
                    
                    restock_btn = ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="#EF4444", tooltip=self.t("Cancel & Restock"), padding=0, width=36, height=36, icon_size=22, on_click=lambda e, i=item["id"]: self.open_cancel_to_stock_dialog(i))

                    max_steps = len(item["steps"]); step_idx = item["step_idx"]; is_processing = item.get("is_processing", False)
                    
                    steps_visual = ft.Column(spacing=2)
                    
                    for idx, s_name in enumerate(item["steps"]):
                        
                        if idx not in [step_idx - 1, step_idx, step_idx + 1]:
                            continue
                            
                        step_time_str = ""
                        step_qty_val = item["quantity"]
                        
                        if idx < step_idx:
                            icon, color, font_w = ft.Icons.CHECK_CIRCLE, SUCCESS, ft.FontWeight.W_600
                            for log in reversed(item["timeline"]):
                                if (log.get("idx") == idx and log["step"].startswith("Completed:")) or (log.get("idx") is None and log["step"] == f"Completed: {s_name}"): 
                                    dt_obj = parse_date(log['time'])
                                    step_qty_val = log.get('qty', item["quantity"])
                                    step_time_str = f" • {dt_obj.strftime('%d %b %Y')} [{step_qty_val:g} {self.t('units')}]"
                                    break
                        elif idx == step_idx and is_processing:
                            icon, color, font_w = ft.Icons.MOTION_PHOTOS_ON, WARNING, ft.FontWeight.W_700
                            for log in reversed(item["timeline"]):
                                if (log.get("idx") == idx and log["step"].startswith("Started:")) or (log.get("idx") is None and log["step"] == f"Started: {s_name}"): 
                                    dt_obj = parse_date(log['time'])
                                    step_qty_val = log.get('qty', item["quantity"])
                                    step_time_str = f" • {dt_obj.strftime('%d %b %Y')} [{step_qty_val:g} {self.t('units')}]"
                                    break
                        elif idx == step_idx and not is_processing: icon, color, font_w = ft.Icons.RADIO_BUTTON_UNCHECKED, PRIMARY, ft.FontWeight.W_600
                        else: icon, color, font_w = ft.Icons.RADIO_BUTTON_UNCHECKED, "#CBD5E1", ft.FontWeight.W_400
                            
                        can_delete = (idx > step_idx) or (idx == step_idx and not is_processing)
                        del_btn = ft.IconButton(ft.Icons.CLOSE, icon_color="#EF4444", icon_size=16, padding=0, width=20, height=20, on_click=lambda e, i=item["id"], s_i=idx: self.confirm_delete_specific_step(i, s_i))
                        
                        display_step_name = f"{idx + 1}. {s_name}"
                        
                        step_container = ft.Container(
                            padding=ft.padding.only(left=5, right=5, top=4, bottom=4), border_radius=6, bgcolor="#F8FAFC" if (idx == step_idx) else ft.colors.TRANSPARENT, 
                            content=ft.Row([
                                ft.Icon(icon, color=color, size=22), 
                                ft.Text(f"{display_step_name}", size=s(20), color=TEXT_MAIN if color != "#CBD5E1" else TEXT_SUB, weight=font_w, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS), 
                                ft.Text(step_time_str, size=s(14), color=TEXT_SUB), 
                                del_btn if can_delete else ft.Container(width=20)
                            ])
                        )
                        
                        draggable_step = ft.Draggable(
                            group=f"steps_{item['id']}", 
                            data={"item_id": item["id"], "step_idx": idx},
                            content=step_container
                        )
                        
                        drop_target = ft.DragTarget(
                            group=f"steps_{item['id']}",
                            data={"item_id": item["id"], "step_idx": idx},
                            content=draggable_step,
                            on_accept=self.handle_step_swap
                        )
                        
                        steps_visual.controls.append(drop_target)

                    if step_idx >= max_steps: btn_text, btn_color, next_btn_disabled = self.t("Ready to Archive"), "#CBD5E1", True 
                    else: btn_text, btn_color, next_btn_disabled = (self.t("Finish Step") if is_processing else self.t("Start Step")), ("#0D9488" if is_processing else PRIMARY), False 

                    add_step_btn = ft.IconButton(ft.Icons.ADD, tooltip="Inject routing step", icon_color=PRIMARY, bgcolor="#EFF6FF", icon_size=18, padding=0, width=28, height=28, on_click=lambda e, i=item["id"]: self.open_custom_step(i))
                    undo_btn = ft.IconButton(ft.Icons.UNDO, tooltip="Revert Last Action", icon_color=TEXT_SUB, hover_color="#F1F5F9", padding=0, width=36, height=36, icon_size=20, on_click=lambda e, i=item["id"]: self.execute_revert(i))
                    move_btn = ft.IconButton(ft.Icons.DRIVE_FILE_MOVE_OUTLINE, tooltip=self.t("Relocate Batch"), icon_color=WARNING, bgcolor="#FFFBEB", padding=0, width=36, height=36, icon_size=20, on_click=lambda e, i=item["id"]: self.open_move_dialog(i))
                    next_btn = ft.ElevatedButton(btn_text, disabled=next_btn_disabled, style=ft.ButtonStyle(color="#FFFFFF", bgcolor=btn_color, shape=ft.RoundedRectangleBorder(radius=6), padding=ft.padding.symmetric(horizontal=12, vertical=0), text_style=ft.TextStyle(size=s(16), weight=ft.FontWeight.W_700)), height=40, on_click=lambda e, i=item["id"]: self.open_confirm_step(i))
                    complete_batch_btn = ft.ElevatedButton(self.t("Archive"), style=ft.ButtonStyle(color="#FFFFFF", bgcolor=SUCCESS, shape=ft.RoundedRectangleBorder(radius=6), padding=ft.padding.symmetric(horizontal=12, vertical=0), text_style=ft.TextStyle(size=s(16), weight=ft.FontWeight.W_700)), height=40, on_click=lambda e, i=item["id"]: self.open_complete_batch(i))

                    add_qty_btn = ft.IconButton(ft.Icons.ADD, icon_color=PRIMARY, bgcolor="#EFF6FF", tooltip=self.t("Add Quantity"), padding=0, width=36, height=36, icon_size=20, on_click=lambda e, i=item["id"]: self.open_add_qty(i))
                    split_btn = ft.IconButton(ft.Icons.CALL_SPLIT, icon_color=WARNING, bgcolor="#FFFBEB", tooltip=self.t("Split Batch"), padding=0, width=36, height=36, icon_size=20, on_click=lambda e, i=item["id"]: self.open_split(i))
                    merge_btn = ft.IconButton(ft.Icons.CALL_MERGE, icon_color=SUCCESS, bgcolor="#ECFDF5", tooltip=self.t("Merge Batch"), padding=0, width=36, height=36, icon_size=20, on_click=lambda e, i=item["id"]: self.open_merge(i))

                    card_content = [ft.Row([batch_display, qty_field, add_qty_btn, ft.Container(expand=True), move_btn, restock_btn], spacing=6)]
                    
                    if item.get("parent"):
                        card_content.append(ft.Container(padding=ft.padding.only(left=5, top=4), content=ft.Row([
                            ft.Icon(ft.Icons.CALL_SPLIT, size=12, color=WARNING),
                            ft.Text(f"{self.t('Split from:')} {item['parent']}", size=s(12), color=WARNING, weight=ft.FontWeight.W_500)
                        ])))
                        
                    card_content.extend([
                        ft.Divider(height=10, color="#F1F5F9"), 
                        steps_visual, 
                        ft.Container(height=4), 
                        # --- ADDED self.t() TO THIS TEXT ---
                        ft.Row([ft.Text(self.t("Inject manual step:"), size=s(12), color=TEXT_SUB, weight=ft.FontWeight.W_500), add_step_btn], alignment=ft.MainAxisAlignment.START)
                    ])

                    left_actions = [complete_batch_btn, split_btn, merge_btn]
                    if step_idx > 0 or is_processing:
                        left_actions.append(undo_btn)

                    action_content = ft.Row([
                        ft.Row(left_actions, spacing=4),
                        next_btn
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

                    card = ft.Container(
                        bgcolor=CARD_BG, border_radius=12, border=ft.border.all(1, BORDER), shadow=ft.BoxShadow(blur_radius=10, color="#00000008", offset=ft.Offset(0, 4)), 
                        content=ft.Column([
                            ft.Container(padding=12, content=ft.Column(card_content, spacing=0)), 
                            ft.Container(padding=10, bgcolor="#F8FAFC", border_radius=ft.border_radius.only(bottom_left=12, bottom_right=12), border=ft.border.only(top=ft.border.BorderSide(1, BORDER)), 
                                content=action_content
                            )
                        ], spacing=0)
                    )
                    
                    col_span = {"xs": 12, "sm": 12, "md": 6, "lg": 6, "xl": 6} 
                    built_cards.append(ft.Column(col=col_span, controls=[card]))

                if len(g_items) == 1 and g_items[0]["name"] == base_name:
                    batch_row.controls.append(built_cards[0])
                else:
                    group_header = ft.Container(
                        padding=ft.padding.only(bottom=5, left=5, right=5),
                        content=ft.Row([
                            ft.Icon(ft.Icons.ACCOUNT_TREE, color=PRIMARY, size=24),
                            ft.Text(f"{self.t('Batch Group:')} {base_name}", size=s(18), weight=ft.FontWeight.W_800, color=TEXT_MAIN)
                        ])
                    )
                    children_row = ft.Container(content=ft.ResponsiveRow(controls=built_cards, columns=12, spacing=12, run_spacing=12), padding=ft.padding.all(0))
                    
                    group_container = ft.Container(
                        bgcolor="#F8FAFC", border=ft.border.all(1, "#CBD5E1"), border_radius=12, padding=12,
                        content=ft.Column([
                            group_header, 
                            children_row
                        ], spacing=0)
                    )
                    batch_row.controls.append(ft.Column(col={"xs": 12}, controls=[group_container]))

            process_btn = ft.ElevatedButton(self.t("Extract to Batch"), icon=ft.Icons.PLAY_ARROW, style=ft.ButtonStyle(color="#FFFFFF", bgcolor=TEXT_MAIN, shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=15)), on_click=lambda e, p=ptype: self.open_process_dialog(p), disabled=(curr_stock <= 0))
            
            stock_badges = []
            
            sorted_products_by_stock = sorted(
                self.products_config.items(), 
                key=lambda item: item[1].get("stock", 0), 
                reverse=True
            )
            
            for p_name, p_data in sorted_products_by_stock:
                p_stk = p_data.get("stock", 0)
                stock_badges.append(
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        bgcolor="#F0FDF4" if p_stk > 0 else "#F8FAFC",
                        border_radius=8,
                        border=ft.border.all(1, "#BBF7D0" if p_stk > 0 else "#E2E8F0"),
                        content=ft.Row([
                            ft.Text(p_name, color="#166534" if p_stk > 0 else "#64748B", size=s(13), weight=ft.FontWeight.W_700),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                bgcolor="#DCFCE7" if p_stk > 0 else "#F1F5F9",
                                border_radius=4,
                                content=ft.Text(f"{p_stk:g}", color="#15803D" if p_stk > 0 else "#94A3B8", size=s(12), weight=ft.FontWeight.W_900)
                            )
                        ], spacing=6)
                    )
                )

            global_stocks_section = ft.Container(
                expand=True,
                content=ft.Row([
                    ft.Container(width=1, height=24, bgcolor="#E2E8F0", margin=ft.margin.symmetric(horizontal=10)),
                    ft.Icon(ft.Icons.ALL_INBOX_ROUNDED, color="#64748B", size=18),
                    # --- ADDED self.t() TO THIS TEXT ---
                    ft.Text(self.t("Global Raw Stock:"), color="#64748B", size=s(13), weight=ft.FontWeight.W_800),
                    ft.Container(content=ft.Row(stock_badges, spacing=8, scroll=ft.ScrollMode.AUTO), expand=True)
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )

            header_row = ft.Container(
                padding=ft.padding.symmetric(horizontal=15, vertical=10),
                bgcolor="#FFFFFF",
                border_radius=10,
                border=ft.border.all(1, "#E2E8F0"),
                shadow=ft.BoxShadow(blur_radius=8, color="#00000005", offset=ft.Offset(0, 2)),
                margin=ft.margin.only(bottom=15),
                content=ft.Row([
                    process_btn,
                    global_stocks_section
                ], alignment=ft.MainAxisAlignment.START)
            )

            self.list_container.controls.append(header_row)
            
            if p_items:
                self.list_container.controls.append(batch_row)
            else:
                self.list_container.controls.append(ft.Text(self.t("No active operations. Extract stock to begin."), color=TEXT_SUB, size=s(14)))

        if self.page: self.update()