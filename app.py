import streamlit as st
import os
import yaml
import json
from datetime import datetime
import requests
import glob
import base64
from generator import model_loader, lora_selector
from generator.wildcard_loader import resolve_prompt
from generator.model_loader import normalize_model_name
from send_to_forge import send_jobs
from utils import load_model_preset

# Load config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)


MODEL_DIR = config["paths"]["model_folder"]
LORA_DIR = config["paths"]["lora_folder"]

FN_INDEX = 465
SESSION_HASH = "uuhnqx1qqor"  # scrape from UI dynamically later

# Load models and LORAs
raw_models = model_loader.get_available_models(MODEL_DIR)
loras = model_loader.get_available_loras(LORA_DIR)

unique_models = {}
for m in raw_models:
    name = m["name"]
    if name not in unique_models or m["metadata"]:
        unique_models[name] = m

models = list(unique_models.values())
model_names = [m["name"] for m in models] or ["No models found"]

# Genre and super prompt selection
WILDCARD_BASE = os.path.join(os.path.dirname(__file__), "wildcards")

def get_super_prompts():
    path = os.path.join(WILDCARD_BASE, "super_prompts")
    return [f for f in os.listdir(path) if f.endswith(".txt")]

# Streamlit UI setup
st.set_page_config(page_title="Orchestrator", layout="wide")
st.title("🎼 Orchestrator")
st.caption("Modular Prompt and LORA Batch Engine for SD Forge")

st.sidebar.header("Prompt Settings")
genre = st.sidebar.selectbox("🎨 Genre", ["fantasy", "sci-fi", "realism", "horror"])



reroll_prompt = st.sidebar.button("🎲 Create New Prompt")

super_prompt_files = get_super_prompts()
if super_prompt_files:
    prompt_file = st.sidebar.selectbox("📜 Super Prompt Template", super_prompt_files)
else:
    st.sidebar.warning("No super prompts found. Please add `.txt` files to `wildcards/super_prompts/`.")
    prompt_file = None

base_prompt = ""
resolved_prompt = ""

if prompt_file:
    prompt_path = os.path.join(WILDCARD_BASE, "super_prompts", prompt_file)
    with open(prompt_path, "r", encoding="utf-8") as f:
        base_prompt = f.read()
    base_prompt = base_prompt.replace("{genre}", genre)
    resolved_prompt = resolve_prompt(base_prompt, genre) if reroll_prompt else ""

categorized_loras = lora_selector.categorize_loras(loras)

use_smart_matching = st.sidebar.checkbox(
    "Auto-detect themes from text to influence LORA weight bias", 
    value=False
)




# Prompt Source options
prompt_source = st.sidebar.radio("Prompt Source", ["Use Wildcards", "Enter Your Own Prompt"])
user_prompt = st.sidebar.text_area(
    "Your Prompt",
    resolved_prompt if prompt_source == "Enter Your Own Prompt" else "",
    height=100
)

# Config values
use_gpt = st.sidebar.checkbox("Use GPT Enhancement", value=config["defaults"].get("gpt_enabled", True))


# Model configuration
st.markdown("### ⚙️ Model Configuration")
    
colA, colB = st.columns(2)

# Resolution picker
res_options = {
    "1024 x 1024": (1024, 1024),
    "1152 x 896": (1152, 896),
    "896 x 1152": (896, 1152),
    "1216 x 832": (1216, 832),
    "832 x 1216": (832, 1216),
    "1344 x 768": (1344, 768),
    "768 x 1344": (768, 1344)
}
with colA:
    model_choice = st.selectbox("Stable Diffusion Model", model_names)
    model_base = normalize_model_name(model_choice)
    model_defaults = load_model_preset(model_choice)
    selected_res = st.selectbox("Resolution", list(res_options.keys()), index=3)  # Default 1216x832
    width, height = res_options[selected_res]
    steps = st.slider("Steps", 10, 100, model_defaults.get("steps", 30))
    batch_size = st.slider("Total Jobs", min_value=1, max_value=50, value=config["defaults"].get("batch_size", 5))
    # Helper for debugging model preset loading
    def sanitize_model_name(name: str) -> str:
        return name.replace("/", "_").replace("\\", "_")
    preset_filename = sanitize_model_name(model_choice) + ".json"
    st.caption(f"🔍 Looking for preset: `config/model_presets/{preset_filename}`")

