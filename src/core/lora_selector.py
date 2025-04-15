# LORA Selector with Cleaned Logic and Debugs
import os
import random
import re
from collections import defaultdict
import json
import time
import yaml
from src.utils.config_loader import load_config
from pathlib import Path

cfg = load_config()
TAGS_PATH = Path(cfg["paths"]["lora_tags"])
CONFIG_PATH = Path(cfg["paths"]["lora_selector_config"])

with TAGS_PATH.open("r", encoding="utf-8") as f:
    TAGS = json.load(f)

with CONFIG_PATH.open("r", encoding="utf-8") as f:
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

TAG_STOP_WORDS = set([
        "sfw", "perform", "tail", "style", "drawing", "character", "pose", 
        "art", "design", "form", "sketch", "painting", "digital", "details"
    ])

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
        "theme", "mood", "feeling", "emotion", "action", "movement", "dynamic", "static", "behind",
        "hands", "shoulder", "covered", "who", "hip", "waist", "thigh", "knee", "calf", "ankle", "footwear",
        "sleeve", "collar", "neck", "earrings", "necklace", "bracelet", "ring", "watch", "belt",
        "pocket", "button", "zipper", "pattern", "piece", "should", "scheme", "creating", "create", "made",
        "features", "yet", "unique", "captivating", "stunning", "beautiful", "gorgeous", "breathtaking",
        "amazing", "fantastic", "incredible", "wonderful", "spectacular", "extraordinary", "exceptional",
        "remarkable", "outstanding", "impressive", "striking", "eye-catching", "visually", "appealing",
        "aesthetic", "artistic", "stylish", "trendy", "charming", "adding", "side", "front", "back", "top",
        "-", "quality", "high", "low", "medium", "soft", "hard", "bright", "dark", "light", "dim",
        "appearance", "solid", "torso", "dim", "yet", "while", "air", "each", "environment",  "surrounding",
        "reminiscent", "accents", "piercing", "adorned", "long", "resting", "air", "against", "sky", 
        "vibrant", "filled", "forward", "tones", "contrast", "vibrant", "viewer", "sharp", "tree", "when", 
        "weight", "before", "after", "during", "while", "between", "along", "across", "through", "past", "towards",
        " short", "slightly", "tall", "lashes", "even", "both", "seem", "if", "not", "just", "like", "as", "such",
        "more", "less", "than", "very", "much", "many", "few", "several", "each", "every", "any", "no",
        "none", "some", "all", "most", "both", "either", "neither", "one", "two", "three", "four",
        "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
        "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "hundred", "thousand",
        "used", "use", "using", "utilize", "utilizing", "utilized", "utilizes", "utilize", "utilizing",
        "own", "stand"

    }
   

    text = text.lower()
    words = set(text.replace(",", " ").replace(".", " ").split())
    keywords = {word for word in words if word and word not in stop_words}
    return keywords

def score_lora_relevance(lora, keywords):
    name = lora["name"].replace("/", "\\")  # tag keys use backslashes
    tag_entry = TAGS.get(name)

    if not tag_entry:
        return 0, []

    all_tags = []
    for group in ("genre", "style", "subject", "tone"):
        all_tags.extend(tag_entry.get(group, []))

    tag_string = " ".join(str(tag).lower() for tag in all_tags)
    matched = [kw for kw in keywords if kw in tag_string and kw not in TAG_STOP_WORDS]


    return len(matched), matched


