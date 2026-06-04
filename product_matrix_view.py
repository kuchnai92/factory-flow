import flet as ft
from datetime import datetime

class ProductMatrixView(ft.Container):
    def __init__(self, page: ft.Page, products_config: dict, save_cb, t):
        super().__init__()
        self.main_page = page  
        self.products = products_config
        self.save_cb = save_cb
        self.t = t
        self.expand = True
        self.visible = False
        self.padding = 15
        self.search_query = ""

        # --- Top Header (Compacted) ---
        header_row = ft.Row([
            ft.Text(self.t("Product Directory"), size=24, weight=ft.FontWeight.W_800, color="#0F172A"),
            ft.ElevatedButton(
                self.t("Add Product"), 
                icon=ft.Icons.ADD, 
                on_click=self.open_add_product_dialog, 
                style=ft.ButtonStyle(
                    bgcolor="#334155", color="white", 
                    shape=ft.RoundedRectangleBorder(radius=20), 
                    padding=ft.padding.symmetric(horizontal=15, vertical=10)
                )
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # --- KPI Cards (Compacted) ---
        self.kpi_total_prods = ft.Text("0", size=20, weight=ft.FontWeight.W_800, color="#0F172A")
        self.kpi_total_stock = ft.Text("0", size=20, weight=ft.FontWeight.W_800, color="#0F172A")
        self.kpi_out_of_stock = ft.Text("0", size=20, weight=ft.FontWeight.W_800, color="#0F172A")

        def make_kpi_card(title, value_ctrl, icon, icon_bg, icon_color):
            return ft.Container(
                expand=True,
                bgcolor="white", border_radius=10, padding=12, 
                border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=8, color="#00000005", offset=ft.Offset(0,2)),
                content=ft.Row([
                    ft.Container(
                        padding=8, bgcolor=icon_bg, border_radius=30, 
                        content=ft.Icon(icon, color=icon_color, size=24)
                    ),
                    ft.Column([
                        ft.Text(title, size=12, color="#64748B", weight=ft.FontWeight.W_700),
                        value_ctrl
                    ], spacing=0)
                ], spacing=12)
            )

        kpi_row = ft.Row([
            make_kpi_card(self.t("Total Products"), self.kpi_total_prods, ft.Icons.PEOPLE_ALT, "#E0F2FE", "#0284C7"),
            make_kpi_card(self.t("Total Raw Stock"), self.kpi_total_stock, ft.Icons.INVENTORY, "#D1FAE5", "#059669"),
            make_kpi_card(self.t("Needs Restock"), self.kpi_out_of_stock, ft.Icons.WARNING_AMBER_ROUNDED, "#FEE2E2", "#DC2626"),
        ], spacing=10)

        # --- Search Bar (Compacted) ---
        self.search_input = ft.TextField(
            hint_text=self.t("Search Products..."),
            prefix_icon=ft.Icons.SEARCH,
            border_radius=8, height=40,
            border_color="#CBD5E1", focused_border_color="#2563EB",
            on_change=self.on_search,
            width=350,
            text_size=14,
            content_padding=10
        )

        # --- Table/Directory Structure (Compacted) ---
        table_header = ft.Container(
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor="#F8FAFC",
            border_radius=ft.border_radius.only(top_left=12, top_right=12),
            border=ft.border.only(bottom=ft.border.BorderSide(1, "#E2E8F0")),
            content=ft.Row([
                ft.Text(self.t("Product Name"), weight=ft.FontWeight.BOLD, color="#64748B", size=13, expand=2),
                ft.Text(self.t("Available Stock"), weight=ft.FontWeight.BOLD, color="#64748B", size=13, expand=1),
                ft.Text(self.t("Routing Steps"), weight=ft.FontWeight.BOLD, color="#64748B", size=13, expand=1),
                ft.Text(self.t("Actions"), weight=ft.FontWeight.BOLD, color="#64748B", size=13, width=120, text_align=ft.TextAlign.CENTER),
            ])
        )

        self.products_list = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

        # --- Main Layout Assembly ---
        self.content = ft.Column(
            expand=True,
            controls=[
                header_row,
                ft.Container(height=5),
                kpi_row,
                ft.Container(height=10),
                self.search_input,
                ft.Container(height=5),
                ft.Container(
                    expand=True,
                    bgcolor="white", border_radius=12,
                    border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=10, color="#00000005", offset=ft.Offset(0,4)),
                    content=ft.Column([
                        table_header,
                        self.products_list
                    ], spacing=0, expand=True) 
                )
            ]
        )

        # ---------------------------------------------------------
        # DIALOGS
        # ---------------------------------------------------------

        # --- Add Product Dialog ---
        self.new_prod_name_input = ft.TextField(label=self.t("Product Name"), prefix_icon=ft.Icons.PERSON, border_radius=8, height=45, text_size=15, content_padding=10, focused_border_color="#2563EB")
        self.new_prod_stock_input = ft.TextField(label=self.t("Opening Stock"), value="0", prefix_icon=ft.Icons.ACCOUNT_BALANCE_WALLET, border_radius=8, height=45, text_size=15, content_padding=10, focused_border_color="#10B981")
        
        self.add_product_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Row([
                ft.Icon(ft.Icons.PEOPLE_ALT, color="#2563EB"),
                ft.Text(self.t("Product Setup"), weight=ft.FontWeight.BOLD, size=20)
            ]),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, color="#2563EB", size=16), ft.Text(self.t("Basic Details"), color="#2563EB", weight=ft.FontWeight.BOLD, size=14)]),
                    self.new_prod_name_input,
                    ft.Container(height=8),
                    ft.Row([ft.Icon(ft.Icons.ATTACH_MONEY, color="#10B981", size=16), ft.Text(self.t("Account Financials (Stock)"), color="#10B981", weight=ft.FontWeight.BOLD, size=14)]),
                    self.new_prod_stock_input
                ], tight=True)
            ),
            actions=[
                ft.TextButton(self.t("Cancel"), on_click=lambda e: self.main_page.close(self.add_product_dialog), style=ft.ButtonStyle(color="#64748B")),
                ft.ElevatedButton(self.t("Save Product"), icon=ft.Icons.SAVE, on_click=self.execute_add_product, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), color="white", bgcolor="#15803D", padding=ft.padding.symmetric(horizontal=15)))
            ]
        )

        # --- Edit Dialog ---
        self.edit_input = ft.TextField(label=self.t("Edit Name"), autofocus=False, on_submit=self.save_edit, border_radius=8, border_color="#CBD5E1", focused_border_color="#2563EB", text_size=16)
        self.current_edit_data = None 
        self.edit_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Text(self.t("Edit Name"), weight=ft.FontWeight.BOLD, size=18), content=self.edit_input,
            actions=[
                ft.TextButton(self.t("Cancel"), on_click=lambda e: self.main_page.close(self.edit_dialog), style=ft.ButtonStyle(color="#64748B")), 
                ft.ElevatedButton(self.t("Save"), on_click=self.save_edit, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), color="#FFFFFF", bgcolor="#2563EB")), 
            ],
        )

        # --- Delete Dialog ---
        self.item_to_delete = None
        self.delete_confirm_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Text(self.t("Confirm Delete"), weight=ft.FontWeight.BOLD, size=18),
            content=ft.Text(self.t("Are you sure you want to delete this?"), size=15),
            actions=[
                ft.TextButton(self.t("Cancel"), on_click=lambda e: self.main_page.close(self.delete_confirm_dialog)),
                ft.ElevatedButton(self.t("Delete"), on_click=self.execute_delete, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), color="white", bgcolor="#EF4444")) 
            ]
        )

        # --- Swap Dialog ---
        self.pending_setup_swap = None
        self.swap_confirm_btn = ft.ElevatedButton(self.t("Yes, Swap"), on_click=self.execute_setup_step_swap, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), color="#FFFFFF", bgcolor="#2563EB"))
        self.swap_confirm_text = ft.Text("", size=15)
        self.swap_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Text(self.t("Confirm Swap"), weight=ft.FontWeight.BOLD, size=18),
            content=self.swap_confirm_text,
            actions=[
                ft.TextButton(self.t("Cancel"), on_click=self.cancel_setup_step_swap, style=ft.ButtonStyle(color="#64748B")),
                self.swap_confirm_btn
            ]
        )

        # --- Stock Dialog ---
        self.current_stock_product = None
        self.show_full_history = False
        self.stock_qty_input = ft.TextField(
            label=self.t("Quantity (+ to add, - to remove)"), expand=True,
            border_radius=8, content_padding=10, text_size=16, height=45, 
            border_color="#E2E8F0", focused_border_color="#10B981", on_submit=self.add_stock_from_dialog
        )
        self.stock_history_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=250)
        self.toggle_history_btn = ft.TextButton(self.t("Show All History"), on_click=self.toggle_history, style=ft.ButtonStyle(color="#2563EB"))
        self.stock_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Text(self.t("Manage Stock"), weight=ft.FontWeight.BOLD, size=20),
            content=ft.Container(
                width=450,
                content=ft.Column([
                    ft.Row([
                        self.stock_qty_input, 
                        ft.ElevatedButton(self.t("Add"), icon=ft.Icons.ADD, on_click=self.add_stock_from_dialog, height=45, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), color="#FFFFFF", bgcolor="#10B981"))
                    ]),
                    ft.Divider(height=15, color="#E2E8F0"),
                    ft.Row([
                        ft.Text(self.t("Stock History"), weight=ft.FontWeight.BOLD, size=16, color="#0F172A"), 
                        self.toggle_history_btn
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    self.stock_history_col
                ], tight=True)
            ),
            actions=[
                ft.TextButton(self.t("Close"), on_click=lambda e: self.main_page.close(self.stock_dialog), style=ft.ButtonStyle(color="#64748B"))
            ]
        )

        # --- Routing Steps Dialog ---
        self.current_steps_product = None
        self.steps_list_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)
        self.steps_list_container = ft.Container(height=350, content=self.steps_list_col)
        self.step_pos_input = ft.TextField(
            label=self.t("No."), width=60, border_radius=8, 
            content_padding=10, height=45, text_size=15, border_color="#E2E8F0", focused_border_color="#2563EB",
            on_submit=self.add_step_from_dialog
        )
        self.step_add_input = ft.TextField(
            label=self.t("New Step Name"), expand=True, border_radius=8, 
            content_padding=10, height=45, text_size=15, border_color="#E2E8F0", focused_border_color="#2563EB",
            on_submit=self.add_step_from_dialog
        )
        self.steps_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Row([
                ft.Icon(ft.Icons.ACCOUNT_TREE_ROUNDED, color="#2563EB", size=24),
                ft.Text(self.t("Routing Steps"), weight=ft.FontWeight.BOLD, size=20)
            ]),
            content=ft.Container(
                width=500,
                content=ft.Column([
                    ft.Text(self.t("Drag and drop to reorder steps."), color="#64748B", size=13),
                    ft.Container(height=5),
                    self.steps_list_container,
                    ft.Divider(height=15, color="#E2E8F0"),
                    ft.Row([
                        self.step_pos_input,
                        self.step_add_input,
                        ft.ElevatedButton(self.t("Add Step"), icon=ft.Icons.ADD, on_click=self.add_step_from_dialog, height=45, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), color="#FFFFFF", bgcolor="#2563EB"))
                    ])
                ], tight=True)
            ),
            actions=[
                ft.TextButton(self.t("Done"), on_click=self.close_steps_dialog, style=ft.ButtonStyle(color="#64748B"))
            ]
        )
        
        self.render_products(is_init=True)


    def show_msg(self, text, color="#10B981"):
        try:
            snack = ft.SnackBar(content=ft.Text(text, color="#FFFFFF", weight=ft.FontWeight.W_500, size=15), bgcolor=color, behavior=ft.SnackBarBehavior.FLOATING, margin=20, shape=ft.RoundedRectangleBorder(radius=8))
            self.main_page.open(snack)
        except: pass

    # --- Live Search Logic ---
    def on_search(self, e):
        self.search_query = e.control.value.lower().strip()
        self.render_products()

    # --- Add Product Logic ---
    def open_add_product_dialog(self, e):
        self.new_prod_name_input.value = ""
        self.new_prod_stock_input.value = "0"
        self.main_page.open(self.add_product_dialog)
        self.main_page.update()
        try: self.new_prod_name_input.focus()
        except: pass

    def execute_add_product(self, e):
        name = self.new_prod_name_input.value.strip()
        stock_str = self.new_prod_stock_input.value.strip()
        
        try: stock = float(stock_str) if stock_str else 0
        except ValueError:
            self.show_msg(self.t("Invalid stock value!"), "#EF4444")
            return
            
        if name and name not in self.products:
            self.products[name] = {"steps": [], "stock": stock, "stock_history": []}
            if stock > 0:
                self.products[name]["stock_history"].append({
                    "qty": stock,
                    "date": datetime.now().strftime("%d %b %Y")
                })
            self.main_page.close(self.add_product_dialog)
            self.render_products()
            self.show_msg(self.t("Product created successfully!"))
        else:
            self.show_msg(self.t("Name invalid or already exists!"), "#EF4444")


    # --- Step Setup / Swapping / Stock / Editing logic ---
    def open_steps_dialog(self, prod_name):
        self.current_steps_product = prod_name
        self.step_add_input.value = ""
        self.step_pos_input.value = ""
        self.refresh_steps_dialog_ui()
        self.main_page.open(self.steps_dialog)
        self.main_page.update()

    def close_steps_dialog(self, e):
        self.current_steps_product = None
        self.main_page.close(self.steps_dialog)

    def refresh_steps_dialog_ui(self):
        self.steps_list_col.controls.clear()
        prod_name = self.current_steps_product
        if not prod_name or prod_name not in self.products: return
        steps = self.products[prod_name].get("steps", [])
        
        if not steps:
            self.steps_list_col.controls.append(ft.Container(padding=20, alignment=ft.alignment.center, content=ft.Text(self.t("No routing steps defined yet."), color="#64748B", italic=True, size=15)))
        else:
            for i, step in enumerate(steps):
                step_container = ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=8), bgcolor="#F8FAFC", border_radius=8, border=ft.border.all(1, "#E2E8F0"),
                    content=ft.Row([
                        ft.Container(padding=4, bgcolor="#EFF6FF", border_radius=20, width=28, height=28, alignment=ft.alignment.center, content=ft.Text(str(i+1), size=13, color="#2563EB", weight=ft.FontWeight.BOLD)),
                        ft.Text(step, expand=True, size=16, color="#334155", weight=ft.FontWeight.W_600),
                        ft.IconButton(ft.Icons.EDIT, icon_color="#60A5FA", icon_size=18, on_click=lambda e, p=prod_name, idx=i: self.open_edit("step", p, idx)),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="#F87171", icon_size=18, on_click=lambda e, p=prod_name, idx=i: self.confirm_delete("step", p, idx))
                    ]) 
                )
                draggable_step = ft.Draggable(group=f"setup_steps_{prod_name}", data={"product": prod_name, "step_idx": i}, content=step_container)
                drop_target = ft.DragTarget(
                    key=f"step_{i}", 
                    group=f"setup_steps_{prod_name}", 
                    data={"product": prod_name, "step_idx": i}, 
                    content=draggable_step, 
                    on_accept=self.handle_setup_step_swap
                )
                
                self.steps_list_col.controls.append(
                    ft.Container(key=f"step_{i}", content=drop_target)
                )

    def add_step_from_dialog(self, e):
        val = self.step_add_input.value.strip()
        pos_val = self.step_pos_input.value.strip()
        if val and self.current_steps_product:
            steps_list = self.products[self.current_steps_product]["steps"]
            target_idx = 0
            
            if pos_val.isdigit():
                idx = int(pos_val) - 1
                if idx < 0: idx = 0
                if idx > len(steps_list): idx = len(steps_list)
                steps_list.insert(idx, val)
                target_idx = idx
            else: 
                steps_list.append(val)
                target_idx = len(steps_list) - 1
                
            self.step_add_input.value = ""
            self.step_pos_input.value = ""
            
            self.refresh_steps_dialog_ui()
            self.render_products()
            
            self.main_page.update()
            self.steps_list_col.scroll_to(key=f"step_{target_idx}", duration=300)
            
            try: self.step_add_input.focus()
            except: pass

    def handle_setup_step_swap(self, e):
        src_control = self.main_page.get_control(e.src_id)
        if not src_control: return
        src_data = src_control.data
        tgt_data = e.control.data
        if src_data["product"] != tgt_data["product"] or src_data["step_idx"] == tgt_data["step_idx"]: return
        prod = src_data["product"]
        src_step_name = self.products[prod]["steps"][src_data["step_idx"]]
        tgt_step_name = self.products[prod]["steps"][tgt_data["step_idx"]]
        self.pending_setup_swap = (prod, src_data["step_idx"], tgt_data["step_idx"])
        self.swap_confirm_text.value = f"{self.t('Are you sure you want to swap')} '{src_step_name}' {self.t('with')} '{tgt_step_name}'?"
        self.main_page.open(self.swap_dialog)
        self.main_page.update()

    def cancel_setup_step_swap(self, e):
        self.pending_setup_swap = None
        self.main_page.close(self.swap_dialog)
        if self.current_steps_product: self.main_page.open(self.steps_dialog)
        self.main_page.update()

    def execute_setup_step_swap(self, e):
        if not hasattr(self, 'pending_setup_swap') or not self.pending_setup_swap: return
        prod, src_idx, tgt_idx = self.pending_setup_swap
        self.products[prod]["steps"][src_idx], self.products[prod]["steps"][tgt_idx] = self.products[prod]["steps"][tgt_idx], self.products[prod]["steps"][src_idx]
        self.pending_setup_swap = None
        self.main_page.close(self.swap_dialog)
        self.render_products()
        if self.current_steps_product:
            self.refresh_steps_dialog_ui()
            self.main_page.open(self.steps_dialog)
        self.show_msg(self.t("Updated successfully!"))
        self.main_page.update()

    def open_stock_dialog(self, prod_name):
        self.current_stock_product = prod_name
        self.show_full_history = False
        self.toggle_history_btn.text = self.t("Show All History")
        self.stock_dialog.title.value = f"{self.t('Manage Stock:')} {prod_name}"
        self.stock_qty_input.value = ""
        self.refresh_stock_history_ui()
        self.main_page.open(self.stock_dialog)
        self.main_page.update()

    def toggle_history(self, e):
        self.show_full_history = not self.show_full_history
        self.toggle_history_btn.text = self.t("Show Recent (10)") if self.show_full_history else self.t("Show All History")
        self.refresh_stock_history_ui()
        self.main_page.update()

    def refresh_stock_history_ui(self):
        self.stock_history_col.controls.clear()
        history = self.products.get(self.current_stock_product, {}).get("stock_history", [])
        display_history = list(reversed(history))
        if not self.show_full_history: display_history = display_history[:10]
        if not display_history:
            self.stock_history_col.controls.append(ft.Container(padding=20, alignment=ft.alignment.center, content=ft.Text(self.t("No stock history found."), color="#64748B", italic=True)))
        else:
            for entry in display_history:
                qty = entry.get("qty", 0); date_str = entry.get("date", "Unknown Date")
                color, sign, bg_color, border_color = ("#10B981", "+", "#ECFDF5", "#D1FAE5") if qty > 0 else ("#EF4444", "", "#FEF2F2", "#FEE2E2")
                self.stock_history_col.controls.append(
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=12, vertical=8), border_radius=8, bgcolor=bg_color, border=ft.border.all(1, border_color),
                        content=ft.Row([
                            ft.Row([ft.Icon(ft.Icons.CALENDAR_TODAY, size=15, color="#64748B"), ft.Text(date_str, size=14, color="#475569", weight=ft.FontWeight.W_600)]),
                            ft.Text(f"{sign}{qty:g}", size=15, color=color, weight=ft.FontWeight.W_900)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                )

    def add_stock_from_dialog(self, e):
        try: qty = float(self.stock_qty_input.value.strip())
        except Exception: self.show_msg(self.t("Invalid quantity!"), "#EF4444"); return
        if qty == 0: return
        prod_name = self.current_stock_product
        current_stock = self.products[prod_name].get("stock", 0)
        if qty < 0 and abs(qty) > current_stock: self.show_msg(self.t("Cannot remove more stock than available!"), "#EF4444"); return
        self.products[prod_name]["stock"] = current_stock + qty
        if "stock_history" not in self.products[prod_name]: self.products[prod_name]["stock_history"] = []
        self.products[prod_name]["stock_history"].append({"qty": qty, "date": datetime.now().strftime("%d %b %Y")})
        self.stock_qty_input.value = ""
        self.refresh_stock_history_ui()
        self.render_products()
        self.show_msg(self.t("Stock updated successfully!"))
        self.main_page.update()

    def open_edit(self, edit_type, product_name, step_index=None):
        self.current_edit_data = {"type": edit_type, "product": product_name, "step": step_index}
        self.edit_input.value = product_name if edit_type == "product" else self.products[product_name]["steps"][step_index]
        self.main_page.open(self.edit_dialog)

    def save_edit(self, e):
        new_val = self.edit_input.value.strip()
        if not new_val: self.show_msg(self.t("Name cannot be empty!"), "#EF4444"); return
        data = self.current_edit_data
        if data["type"] == "product":
            if new_val != data["product"] and new_val in self.products: self.show_msg(self.t("Name invalid or already exists!"), "#EF4444"); return
            self.products[new_val] = self.products.pop(data["product"])
            if self.current_steps_product == data["product"]:
                self.current_steps_product = new_val
                self.steps_dialog.title.controls[1].value = f"{self.t('Routing Steps:')} {new_val}"
        elif data["type"] == "step": self.products[data["product"]]["steps"][data["step"]] = new_val
        self.main_page.close(self.edit_dialog)
        self.render_products()
        if self.current_steps_product: self.refresh_steps_dialog_ui()
        self.show_msg(self.t("Updated successfully!"))
        self.main_page.update()

    def confirm_delete(self, delete_type, product_name, step_index=None):
        self.item_to_delete = {"type": delete_type, "product": product_name, "step": step_index}
        self.main_page.open(self.delete_confirm_dialog)

    def execute_delete(self, e):
        data = self.item_to_delete
        if not data: return
        if data["type"] == "product": del self.products[data["product"]]
        elif data["type"] == "step": self.products[data["product"]]["steps"].pop(data["step"])
        self.item_to_delete = None
        self.main_page.close(self.delete_confirm_dialog)
        self.render_products()
        if self.current_steps_product: self.refresh_steps_dialog_ui()
        self.show_msg(self.t("Updated successfully!"))
        self.main_page.update()

    def render_products(self, is_init=False):
        self.products_list.controls.clear()
        
        total_prods = 0
        total_stock = 0
        out_of_stock = 0

        for prod_name, prod_data in self.products.items():
            if self.search_query and self.search_query not in prod_name.lower():
                continue
                
            total_prods += 1
            stock_qty = prod_data.get("stock", 0)
            total_stock += stock_qty
            if stock_qty <= 0: out_of_stock += 1
            
            steps_count = len(prod_data.get("steps", []))

            # --- COMPACTED ROW PADDING ---
            row_container = ft.Container(
                padding=ft.padding.symmetric(horizontal=15, vertical=8),
                border=ft.border.only(bottom=ft.border.BorderSide(1, "#F1F5F9")),
                content=ft.Row([
                    ft.Text(prod_name, expand=2, weight=ft.FontWeight.W_800, color="#0F172A", size=20), # INCREASED SIZE HERE
                    ft.Text(f"{stock_qty:g}", expand=1, color="#EF4444" if stock_qty <= 0 else "#10B981", weight=ft.FontWeight.W_800, size=16),
                    
                    ft.Container(
                        expand=1,
                        content=ft.Row([
                            ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, size=18, color="#2563EB"),
                            ft.Text(f"{steps_count}", size=16, color="#2563EB", weight=ft.FontWeight.W_700)
                        ], spacing=6),
                        on_click=lambda e, p=prod_name: self.open_steps_dialog(p),
                        ink=True,
                        tooltip=self.t("Edit Steps")
                    ),

                    ft.Row([
                        ft.IconButton(ft.Icons.INFO_OUTLINE, icon_color="#10B981", icon_size=20, tooltip=self.t("Manage Stock"), on_click=lambda e, p=prod_name: self.open_stock_dialog(p)),
                        ft.IconButton(ft.Icons.EDIT, icon_color="#3B82F6", icon_size=20, tooltip=self.t("Edit Product Name"), on_click=lambda e, p=prod_name: self.open_edit("product", p)),
                        ft.IconButton(ft.Icons.DELETE, icon_color="#EF4444", icon_size=20, tooltip=self.t("Delete Product"), on_click=lambda e, p=prod_name: self.confirm_delete("product", p)),
                    ], width=120, alignment=ft.MainAxisAlignment.END, spacing=0)

                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )
            
            self.products_list.controls.append(row_container)

        self.kpi_total_prods.value = str(total_prods)
        self.kpi_total_stock.value = f"{total_stock:g}"
        self.kpi_out_of_stock.value = str(out_of_stock)

        if not self.products_list.controls:
            self.products_list.controls.append(
                ft.Container(
                    padding=30, alignment=ft.alignment.center, 
                    content=ft.Text(self.t("No products found."), color="#64748B", size=15, italic=True)
                )
            )

        if not is_init:
            if self.main_page:
                try: self.update()
                except Exception: pass
            if hasattr(self, 'save_cb') and self.save_cb:
                self.save_cb()