from lora_audit import get_unused_loras_grouped_by_model_and_category

# This function now uses fuzzy matching (basename + alias vs activations/prompts)
unused_loras = get_unused_loras_grouped_by_model_and_category()

# You can change this if you want to focus on a different model family
model_focus = "Flux"

if model_focus in unused_loras:
    print(f"\n🧩 UNUSED LORAs in '{model_focus}'\n")
    total = 0
    for category, loras in unused_loras[model_focus].items():
        if not loras:
            continue
        print(f"📁 {category} — {len(loras)} unused")
        for lora in sorted(loras):
            print(f"   - {lora}")
        total += len(loras)
        print("")
    print(f"✅ Total unused in '{model_focus}': {total}")
else:
    print(f"❌ No unused LORAs found in model folder '{model_focus}'")
