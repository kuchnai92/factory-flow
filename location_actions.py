import uuid
import copy
from datetime import datetime

def parse_qty(val):
    try: return float(val)
    except (ValueError, TypeError): return None

class LocationActionsMixin:
    def handle_step_swap(self, e):
        src_control = self.page.get_control(e.src_id)
        if not src_control: return
        src_data = src_control.data
        tgt_data = e.control.data
        
        if src_data == tgt_data: return
        
        item = self.get_item_by_id(src_data["item_id"])
        if not item: return
        
        src_step_name = item["steps"][src_data["step_idx"]]
        tgt_step_name = item["steps"][tgt_data["step_idx"]]
        
        self.pending_step_swap = (src_data["item_id"], src_data["step_idx"], tgt_data["step_idx"])
        self.swap_confirm_text.value = f"{self.t('Are you sure you want to swap')} '{src_step_name}' {self.t('with')} '{tgt_step_name}'?"
        self.page.open(self.swap_dialog)
        self.page.update()

    def execute_step_swap(self, e):
        if not hasattr(self, 'pending_step_swap') or not self.pending_step_swap: return
        item_id, src_idx, tgt_idx = self.pending_step_swap
        
        item = self.get_item_by_id(item_id)
        if item:
            item["steps"][src_idx], item["steps"][tgt_idx] = item["steps"][tgt_idx], item["steps"][src_idx]
            if item["step_idx"] == src_idx:
                item["step_idx"] = tgt_idx
            elif item["step_idx"] == tgt_idx:
                item["step_idx"] = src_idx
                
        self.pending_step_swap = None
        self.page.close(self.swap_dialog)
        self.render()

    def revert_archived_batch(self, base_name):
        tab_data = self.get_current_data()["data"][self.get_current_data()["tabs"][self.get_current_data()["active_tab"]]]
        history = tab_data["history"]
        active = tab_data["active"]
        
        items_to_revert = [item for item in history if item.get("entry_type") == "Batch" and item.get("name", "").split(".")[0] == base_name]
        
        for item in items_to_revert:
            history.remove(item)
            item.pop("date_completed", None)
            item.pop("entry_type", None)
            item["timeline"].append({"step": "Reverted from Archive", "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "qty": item["quantity"]})
            active.append(item)
            
        self.render()
        self.page.update()
        self.show_snackbar(f"{self.t('Batch')} {base_name} {self.t('reverted to Active Matrix!')}")

    def save_l3_tab(self, e):
        val = self.l3_name_input.value.strip()
        if not val: return
        data_ctx = self.get_current_data()
        if val not in data_ctx["tabs"]:
            data_ctx["tabs"].append(val); data_ctx["data"][val] = {"stock": {}, "active": [], "history": []}; data_ctx["active_tab"] = len(data_ctx["tabs"]) - 1
            self.page.close(self.l3_dialog); self.render()
        else: self.show_snackbar(self.t("Name invalid or already exists!"), True)

    def save_edit_l3_tab(self, e):
        val = self.l3_edit_name_input.value.strip()
        if not val: return
        data_ctx = self.get_current_data()
        old_name = self.l3_target_edit_name
        
        if val != old_name:
            if val in data_ctx["tabs"]:
                self.show_snackbar(self.t("Name already exists!"), True)
                return
            idx = data_ctx["tabs"].index(old_name)
            data_ctx["tabs"][idx] = val
            data_ctx["data"][val] = data_ctx["data"].pop(old_name)
            
        self.page.close(self.l3_edit_dialog)
        self.render()

    def execute_delete_l3(self, e):
        data_ctx = self.get_current_data()
        name = self.l3_target_delete_name
        if name in data_ctx["tabs"]:
            data_ctx["tabs"].remove(name)
            del data_ctx["data"][name]
            
            if data_ctx["active_tab"] >= len(data_ctx["tabs"]):
                data_ctx["active_tab"] = max(0, len(data_ctx["tabs"]) - 1)
                
        self.page.close(self.delete_l3_confirm_dialog)
        self.render()

    def execute_process(self, e):
        ptype = self.current_process_product; qty = parse_qty(self.process_qty_input.value)
        batch_name = self.process_batch_input.value.strip()
        if not batch_name: return
        if qty is None or qty <= 0: return
        
        current_stock = self.products_config.get(ptype, {}).get("stock", 0)
        if qty > current_stock: 
            self.show_snackbar(f"{self.t('Not enough stock! Only ')} {current_stock:g} {self.t(' available.')}", True)
            return
            
        self.products_config[ptype]["stock"] = current_stock - qty
        
        independent_steps = list(self.products_config.get(ptype, {}).get("steps", []))
        time_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        
        data_ctx = self.get_current_data()
        tab_data = data_ctx["data"][data_ctx["tabs"][data_ctx["active_tab"]]]
        tab_data["active"].append({"id": str(uuid.uuid4()), "type": ptype, "name": batch_name, "quantity": qty, "steps": independent_steps, "step_idx": 0, "is_processing": False, "timeline": [{"step": "Created from Stock", "time": time_str, "qty": qty}]})
        self.page.close(self.process_dialog); self.render()

    def execute_split(self, e):
        item, active_items_list = self.get_item_by_id(self.current_action_item, return_list=True)
        total_split_qty = 0
        new_branches = []
        
        for row in self.split_fields_container.controls:
            name = row.controls[0].value.strip()
            qty = parse_qty(row.controls[1].value)
            if not name or qty is None or qty <= 0:
                self.show_snackbar(self.t("Invalid name or quantity in branches!"), True); return
            if name in self.get_all_batch_names_for_product(item["type"]) or name == item["name"]:
                 self.show_snackbar(f"Batch '{name}' already exists!", True); return
            total_split_qty += qty
            new_branches.append({"name": name, "qty": qty})
            
        if total_split_qty >= item["quantity"]:
            self.show_snackbar(self.t("Split total cannot exceed available quantity!"), True); return
            
        item["quantity"] -= total_split_qty
        
        children_to_add = []
        for b in new_branches:
            child = copy.deepcopy(item) 
            child["id"] = str(uuid.uuid4())
            child["name"] = b["name"]
            child["quantity"] = b["qty"]
            child["parent"] = item["name"] if item["name"] != item["name"].split(".")[0] else f"{item['name'].split('.')[0]}.1"
            for log in child["timeline"]: log["qty"] = child["quantity"]
            child["timeline"].append({"step": f"Created from split ({item['name']})", "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "qty": b["qty"]})
            children_to_add.append(child)
            
        for log in item["timeline"]: log["qty"] = item["quantity"]
            
        item["timeline"].append({"step": f"Split {total_split_qty:g} units into {len(new_branches)} branches", "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "qty": item["quantity"]})
        
        base_name = item["name"].split(".")[0]
        if item["name"] == base_name: item["name"] = f"{base_name}.1"
        
        active_items_list.extend(children_to_add)
        self.page.close(self.split_dialog); self.render()

    def execute_merge(self, e):
        target_name = self.merge_dd.value
        if not target_name: return
        item, active_items_list = self.get_item_by_id(self.current_action_item, return_list=True)
        
        target_item = next((b for b in active_items_list if b["name"] == target_name), None)
        if not target_item: return
        
        target_item["quantity"] += item["quantity"]
        for log in target_item["timeline"]: log["qty"] = target_item["quantity"]
            
        target_item["timeline"].append({"step": f"Merged from {item['name']}", "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "qty": target_item["quantity"]})
        
        active_items_list.remove(item)
        self.page.close(self.merge_dialog); self.render()

    def execute_add_qty(self, e):
        qty_str = self.add_qty_input.value.strip()
        try: qty = float(qty_str)
        except ValueError: return
            
        if qty == 0: return
        is_free_stock = self.free_stock_checkbox.value
        item = self.get_item_by_id(self.current_action_item)
        
        if qty > 0:
            if not is_free_stock:
                curr_stock = self.products_config.get(item["type"], {}).get("stock", 0)
                if qty > curr_stock: 
                    self.show_snackbar(f"{self.t('Not enough stock! Only ')} {curr_stock:g} {self.t(' available.')}", True)
                    return
                self.products_config[item["type"]]["stock"] = curr_stock - qty
                
            item["quantity"] += qty
            action_text = " (Free Stock)" if is_free_stock else " from stock"
            item["timeline"].append({"step": f"Added {qty:g} units{action_text}", "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "qty": item["quantity"]})
        else:
            remove_qty = abs(qty)
            if remove_qty > item["quantity"]:
                self.show_snackbar(self.t("Cannot remove more than batch has!"), True)
                return
                
            if not is_free_stock:
                curr_stock = self.products_config.get(item["type"], {}).get("stock", 0)
                self.products_config[item["type"]]["stock"] = curr_stock + remove_qty
                
            item["quantity"] -= remove_qty
            action_text = " (Free/Discarded)" if is_free_stock else " to stock"
            item["timeline"].append({"step": f"Removed {remove_qty:g} units{action_text}", "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "qty": item["quantity"]})
            
        self.page.close(self.add_qty_dialog)
        self.render()

    def execute_cancel_to_stock(self, e):
        qty_str = self.cancel_to_stock_qty_input.value.strip()
        qty = parse_qty(qty_str)
        if qty is None or qty <= 0: return
            
        item, active_items_list = self.get_item_by_id(self.current_action_item, return_list=True)
        
        if qty > item["quantity"]:
            self.show_snackbar(self.t("Cannot return more than batch has!"), True)
            return
            
        curr_stock = self.products_config.get(item["type"], {}).get("stock", 0)
        self.products_config[item["type"]]["stock"] = curr_stock + qty
        
        if qty == item["quantity"]:
            active_items_list.remove(item)
            remaining = [b for b in active_items_list if b["type"] == item["type"]]
            if not remaining and self.active_product_filter == item["type"]: self.active_product_filter = None
            self.show_snackbar(self.t("Batch fully removed and restocked."))
        else:
            item["quantity"] -= qty
            for log in item["timeline"]: log["qty"] = item["quantity"]
            item["timeline"].append({"step": f"Returned {qty:g} units to stock", "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "qty": item["quantity"]})
            
        self.page.close(self.cancel_to_stock_dialog)
        self.render()

    def execute_custom_step(self, e):
        if self.custom_step_input.visible:
            val = self.custom_step_input.value.strip()
        else:
            val = self.step_dropdown.value
            if val in [self.t("No remaining steps"), self.t("No steps defined")]:
                val = None
            
        pos_str = self.custom_step_pos_input.value.strip()
        
        if val:
            item = self.get_item_by_id(self.current_action_item)
            pos_idx = len(item["steps"]) 
            if pos_str.isdigit():
                pos_idx = int(pos_str) - 1
                if pos_idx < 0: pos_idx = 0
                if pos_idx > len(item["steps"]): pos_idx = len(item["steps"])
            
            item["steps"].insert(pos_idx, val)
            
            ptype = item["type"]
            if ptype in self.products_config and val not in self.products_config[ptype].get("steps", []):
                self.products_config[ptype]["steps"].append(val)
            
            if pos_idx < item["step_idx"]: item["step_idx"] += 1
            elif pos_idx == item["step_idx"] and item.get("is_processing"): item["step_idx"] += 1
            
            self.page.close(self.step_dialog)
            self.render()
        else:
            self.show_snackbar(self.t("Please enter or select a valid step!"), True)

    def execute_move(self, e):
        fac, loc, sub = self.move_fac_dd.value, self.move_loc_dd.value, self.move_sub_dd.value
        if not (fac and loc and sub): return
        curr_fac, curr_loc = self.get_context(); curr_sub = self.get_current_data()["tabs"][self.get_current_data()["active_tab"]]
        item, active_items_list = self.get_item_by_id(self.current_action_item, return_list=True)
        active_items_list.remove(item)
        item["timeline"].append({"step": f"Relocated: [{curr_fac} > {curr_loc} > {curr_sub}] → [{fac} > {loc} > {sub}]", "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "qty": item["quantity"]})
        target_key = f"{fac}::{loc}"
        if target_key not in self.level3_data: self.level3_data[target_key] = {"tabs": [sub], "active_tab": 0, "data": {sub: {"stock": {}, "active": [], "history": []}}}
        elif sub not in self.level3_data[target_key]["data"]: self.level3_data[target_key]["tabs"].append(sub); self.level3_data[target_key]["data"][sub] = {"stock": {}, "active": [], "history": []}
        self.level3_data[target_key]["data"][sub]["active"].append(item)
        self.page.close(self.move_dialog); self.show_snackbar("Batch safely relocated!"); self.render()

    def execute_step(self, e):
        item, active_items_list = self.get_item_by_id(self.current_action_item, return_list=True)
        if item["step_idx"] < len(item["steps"]):
            step_name = item["steps"][item["step_idx"]]
            idx_val = item["step_idx"]
            if not item.get("is_processing", False): item["is_processing"] = True; item["timeline"].append({"step": f"Started: {step_name}", "idx": idx_val, "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "qty": item["quantity"]})
            else: item["is_processing"] = False; item["timeline"].append({"step": f"Completed: {step_name}", "idx": idx_val, "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "qty": item["quantity"]}); item["step_idx"] += 1
        self.page.close(self.confirm_dialog); self.render()

    def execute_delete_step(self, e):
        if not self.delete_type_data: return
        item = self.get_item_by_id(self.delete_type_data["id"])
        step_idx = self.delete_type_data["idx"]
        if item and step_idx < len(item["steps"]): item["steps"].pop(step_idx)
        self.delete_type_data = None
        self.page.close(self.delete_confirm_dialog)
        self.render()

    def execute_revert(self, item_id):
        item = self.get_item_by_id(item_id)
        if not item: return
        if item.get("is_processing", False):
            item["is_processing"] = False
            if item["timeline"] and "Started:" in item["timeline"][-1]["step"]: item["timeline"].pop()
        elif item["step_idx"] > 0:
            item["step_idx"] -= 1; item["is_processing"] = True
            if item["timeline"] and "Completed:" in item["timeline"][-1]["step"]: item["timeline"].pop()
        self.render()

    def execute_complete_batch(self, e):
        item, active_items_list = self.get_item_by_id(self.current_action_item, return_list=True)
        data_ctx = self.get_current_data()
        tab_data = data_ctx["data"][data_ctx["tabs"][data_ctx["active_tab"]]]
        history_item = copy.deepcopy(item)
        history_item["date_completed"] = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        history_item["timeline"].append({"step": self.t("Batch Finalized & Archived"), "time": history_item["date_completed"], "qty": item["quantity"]})
        history_item["entry_type"] = "Batch"
        
        tab_data["history"].append(history_item)
        active_items_list.remove(item) 
        
        self.page.close(self.complete_batch_dialog)
        
        remaining = [b for b in active_items_list if b["type"] == item["type"]]
        if not remaining and self.active_product_filter == item["type"]:
            self.active_product_filter = None
            
        self.render()
        self.page.update()