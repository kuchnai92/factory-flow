import json
import os
import hashlib
import sys
import re
import threading

# --- Local Memory Variables ---
inventory = []
invoices = []
customers = []

state = {
    "is_logged_in": False,
    "is_test_mode": False,
    "nav_index": 0,
    "search_query": "",
    "current_page": 1,
    "billing_items": [],
    "last_layout_mode": None,
    "rev_hidden": True
}

# --- Cloud Backup Credentials ---
SUPABASE_URL = "YOUR_NEW_SUPABASE_URL_HERE"
SUPABASE_KEY = "YOUR_NEW_SUPABASE_KEY_HERE"

supabase = None
HAS_SUPABASE = False

def connect_supabase_bg():
    global supabase, HAS_SUPABASE
    try:
        from supabase import create_client, Client
        if "YOUR_" not in SUPABASE_URL:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            HAS_SUPABASE = True
            print("✅ Connected to Supabase Cloud Successfully.")
        else:
            print("⚠️ Supabase Keys are missing.")
    except ImportError:
        print("❌ Error: 'supabase' library not installed.")
        HAS_SUPABASE = False
    except Exception as e:
        print(f"❌ Supabase Connection Error: {e}")
        HAS_SUPABASE = False

threading.Thread(target=connect_supabase_bg, daemon=True).start()

# --- JSON File Path Setup (Keeps data in the app) ---
IS_WINDOWS_DESKTOP = (sys.platform == "win32")

if getattr(sys, 'frozen', False):
    BASE_INTERNAL_DIR = sys._MEIPASS 
    BASE_EXTERNAL_DIR = os.path.dirname(sys.executable)
else:
    BASE_INTERNAL_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_EXTERNAL_DIR = BASE_INTERNAL_DIR

if IS_WINDOWS_DESKTOP:
    REAL_DATA_DIR = os.path.join(BASE_EXTERNAL_DIR, "data")
else:
    try:
        user_home = os.path.expanduser("~")
        REAL_DATA_DIR = os.path.join(user_home, "AminSons_Data")
    except:
        REAL_DATA_DIR = os.path.join(BASE_EXTERNAL_DIR, "data")

# Create the data folder automatically if it doesn't exist
if not os.path.exists(REAL_DATA_DIR):
    try: os.makedirs(REAL_DATA_DIR)
    except: pass

DATA_DIR = REAL_DATA_DIR
INVENTORY_FILE = ""
INVOICES_JSON = ""
CUSTOMERS_FILE = ""
CONFIG_FILE = os.path.join(REAL_DATA_DIR, "config.json")

CURRENT_ADMIN = "default"

# --- JSON Read/Write Functions ---
def load_data(file_path, default_value):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                if "inventory" in file_path and isinstance(data, list):
                    for item in data:
                        if "category" not in item: item["category"] = "General"
                return data
        except:
            return default_value
    return default_value

def save_data(file_path, data):
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Save Error: {e}")

# --- Security Functions ---
def hash_val(text):
    return hashlib.sha256(str(text).encode()).hexdigest()

SEC_KEY_HASH = hash_val("youmekutameyoukuta")

# Load configuration (Admin Passwords) from JSON
config = load_data(CONFIG_FILE, {
    "admins": {"default": hash_val("123")} # --- DEFAULT PASSWORD SET TO 123 ---
})

# --- Profile/Workspace Setup ---
def setup_paths(username):
    global DATA_DIR, INVENTORY_FILE, INVOICES_JSON, CUSTOMERS_FILE, CURRENT_ADMIN
    CURRENT_ADMIN = username
    
    if state.get("is_test_mode"):
        DATA_DIR = os.path.join(REAL_DATA_DIR, "test_data")
    else:
        DATA_DIR = os.path.join(REAL_DATA_DIR, f"data_{username}")
    
    if not os.path.exists(DATA_DIR):
        try: os.makedirs(DATA_DIR)
        except: pass
        
    INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.json")
    INVOICES_JSON = os.path.join(DATA_DIR, "invoices.json")
    CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")

def get_id_sort_key(item):
    try:
        id_str = str(item.get('id', '0'))
        numbers = re.findall(r'\d+', id_str)
        if numbers: return int(numbers[0])
        return 0
    except: return 0

def reindex_collection(data_list, prefix):
    data_list.sort(key=get_id_sort_key)
    for index, item in enumerate(data_list):
        item['id'] = f"{prefix}{index + 1}"