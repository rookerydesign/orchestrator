# Orchestrator for SD Forge
# This script is designed to work with the SD Forge API and provides a user interface for generating images using various models and LORAs.
# It allows users to select models, LORAs, and other parameters, and then generates images based on the selected configurations.
# The script uses Streamlit for the user interface and includes various utility functions for managing models, LORAs, and prompts.

import streamlit as st
import os
import yaml
import json
from datetime import datetime
import requests
import glob
import random
from generator import model_loader, lora_selector
from generator.wildcard_loader import resolve_prompt
from generator.model_loader import normalize_model_name
from send_to_forge import send_jobs
from utils.model_tools import load_model_preset
from utils.llm_enhance import enhance_prompt_with_llm
from utils.wildcard_refresher import refresh_wildcards_claude
from utils.model_tools import load_model_preset, sanitize_model_name
from utils.wildcard_prompts import get_prompt_template
from utils.wildcard_cleaner import smart_clean_wildcards
from generator.favorite_combo_selector import load_favorite_combos, pick_random_favorite_combo
from generator.lora_selector import extract_keywords
from generator.update_lora_wildcards import main as update_wildcards_main


# Load config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

claude_api_key = config.get("api_keys", {}).get("claude")
openai_api_key = config.get("api_keys", {}).get("openai")

MODEL_DIR = config["paths"]["model_folder"]
LORA_DIR = config["paths"]["lora_folder"]

FN_INDEX = 465
SESSION_HASH = "uuhnqx1qqor"  # scrape from UI dynamically later

# Streamlit UI setup
st.set_page_config(page_title="Orchestrator", layout="wide")
st.title("🎼 Orchestrator")
st.caption("Modular Prompt and LORA Batch Engine for SD Forge")

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

# Sidebar settings
st.sidebar.header("Prompt Settings")

st.sidebar.markdown("")
col1, col2 = st.sidebar.columns(2)
with col1:
    use_gpt = st.checkbox("Use GPT Enhancement", value=True, key="use_gpt_logic")
with col2:
    # # --- [Moved up] Auto-detect toggle ---
    # use_smart_matching = st.checkbox(
    # "Prompts influence LORA weights", 
    # value=True
    # )

    resolved_prompt = st.session_state.get("enhanced_prompt", "")

use_smart_matching = value=False

st.sidebar.markdown("")  # blank space

# Second row of toggles or controls
col3, col4 = st.sidebar.columns(2)
with col3:
    genre = st.selectbox("🎨 Genre to Prompt for", ["fantasy", "sci-fi", "realism", "horror"])
    
    # --- [Moved up] Super Prompt Template ---
    WILDCARD_BASE = os.path.join(os.path.dirname(__file__), "wildcards")
    def get_super_prompts():
        path = os.path.join(WILDCARD_BASE, "super_prompts")
        return [f for f in os.listdir(path) if f.endswith(".txt")]

    super_prompt_files = get_super_prompts()
with col4:
    if super_prompt_files:
        prompt_file = st.selectbox("📜 Super Prompt Template", super_prompt_files)
    else:
        st.sidebar.warning("No super prompts found. Please add `.txt` files to `wildcards/super_prompts/`.")
        prompt_file = None

reroll_prompt = st.sidebar.button("🎲 Create New Prompt", key="reroll_prompt", use_container_width=True)

st.sidebar.markdown("")  # blank space

col5, col6 = st.sidebar.columns(2)

# Temporary toggle values (not yet linked to logic)
use_wildcards_tmp = col5.toggle("🧩 Wildcards", value=True, key="use_wildcards")
use_manual_tmp = col6.toggle("✍️ Manual Prompt", value=not use_wildcards_tmp, key="use_manual")

# Determine final prompt source without writing to session_state directly
# Only allow one active at a time (manual takes precedence if both are selected)
if use_manual_tmp:
    prompt_source = "Enter Your Own Prompt"
elif use_wildcards_tmp:
    prompt_source = "Use Wildcards"
else:
    prompt_source = "Use Wildcards"  # fallback

