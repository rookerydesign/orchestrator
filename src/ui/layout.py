import gradio as gr
from src.ui.components.prompt_tab import render_prompt_tab
from src.ui.components.lora_tab import render_lora_tab
from src.ui.components.batch_tab import render_batch_tab
from src.ui.components.dispatch_tab import render_dispatch_tab
from src.ui.components.tools_tab import render_tools_tab

def build_ui():
    prompt_state = gr.State("") # 🧠 Shared prompt passed between tabs

    # Initialize the Gradio app tabs with title and theme
    with gr.Blocks(title="Orchestrator Gradio UI") as app:
        with gr.Tabs():
            with gr.TabItem("🧠 Prompt Lab"):
                prompt_tab_inputs = render_prompt_tab(prompt_state)
            with gr.TabItem("🎨 LORA Lab"):
                render_lora_tab(prompt_state)
            with gr.TabItem("📦 Batch Builder"):
                render_batch_tab()
            with gr.TabItem("🚀 Dispatch Center"):
                render_dispatch_tab()
            with gr.TabItem("🛠️ Tools"):
                render_tools_tab()    
    return app

if __name__ == "__main__":
    app = build_ui()
    app.launch()
