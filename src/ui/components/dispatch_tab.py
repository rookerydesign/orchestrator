# Orchestrator for SD Forge - Dispatch Center Tab
# This module defines the UI for dispatching prompt batches to Stable Diffusion Forge.
# Includes functionality for sending latest batch, starting all unsent batches, and job control (pause/resume/cancel).

import gradio as gr

def render_dispatch_tab():
    def simulate_dispatch(action):
        return f"Simulated action: {action}"

    with gr.Row():
        action = gr.Radio(choices=["▶️ Start Latest Batch", "▶️ Start All Unsent", "⏸️ Pause", "▶️ Resume", "❌ Cancel"], value="▶️ Start Latest Batch", label="Action")
        dispatch_btn = gr.Button("🚀 Execute")
    
    result = gr.Textbox(label="Dispatch Status", lines=3)

    dispatch_btn.click(fn=simulate_dispatch, inputs=[action], outputs=result)