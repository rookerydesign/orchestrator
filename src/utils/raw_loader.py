from src.core.model_loader import get_available_models, load_loras
#

def load_models_and_loras(model_dir, lora_dir):
    raw_models = get_available_models(model_dir)
    raw_loras = load_loras(lora_dir)

    unique_models = {}
    for m in raw_models:
        name = m["name"]
        if name not in unique_models or m.get("metadata"):
            unique_models[name] = m

    models = list(unique_models.values())
    model_names = [m["name"] for m in models] or ["No models found"]

    return models, model_names, raw_loras
