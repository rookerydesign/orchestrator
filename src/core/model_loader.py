import os
import json

# --- Normalization & Alias Helpers ---

MODEL_ALIASES = {
    "flux dev": "flux",
    "flux1devhypernf4": "flux",
    "flux1DevHyperNF4Flux1DevBNB_flux1DevHyperNF4": "flux",
    "flux_dev": "flux",
    "sdxl 1.0": "sdxl",
    "sdxl": "sdxl",
    "Pony": "pony",
    "pony": "pony"
}

def normalize_model_name(name):
    if not name:
        return ""
    
    name = name.lower().strip()

    if "flux" in name:
        return "flux"
    if "sdxl" in name:
        return "sdxl"
    if "pony" in name:
        return "pony"
    
    return name


# --- Model Loader ---

def get_available_models(model_dir):
    models = []

    for root, _, files in os.walk(model_dir):
        for file in files:
            if file.endswith((".safetensors", ".ckpt")):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, model_dir)
                base_name = os.path.splitext(rel_path)[0].replace("\\", "/")

                metadata = {}
                for ext in [".json", ".info"]:
                    meta_path = os.path.join(root, os.path.splitext(file)[0] + ext)
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path, "r", encoding="utf-8") as f:
                                metadata = json.load(f)
                        except:
                            pass

                models.append({
                    "name": base_name,
                    "file": full_path,
                    "metadata": metadata
                })

    return models

# --- LORA Loader ---

def load_loras(lora_dir):
    loras = []

    for root, _, files in os.walk(lora_dir):
        for file in files:
            if file.endswith(".safetensors"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, lora_dir)
                base_name = os.path.splitext(rel_path)[0].replace("\\", "/")

                lora_entry = {
                    "name": base_name,
                    "file": full_path,
                    "activation": None,
                    "weight": 1.0,
                    "base_model": "",
                    "tags": [],
                    "metadata": {}
                }

                for ext in [".json", ".info"]:
                    meta_path = os.path.join(root, os.path.splitext(file)[0] + ext)
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path, "r", encoding="utf-8") as f:
                                meta_data = json.load(f)

                            lora_entry["metadata"].update(meta_data)

                            possible_keys = ["activation text", "activation_text", "trigger", "trained words"]
                            for key in possible_keys:
                                if key in meta_data:
                                    value = meta_data[key]
                                    if isinstance(value, list) and value:
                                        lora_entry["activation"] = value[0]  # Use first alias
                                    elif isinstance(value, str):
                                        lora_entry["activation"] = value.strip()
                                    break
                            if "preferred weight" in meta_data:
                                lora_entry["weight"] = meta_data["preferred weight"]

                            # Try to extract baseModel from all known locations
                            model_block = meta_data.get("model", {})
                            base_model_candidates = [
                                model_block.get("baseModel"),
                                model_block.get("baseModelType"),
                                meta_data.get("baseModel"),
                                meta_data.get("baseModelType"),
                                meta_data.get("sd version")
                            ]

                            # Pick the first normalized, non-empty value
                            for candidate in base_model_candidates:
                                if candidate and str(candidate).lower() != "unknown":
                                    norm = normalize_model_name(candidate)
                                    if norm:
                                        lora_entry["base_model"] = norm
                                        break

                            # Final fallback if nothing usable was found
                            if not lora_entry["base_model"]:
                                lora_entry["base_model"] = normalize_model_name(base_name)
                      

                            if "tags" in meta_data:
                                lora_entry["tags"] = meta_data["tags"]

                        except Exception as e:
                            print(f"Error parsing metadata from {meta_path}: {e}")

                loras.append(lora_entry)

    return loras
