
import json
import os

def normalize_key(text):
    return text.lower().replace(" ", "").replace("-", "").replace("_", "")

def load_local_lora_registry(json_path):
    """
    Loads lora_tags.json and creates a normalized index
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    registry = {}
    for path, meta in data.items():
        activation = meta.get("activation", "")
        if not activation:
            continue
        norm_key = normalize_key(activation)
        registry[norm_key] = {
            "activation": activation,
            "path": path,
            "weight": meta.get("preferred_weight", 0.7),
            "full_meta": meta
        }

    return registry

def match_lora_by_prompt_tag(tag_name, registry):
    """
    Try to find a local LORA by activation name from a civitai tag
    """
    norm_tag = normalize_key(tag_name)
    if norm_tag in registry:
        return registry[norm_tag]
    return None
