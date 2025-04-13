# 🔮 Orchestrator — Future Development Plans

A living roadmap for future enhancements, experiments, and architecture upgrades across the Orchestrator ecosystem.

---

## 🧱 Phase 0: Foundational Refactor & Gradio UI Upgrade *(Next Priority)*

### ✅ Goal:
Replace the Streamlit interface with a modern, modular Gradio UI and refactor the app into composable Python functions for better long-term maintainability.

### 🔧 Tasks:
- Port existing features to Gradio (wildcard prompt engine, LORA matching, batch submission, etc.)
- Refactor core logic into reusable modules:
  - `prompt_generator.py`
  - `lora_selector.py`
  - `forge_dispatcher.py`
  - `config.py` / `utils.py`
- Organize UI layout with:
  - Tabs for generation, batch tools, and config
  - Live preview outputs and payload summaries
  - Upload/drop-zone for `.json` prompt files

### ⏭️ Next Steps:
- Scaffold new folder structure for code organization
- Build MVP Gradio interface with a working prompt > image flow
- Begin modularizing each feature into separate functions

---

## 🧩 Modular Pipeline Execution

Allow generation to flow through customizable steps, either defined manually or visually:

- Define each stage of the workflow in JSON:
  ```json
  [
    { "id": "wildcardGen", "type": "generatePrompt" },
    { "id": "enhancePrompt", "type": "llmEnhance" },
    { "id": "matchLORA", "type": "selectLoras" },
    { "id": "submitToForge", "type": "dispatch" }
  ]
  ```
- Support skipping steps, rerunning individual stages, or loading from saved pipeline configs
- Eventually allow UI-based pipeline construction

---

## 🧬 Character & Storyline Profiles

Introduce persistent narrative and visual configuration profiles stored as `.json` or `.yaml`.

### Profile Attributes:
- `character`, `setting`, `style`, `backstory`
- Preferred wildcard weights
- Pre-selected or weighted LORAs

Use profiles to:
- Preload prompt fields
- Influence randomization patterns
- Feed LLM memory or world model logic

---

## 📁 Smart Folder Monitoring

Enable lightweight automation for re-indexing LORA metadata:

- Monitor specified folders for `.safetensors` file changes
- Debounce changes with ~2s delay
- Automatically:
  - Re-parse `.info` and `.json` files
  - Flag missing metadata
  - Notify UI of new LORAs scanned

---

## 🧠 LLM Memory / World Models

Introduce evolving session-based prompt memory for thematic and story coherence.

### Early Features:
- Store previous prompt metadata, tags, and character info
- Inject into prompt enhancement as optional context
- Enable "continue scene" or "develop character" prompts

---

## 🖼️ Vision Model Feedback Loop

Use CLIP, BLIP, or similar models to evaluate outputs and refine prompt systems.

### Ideas:
- Extract post-image tags and compare to prompt goals
- Score:
  - Tag fulfillment
  - Style accuracy
- Track prompt component effectiveness over time
- Auto-adjust wildcard weights based on success rates

---

## 🔗 Integration Ideas

### ComfyUI / Forge:
- Export prompt formats directly to ComfyUI-compatible templates
- Optional “Send to Forge” or “Send to Comfy” toggle per prompt

### Fullstack App:
- Post job outputs + metadata to your local gallery UI
- Sync favorite images with React frontend via Flask API

---

## 🛠️ Wishlist & Long-Term Ideas

- Genre-aware prompt templates
- Tag-based LORA filtering and scoring
- Batch LORA test mode for style previews
- Dynamic prompt conditioning (vision-informed adjustments)
- API mode for external trigger dispatches (future proofing)

---

## 🌟 Dev Milestones Summary

| Milestone                       | Status       |
|--------------------------------|--------------|
| Gradio UI + Core Refactor      | 🔜 Starting  |
| Modular Function Pipeline      | 🟡 Planned   |
| Profile System                 | 🟡 Planned   |
| Vision Feedback Loop           | 🟡 Planned   |
| ComfyUI / Gallery Integration  | 🟡 Planned   |

---
