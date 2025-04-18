# Orchestrator for SD Forge - Image Gen Settings Tab
# This module defines the UI for configuring Forge image generation parameters.

import gradio as gr

def render_image_settings_tab(selected_model_state=None):
    with gr.Column():
        gr.Markdown("## 🎨 Image Generation Settings")

        model_selector = gr.Dropdown(
            choices=["flux", "pony", "sdxl"],
            value="flux",
            label="Model"
        )
        
        # Connect model_selector to selected_model_state
        if selected_model_state is not None:
            model_selector.change(
                fn=lambda x: x,
                inputs=[model_selector],
                outputs=[selected_model_state]
            )
        
        sampler = gr.Dropdown(
            choices=["Euler", "DPM++ 2M", "DDIM"],
            value="Euler",
            label="Sampler"
        )
        scheduler = gr.Dropdown(
            choices=["Beta", "Linear", "Karras"],
            value="Beta",
            label="Scheduler"
        )
        steps = gr.Slider(minimum=5, maximum=100, value=30, label="Steps")
        cfg_scale = gr.Slider(minimum=1.0, maximum=20.0, value=7.5, label="CFG Scale")

        hires_fix = gr.Checkbox(label="Enable Hi-Res Fix", value=True)
        hires_steps = gr.Slider(minimum=1, maximum=50, value=15, label="Hi-Res Steps")
        denoising_strength = gr.Slider(minimum=0.0, maximum=1.0, value=0.4, label="Denoising Strength")

        resolution = gr.Radio(
            choices=["512x768", "832x1216", "1024x1536"],
            value="832x1216",
            label="Resolution"
        )

        gr.Markdown("💡 These settings will be included in Forge dispatch payloads.")
        

    return  # No output required yet
