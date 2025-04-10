import re
import json
import requests
import streamlit as st
import time
import random




def load_flair_addons(path="wildcards/common/flair_addons.txt"):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]



flair = random.choice(load_flair_addons())

def enhance_prompt_with_llm(prompt, genre="", retries=3, base_delay=1.5):
    style_guide = {
        "fantasy": "Describe rich dark fantasy characters in a scene, using poetic language, ancient influences, occult and mystical elements.",
        "sci-fi": "Describe futuristic characters in a scene with advanced tech, cyberpunk imagery, and speculative design.",
        "realism": "Use grounded, visual details to describe a character in a scene — clothing, expression, posture, setting, weather, texture — evoking real-world moments.",
        "horror": "Describe unsettling visual scenes and characters using eerie lighting, grotesque details, shadowed elements, and psychological discomfort."
    }

    full_prompt = (
    f"You are enhancing prompts for an AI image generation tool.\n"
    f"Rewrite and extend the prompt below into a visually rich, detailed {genre} scene. "
    f"{style_guide[genre]} Avoid narrative storytelling — describe what should be *seen* in the image.\n"
    f"Use evocative, cinematic, and symbolic language to bring out mood, atmosphere, and material detail.\n"
    f"Do NOT write a backstory or inner thoughts. Focus only on visual elements.\n"
    f"Keep the original subject central. Do not list items — describe the full visual composition.\n"
    f"Do not include any headers like 'Enhanced Prompt', 'Output', or 'Result'. Output only the rewritten text — nothing else.\n\n"
    f"Original Prompt:\n{prompt}\n\n"
)


    def strip_llm_headers(text: str) -> str:
        # Remove any leading label like "Enhanced Prompt:", "Output:", etc.
        return re.sub(r"^(Enhanced Prompt|Extended Prompt|Output|Rewritten Prompt)\s*:\s*", "", text.strip(), flags=re.IGNORECASE)


    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                "http://localhost:1234/v1/completions",  # LM Studio uses /completions for raw prompts
                headers={"Content-Type": "application/json"},
                json={
                    "prompt": full_prompt,
                    "max_tokens": 600,
                    "temperature": 0.9,
                    "stop": ["###"]
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            raw_output = result["choices"][0]["text"].strip()
            cleaned_output = strip_llm_headers(raw_output)
            return cleaned_output
        except requests.exceptions.RequestException as e:
            st.warning(f"⚠️ GPT enhancement failed (attempt {attempt}): {e}")
            if attempt < retries:
                wait_time = base_delay * attempt
                time.sleep(wait_time)
            else:
                st.warning("⚠️ All GPT enhancement attempts failed. Using raw prompt.")
                return prompt