# Show input only if manual is selected
if prompt_source == "Enter Your Own Prompt":
    user_prompt = st.sidebar.text_area("Your Prompt", resolved_prompt, height=100)
else:
    user_prompt = ""

# col7, col8 = st.sidebar.columns(2)

# use_favs_tmp = col7.toggle("✨ Favourites", value=True, key="use_favs")
# use_keyword_tmp = col8.toggle("📒 Keyword Selection", value=not use_favs_tmp, key="use_keyword")

# # Mutual exclusivity
# use_favs = use_favs_tmp
# use_smart_matching = not use_favs_tmp  # replaces use_keyword
st.sidebar.markdown("---")

selection_mode = st.sidebar.radio(
    "🎛️ Selection Mode",
    ["✨ Favourites", "✍️ Keyword Selection", "🧪 Discovery"],
    index=1,  # default to Keyword
    horizontal=True,
)
st.sidebar.markdown("**How it works:**")
st.sidebar.caption("""
- ✨ Favourites: Picks from curated combos.
- ✍️ Keyword: Matches tags from prompt.
- 🧪 Discovery: Prioritizes underused LORAs.
""")

use_favs = selection_mode == "✨ Favourites"
use_smart_matching = selection_mode == "✍️ Keyword Selection"
use_discovery = selection_mode == "🧪 Discovery"

st.sidebar.markdown("---")
# --- Wildcard Refresher ---
st.sidebar.markdown("### 🧠 Wildcard Refresher")

col1, col2 = st.sidebar.columns(2)
with col1:
    refresh_genre = st.selectbox("Genre", ["fantasy", "sci-fi", "horror", "realism"], key="refresh_genre")
with col2:
    refresh_category = st.selectbox("Category", ["classes", "garb", "holding", "humanoids", "setting"], key="refresh_category")

if st.sidebar.button("🔁 Refresh with LLM", use_container_width=True):
    if not claude_api_key:
        st.warning("Please enter your Claude API key.")
    else:
        wildcard_dir = "wildcards"

        added, err = refresh_wildcards_claude(claude_api_key, refresh_genre, refresh_category, wildcard_dir)
        if err:
            st.error(err)
        elif added:
            st.success(f"✅ Added {len(added)} entries to {genre}/{refresh_category}.txt")
            with st.expander("🆕 New Entries"):
                st.write("\n".join(added))
        else:
            st.info("No new entries added — Claude returned all known items.")

st.sidebar.markdown("### 🔄 LORA Wildcard Sync")
if st.sidebar.button("🔄 Update LORA Wildcards", use_container_width=True):
    try:
        added, removed = update_wildcards_main()
        st.success(f"✅ Wildcards updated — {added} added, {removed} removed.")
    except Exception as e:
        st.error(f"❌ Failed to update wildcards: {e}")

    
st.sidebar.markdown("---")

# --- Wildcard Cleaner ---
from utils.wildcard_cleaner import clean_wildcards_with_llm

st.sidebar.markdown("### 🧼 Wildcard Cleaner")

col1, col2 = st.sidebar.columns(2)
with col1:
    clean_genre = st.selectbox("Genre", ["fantasy", "sci-fi", "horror", "realism"], key="clean_genre")
with col2:
    clean_category = st.selectbox(
        "Category", ["classes", "garb", "holding", "humanoids", "setting"], key="clean_category"
    )
clean_file = f"wildcards/{clean_genre}/{clean_category}.txt"
if st.sidebar.button("🧹 Clean Wildcard File with LLM", use_container_width=True):
    # ... [rest of original logic remains unchanged]

    try:
        with open(clean_file, "r", encoding="utf-8") as f:
            entries = [line.strip() for line in f if line.strip()]

        st.info(f"Sending {len(entries)} entries to LLM for cleanup...")
        cleaned = smart_clean_wildcards(entries, genre=clean_genre, category=clean_category)
        st.session_state["cleaned_entries"] = cleaned
        st.session_state["ready_to_save"] = True

        if cleaned:
            original_count = len(entries)
            cleaned_count = len(cleaned)
            reduction_pct = 100 * (1 - (cleaned_count / original_count)) if original_count > 0 else 0

            st.success(f"✅ LLM returned {cleaned_count} cleaned entries.")
            st.markdown(f"🗂️ Original: `{original_count}` entries")
            st.markdown(f"📉 Reduction: `{reduction_pct:.1f}%`")

            if reduction_pct > 80:
                st.warning("⚠️ More than 80% of wildcards were removed. This may indicate over-filtering.")

            with st.expander("🔍 Preview Cleaned Wildcards"):
                st.text("\n".join(cleaned))

        else:
            st.warning("⚠️ No cleaned entries returned.")
    except FileNotFoundError:
        st.error(f"❌ File not found: {clean_file}")
    except Exception as e:
        st.error(f"❌ Error during cleanup: {e}")