with colB:
    sampler_options = [
        "Euler", "Euler a", "DPM++ 2M SDE", "DPM++ 3M SDE", "DPM++ 2M", "DPM++ SDE", "DDIM", "DEIS"
    ]
    sampler_default = model_defaults.get("sampler", "Euler")
    sampler_index = sampler_options.index(sampler_default) if sampler_default in sampler_options else 0
    sampler = st.selectbox("Sampler", sampler_options, index=sampler_index)

    scheduler_options = [
        "Simple", "Beta", "Normal", "Karras", "Exponential", "SGM Uniform", "DDIM"
    ]
    scheduler_default = model_defaults.get("scheduler", "Beta")
    scheduler_index = scheduler_options.index(scheduler_default) if scheduler_default in scheduler_options else 0
    scheduler = st.selectbox("Scheduler", scheduler_options, index=scheduler_index)

    cfg_scale = st.slider("CFG Scale", 1.0, 20.0, model_defaults.get("cfg_scale", 7.0))
    # Denoising strength slider
    denoise_strength = st.slider("Denoising Strength", 0.1, 1.0, config["defaults"].get("denoising_strength", 0.4))
    # In the colB section where you have other hi-res related settings
    hires_steps = st.slider("Hi-res Steps", 0, 50, model_defaults.get("hires_steps", 0), 
                        help="0 means use same as base steps")

# Select LORAs + capture debug log
if reroll_prompt or "initial_lora_pick" not in st.session_state:
    selected_loras, lora_debug_log = lora_selector.select_loras_for_prompt(
        categorized_loras, model_base, resolved_prompt, use_smart_matching
    )
    st.session_state["initial_lora_pick"] = (selected_loras, lora_debug_log)
else:
    selected_loras, lora_debug_log = st.session_state["initial_lora_pick"]

# 🧩 Build inline LORA activations
lora_injections = []

for lora in selected_loras:
    filename = os.path.splitext(os.path.basename(lora["file"]))[0]
    weight = float(lora.get("weight", 0.6)) or 0.6

    if lora.get("activation"):
        act = f"<lora:{filename}:{weight}>"
        lora_injections.append(f"{act} {lora['activation']}")
    else:
        act = f"<lora:{filename}:{weight}>"
        lora_injections.append(act)

lora_block = ", ".join(lora_injections)
final_with_loras = f"{resolved_prompt}, {lora_block}".strip(", ")

if reroll_prompt and resolved_prompt:
    st.markdown("### 🧠 Prompt Preview")
    final_prompt = st.text_area("Resolved Prompt", value=final_with_loras, height=150)
else:
    final_prompt = ""

# Highres fix toggle (keep as is)
hires_fix = st.checkbox("Enable Highres Fix", value=True)




# Filter & display LORAs
st.sidebar.markdown("----")
st.sidebar.markdown("#### LORA Filters")


# Display LORAs used
with st.sidebar:
    with st.expander("🎯 Selected LORAs for Prompt", expanded=True):
        if not selected_loras:
            st.write("No LORAs selected.")
        else:
            for l in selected_loras:
                lora_label = f"✅ `{l['name']}`"
                if l.get("activation"):
                    lora_label += f" <span style='color:#999;'>(→ {l['activation']}, {l.get('weight', 1.0)})</span>"
                st.markdown(lora_label, unsafe_allow_html=True)

