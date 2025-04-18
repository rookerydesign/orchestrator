# Updated Prompt Tab with integrated LORA Selection
import gradio as gr
import requests
from PIL import Image
from io import BytesIO
from src.core.prompt_generator import generate_prompts
from src.core.llm_interface import enhance_prompt_with_llm
from src.core.favorite_combo_selector import pick_random_favorite_combo, load_favorite_combos
from src.core.lora_selector import categorize_loras, select_loras_for_prompt, extract_keywords
from src.core.model_loader import normalize_model_name
from src.core.civitai_trending_selector import get_trending_combo_with_preview


DEFAULT_GENRE = "fantasy"
BASE_MODEL = normalize_model_name("Flux1DevHyperNF4")

# State to pass LORAs forward if needed
def render_prompt_tab(shared_prompt_state=None, selected_model_state=None, available_loras=None):
    # print(f"[DEBUG] LORAs received in render_prompt_tab: {len(available_loras) if available_loras else 'None'}")
    # print(f"[DEBUG] First LORA structure: {available_loras[0] if available_loras and len(available_loras) > 0 else 'None'}")

    def generate_single_prompt(template, genre, use_llm, lora_mode, filter_nsfw=True, civitai_limit="50"):
        model_name = normalize_model_name(selected_model_state.value if selected_model_state else "flux")
        # print(f"[DEBUG] Using normalized base_model: {model_name}")

        # Handle tuple case (from load_models_and_loras)
        if isinstance(available_loras, tuple) and len(available_loras) == 3:
            model_name, _, all_loras = available_loras
        else:
            all_loras = available_loras or []
        
        # print(f"[DEBUG] LORA count before categorization: {len(all_loras)}")
        
        # Moved categorized definition outside the loop
        categorized = categorize_loras(all_loras)
        
        # print(f"[DEBUG] Categories found: {list(categorized.keys())}")
        # for cat_key, loras in categorized.items():
        #     print(f"[DEBUG] Category {cat_key}: {len(loras)} LORAs")
        
        base_prompt = generate_prompts(template, genre=genre, batch_size=1)[0]
        final_prompt = enhance_prompt_with_llm(base_prompt, genre) if use_llm else base_prompt
        # print(f"[DEBUG] Generated prompt: {final_prompt[:50]}...")

        if shared_prompt_state is not None:
            shared_prompt_state.value = final_prompt

        selected_loras = []
        lora_debug_log = []
        # print(f"[DEBUG] Selecting LORAs with mode: {lora_mode}")

        if lora_mode == "✨ Favorites":
            # print("[DEBUG] Entering Favorites mode")
            combos = load_favorite_combos()
            # print(f"[DEBUG] Loaded {len(combos)} favorite combos")
            picked = pick_random_favorite_combo(
                combos,
                genre=genre,
                prompt_keywords=extract_keywords(final_prompt)
            )
            # print(f"[DEBUG] Picked combo: {picked}")
            selected_loras = picked["loras"]
            lora_debug_log = [
                {
                    "name": l["name"],
                    "weight": l["weight"],
                    "category": "from_favorites",
                    "reasons": ["Picked from favorites DB"]
                } for l in selected_loras
            ]

        elif lora_mode == "✍️ Keyword":
            print("[DEBUG] Entering Keyword mode")
            # categorized = categorize_loras(all_loras)
            selected_loras, lora_debug_log = select_loras_for_prompt(
                categorized_loras=categorized,
                base_model=model_name,
                resolved_prompt=final_prompt,
                use_smart_matching=True,
                genre=genre
            )
            print(f"[DEBUG] Selected {len(selected_loras)} LORAs using smart matching")

        elif lora_mode == "📜 Prompt LORAs":
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
                
        elif lora_mode == "🔥 Trending":
            try:
                # Get trending combo from CivitAI
                # Convert limit to integer
                limit = int(civitai_limit)
                
                # Get the currently selected model
                model_name = normalize_model_name(selected_model_state.value if selected_model_state else "flux")
                
                result = get_trending_combo_with_preview(
                    genre=genre,
                    nsfw=not filter_nsfw,
                    limit=limit,
                    model_name=model_name
                )
                selected_loras = result["selected_loras"]
                lora_debug_log = result["debug_log"]
                trending_web_url = result.get("trending_web_url", "")
                
                # If no LORAs were found, add a message with the web URL
                if not selected_loras and trending_web_url:
                    lora_debug_log = [{
                        "name": "No trending images with LORAs found",
                        "weight": "-",
                        "category": "info",
                        "reasons": [f"Check trending images at: {trending_web_url}"]
                    }]
                
                # If we have a preview image URL, display it
                preview_url = result.get("preview_url")
                if preview_url:
                    try:
                        response = requests.get(preview_url)
                        if response.status_code == 200:
                            img = Image.open(BytesIO(response.content))
                            preview_image.update(value=img, visible=True)
                    except Exception as e:
                        print(f"[ERROR] Failed to load preview image: {e}")
                
                # If we have a prompt from CivitAI, use it instead of the generated one
                civitai_prompt = result.get("prompt")
                if civitai_prompt:
                    final_prompt = civitai_prompt
                    if shared_prompt_state is not None:
                        shared_prompt_state.value = final_prompt
                
            except Exception as e:
                print(f"[ERROR] Trending mode failed: {e}")
                selected_loras = []
                lora_debug_log = [{
                    "name": "Trending error",
                    "weight": "-",
                    "category": "error",
                    "reasons": [str(e)]
                }]

        # Format output
        prompt_preview = f"{final_prompt}\n\n---\nLORAs selected:\n" + "\n".join([
            f"• {l['name']} @ {l['weight']}" + (f" ({l['category']})" if 'category' in l else '')
            for l in lora_debug_log
        ])
        
        # Add generation parameters if available (for trending mode)
        if lora_mode == "🔥 Trending" and "result" in locals() and "generation_params" in result:
            gen_params = result.get("generation_params", {})
            if gen_params:
                prompt_preview += "\n\n---\nGeneration Parameters:\n"
                for key, value in gen_params.items():
                    prompt_preview += f"• {key}: {value}\n"
        
        # Set preview image visibility based on mode
        preview_visible = False
        if lora_mode == "🔥 Trending" and "result" in locals():
            preview_visible = result.get("preview_url") is not None
        
        return prompt_preview, gr.update(visible=preview_visible)

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
    with gr.Row():
        use_llm = gr.Checkbox(label="Enhance Prompt with LLM", value=False)
        filter_nsfw = gr.Checkbox(label="Filter NSFW Content", value=True)
    
    with gr.Row(visible=False) as trending_options:
        civitai_limit = gr.Dropdown(
            choices=["10", "25", "50", "75", "100"],
            value="50",
            label="CivitAI Results Limit"
        )
    lora_mode = gr.Radio(
        choices=["✨ Favorites", "✍️ Keyword", "🧪 Discovery", "🔥 Trending", "📜 Prompt LORAs"],
        value="✍️ Keyword",
        label="LORA Selection Mode"
    )

    output_box = gr.Textbox(label="Final Prompt + Selected LORAs", lines=10)
    preview_image = gr.Image(label="Preview Image", visible=False)
    reroll_btn = gr.Button("Reroll Prompt")

    # Show/hide trending options based on LORA mode
    def update_trending_options_visibility(lora_mode):
        return gr.update(visible=lora_mode == "🔥 Trending")
    
    lora_mode.change(
        fn=update_trending_options_visibility,
        inputs=[lora_mode],
        outputs=[trending_options]
    )
    
    reroll_btn.click(
        fn=generate_single_prompt,
        inputs=[template, genre, use_llm, lora_mode, filter_nsfw, civitai_limit],
        outputs=[output_box, preview_image]
    )

    # Regenerate only LORAs when LORA mode is changed
    def regenerate_loras_only(template, genre, use_llm, lora_mode, filter_nsfw=True, civitai_limit="50"):
        # Reuse previously generated prompt
        final_prompt = shared_prompt_state.value or ""
        model_name = normalize_model_name(selected_model_state.value if selected_model_state else "flux")

        # Unpack LORAs if needed
        all_loras = available_loras or []
        categorized = categorize_loras(all_loras)

        selected_loras = []
        lora_debug_log = []

        if lora_mode == "✨ Favorites":
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

        elif lora_mode == "✍️ Keyword":
            selected_loras, lora_debug_log = select_loras_for_prompt(
                categorized_loras=categorized,
                base_model=model_name,
                resolved_prompt=final_prompt,
                use_smart_matching=True,
                genre=genre
            )

        elif lora_mode == "📜 Prompt LORAs":
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
                
        elif lora_mode == "🔥 Trending":
            try:
                # Get trending combo from CivitAI
                # Convert limit to integer
                limit = int(civitai_limit)
                
                # Get the currently selected model
                model_name = normalize_model_name(selected_model_state.value if selected_model_state else "flux")
                
                result = get_trending_combo_with_preview(
                    genre=genre,
                    nsfw=not filter_nsfw,
                    limit=limit,
                    model_name=model_name
                )
                selected_loras = result["selected_loras"]
                lora_debug_log = result["debug_log"]
                trending_web_url = result.get("trending_web_url", "")
                
                # If no LORAs were found, add a message with the web URL
                if not selected_loras and trending_web_url:
                    lora_debug_log = [{
                        "name": "No trending images with LORAs found",
                        "weight": "-",
                        "category": "info",
                        "reasons": [f"Check trending images at: {trending_web_url}"]
                    }]
                
                # If we have a preview image URL, display it
                preview_url = result.get("preview_url")
                if preview_url:
                    try:
                        response = requests.get(preview_url)
                        if response.status_code == 200:
                            img = Image.open(BytesIO(response.content))
                            preview_image.update(value=img, visible=True)
                    except Exception as e:
                        print(f"[ERROR] Failed to load preview image: {e}")
                
                # If we have a prompt from CivitAI, use it instead of the generated one
                civitai_prompt = result.get("prompt")
                if civitai_prompt:
                    final_prompt = civitai_prompt
                    if shared_prompt_state is not None:
                        shared_prompt_state.value = final_prompt
                
            except Exception as e:
                print(f"[ERROR] Trending mode failed: {e}")
                selected_loras = []
                lora_debug_log = [{
                    "name": "Trending error",
                    "weight": "-",
                    "category": "error",
                    "reasons": [str(e)]
                }]

        # Format combined output
        prompt_preview = f"{final_prompt}\n\n---\nLORAs selected:\n" + "\n".join([
            f"• {l['name']} @ {l['weight']}" + (f" ({l['category']})" if 'category' in l else '')
            for l in lora_debug_log
        ])
        
        # Add generation parameters if available (for trending mode)
        if lora_mode == "🔥 Trending" and "result" in locals() and "generation_params" in result:
            gen_params = result.get("generation_params", {})
            if gen_params:
                prompt_preview += "\n\n---\nGeneration Parameters:\n"
                for key, value in gen_params.items():
                    prompt_preview += f"• {key}: {value}\n"
        
        # Set preview image visibility based on mode
        preview_visible = False
        if lora_mode == "🔥 Trending" and "result" in locals():
            preview_visible = result.get("preview_url") is not None
        
        return prompt_preview, gr.update(visible=preview_visible)

    # Trigger LORA refresh when mode changes (without touching prompt)
    lora_mode.change(
        fn=regenerate_loras_only,
        inputs=[template, genre, use_llm, lora_mode, filter_nsfw, civitai_limit],
        outputs=[output_box, preview_image]
    )
    
    return [template, genre, output_box, preview_image, filter_nsfw, civitai_limit]
