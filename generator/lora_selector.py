
import os
import random
from collections import defaultdict
import json

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "lora_config.json")
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

def categorize_loras(lora_list):
    categorized = defaultdict(list)
    for lora in lora_list:
        folder_parts = lora['name'].split("/")
        if len(folder_parts) < 2:
            continue
        folder_name = folder_parts[-2]
        category = CONFIG["categories"].get(folder_name, "unknown")
        base_model = lora.get("base_model", "unknown")
        categorized[(base_model, category)].append(lora)
    return categorized

def weighted_choice(choices):
    total = sum(weight for _, weight in choices)
    r = random.uniform(0, total)
    upto = 0
    for choice, weight in choices:
        if upto + weight >= r:
            return choice
        upto += weight
    return choices[-1][0]  # fallback

def select_loras_for_prompt(categorized_loras, base_model):
    # Decide total number of LORAs
    counts = CONFIG["preferred_lora_count"]
    weights = CONFIG["preferred_lora_weights"]
    total_loras = random.choices(counts, weights=weights)[0]
    
    selected = []

    # Always include one detailer
    detailers = categorized_loras.get((base_model, "detailer"), [])
    if detailers:
        selected.append(random.choice(detailers))

    remaining = total_loras - 1
    if remaining <= 0:
        return selected

    # Build weighted category pool (excluding detailer)
    weighted_categories = [(cat, wt) for cat, wt in CONFIG["weights"].items() if cat != "detailer"]

    recent_character_used = False  # Can be stored externally in future

    while remaining > 0:
        category = weighted_choice(weighted_categories)

        # Prevent double character/fx if flagged
        if category == "character" and recent_character_used:
            continue

        lora_pool = categorized_loras.get((base_model, category), [])
        if not lora_pool:
            continue

        candidate = random.choice(lora_pool)
        if candidate in selected:
            continue  # skip duplicates

        selected.append(candidate)
        remaining -= 1

        if category == "character":
            recent_character_used = True

    return selected
