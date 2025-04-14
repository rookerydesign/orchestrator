import sqlite3
import random
import re
import yaml
import sys
import os
from copy import deepcopy

from utils.lora_audit import get_unused_loras_grouped_by_model_and_category



CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

LORA_DIR = config["paths"]["lora_folder"]
FAVORITES_DB = config["paths"]["favorites_db"]

def normalize_combo_signature(loras):
    return tuple(sorted((l["name"], round(l["weight"], 2)) for l in loras))

def load_favorite_combos():
    conn = sqlite3.connect(FAVORITES_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT prompt, loras, gen_settings, image_size, tags FROM images")
    rows = cursor.fetchall()
    conn.close()

    combos = []
    seen_signatures = set()

    for prompt, loras_str, gen_settings, image_size, tags in rows:
        matches = re.findall(r"<lora:([^:>]+):?([\d.]*)?>", loras_str or "")
        parsed_loras = [{"name": name, "weight": float(weight) if weight else 0.6} for name, weight in matches]
        
        sig = normalize_combo_signature(parsed_loras)
        if sig in seen_signatures:
            continue  # skip duplicates
        seen_signatures.add(sig)

        combos.append({
            "prompt": prompt,
            "loras": parsed_loras,
            "gen_settings": gen_settings,
            "image_size": image_size,
            "tags": tags,
        })

    return combos



def prompt_matches_tags(prompt_keywords, tag_string):
    tags = set(tag_string.lower().split(","))
    return any(kw in tags for kw in prompt_keywords)

def pick_random_favorite_combo(combos, genre=None, prompt_keywords=None, discovery_mode=False):
    

    if not prompt_keywords:
        prompt_keywords = set()

    scored = []

    for combo in combos:
        tags = (combo.get("tags") or "").lower()
        match_score = sum(1 for kw in prompt_keywords if kw in tags)
        weight = 1 + (0.25 * match_score)  # Light bias
        scored.append((combo, weight))

    combos, weights = zip(*scored)
    picked = random.choices(combos, weights=weights, k=1)[0]

    # 🔁 Optionally modify combo to include underused LORA
    if discovery_mode:
        try:
            unused_by_cat = get_unused_loras_grouped_by_model_and_category()
            used_lora_names = {l["name"] for l in picked["loras"]}
            picked = inject_new_lora_variant(
                picked, all_known_loras_by_category=unused_by_cat, used_lora_names=used_lora_names
            )
        except Exception as e:
            print(f"[⚠️ Discovery Mode] Failed to inject unused LORA: {e}")

    return picked

def inject_new_lora_variant(combo, all_known_loras_by_category, used_lora_names):
    if random.random() > 0.2:  # 20% chance to mutate
        return combo

    new_combo = deepcopy(combo)
    replaceable = [l for l in new_combo["loras"] if l["name"] in used_lora_names]
    if not replaceable:
        return combo

    to_replace = random.choice(replaceable)
    folder_parts = to_replace['name'].split("/")
    folder_category = folder_parts[-2] if len(folder_parts) >= 2 else "unknown"
    category = config["categories"].get(folder_category, "unknown")
    candidates = all_known_loras_by_category.get(category, [])

    unused = [n for n in candidates if n not in used_lora_names]
    if not unused:
        return combo

    new_lora = {
        "name": random.choice(unused),
        "weight": to_replace["weight"]
    }
    to_replace_index = new_combo["loras"].index(to_replace)
    new_combo["loras"][to_replace_index] = new_lora
    new_combo["debug_note"] = f"🔄 Swapped in new LORA: {new_lora['name']} from category {category}"
    return new_combo
