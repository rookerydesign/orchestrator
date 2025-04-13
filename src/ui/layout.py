import gradio as gr
from src.ui.components.prompt_tab import render_prompt_tab
from src.ui.components.lora_tab import render_lora_tab
from src.ui.components.batch_tab import render_batch_tab

def build_ui():
    with gr.Blocks(title="Orchestrator Gradio UI") as app:
        with gr.Tabs():
            with gr.TabItem("🧠 Prompt Lab"):
                render_prompt_tab()
            with gr.TabItem("🎨 LORA Lab"):
                render_lora_tab()
            with gr.TabItem("📦 Batch Builder"):
                render_batch_tab()
    return app

if __name__ == "__main__":
    app = build_ui()
    app.launch()