def select_loras_for_prompt(categorized_loras, base_model, resolved_prompt=None, use_smart_matching=False, genre=None):
    print(f"[DEBUG] select_loras_for_prompt started — LORAs: {sum(len(v) for v in categorized_loras.values())}, Prompt: {resolved_prompt[:80]}...")
    print(f"[DEBUG] Smart matching: {use_smart_matching}, Genre: {genre}")

    default_strengths = CONFIG.get("default_lora_weights", {})
    fuzz = CONFIG.get("weight_fuzz_range", 0.05)
    count_choices = CONFIG.get("preferred_lora_count", [2, 3, 4])
    count_weights = CONFIG.get("preferred_lora_weights", [1, 1, 1])

    if not count_choices or not count_weights or len(count_choices) != len(count_weights):
        print("[ERROR] Invalid preferred_lora_count or preferred_lora_weights in config")
        return [], [{
            "name": "[Config Error]",
            "weight": "-",
            "category": "config",
            "reasons": ["Missing or mismatched count/weight config"]
        }]

    print(f"[DEBUG] Raw CONFIG keys: {list(CONFIG.keys())}")
    print(f"[DEBUG] Count choices: {count_choices} (len={len(count_choices)})")
    print(f"[DEBUG] Count weights: {count_weights} (len={len(count_weights)})")

    try:
        total_loras = random.choices(count_choices, weights=count_weights)[0]
        print(f"[DEBUG] Will select {total_loras} LORAs total")
    except Exception as e:
        print(f"[ERROR] Failed during random.choices: {e}")
        total_loras = 3

    prompt_keywords = extract_keywords(resolved_prompt) if use_smart_matching and resolved_prompt else set()
    selection_log = []
    category_usage_count = defaultdict(int)
    selected = []

    # Always include one detailer
    detailers = categorized_loras.get((base_model, "detailer"), [])
    if detailers:
        chosen = random.choice(detailers)
        base_weight = default_strengths.get("detailer", 0.9)
        chosen["weight"] = round(random.uniform(base_weight - fuzz, base_weight + fuzz), 2)
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

    # Build weighted category list
    category_biases = CONFIG.get("weights", {})
    weighted_categories = []
    for cat, wt in category_biases.items():
        if cat == "detailer":
            continue
        if genre != "realism" and cat in ("artist", "general"):
            wt *= 1.4
        elif genre == "realism" and cat in ("characters", "fx"):
            wt *= 1.3
        weighted_categories.append((cat, wt))

    recent_character_used = False
    attempts = 0
    max_attempts = 100

    while remaining > 0 and attempts < max_attempts:
        attempts += 1
        print(f"[DEBUG] Remaining: {remaining} — picking next category (attempt {attempts})")
        category = weighted_choice(weighted_categories)
        print(f"[DEBUG] Picked category: {category}")

        if category == "characters" and recent_character_used:
            print("[DEBUG] Skipping characters due to recent use")
            continue

        lora_pool = categorized_loras.get((base_model, category), [])
        if not lora_pool:
            print(f"[DEBUG] No LORAs found for category: {category}")
            continue

        reasons = []
        candidate = None

        if prompt_keywords and use_smart_matching:
            print(f"[DEBUG] Matching against {len(lora_pool)} LORAs in category: {category}")
            start_time = time.time()
            scored = [(l, *score_lora_relevance(l, prompt_keywords)) for l in lora_pool]
            print(f"[DEBUG] Scoring took: {time.time() - start_time:.2f}s")
            scored.sort(key=lambda x: -x[1])
            top_scored = [l for l, score, _ in scored if score > 0]

            if top_scored:
                candidate = random.choice(top_scored[:5])
                _, _, matched_keywords = next((x for x in scored if x[0] == candidate), (None, 0, []))
                reasons.append(f"Matched tags: {', '.join(matched_keywords)}")

        if not candidate:
            candidate = random.choice(lora_pool)
            reasons.append("Random fallback (no match or smart matching disabled)")

        if candidate in selected:
            print("[DEBUG] Duplicate candidate — retrying")
            continue

        base_weight = default_strengths.get(category, 0.6)
        usage_count = category_usage_count[category]
        if usage_count > 0:
            base_weight = max(base_weight - (0.1 * usage_count), 0.3)

        weight = round(random.uniform(base_weight - fuzz, base_weight + fuzz), 2)
        candidate["weight"] = weight
        selected.append(candidate)
        category_usage_count[category] += 1
        remaining -= 1

        selection_log.append({
            "name": candidate["name"],
            "weight": weight,
            "category": category,
            "reasons": reasons
        })

        if category == "characters":
            recent_character_used = True

    if attempts >= max_attempts:
        print("[WARNING] Exited LORA selection loop after max attempts")

    return selected, selection_log
