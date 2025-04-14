# Orchestrator for SD Forge - Batch Builder Tab
# This module allows users to generate multiple prompt jobs, enhance them via LLM,
# inject LORA tags, and save the full batch for later dispatch.

import gradio as gr
import json
import os
from datetime import datetime
from pathlib import Path

from src.core.prompt_generator import generate_prompts
from src.core.llm_interface import enhance_prompt_with_llm
from src.utils.config_loader import load_config

config = load_config()
WILDCARD_BASE = Path(config["paths"]["wildcard_folder"])
BATCH_DIR = Path("saved_batches")
BATCH_DIR.mkdir(parents=True, exist_ok=True)



def simulate_lora_injection(prompt: str) -> str:
    # TODO: Replace with actual LORA selection + tag injection
    return prompt + ", <lora:faux_style:0.65>"

def build_ui_config():
    return {
        "model": config["defaults"]["model"],
        "steps": config["defaults"]["steps"],
        "hires_steps": config["defaults"].get("hires_steps", 4),
        "cfg_scale": config["defaults"]["cfg_scale"],
        "hr_cfg_scale": config["defaults"].get("hr_cfg_scale", config["defaults"]["cfg_scale"]),
        "sampler": config["defaults"]["sampler"],
        "scheduler": config["defaults"]["scheduler"],
        "hires_fix": config["defaults"]["hires_fix"],
        "denoising_strength": config["defaults"]["denoising_strength"],
        "hr_scale": config["defaults"]["hr_scale"],
        "upscaler": config["defaults"]["upscaler"],
        "width": 832,
        "height": 1216,
        "negative_prompt": config["defaults"]["negative_prompt"],
        "controlnet": {},
        "controlnet_extra_1": {},
        "controlnet_extra_2": {}
    }

def generate_batch_jobs(base_prompt, genre, batch_size, use_llm):
    jobs = []
    for _ in range(batch_size):
        raw_prompt = base_prompt
        enhanced = enhance_prompt_with_llm(raw_prompt, genre) if use_llm else raw_prompt
        final_prompt = simulate_lora_injection(enhanced)

        job = {
            "prompt": final_prompt,
            "ui_config": build_ui_config()
        }
        jobs.append(job)
    return jobs

def save_batch_to_json(jobs):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = BATCH_DIR / f"batch_{timestamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)
    return str(out_path)

def render_batch_tab(shared_prompt_state=None):
    print(f"[DEBUG] Batch tab loaded. shared_prompt_state exists: {shared_prompt_state is not None}")
    if shared_prompt_state is not None:
        print(f"[DEBUG] Initial prompt state value in batch_tab: {shared_prompt_state.value}")
    
    genre = gr.Dropdown(choices=["fantasy", "sci-fi", "realism", "horror", "characters", "nsfw"], label="Genre", value="fantasy")
    batch_size = gr.Slider(1, 50, value=5, step=1, label="Jobs to Generate")
    use_llm = gr.Checkbox(label="✨ Enhance with LLM", value=True)

    base_prompt_display = gr.Textbox(
        label="📥 Base Prompt",
        lines=4,
        interactive=True
    )


    # Keep the existing state change handler for completeness
    def populate_prompt_state(prompt):
        print(f"[BATCH TAB] Auto-populating with: {prompt}")
        return prompt

    if shared_prompt_state:
        shared_prompt_state.change(
            fn=populate_prompt_state,
            inputs=[shared_prompt_state],
            outputs=[base_prompt_display]
        )

        # Add a manual check button for debugging
        check_state_btn = gr.Button("Check State", visible=False)  # Hidden in UI
        

    preview = gr.Textbox(label="🧾 Preview First Job Prompt", lines=6)
    saved_path = gr.Textbox(label="📦 Saved Batch Path")
    generate_button = gr.Button("🛠️ Generate & Save Batch")

    def generate_and_save(genre, batch_size, use_llm, base_prompt):
        jobs = generate_batch_jobs(base_prompt, genre, batch_size, use_llm)
        path = save_batch_to_json(jobs)
        preview_prompt = jobs[0]["prompt"] if jobs else "No prompt generated."
        return preview_prompt, path

    generate_button.click(
        fn=generate_and_save,
        inputs=[genre, batch_size, use_llm, base_prompt_display],
        outputs=[preview, saved_path]
    )

    return [genre, batch_size, use_llm, base_prompt_display]