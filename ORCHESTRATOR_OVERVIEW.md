# 🎛️ Orchestrator Overview

A modular prompt and LORA orchestration engine for **Stable Diffusion Forge**, enabling intelligent, dynamic prompt generation, LORA selection, and batch processing.

---

## ✅ Current Capabilities

- 🧠 **Wildcard Prompt Engine**  
  Generates prompts using flexible category-based randomization across genre, style, archetype, and more.

- 🎨 **LORA Matching System**  
  Dynamically selects LORAs based on keyword matches in `.info` and `.json` metadata, ensuring contextual relevance.

- 🔍 **GPT-Enhanced Prompting** *(via LM Studio API)*  
  Sends wildcard-generated prompts to a local LLM (e.g. MythoMax) for enhancement. Toggleable in the sidebar.

- 🗂️ **Batch Prompt Saving**  
  Save generated prompts to `.json` files for automated batch submission later.

- 🚀 **Forge Job Dispatch**  
  Submits prompts directly to Stable Diffusion Forge using a 161-field payload mimicking the UI submission format.

- 📦 **Smart Payload Saving**  
  Saves jobs with associated metadata and optional validation.

- ⚙️ **Hi-Res & CFG Controls**  
  Supports `hires_fix`, `hires_steps`, `denoising_strength`, and base/hires `cfg_scale`.

---

## 🧪 In Progress / Experimental

- [ ] **Prompt-Guided Image Matching / Conditioning**  
- [ ] **LLM Prompt Templates** — Style/genre aware enhancement options  
- [ ] **Streamlined Progress Feedback** during batch processing  
- [ ] **Prompt Ranking / Curation Interface**

---

## 🛠️ Local Setup Notes

- Requires **Stable Diffusion Forge** running locally.
- **LM Studio** must have "Local LLM Service" enabled for prompt enhancement.
- Use GGUF quantized models under 8GB for best results on 12GB GPUs.
- Add `saved_batches/` and `config/` to `.gitignore`.

---

## ⚠️ Known Quirks

- Forge API expects exactly **161 fields** in its data payload — enforced by validation.
- Prompts are sent to the LLM *before* LORA selection to improve contextual matching.

---

## 🗺️ Development Roadmap

### ✅ Phase 1: Core Setup
- Streamlit app scaffold, config file, `.gitignore`, GitHub repo ✅
- Model + LORA folder support with recursive metadata parsing ✅
- Base model fallback logic and folder categorization ✅

### ✅ Phase 2: LORA Selector Engine
- Weighted random selection per category  
- Fallback logic, detailer injection, 1–6 LORA spread  
- Streamlit UI for LORA testing, preview, and reroll ✅

### 🔨 Phase 3: Prompt Composer *(Upcoming)*
- Prompt generation from wildcards, manual input, or genre templates  
- Inline LORA activation text injection  
- Save prompt + metadata to `.json`, `.txt`, or `.csv`

### 🛰️ Phase 4: Forge Integration
- Local API dispatch with queue or async support  
- Save images + metadata with history view

---

## 🌟 Wishlist & Ideas

- Model preview thumbnails via `.preview.png`
- Semantic prompt → LORA matching (e.g., "analog + cinematic" triggers style LORAs)
- Tag-based filtering or effectiveness scoring
- LORA test mode: batch by LORA to preview style swatches

---

## 📍 Next Focus (as of April 2025)

- Begin genre-aware storytelling via LLM  
- Improve UI feedback during batch runs (step-wise, real-time messages)

---
