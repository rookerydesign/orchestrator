
import streamlit as st
import os
import yaml
from generator import model_loader

# Load config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)


MODEL_DIR = config["paths"]["model_folder"]
LORA_DIR = config["paths"]["lora_folder"]

# Load models and LORAs
# Load models (and deduplicate by name)
raw_models = model_loader.get_available_models(MODEL_DIR)
loras = model_loader.get_available_loras(LORA_DIR)


# Use a dictionary keyed by name to remove duplicates
unique_models = {}
for m in raw_models:
    name = m["name"]
    if name not in unique_models or m["metadata"]:  # prioritize one with metadata
        unique_models[name] = m

models = list(unique_models.values())
model_names = [m["name"] for m in models] or ["No models found"]

# Load lora_selector
from importlib.util import spec_from_file_location, module_from_spec
selector_path = os.path.join("generator", "lora_selector.py")
spec = spec_from_file_location("lora_selector", selector_path)
lora_selector = module_from_spec(spec)
spec.loader.exec_module(lora_selector)

# Create Streamlit UI
st.set_page_config(page_title="Orchestrator", layout="wide")
st.title("🎼 Orchestrator")
st.caption("Modular Prompt and LORA Batch Engine for SD Forge")

st.sidebar.header("Prompt Settings")
prompt_source = st.sidebar.radio("Prompt Source", ["Use Wildcards", "Enter Your Own Prompt"])
user_prompt = ""
if prompt_source == "Enter Your Own Prompt":
    user_prompt = st.sidebar.text_area("Your Prompt", height=100)
else:
    user_prompt = "Loaded from wildcard template..."

genre = st.sidebar.selectbox("Genre/Theme", ["Fantasy", "Sci-Fi", "Cyberpunk", "Surreal", "Realistic"])
use_gpt = st.sidebar.checkbox("Use GPT Enhancement", value=config["defaults"].get("gpt_enabled", True))
batch_size = st.sidebar.slider("Batch Size", min_value=1, max_value=50, value=config["defaults"].get("batch_size", 5))

st.sidebar.header("Model Settings")
model_names = [m["name"] for m in models] or ["No models found"]
model_choice = st.sidebar.selectbox("Stable Diffusion Model", model_names)

steps = st.sidebar.slider("Steps", 10, 100, config["defaults"].get("steps", 30))
cfg_scale = st.sidebar.slider("CFG Scale", 1.0, 20.0, config["defaults"].get("cfg_scale", 7.0))
sampler = st.sidebar.selectbox("Sampler", ["Euler", "Euler a", "DPM++ 2M", "DPM++ SDE", "Heun", "DDIM"])
hires_fix = st.sidebar.checkbox("Enable Highres Fix", value=config["defaults"].get("hires_fix", True))
denoise_strength = st.sidebar.slider("Denoising Strength", 0.1, 1.0, config["defaults"].get("denoising_strength", 0.4))
hr_scale = st.sidebar.slider("HR Upscale Factor", 1.0, 2.0, config["defaults"].get("hr_scale", 1.43))
upscaler = st.sidebar.selectbox("Upscaler", ["None", "4x-AnimeSharp", "Latent", "R-ESRGAN"])

# Normalize model name for compatibility check
from generator.model_loader import normalize_model_name
model_base = normalize_model_name(model_choice)

# Categorize LORAs using the loaded list
categorized_loras = lora_selector.categorize_loras(loras)

# Reroll button
st.sidebar.markdown("----")
reroll = st.sidebar.button("🎲 Reroll LORA Selection")

# Select a LORA set for this model
selected_loras = []
if reroll or "initial_lora_pick" not in st.session_state:
    selected_loras = lora_selector.select_loras_for_prompt(categorized_loras, model_base)
    st.session_state["initial_lora_pick"] = selected_loras
else:
    selected_loras = st.session_state["initial_lora_pick"]


# LORA filter options
st.sidebar.markdown("----")
st.sidebar.markdown("#### LORA Filters")

# Show-all toggle
show_all_loras = st.sidebar.checkbox("Show All LORAs", value=False)

# Dropdown by root folder (e.g., Flux, SDXL, Pony)
lora_roots = sorted(set([l["name"].split("/")[0] for l in loras]))
selected_root = st.sidebar.selectbox("Filter by Folder", ["All"] + lora_roots)

# Display LORAs
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

    with st.expander("📚 LORA List", expanded=True):
        lora_container = st.container()
        lora_container.markdown("<div style='max-height: 300px; overflow-y: auto;'>", unsafe_allow_html=True)

        for lora in loras:
            if selected_root != "All" and not lora["name"].startswith(selected_root + "/"):
                continue
            if not show_all_loras and lora.get("base_model") and not lora["base_model"].startswith(model_base):
                continue


            label = f"✅ `{lora['name']}`"
            if lora.get("activation"):
                label += f" <span style='color:#999;'>(→ {lora['activation']})</span>"
            lora_container.markdown(label, unsafe_allow_html=True)

        lora_container.markdown("</div>", unsafe_allow_html=True)
   
      

# Preview and action buttons
st.markdown("### 🧠 Prompt Preview")
st.code(user_prompt, language='text')

st.markdown("### 🔧 Generation Configuration")
st.json({
    "model": model_choice,
    "steps": steps,
    "cfg_scale": cfg_scale,
    "sampler": sampler,
    "hires_fix": hires_fix,
    "denoising_strength": denoise_strength,
    "hr_scale": hr_scale,
    "upscaler": upscaler
})

col1, col2 = st.columns([1, 1])
with col1:
    st.button("💾 Save Prompt Batch for Later")
with col2:
    st.button("▶️ Start Batch Generation")
