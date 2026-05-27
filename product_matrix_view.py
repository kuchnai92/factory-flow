import flet as ft

class ProductMatrixView(ft.Container):
    def __init__(self, page: ft.Page, products_config: dict, save_cb, t):
        super().__init__()
        self.main_page = page  
        self.products = products_config
        self.save_cb = save_cb
        self.t = t
        self.expanded_products = set()
        self.expand = True
        self.visible = False
        self.padding = 20

        self.product_name_input = ft.TextField(
            label=self.t("New Product Name"), expand=True, on_submit=self.add_product,
            border_radius=8, border_color="#CBD5E1", focused_border_color="#2563EB", cursor_color="#2563EB",
            text_size=16, height=50, content_padding=ft.padding.symmetric(horizontal=15, vertical=10)
        )
        self.add_product_btn = ft.ElevatedButton(
            self.t("Create Product"), icon=ft.Icons.ADD, on_click=self.add_product, height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), color="#FFFFFF", bgcolor="#2563EB") 
        )

        self.products_grid = ft.ResponsiveRow(columns=12, spacing=15, run_spacing=15)
        self.products_list = ft.ListView(controls=[self.products_grid], expand=True, spacing=15, padding=ft.padding.only(bottom=40))

        self.content = ft.Column(
            expand=True,
            controls=[
                ft.Row([
                    ft.Column([
                        ft.Text(self.t("Product Setup Matrix"), size=26, weight=ft.FontWeight.W_800, color="#0F172A"),
                        ft.Text(self.t("Define global routing, processing steps, and manage raw stock levels."), size=15, color="#64748B"),
                    ], expand=True)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                ft.Container(
                    padding=15, bgcolor="#FFFFFF", border_radius=12, border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=10, color="#00000008", offset=ft.Offset(0, 4)),
                    content=ft.ResponsiveRow([
                        ft.Column(col={"xs": 12, "sm": 8}, controls=[self.product_name_input]),
                        ft.Column(col={"xs": 12, "sm": 4}, controls=[self.add_product_btn])
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                ft.Container(height=10),
                self.products_list
            ]
        )
        
        self.edit_input = ft.TextField(label=self.t("Edit Name"), autofocus=True, on_submit=self.save_edit, border_radius=8, border_color="#CBD5E1", focused_border_color="#2563EB", text_size=16)
        self.current_edit_data = None 

        self.edit_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Text(self.t("Edit Name"), weight=ft.FontWeight.BOLD, size=20), content=self.edit_input,
            actions=[
                ft.TextButton(self.t("Cancel"), on_click=lambda e: self.main_page.close(self.edit_dialog), style=ft.ButtonStyle(color="#64748B")), 
                ft.ElevatedButton(self.t("Save"), on_click=self.save_edit, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), color="#FFFFFF", bgcolor="#2563EB")), 
            ],
        )

        self.item_to_delete = None
        self.delete_confirm_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Text(self.t("Confirm Delete"), weight=ft.FontWeight.BOLD, size=20),
            content=ft.Text(self.t("Are you sure you want to delete this?"), size=16),
            actions=[
                ft.TextButton(self.t("Cancel"), on_click=lambda e: self.main_page.close(self.delete_confirm_dialog)),
                ft.ElevatedButton(self.t("Delete"), on_click=self.execute_delete, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), color="white", bgcolor="#EF4444")) 
            ]
        )

        self.pending_setup_swap = None
        self.swap_confirm_btn = ft.ElevatedButton(self.t("Yes, Swap"), on_click=self.execute_setup_step_swap, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), color="#FFFFFF", bgcolor="#2563EB"))
        self.swap_confirm_text = ft.Text("", size=16)
        self.swap_dialog = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Text(self.t("Confirm Swap"), weight=ft.FontWeight.BOLD, size=20),
            content=self.swap_confirm_text,
            actions=[
                ft.TextButton(self.t("Cancel"), on_click=lambda e: (setattr(self, 'pending_setup_swap', None), self.main_page.close(self.swap_dialog)), style=ft.ButtonStyle(color="#64748B")),
                self.swap_confirm_btn
            ]
        )
        
        self.render_products(is_init=True)

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

    def execute_setup_step_swap(self, e):
        if not hasattr(self, 'pending_setup_swap') or not self.pending_setup_swap: return
        prod, src_idx, tgt_idx = self.pending_setup_swap
        
        self.products[prod]["steps"][src_idx], self.products[prod]["steps"][tgt_idx] = self.products[prod]["steps"][tgt_idx], self.products[prod]["steps"][src_idx]
            
        self.pending_setup_swap = None
        self.main_page.close(self.swap_dialog)
        self.render_products()
        self.show_msg(self.t("Updated successfully!"))

    def show_msg(self, text, color="#10B981"):
        try:
            snack = ft.SnackBar(content=ft.Text(text, color="#FFFFFF", weight=ft.FontWeight.W_500, size=16), bgcolor=color, behavior=ft.SnackBarBehavior.FLOATING, margin=20, shape=ft.RoundedRectangleBorder(radius=8))
            self.main_page.open(snack)
        except: pass

    def add_product(self, e):
        name = self.product_name_input.value.strip()
        if name and name not in self.products:
            self.products[name] = {"steps": [], "stock": 0}; self.expanded_products.add(name); self.product_name_input.value = ""; self.render_products(); self.show_msg(self.t("Updated successfully!"))
        else: self.show_msg(self.t("Name invalid or already exists!"), "#EF4444")

    def add_step(self, product_name, step_name, input_field):
        if step_name: self.products[product_name]["steps"].append(step_name); self.expanded_products.add(product_name); input_field.value = ""; self.render_products()

    def add_stock_to_product(self, prod_name, qty_input):
        try:
            qty = float(qty_input.value.strip())
        except Exception:
            self.show_msg(self.t("Invalid quantity!"), "#EF4444")
            return
        if qty == 0: return
        
        current_stock = self.products[prod_name].get("stock", 0)
        
        if qty < 0 and abs(qty) > current_stock:
            self.show_msg(self.t("Cannot remove more stock than available!"), "#EF4444")
            return
            
        self.products[prod_name]["stock"] = current_stock + qty
        qty_input.value = ""
        self.render_products()
        self.show_msg(self.t("Stock updated successfully!"))

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
            if data["product"] in self.expanded_products: self.expanded_products.remove(data["product"]); self.expanded_products.add(new_val)
        elif data["type"] == "step": self.products[data["product"]]["steps"][data["step"]] = new_val
        self.main_page.close(self.edit_dialog); self.render_products(); self.show_msg(self.t("Updated successfully!"))

    def confirm_delete(self, delete_type, product_name, step_index=None):
        self.item_to_delete = {"type": delete_type, "product": product_name, "step": step_index}
        self.main_page.open(self.delete_confirm_dialog)

    def execute_delete(self, e):
        data = self.item_to_delete
        if not data: return
        if data["type"] == "product":
            del self.products[data["product"]]
            self.expanded_products.discard(data["product"])
        elif data["type"] == "step":
            self.products[data["product"]]["steps"].pop(data["step"])
        
        self.item_to_delete = None
        self.main_page.close(self.delete_confirm_dialog)
        self.render_products()
        self.show_msg(self.t("Updated successfully!"))
    
    def handle_expansion(self, e, prod_name):
        # BUG FIX: Ensure strict safety checks to prevent ghost-reopening
        is_expanded = str(e.data).lower() == "true"
        if is_expanded:
            self.expanded_products.add(prod_name)
        else:
            self.expanded_products.discard(prod_name)

    def render_products(self, is_init=False):
        self.products_grid.controls.clear()
        
        for prod_name, prod_data in self.products.items():
            steps = prod_data.get("steps", [])
            stock_qty = prod_data.get("stock", 0)
            
            steps_column = ft.Column(spacing=0)
            for i, step in enumerate(steps):
                step_container = ft.Container(
                    padding=ft.padding.only(left=10, top=8, bottom=8), 
                    border=ft.border.only(bottom=ft.border.BorderSide(1, "#F1F5F9")),
                    content=ft.Row([
                        ft.Container(padding=6, bgcolor="#EFF6FF", border_radius=20, content=ft.Text(str(i+1), size=14, color="#2563EB", weight=ft.FontWeight.BOLD)),
                        ft.Text(step, expand=True, size=18, color="#334155", weight=ft.FontWeight.W_600, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.IconButton(ft.Icons.EDIT, icon_color="#60A5FA", icon_size=18, padding=0, width=34, height=34, on_click=lambda e, p=prod_name, idx=i: self.open_edit("step", p, idx)),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="#F87171", icon_size=18, padding=0, width=34, height=34, on_click=lambda e, p=prod_name, idx=i: self.confirm_delete("step", p, idx))
                    ]) 
                )

                draggable_step = ft.Draggable(
                    group=f"setup_steps_{prod_name}", 
                    data={"product": prod_name, "step_idx": i},
                    content=step_container
                )
                
                drop_target = ft.DragTarget(
                    group=f"setup_steps_{prod_name}",
                    data={"product": prod_name, "step_idx": i},
                    content=draggable_step,
                    on_accept=self.handle_setup_step_swap
                )
                
                steps_column.controls.append(drop_target)

            stock_input = ft.TextField(label=self.t("Add or Reduce Qty (Use -)"), expand=True, border_radius=8, content_padding=10, text_size=16, height=48, border_color="#E2E8F0", focused_border_color="#10B981")
            stock_input.on_submit = lambda e, p=prod_name, inp=stock_input: self.add_stock_to_product(p, inp)
            add_stock_btn = ft.ElevatedButton(self.t("Import Stock"), icon=ft.Icons.ADD_SHOPPING_CART, height=48, on_click=lambda e, p=prod_name, inp=stock_input: self.add_stock_to_product(p, inp), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), color="#FFFFFF", bgcolor="#10B981"))
            
            stock_row = ft.Container(
                padding=ft.padding.only(left=10, right=10, top=15, bottom=10),
                bgcolor="#F8FAFC",
                content=ft.Row([stock_input, add_stock_btn])
            )

            step_input = ft.TextField(label=self.t("Add routing step"), expand=True, border_radius=8, content_padding=10, text_size=16, height=48, border_color="#E2E8F0", focused_border_color="#2563EB")
            step_input.on_submit = lambda e, p=prod_name, inp=step_input: self.add_step(p, inp.value.strip(), inp)
            add_step_btn = ft.IconButton(ft.Icons.ADD, icon_color="#FFFFFF", bgcolor="#2563EB", icon_size=20, width=48, height=48, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=lambda e, p=prod_name, inp=step_input: self.add_step(p, inp.value.strip(), inp))
            steps_column.controls.append(ft.Container(padding=ft.padding.only(left=10, right=10, top=10, bottom=15), content=ft.Row([step_input, add_step_btn])))

            title_row = ft.Row([
                ft.Text(prod_name, size=20, weight=ft.FontWeight.W_800, color="#0F172A"),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                    bgcolor="#EFF6FF" if stock_qty > 0 else "#F1F5F9", 
                    border_radius=12,
                    border=ft.border.all(1, "#BFDBFE" if stock_qty > 0 else "#E2E8F0"),
                    content=ft.Row([
                        ft.Icon(ft.Icons.INVENTORY_2_ROUNDED, size=16, color="#2563EB" if stock_qty > 0 else "#94A3B8"),
                        ft.Text(f"{stock_qty:g} {self.t('units')}", color="#2563EB" if stock_qty > 0 else "#94A3B8", weight=ft.FontWeight.BOLD, size=14)
                    ], spacing=4)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            card = ft.Container(
                bgcolor="#FFFFFF", border_radius=12, border=ft.border.all(1, "#E2E8F0"), shadow=ft.BoxShadow(blur_radius=10, color="#00000008", offset=ft.Offset(0, 4)),
                content=ft.ExpansionTile(
                    title=title_row,
                    leading=ft.Container(padding=8, bgcolor="#F8FAFC", border_radius=8, content=ft.Icon(ft.Icons.CATEGORY_OUTLINED, color="#64748B", size=22)),
                    controls_padding=0, initially_expanded=(prod_name in self.expanded_products),
                    on_change=lambda e, p=prod_name: self.handle_expansion(e, p),
                    trailing=ft.Row([
                        ft.IconButton(ft.Icons.EDIT, icon_color="#60A5FA", icon_size=20, on_click=lambda e, p=prod_name: self.open_edit("product", p)),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="#F87171", icon_size=20, on_click=lambda e, p=prod_name: self.confirm_delete("product", p)),
                    ], tight=True),
                    controls=[ft.Divider(height=1, color="#E2E8F0"), stock_row, ft.Divider(height=1, color="#E2E8F0"), steps_column]
                )
            )
            self.products_grid.controls.append(ft.Column(col={"xs": 12, "md": 6, "xl": 4}, controls=[card]))
        
        if not is_init:
            if self.main_page:
                try: self.update()
                except Exception: pass
            if hasattr(self, 'save_cb') and self.save_cb:
                self.save_cb()