if st.session_state.get("ready_to_save") and "cleaned_entries" in st.session_state:
    if st.button("💾 Overwrite File with Cleaned Entries"):
        try:
            with open(clean_file, "w", encoding="utf-8") as f:
                for entry in st.session_state["cleaned_entries"]:
                    f.write(entry + "\n")
            st.success("✅ Wildcard file updated successfully.")
            with st.expander("📂 Updated File Contents"):
                st.text("\n".join(st.session_state["cleaned_entries"]))
        except Exception as e:
            st.error(f"❌ Failed to save file: {e}")



# Get available templates
WILDCARD_BASE = os.path.join(os.path.dirname(__file__), "wildcards")


def get_super_prompts():
    path = os.path.join(WILDCARD_BASE, "super_prompts")
    return [f for f in os.listdir(path) if f.endswith(".txt")]


# Initialize resolved prompt to empty
base_prompt = ""
resolved_prompt = ""
enhanced_prompt = ""

# Only handle prompt logic if user clicked button
if reroll_prompt and prompt_file:
    prompt_path = os.path.join(WILDCARD_BASE, "super_prompts", prompt_file)
    with open(prompt_path, "r", encoding="utf-8") as f:
        base_prompt = f.read()
    base_prompt = base_prompt.replace("{genre}", genre)

    raw_prompt = resolve_prompt(base_prompt, genre)

    if use_gpt:
        enhanced_prompt = enhance_prompt_with_llm(raw_prompt, genre)
    else:
        enhanced_prompt = raw_prompt

    st.session_state["enhanced_prompt"] = enhanced_prompt
    resolved_prompt = enhanced_prompt

elif "enhanced_prompt" in st.session_state:
    resolved_prompt = st.session_state["enhanced_prompt"]


    # Pull from session cache if not rerolling
    enhanced_prompt = st.session_state.get("enhanced_prompt", "")
    resolved_prompt = enhanced_prompt

categorized_loras = lora_selector.categorize_loras(loras)


# Model configuration
st.markdown("### ⚙️ Model Configuration")
    
colA, colB = st.columns(2)

# Resolution picker
res_options = {
    "1024 x 1024 Square": (1024, 1024),
    "1152 x 896 Landscape": (1152, 896),
    "896 x 1152 Portrait": (896, 1152),
    "1216 x 832 Landscape": (1216, 832),
    "832 x 1216 Portrait": (832, 1216),
    "1344 x 768 Landscape": (1344, 768),
    "768 x 1344 Portrait": (768, 1344)
}
with colA:
    model_choice = st.selectbox("Stable Diffusion Model", model_names)
    model_base = normalize_model_name(model_choice)
    model_defaults = load_model_preset(model_choice)
    selected_res = st.selectbox("Resolution", list(res_options.keys()), index=4)  # Default 1216x832
    width, height = res_options[selected_res]
    steps = st.slider("Steps", 10, 100, model_defaults.get("steps", 30))
    batch_size = st.slider("Total Jobs", min_value=1, max_value=50, value=config["defaults"].get("batch_size", 1))
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
    hires_steps = st.slider("Hi-res Steps", 0, 50, model_defaults.get("hires_steps", 4), 
                        help="0 means use same as base steps")

