# Orchestrator for SD Forge - LORA Selection Tab (Stable Refactor)
# Adds robust prompt-sharing, LORA mode logic, and safe debugging.

import gradio as gr
from src.core.lora_selector import categorize_loras, select_loras_for_prompt
from src.utils.config_loader import load_config

# Load config once
cfg = load_config()
DEFAULT_GENRE = "fantasy"
BASE_MODEL = "Flux1DevHyperNF4"

def render_lora_tab(shared_prompt_state=None):
    tab_switch = gr.Textbox(visible=False)  # Hidden field to trigger state refresh

    with gr.Row():
        prompt_input = gr.Textbox(
            label="Prompt (from previous tab)",
            lines=3,
            interactive=True,
            placeholder="Prompt will auto-load when you open this tab."
        )

        mode = gr.Radio(
            choices=["Favorites", "Keyword", "Discovery", "Prompt LORAs"],
            value="Keyword",
            label="LORA Selection Mode"
        )

    with gr.Row():
        run_selector_btn = gr.Button("🔍 Run LORA Selector")
        output_lora_preview = gr.Textbox(label="Selected LORAs (Log)", lines=10)

    # --- Shared State Sync (called on tab switch) ---
    def populate_prompt_on_tab_change(_tab_trigger, shared_prompt):
        print(f"[LORA TAB] Loaded prompt from shared state: {shared_prompt}")
        return shared_prompt or ""

    # --- Real Logic for Smart Matching ---
    # def simulate_lora_selection(prompt, mode, available_loras):
    #     if not prompt.strip():
    #         return "⚠️ No prompt provided."

    #     if mode == "✍️ Keyword":
    #         all_loras = available_loras if available_loras else []

    #         if not all_loras:
    #             return "⚠️ No LORAs loaded (available_loras is empty or missing)."

    #         try:
    #             categorized = categorize_loras(all_loras)
    #         except Exception as e:
    #             return f"[ERROR] Failed to categorize LORAs: {str(e)}"

            
    #         selected, log = select_loras_for_prompt(
    #             categorized_loras=categorized,
    #             base_model=BASE_MODEL,
    #             resolved_prompt=prompt,
    #             use_smart_matching=True,
    #             genre=DEFAULT_GENRE
    #         )
    #         lines = []
    #         for lora in log:
    #             lines.append(f"• {lora['name']} @ {lora['weight']} ({lora['category']})")
    #             if "reasons" in lora:
    #                 for reason in lora["reasons"]:
    #                     lines.append(f"   ↳ {reason}")
    #         return "\n".join(lines) or "❌ No matches found."

    #     elif mode == "Prompt LORAs":
    #         return "[Prompt LORA mode] Extracts embedded tags from prompt — coming soon."

    #     elif mode == "Favorites":
    #         return "[Favorites mode] Uses preset combos — not wired up yet."

    #     elif mode == "Discovery":
    #         return "[Discovery mode] Underused LORA boost — coming soon."

    #     return f"⚠️ Mode '{mode}' not implemented."

    # # Hook up trigger and actions
    # run_selector_btn.click(
    #     fn=simulate_lora_selection,
    #     inputs=[prompt_input, mode],
    #     outputs=[output_lora_preview]
    # )


    # tab_switch.change(
    #     fn=populate_prompt_on_tab_change,
    #     inputs=[tab_switch, shared_prompt_state],
    #     outputs=[prompt_input]
    # )

    # return [tab_switch, prompt_input, mode, output_lora_preview]
