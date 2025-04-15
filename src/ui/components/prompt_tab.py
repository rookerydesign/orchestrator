# Updated Prompt Tab with integrated LORA Selection
import gradio as gr
from src.core.prompt_generator import generate_prompts
from src.core.llm_interface import enhance_prompt_with_llm
from src.core.favorite_combo_selector import pick_random_favorite_combo, load_favorite_combos
from src.core.lora_selector import categorize_loras, select_loras_for_prompt, extract_keywords
from src.core.model_loader import normalize_model_name


DEFAULT_GENRE = "fantasy"
BASE_MODEL = normalize_model_name("Flux1DevHyperNF4")

# State to pass LORAs forward if needed
def render_prompt_tab(shared_prompt_state=None, selected_model_state=None, available_loras=None):
    # print(f"[DEBUG] LORAs received in render_prompt_tab: {len(available_loras) if available_loras else 'None'}")
    # print(f"[DEBUG] First LORA structure: {available_loras[0] if available_loras and len(available_loras) > 0 else 'None'}")

    def generate_single_prompt(template, genre, use_llm, lora_mode):
        model_name = normalize_model_name(selected_model_state.value if selected_model_state else "flux")
        print(f"[DEBUG] Using normalized base_model: {model_name}")

        all_loras = available_loras or []
        print(f"[DEBUG] LORA count before categorization: {len(all_loras)}")
        print(f"[DEBUG] Sample LORA data: {all_loras[0] if all_loras else 'None'}")
        
        categorized = categorize_loras(all_loras)
        print(f"[DEBUG] Categories found: {list(categorized.keys())}")
        for cat_key, loras in categorized.items():
            print(f"[DEBUG] Category {cat_key}: {len(loras)} LORAs")
        base_prompt = generate_prompts(template, genre=genre, batch_size=1)[0]
        final_prompt = enhance_prompt_with_llm(base_prompt, genre) if use_llm else base_prompt

        if shared_prompt_state is not None:
            shared_prompt_state.value = final_prompt

        selected_loras = []
        lora_debug_log = []
        

        if lora_mode == "Favorites":
            combos = load_favorite_combos()
            picked = pick_random_favorite_combo(
                combos,
                genre=genre,
                prompt_keywords=extract_keywords(final_prompt)
            )
            selected_loras = picked["loras"]
            lora_debug_log = [
                {
                    "name": l["name"],
                    "weight": l["weight"],
                    "category": "from_favorites",
                    "reasons": ["Picked from favorites DB"]
                } for l in selected_loras
            ]

        elif lora_mode == "Keyword":
            categorized = categorize_loras(all_loras)
            selected_loras, lora_debug_log = select_loras_for_prompt(
                categorized_loras=categorized,
                base_model=model_name,
                resolved_prompt=final_prompt,
                use_smart_matching=True,
                genre=genre
            )
            print(f"[DEBUG] Selected {len(selected_loras)} LORAs using smart matching")

        elif lora_mode == "Prompt LORAs":
            lora_debug_log = [{
                "name": "Prompt-defined LORAs",
                "weight": "-",
                "category": "manual",
                "reasons": ["Embedded via prompt"]
            }]

        elif lora_mode == "🧪 Discovery":
            from src.core.discovery_selector import select_discovery_loras
            from src.utils.lora_audit import get_unused_loras_grouped_by_model_and_category

            try:
                categorized_unused = get_unused_loras_grouped_by_model_and_category()
                selected_loras, lora_debug_log = select_discovery_loras(BASE_MODEL, categorized_unused)
            except Exception as e:
                print(f"[ERROR] Discovery mode failed: {e}")
                selected_loras = []
                lora_debug_log = [{
                    "name": "Discovery error",
                    "weight": "-",
                    "category": "error",
                    "reasons": [str(e)]
                }]

        # Format output
        prompt_preview = f"{final_prompt}\n\n---\nLORAs selected:\n" + "\n".join([
            f"• {l['name']} @ {l['weight']}" + (f" ({l['category']})" if 'category' in l else '')
            for l in lora_debug_log
        ])
        return prompt_preview

    template = gr.Textbox(
        label="Prompt Template",
        value="A ^^classes^^ wearing ^^garb^^ in a ^^setting^^",
        lines=3
    )
    genre = gr.Dropdown(
        choices=["fantasy", "sci-fi", "realism", "horror", "characters", "nsfw"],
        value="fantasy",
        label="Genre"
    )
    use_llm = gr.Checkbox(label="Enhance Prompt with LLM", value=False)
    lora_mode = gr.Radio(
        choices=["Favorites", "Keyword", "Discovery", "Prompt LORAs"],
        value="Keyword",
        label="LORA Selection Mode"
    )

    output_box = gr.Textbox(label="Final Prompt + Selected LORAs", lines=10)
    reroll_btn = gr.Button("Reroll Prompt")

    reroll_btn.click(
        fn=generate_single_prompt,
        inputs=[template, genre, use_llm, lora_mode],
        outputs=[output_box]
    )
    return [template, genre, output_box]
