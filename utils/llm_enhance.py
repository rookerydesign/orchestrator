import os
import json
import requests
import streamlit as st
import time
import random





flair_addons = [
    "Use dreamlike, surreal phrasing.",
    "Add cinematic flair and ambient mood.",
    "Inject metaphor and synesthesia.",
    "Introduce mystery or tension.",
    "Describe what is *felt*, not just seen.",
    "Avoid common tropes; make it unusual."
]

extra_flair = random.choice(flair_addons)

def enhance_prompt_with_llm(prompt, genre="", retries=3, base_delay=1.5):
    style_guide = {
        "fantasy": "Add rich, poetic fantasy descriptions, ancient language, and mythical elements.",
        "sci-fi": "Add futuristic tech details, cyberpunk imagery, and scientific depth.",
        "realism": "Use grounded, lifelike details with emotional nuance and believable settings.",
        "horror": "Add dark, eerie atmosphere, unsettling details, monstrous creatures and psychological tension."
    }

    full_prompt = (
    f"Prompt:\n{prompt}\n\n"
    f"Rewrite the prompt above as a {genre} prompt. Expand it with imaginative, emotional, and visual richness. "
    f"Use metaphor, evocative language, immersive world-building. {extra_flair} Avoid clichés. Surprise me.\n\n"
    f"Keep the primary subject or character of the original prompt central to the composition.\n\n"
    f"Enhanced Prompt:"
)


    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                "http://localhost:1234/v1/completions",  # LM Studio uses /completions for raw prompts
                headers={"Content-Type": "application/json"},
                json={
                    "prompt": full_prompt,
                    "max_tokens": 500,
                    "temperature": 1.1,
                    "stop": ["###"]
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["text"].strip()
        except requests.exceptions.RequestException as e:
            st.warning(f"⚠️ GPT enhancement failed (attempt {attempt}): {e}")
            if attempt < retries:
                wait_time = base_delay * attempt
                time.sleep(wait_time)
            else:
                st.warning("⚠️ All GPT enhancement attempts failed. Using raw prompt.")
                return prompt