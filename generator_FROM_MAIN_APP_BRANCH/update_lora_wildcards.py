# This script generates wildcard files for Lora models based on their metadata.
# It reads the Lora tags from a JSON file, builds an index of Lora models,
# and writes the wildcards to text files in a specified directory.

import os
import json
import yaml

# --- CONFIG LOADING ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

LORA_TAGS_PATH = os.path.join(os.path.dirname(__file__), "lora_tags.json")
LORA_DIR = config["paths"]["lora_folder"]
WILDCARD_BASE = os.path.abspath(os.path.join(
    os.path.dirname(CONFIG_PATH),
    config["paths"]["wildcard_folder"].strip("/\\"),
    "loras"
))


DEFAULT_WEIGHT = 0.7  # fallback if no weight set


def load_lora_tags():
    if not os.path.exists(LORA_TAGS_PATH):
        return {}
    with open(LORA_TAGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_lora_tags(tags):
    with open(LORA_TAGS_PATH, "w", encoding="utf-8") as f:
        json.dump(tags, f, indent=2)

def normalize_tag_keys(tags):
    """Move any flat entries like preferred_weight into their correct nested keys."""
    normalized = {}
    for key, value in tags.items():
        if not isinstance(value, dict):
            continue  # skip malformed

        new_key = key.replace("/", "\\\\")  # for normalize_tag_keys()

        # Merge if another tag exists with a similar basename
        if new_key not in normalized:
            normalized[new_key] = value
        else:
            normalized[new_key].update(value)
    return normalized

def build_lora_index():
    index = {}
    for root, _, files in os.walk(LORA_DIR):
        for f in files:
            if not f.endswith(".safetensors"):
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, LORA_DIR)
            parts = rel_path.split(os.sep)
            if len(parts) < 3:
                continue  # Skip anything not model/category/lora
            base_model = parts[0]
            category = parts[1]
            key = rel_path.replace("/", "\\\\").replace(".safetensors", "")  # for build_lora_index()
            index[key] = {
                "file": full_path,
                "name": os.path.splitext(f)[0],
                "category": category,
                "base_model": base_model,
            }
    return index


def update_tags_with_defaults(lora_index, tags):
    changed = False
    for rel_path, meta in lora_index.items():
        if rel_path not in tags:
            tags[rel_path] = {
                "activation": meta["name"],
                "preferred_weight": DEFAULT_WEIGHT,
            }
            changed = True
        else:
            if "preferred_weight" not in tags[rel_path]:
                tags[rel_path]["preferred_weight"] = DEFAULT_WEIGHT
                changed = True
    return changed


def write_wildcards(lora_index, tags):
    groups = {}
    for rel_path, meta in lora_index.items():
        model = meta["base_model"].lower()
        category = meta["category"].lower().replace(" ", "_")
        activation = tags[rel_path]["activation"]
        weight = tags[rel_path].get("preferred_weight", DEFAULT_WEIGHT)
        entry = activation  # Store just the name, weight will be added dynamically later
        key = (model, category)
        groups.setdefault(key, []).append(entry)

    os.makedirs(WILDCARD_BASE, exist_ok=True)
    total_added, total_removed = 0, 0

    for (model, category), entries in groups.items():
        out_folder = os.path.join(WILDCARD_BASE, model)
        os.makedirs(out_folder, exist_ok=True)
        out_path = os.path.join(out_folder, f"{category}.txt")

        existing = []
        if os.path.exists(out_path):
            with open(out_path, "r", encoding="utf-8") as f:
                existing = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        updated = [e for e in existing if e in entries]  # keep known
        added = [e for e in entries if e not in updated]  # add new
        removed = len(existing) - len(updated)
        final = updated + added

        with open(out_path, "w", encoding="utf-8") as f:
            for line in final:
                f.write(line + "\n")

        total_added += len(added)
        total_removed += removed

    return total_added, total_removed


def main():
    tags = load_lora_tags()
    tags = normalize_tag_keys(tags)
    lora_index = build_lora_index()

    if update_tags_with_defaults(lora_index, tags):
        print("🔄 Extended lora_tags.json with missing weights.")
        save_lora_tags(tags)

    added, removed = write_wildcards(lora_index, tags)
    print(f"✨ Wildcards updated. {added} added, {removed} removed.")
    return added, removed


if __name__ == "__main__":
    main()