# Select LORAs + capture debug log
if reroll_prompt or "initial_lora_pick" not in st.session_state:
    if use_favs:
        favorite_combos = load_favorite_combos()
        picked = pick_random_favorite_combo(
            favorite_combos,
            genre=genre,
            prompt_keywords=extract_keywords(resolved_prompt)
        )
        selected_loras = picked["loras"]
        lora_debug_log = [
            {
                "name": l["name"],
                "weight": l["weight"],
                "category": "from_favorites",
                "reasons": ["✨ Picked from favorites DB"]
            } for l in selected_loras
        ]

    elif use_smart_matching:
        selected_loras, lora_debug_log = lora_selector.select_loras_for_prompt(
            categorized_loras, model_base, resolved_prompt,
            use_smart_matching, genre=genre
        )

    elif use_discovery:
        from generator.discovery_selector import select_discovery_loras
        from utils.lora_audit import get_unused_loras_grouped_by_model_and_category

        unused_by_model_cat = get_unused_loras_grouped_by_model_and_category()
        underused = unused_by_model_cat.get(model_base.capitalize(), {})


        print(f"[🧪 APP] Discovery mode: model_base='{model_base}' → found categories: {list(underused.keys())}")

        # This assumes you're passing in the underused LORAs grouped by (base_model, category)
        selected_loras, lora_debug_log = select_discovery_loras(model_base, unused_by_model_cat)


    else:
        selected_loras, lora_debug_log = st.session_state.get("initial_lora_pick", ([], []))

    st.session_state["initial_lora_pick"] = (selected_loras, lora_debug_log)
else:
    selected_loras, lora_debug_log = st.session_state["initial_lora_pick"]


# 🧩 Build inline LORA activations
lora_injections = []

for lora in selected_loras:
    # ✅ Use explicit 'name' if it's there — this prevents file-based overrides
    full_name = lora.get("name", "unknown")
    filename = os.path.basename(full_name)
    weight = float(lora.get("weight", 0.6)) or 0.6
    activation = lora.get("activation") or filename

    act = f"<lora:{filename}:{weight}>"
    if activation and activation != filename:
        lora_injections.append(f"{act} {activation}")
    else:
        lora_injections.append(act)

    # # Add debug print here
    # print(f"LORA Debug: full_name='{full_name}', filename='{filename}', activation='{activation}', act='{act}'")

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

lora_roots = sorted(set(
    l["name"].split("/")[0]
    for l in loras
    if isinstance(l, dict) and "name" in l and "/" in l["name"]
))

selected_root = st.sidebar.selectbox("Filter by Folder", ["All"] + lora_roots)

# Full LORA list
with st.sidebar.expander("📚 LORA List", expanded=False):
    lora_container = st.container()
    lora_container.markdown("<div style='max-height: 300px; overflow-y: auto;'>", unsafe_allow_html=True)
    for lora in loras:
        if selected_root != "All" and not lora["name"].startswith(selected_root + "/"):
            continue
        if not isinstance(lora, dict):
            continue
        if not lora.get("base_model") or not lora["base_model"].startswith(model_base):
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
            "file": l.get("file", ""),  # Safe fallback
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
        
        # Before the loop:
        last_prompt = st.session_state.get("enhanced_prompt", None)

        prompt_path = os.path.join(WILDCARD_BASE, "super_prompts", prompt_file)
        with open(prompt_path, "r", encoding="utf-8") as f:
            base_prompt = f.read()

        base_prompt = base_prompt.replace("{genre}", genre)

        # Resolve new prompt
        with st.spinner(f"🧠 Enhancing {batch_size} prompts..."):
            for i in range(batch_size):
                if i == 0 and last_prompt:
                    enhanced_prompt = last_prompt
                else:
                    raw_prompt = resolve_prompt(base_prompt, genre)
                    enhanced_prompt = enhance_prompt_with_llm(raw_prompt, genre) if use_gpt else raw_prompt

                resolved = enhanced_prompt
    
                # Get new LORAs
                loras_this_round, _ = lora_selector.select_loras_for_prompt(
                    categorized_loras, model_base, resolved, use_smart_matching, genre=genre
                )

                # Build LORA string
                # Build LORA string
                lora_injections = []

                for lora in loras_this_round:
                    # ✅ Always prefer the 'name' field for prompt injection
                    full_name = lora.get("name", "unknown")  # Prefer 'name' key
                    filename = os.path.basename(full_name)
                    weight = float(lora.get("weight", 0.6)) or 0.6
                    activation = lora.get("activation") or filename

                    act = f"<lora:{filename}:{weight}>"
                    if activation and activation != filename:
                        lora_injections.append(f"{act} {activation}")
                    else:
                        lora_injections.append(act)
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

