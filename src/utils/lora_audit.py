# The script processes a database of LORA activations and their usage in images, 
# comparing them against a list of available LORAs on disk. 
# It categorizes the LORAs by model family and category, and identifies which ones are unused.
# The script also includes functions to extract keywords from prompts and to load LORA configurations from a YAML file.
#  
import os
import sys
import glob
from src.utils.raw_loader import load_models_and_loras # ✅ load real lora entries
import yaml
import re
import json


from src.utils.config_loader import load_config
config = load_config()

LORA_DIR = config["paths"]["lora_folder"]
FAVORITES_DB = config["paths"]["favorites_db"]


def get_used_lora_ids_from_raw_db():
    import sqlite3
    used = set()
    conn = sqlite3.connect(FAVORITES_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT loras, prompt FROM images")
    rows = cursor.fetchall()
    conn.close()

    for loras_str, prompt_str in rows:
        combined = f"{loras_str or ''} {prompt_str or ''}".lower()
        matches = re.findall(r"<lora:([^:>]+):", combined)
        used.update(m.strip().lower() for m in matches)
    return used

def get_all_loras_on_disk(lora_dir=LORA_DIR):
    all_loras = []
    for path in glob.glob(os.path.join(lora_dir, "**", "*.safetensors"), recursive=True):
        relative = os.path.relpath(path, lora_dir).replace("\\", "/")
        name = os.path.splitext(relative)[0]
        all_loras.append(name)
    return set(all_loras)

def get_all_lora_names_from_db(combos):
    used = set()
    for combo in combos:
        for lora in combo["loras"]:
            if "activation" in lora:
                used.add(lora["activation"])
            used.add(os.path.basename(lora["name"]))
    return used

def get_used_lora_identifiers_from_raw_db():
    import sqlite3
    used = set()
    conn = sqlite3.connect(FAVORITES_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT loras, prompt FROM images")
    rows = cursor.fetchall()
    conn.close()

    for loras_str, prompt_str in rows:
        combined = f"{loras_str or ''} {prompt_str or ''}".lower()
        # Grab activations from <lora:NAME:...>
        matches = re.findall(r"<lora:([^:>]+):", combined)
        used.update(m.strip() for m in matches)
        # You can also pull some meaningful words from prompt if needed:
        # used.update(w for w in combined.split() if len(w) > 4)

    return used

def get_unused_loras_grouped_by_model_and_category():
    used_ids = get_used_lora_ids_from_raw_db()  # Get activation names used
    
    # Add normalization to the matching function
    def normalize_for_matching(name):
        """Normalize names for better matching between DB and filesystem"""
        if not name:
            return ""
        # Remove common prefixes/suffixes, standardize separators
        name = name.lower().strip()
        name = re.sub(r'[^\w]+', '_', name)  # unify all separators
        name = name.replace('_lora', '')
        name = re.sub(r'flux.*$', '', name)  # strip suffixes like 'flux_v1'
        return name.strip('_')
    
    # Normalize all used IDs
    normalized_used_ids = {normalize_for_matching(id) for id in used_ids}
    

    # Change this line to unpack the tuple
    _, _, all_loras = load_models_and_loras(model_dir="unused", lora_dir=LORA_DIR)
    print(f"[DEBUG] Sample entry in all_loras: {all_loras[0] if all_loras else 'EMPTY'}")
    grouped = {}

    for lora in all_loras:
        lora_path = lora["name"]                   # e.g. Flux/Artist Styles/Cyberpunk_Anime
        folder_parts = lora_path.split("/")
        if len(folder_parts) < 3:
            continue

        model_family = folder_parts[0]
        folder_category = folder_parts[-2]
        category = config["categories"].get(folder_category, "unknown")

        # Get potential match identifiers
        if not isinstance(lora, dict):
            print(f"[ERROR] Invalid LORA object: type={type(lora)}, value={lora}")
            continue
        filename = os.path.basename(lora_path)
        activation = (lora.get("activation") or "").lower()
        
        
        # Normalize for better matching
        norm_filename = normalize_for_matching(filename)
        # print(f"[DEBUG] Checking LORA: '{filename}' | Norm: '{norm_filename}' | Activation: '{activation}'")
        norm_activation = normalize_for_matching(activation)
        
        # Also try with common variations
        aliases = [
            norm_filename,
            norm_activation,
            normalize_for_matching(filename.replace("_", " ")),  # Some users may add spaces instead of underscores
            # Add any other common variations
        ]
        
        # Check if any alias matches
        is_used = any(alias in normalized_used_ids for alias in aliases if alias)
        
        if is_used:
            print(f"[DEBUG] Skipping '{lora['name']}' — matched via normalized name/alias")
            continue  # It's been used
            
        # Only add to unused group if we reach here
        grouped.setdefault(model_family.lower(), {}).setdefault(category.lower(), []).append(lora_path)

    print(f"[AUDIT] Returning type: {type(grouped)} | Sample keys: {list(grouped.keys())[:5]}")
    return grouped

def get_used_lora_activations():
    import sqlite3
    used = set()
    conn = sqlite3.connect(FAVORITES_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT loras FROM images")
    rows = cursor.fetchall()
    conn.close()

    for (loras_str,) in rows:
        matches = re.findall(r"<lora:([^:>]+):", loras_str or "")
        used.update(m.strip().lower() for m in matches)
    return used