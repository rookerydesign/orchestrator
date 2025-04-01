
# 🧭 Orchestrator Project Roadmap

A modular system for intelligent, dynamic prompt and LORA composition for Stable Diffusion WebUI Forge.

---

## ✅ Phase 1: Core Setup — ✅ Complete

### 🔧 Infrastructure
- [x] `app.py` built in **Streamlit**
- [x] Custom `config.yaml` for paths and defaults
- [x] `.gitignore` created
- [x] Git repo initialized and pushed to GitHub ✅

### 📁 Folder + Model/LORA Handling
- [x] Model loading from `/Stable-diffusion/` with metadata parsing
- [x] LORA loading from `/Lora/`, scanned recursively
- [x] Compatible `.json` / `.info` metadata parsing for LORAs
- [x] Automatic base model detection using fallback logic (JSON > INFO > folder > name)
- [x] Categorization by folder → category map
- [x] Folders support multiple base models (Flux, SDXL, Pony)

---

## ✅ Phase 2: LORA Selector Engine — ✅ Complete

### 🔬 Smart LORA Logic
- [x] LORA selection per base model using weighted randomness
- [x] Configurable weights per category (`detailer`, `artist`, `general`, `fx`, `character`, `people_style`)
- [x] Detailer is always included
- [x] Ranges 1–6 LORAs per generation (1 and 6 weighted least)
- [x] Support for intelligent fallback if metadata missing
- [x] Config lives in `lora_config.json`

### 🎛️ Streamlit UI Integration
- [x] Dropdown for model base selection
- [x] Sidebar toggle for wildcard vs manual prompt
- [x] “🎲 Reroll LORA Selection” to test selector
- [x] Display chosen LORAs in their categories, sorted and labeled
- [x] Filtered LORAs by model compatibility and folder root

---

## 🔜 Phase 3: Prompt Composer (Upcoming)

### 🎨 Prompt Building
- [ ] Compose prompt from:
  - [ ] Wildcard rules
  - [ ] Manual input
  - [ ] Genre preset + enhancement via GPT or LLM
- [ ] Inject LORA activation texts with weights inline
- [ ] Keyword injection from LORA metadata
- [ ] Auto-detect themes from text to influence LORA weight bias

### 📦 Output & Export
- [ ] Save composed prompts + metadata to:
  - [ ] `.json` for automation
  - [ ] `.txt` for manual Forge batch input
  - [ ] Optional `.csv` for visual overview
- [ ] Load prompt batch files for reuse

---

## 🚀 Phase 4: Forge Integration (Later)

### 🧠 Automation
- [ ] Send prompt batch to Forge via API (locally)
- [ ] Async or queued generation
- [ ] Save images + metadata with ID
- [ ] Store prompt history for reuse

---

## 🧾 Bonus Ideas / Wishlist

- [ ] GPT toggle (like “Enhance Prompt” in UI)
- [ ] Model preview thumbnails from `.preview.png`
- [ ] Advanced semantic matching (e.g. “analog + cinematic” → lighting LORAs)
- [ ] Filtering LORAs by tags or effectiveness
- [ ] LORA test mode (generate 1 batch per LORA for style swatch)

---

## 💡 Current Status (as of Apr 2, 2025)

You’re fully set up with:
- Model and LORA loading with metadata parsing ✅
- LORA selection engine and category weighting ✅
- Streamlit interface with dynamic LORA preview ✅
- Git repo initialized and pushed ✅