# Show log
with st.sidebar.expander("🧠 LORA Selection Debug Info"):
    if lora_debug_log:
        for entry in lora_debug_log:
            st.markdown(f"**{entry['name']}** (weight: {entry['weight']})")
            for r in entry["reasons"]:
                st.markdown(f"- {r}")
    else:
        st.write("No debug info available.")

lora_roots = sorted(set([l["name"].split("/")[0] for l in loras]))
selected_root = st.sidebar.selectbox("Filter by Folder", ["All"] + lora_roots)

# Full LORA list
with st.sidebar.expander("📚 LORA List", expanded=False):
    lora_container = st.container()
    lora_container.markdown("<div style='max-height: 300px; overflow-y: auto;'>", unsafe_allow_html=True)
    for lora in loras:
        if selected_root != "All" and not lora["name"].startswith(selected_root + "/"):
            continue
        if not lora.get("base_model") and not lora["base_model"].startswith(model_base):
            continue
        label = f"✅ `{lora['name']}`"
        if lora.get("activation"):
            label += f" <span style='color:#999;'>(→ {lora['activation']})</span>"
        lora_container.markdown(label, unsafe_allow_html=True)
    lora_container.markdown("</div>", unsafe_allow_html=True)


# 👇 Prepare the generation payload
generation_payload = {
    "prompt": final_prompt,
    "model": model_choice,
    "base_model": model_base,
    "loras": [
        {
            "name": l["name"],
            "file": l["file"],
            "activation": l.get("activation", ""),
            "weight": l.get("weight", 0.6)
        } for l in selected_loras
    ],
    "steps": steps,
    "hires_steps": hires_steps,
    "width": width,
    "height": height,
    "cfg_scale": cfg_scale,
    "sampler": sampler,
    "scheduler": "Beta",
    "hires_fix": hires_fix,
    "hr_cfg_scale": cfg_scale,
    "denoising_strength": denoise_strength,
    "hr_scale": 1.43,
    "upscaler": "4x-AnimeSharp",
    "batch_size": batch_size,
    "genre": genre,
    "template": prompt_file,
    "use_gpt": use_gpt,
    "smart_matching": use_smart_matching
}
from send_to_forge import build_forge_payload

# 👇 Buttons stay here (and can now use `generation_payload`)
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("💾 Save Prompt Batch for Later"):
        # Generate a full batch of prompts
        batch_payload = []
        for _ in range(batch_size):
            # Resolve new prompt
                resolved = resolve_prompt(base_prompt, genre)

                # Get new LORAs
                loras_this_round, _ = lora_selector.select_loras_for_prompt(
                    categorized_loras, model_base, resolved, use_smart_matching
                )

                # Build LORA string
                lora_injections = []
                for lora in loras_this_round:
                    filename = os.path.splitext(os.path.basename(lora["file"]))[0]
                    weight = float(lora.get("weight", 0.6)) or 0.6
                    if lora.get("activation"):
                        lora_injections.append(f"<lora:{filename}:{weight}> {lora['activation']}")
                    else:
                        lora_injections.append(f"<lora:{filename}:{weight}>")

                lora_block = ", ".join(lora_injections)
                final_prompt = f"{resolved}, {lora_block}".strip(", ")

                ui_config = {
                    "model": model_choice,
                    "steps": steps,
                    "hires_steps": hires_steps,
                    "cfg_scale": cfg_scale,
                    "hr_cfg_scale": cfg_scale,
                    "sampler": sampler,
                    "scheduler": scheduler,
                    "hires_fix": hires_fix,
                    "denoising_strength": denoise_strength,
                    "hr_scale": 1.43,
                    "upscaler": "4x-AnimeSharp",
                    "width": width,
                    "height": height,
                    "controlnet": {},
                    "controlnet_extra_1": {},
                    "controlnet_extra_2": {}
                }
                # Build full Forge payload
                payload = build_forge_payload(final_prompt, ui_config)

                batch_payload.append({
                    "prompt": final_prompt,
                    "payload": payload
                })
         # Save to file
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_path = os.path.join("saved_batches", f"batch_{timestamp}.json")
        os.makedirs("saved_batches", exist_ok=True)
        # Save to file first
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(batch_payload, f, indent=2)

        # ✅ Reopen in read mode to preview payload size
        with open(out_path, "r", encoding="utf-8") as f:
            preview_jobs = json.load(f)

        if preview_jobs and "payload" in preview_jobs[0]:
            st.text(f"✅ First saved payload has {len(preview_jobs[0]['payload']['data'])} elements.")
        else:
            st.warning("⚠️ Payload missing or malformed in preview.")
        st.success(f"✅ Batch of {batch_size} prompts saved to `{out_path}`")
    from send_to_forge import send_jobs

