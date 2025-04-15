# This part of the codebase selects LORA files for a discovery mode in an AI image generation tool.
# It randomly selects LORA files from a categorized list of ones that havent been used before in a predetermined database of favorites, 
# ensuring that at least one detailer is included and that the selection is diverse across categories.  

import random
from collections import defaultdict
import json
import os

# Load tag data
TAGS_PATH = os.path.join(os.path.dirname(__file__), "lora_tags.json")
with open(TAGS_PATH, "r") as f:
    TAGS = json.load(f)

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "lora_config.json")
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

DEFAULT_WEIGHTS = CONFIG.get("default_lora_weights", {})
FUZZ = CONFIG.get("weight_fuzz_range", 0.05)


def select_discovery_loras(model_base, categorized_loras):
    selected = []
    debug_log = []
    category_usage_count = defaultdict(int)

    
    model_key = model_base.capitalize()  # Match the capitalization from get_unused_loras_grouped_by_model_and_category
    underused = categorized_loras.get(model_key, {})

    if not underused:
        print(f"[DISCOVERY] No unused LORAs found for model '{model_key}', available models: {list(categorized_loras.keys())}")
        return selected, debug_log
        
    # Rest of function remains the same...

    counts = CONFIG.get("preferred_lora_count", [3, 4, 5])
    weights = CONFIG.get("preferred_lora_weights", [1, 2, 1])
    total_loras = random.choices(counts, weights=weights)[0]

    # ✅ Always include one detailer
    detailers = underused.get("detailer", [])
    if detailers:
        chosen_path = random.choice(detailers)
        filename = os.path.basename(chosen_path)
        base_weight = DEFAULT_WEIGHTS.get("detailer", 0.9)
        chosen_weight = round(random.uniform(base_weight - FUZZ, base_weight + FUZZ * 2), 2)
        selected.append({
            "name": filename,
            "weight": chosen_weight,
            "activation": filename
        })
        debug_log.append({
            "name": filename,
            "weight": chosen_weight,
            "category": "detailer",
            "reasons": ["Discovery mode - always include a detailer"]
        })
        remaining = total_loras - 1
    else:
        remaining = total_loras

    # 🔁 Continue pulling from other categories
    available_categories = [cat for cat in underused if cat.lower() != "detailer"]

    while remaining > 0 and available_categories:
        category = random.choice(available_categories)
        pool = underused.get(category, [])
        if not pool:
            available_categories.remove(category)
            continue

        candidate_path = random.choice(pool)
        filename = os.path.basename(candidate_path)

        base_weight = DEFAULT_WEIGHTS.get(category, 0.6)
        usage_count = category_usage_count[category]
        if usage_count > 0:
            base_weight = max(base_weight - (0.1 * usage_count), 0.3)

        weight = round(random.uniform(base_weight - FUZZ, base_weight + FUZZ), 2)

        selected.append({
            "name": filename,
            "weight": weight,
            "activation": filename
        })
        debug_log.append({
            "name": filename,
            "weight": weight,
            "category": category,
            "reasons": ["Discovery mode - underused LORA"]
        })

        category_usage_count[category] += 1
        remaining -= 1

    return selected, debug_log

