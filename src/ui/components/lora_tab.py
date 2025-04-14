# Orchestrator for SD Forge - LORA Selection Tab
# This module defines the LORA Lab tab in the Gradio interface.
# It provides a UI for selecting LORAs based on different strategies (e.g., favorites, keyword match, discovery).
# This version uses placeholder logic and a shared prompt input to demonstrate data flow between tabs.

import gradio as gr

# This shared state object allows data (e.g., prompt text) to be passed between Gradio tabs.
shared_prompt = gr.State("")

# Main rendering function for the LORA tab.
# Called from layout.py to render the contents of the "LORA Lab" tab.

def render_lora_tab(shared_prompt_state=None):

    def simulate_lora_selection(prompt, mode):
        # This function simulates LORA selection based on a given prompt and selection mode.
        # In the full app, this will be replaced with actual logic from lora_selector.py.
        return f"Selected LORAs for mode '{mode}' and prompt: {prompt[:60]}..."

    # Input fields
    with gr.Row():
        prompt_input = gr.Textbox(
            label="📥 Prompt (from previous tab)",
            lines=3,
            interactive=True,
            info="Paste a prompt here or wait for shared state to update."
        )
        if shared_prompt_state is not None:
            prompt_input.change(fn=lambda x: x, inputs=[shared_prompt_state], outputs=[prompt_input])
        mode = gr.Radio(
            choices=["✨ Favorites", "✍️ Keyword", "🧪 Discovery"],
            value="✍️ Keyword",
            label="LORA Selection Mode"
        )

    # Trigger button and result display
    with gr.Row():
        simulate_btn = gr.Button("🔍 Simulate LORA Selection")
        result = gr.Textbox(label="LORA Output", lines=4)

    # Bind the button click to the simulated function
    simulate_btn.click(fn=simulate_lora_selection, inputs=[prompt_input, mode], outputs=result)

    # Return references to inputs or states if needed by layout
    return [prompt_input, shared_prompt]