with col2:
    # Utility: track which batches have already been sent
    SENT_LOG = "sent_batches.log"

    def get_sent_batches():
        if not os.path.exists(SENT_LOG):
            return set()
        with open(SENT_LOG, "r") as f:
            return set(line.strip() for line in f.readlines())

    def mark_batch_as_sent(batch_filename):
        with open(SENT_LOG, "a") as f:
            f.write(batch_filename + "\n")

    # Button 1: Start Latest
    if st.button("▶️ Start Latest Batch"):
        saved_dir = "saved_batches"
        batch_files = sorted(glob.glob(os.path.join(saved_dir, "batch_*.json")), reverse=True)

        if not batch_files:
            st.error("❌ No saved batch file found.")
        else:
            latest_batch = os.path.basename(batch_files[0])
            st.info(f"📦 Using latest batch: `{latest_batch}`")

            if latest_batch in get_sent_batches():
                st.warning("⚠️ Latest batch already sent. Consider using 'Start All Incomplete Batches'.")
            else:
                with open(os.path.join(saved_dir, latest_batch), "r", encoding="utf-8") as f:
                    jobs = json.load(f)

                # Only create output folder if Forge doesn't already handle outputs
                output_dir = None  # Set to None to skip unused folder creation

                # Progress bars
                batch_bar = st.progress(0, text="📦 Starting batch...")
                job_bar = st.progress(0, text="⏳ Initializing...")

                def on_job_progress(pct, label="⏳ Working..."):
                    job_bar.progress(pct, text=label)

                def on_batch_progress(current_idx, total_jobs):
                    pct = (current_idx + 1) / total_jobs
                    batch_bar.progress(pct, text=f"📦 Job {current_idx + 1} / {total_jobs}")

                try:
                    send_jobs(
                        jobs,
                        output_dir,
                        ui_config,
                        on_job_progress=on_job_progress,
                        on_batch_progress=on_batch_progress
                    )
                    mark_batch_as_sent(latest_batch)
                    st.success(f"✅ Batch `{latest_batch}` sent and logged.")
                except Exception as e:
                    st.error(f"❌ Failed to send batch `{latest_batch}`: {e}")

    # Button 2: Start All Incomplete
    if st.button("▶️ Start All Incomplete Batches"):
        saved_dir = "saved_batches"
        batch_files = sorted(glob.glob(os.path.join(saved_dir, "batch_*.json")))
        sent = get_sent_batches()

        unsent_batches = [os.path.basename(b) for b in batch_files if os.path.basename(b) not in sent]

        if not unsent_batches:
            st.info("✅ All batches already sent.")
        else:
            for idx, batch_name in enumerate(unsent_batches):
                st.info(f"📦 Sending batch `{batch_name}` ({idx + 1}/{len(unsent_batches)})")
                with open(os.path.join(saved_dir, batch_name), "r", encoding="utf-8") as f:
                    jobs = json.load(f)

                output_dir = None  # Skip creating empty folders

                batch_bar = st.progress(0, text=f"📦 Starting batch {idx + 1}")
                job_bar = st.progress(0, text="⏳ Initializing...")

                def on_job_progress(pct, label="⏳ Working..."):
                    job_bar.progress(pct, text=label)

                def on_batch_progress(current_idx, total_jobs):
                    pct = (current_idx + 1) / total_jobs
                    batch_bar.progress(pct, text=f"📦 Job {current_idx + 1} / {total_jobs}")

                send_jobs(
                    jobs,
                    output_dir,
                    ui_config,
                    on_job_progress=on_job_progress,
                    on_batch_progress=on_batch_progress
                )

                mark_batch_as_sent(batch_name)
                st.success(f"✅ Batch `{batch_name}` complete and logged.")


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