with col2:

    if st.button("▶️ Start Batch Generation"):
        saved_dir = "saved_batches"
        batch_files = sorted(glob.glob(os.path.join(saved_dir, "batch_*.json")), reverse=True)

        if not batch_files:
            st.error("❌ No saved batch file found.")
        else:
            latest_batch = batch_files[0]
            st.info(f"📦 Using latest batch file: `{os.path.basename(latest_batch)}`")

            with open(latest_batch, "r", encoding="utf-8") as f:
                jobs = json.load(f)

            output_dir = os.path.join("generated_outputs", os.path.splitext(os.path.basename(latest_batch))[0])

            # Dynamically gather UI settings from sidebar
            ui_config = {
                "model": model_choice,
                "batch_size": batch_size,
                "steps": steps,
                "hires_steps": hires_steps,
                "cfg_scale": cfg_scale,
                "hr_cfg_scale": cfg_scale,
                "sampler": sampler,
                "scheduler": scheduler,
                "hires_fix": hires_fix,
                "denoising_strength": denoise_strength,
                "hr_scale": 1.43,
                "upscaler": "4x-AnimeSharp",
                "width": width,
                "height": height
            }

            # Progress bars
            batch_bar = st.progress(0, text="📦 Starting batch...")
            job_bar = st.progress(0, text="⏳ Initializing...")

            # Progress callbacks
            def on_job_progress(pct, label="⏳ Working..."):
                job_bar.progress(pct, text=label)

            def on_batch_progress(current_idx, total_jobs):
                pct = (current_idx + 1) / total_jobs
                batch_bar.progress(pct, text=f"📦 Job {current_idx + 1} / {total_jobs}")

            # 🔥 Kick off
            send_jobs(
                jobs,
                output_dir,
                ui_config,
                on_job_progress=on_job_progress,
                on_batch_progress=on_batch_progress
            )

    # Pause/resume handling
    if "batch_paused" not in st.session_state:
        st.session_state["batch_paused"] = False

    if st.button("⏸️ Pause Batch"):
        st.session_state["batch_paused"] = True
        st.warning("⏸️ Batch paused...")

    if st.button("▶️ Resume Batch"):
        st.session_state["batch_paused"] = False
        st.success("▶️ Resumed batch processing.")

    

    # Cancel active Forge job
    def cancel_forge_job():
        try:
            event_id = st.session_state.get("last_event_id", "")
            if not event_id:
                st.warning("⚠️ No active event_id found to cancel.")
                return

            cancel_payload = {
                "session_hash": SESSION_HASH,
                "fn_index": FN_INDEX,
                "event_id": event_id
            }

            res = requests.post(
                "http://127.0.0.1:7860/cancel",
                json=cancel_payload,
                headers={"Content-Type": "application/json"}
            )
            res.raise_for_status()
            st.success("🛑 Job cancelled successfully.")

        except requests.exceptions.RequestException as e:
            st.error(f"❌ Failed to cancel job: {e}")

    if st.button("❌ Cancel Active Job"):
        cancel_forge_job()




# 👇 Display payload *after* buttons but declared before
with st.expander("📦 Generation Payload", expanded=False):
    st.json(generation_payload)