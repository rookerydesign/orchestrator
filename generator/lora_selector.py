import os
import random
import re
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


def extract_keywords(text):
    stop_words = {
        "the", "a", "an", "in", "on", "at", "with", "by", "for", "of", "to", "is", "are",
        "and", "or", "be", "this", "that", "it", "as", "from", "was", "were", "has", "have",
        "but", "not", "their", "them", "he", "she", "they", "we", "you", "your", "i", "my",
        "his", "her", "its", "our", "us", "also", "which", "one", "other", "some", "any", 
        "all", "image", "prompt", "leg", "body", "face", "eyes", "hair", "skin", "clothes",
        "scene", "background", "appears", "color", "style", "art", "character", "can", "like",
        "figure", "green", "blue", "red", "yellow", "black", "white", "brown", "pink", "purple",
        "arm", "hand", "foot", "head", "mouth", "nose", "ear", "smile", "expression", "pose",
        "line", "shape", "form", "size", "proportion", "detail", "texture", "into", "out",
        "over", "under", "between", "above", "below", "near", "far", "close", "around", "about",
        "theme", "mood", "feeling", "emotion", "action", "movement", "dynamic", "static", "behind"
    }

    text = text.lower()
    words = set(text.replace(",", " ").replace(".", " ").split())
    keywords = {word for word in words if word and word not in stop_words}
    return keywords



def score_lora_relevance(lora, keywords):
    activation = str(lora.get("activation") or "")
    description = str(lora.get("metadata", {}).get("description") or "")
    tags = " ".join(str(t) for t in lora.get("metadata", {}).get("tags", []) if t)
    prompts = " ".join(str(p) for p in lora.get("metadata", {}).get("samplePrompts", []) if p)
    combined = f"{activation} {description} {tags} {prompts}".lower()
    return sum(1 for kw in keywords if kw in combined)


def select_loras_for_prompt(categorized_loras, base_model, resolved_prompt=None, use_smart_matching=False):
    DEFAULT_WEIGHTS = {
        "Detailers": 0.9,
        "Artist Styles": 0.8,
        "General Styles": 0.7,
        "Textures & Looks": 0.5,
        "Characters": 0.5,
        "People styles": 0.7
    }

    prompt_keywords = extract_keywords(resolved_prompt) if use_smart_matching and resolved_prompt else set()
    selection_log = []

    # Decide total number of LORAs
    counts = CONFIG["preferred_lora_count"]
    weights = CONFIG["preferred_lora_weights"]
    total_loras = random.choices(counts, weights=weights)[0]

    selected = []

    # ✅ Always include one detailer
    detailers = categorized_loras.get((base_model, "detailer"), [])
    if detailers:
        chosen = random.choice(detailers)
        base_weight = DEFAULT_WEIGHTS.get("Detailers", 0.9)
        chosen["weight"] = round(random.uniform(base_weight - 0.05, base_weight + 0.1), 2)
        selected.append(chosen)

        selection_log.append({
            "name": chosen["name"],
            "weight": chosen["weight"],
            "category": "Detailers",
            "reasons": ["Always included"]
        })

        remaining = total_loras - 1
    else:
        remaining = total_loras

    if remaining <= 0:
        return selected, selection_log

    weighted_categories = [(cat, wt) for cat, wt in CONFIG["weights"].items() if cat.lower() != "detailer"]
    recent_character_used = False

    while remaining > 0:
        category = weighted_choice(weighted_categories)

        if category.lower() == "characters" and recent_character_used:
            continue

        lora_pool = categorized_loras.get((base_model, category), [])
        if not lora_pool:
            continue

        reasons = []
        candidate = None

        if prompt_keywords and use_smart_matching:
            scored = [(l, score_lora_relevance(l, prompt_keywords)) for l in lora_pool]
            scored.sort(key=lambda x: -x[1])
            top_scored = [l for l, score in scored if score > 0]

            if top_scored:
                candidate = random.choice(top_scored[:5])
                combined_text = " ".join([
                    str(candidate.get("activation") or ""),
                    str(candidate.get("metadata", {}).get("description") or ""),
                    " ".join(str(t) for t in candidate.get("metadata", {}).get("tags", [])),
                    " ".join(str(p) for p in candidate.get("metadata", {}).get("samplePrompts", []))
                ]).lower()
                matched_keywords = [kw for kw in prompt_keywords if kw in combined_text]
                reasons.append(f"Matched keywords: {', '.join(matched_keywords)}")

        if not candidate:
            candidate = random.choice(lora_pool)
            reasons.append("Random fallback (no match or smart matching disabled)")

        if candidate in selected:
            continue

        base_weight = DEFAULT_WEIGHTS.get(category, 0.6)
        weight = round(random.uniform(base_weight - 0.05, base_weight + 0.1), 2)
        candidate["weight"] = weight
        selected.append(candidate)

        selection_log.append({
            "name": candidate["name"],
            "weight": weight,
            "category": category,
            "reasons": reasons
        })

        remaining -= 1
        if category.lower() == "characters":
            recent_character_used = True

    return selected, selection_log
