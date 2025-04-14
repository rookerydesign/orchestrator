# src/core/llm_interface.py

import re
import json
import requests
import time
import random

style_guide = {
    "fantasy": "Describe rich fantasy characters in a scene, using ancient influences, occult and mystical elements.",
    "sci-fi": "Describe science-fiction characters in a scene with advanced tech, cyberpunk imagery, and speculative design.",
    "realism": "Use grounded, visual details to describe a character in a scene — clothing, expression, posture, setting, weather, texture — evoking real-world moments.",
    "horror": "Describe unsettling visual scenes and characters using eerie lighting, grotesque details, shadowed elements, and psychological discomfort.",
    "characters": "Focus on portraiture, facial expressions, costumes, ethnic diversity, gender styles, and material detail.",
    "nsfw": "Use adult themes with artistic flair, focusing on mood, sensuality, composition, and visual texture. No narration."
}


def enhance_prompt_with_llm(prompt, genre="", retries=3, base_delay=1.5):
    full_prompt = (
        f"You are enhancing prompts for an AI image generation tool.\n"
        f"Rewrite the prompt below into a visually rich, detailed {genre} character exploration. "
        f"{style_guide.get(genre, '')} Avoid narrative storytelling — describe what should be *seen* in the image.\n"
        f"Use evocative, cinematic, and symbolic language to bring out mood, atmosphere, and material details like appearance, color and texture.\n"
        f"Do NOT write a backstory or inner thoughts. Focus only on visual elements.\n"
        f"Limit the output to 175 words or fewer. Focus on clarity, composition, and visual impact.\n\n"
        f"Do not include any formatting or headers like 'Enhanced Prompt', 'Output', 'Rewritten Text' or 'Result'. Output only the rewritten text — nothing else.\n"
        f"Original Prompt:\n{prompt}\n\n"
    )

    def strip_llm_headers(text: str) -> str:
        """
        Remove unwanted headers or prefixes that local LLMs may prepend
        to an enhanced prompt, like 'Output:', 'Enhanced Prompt:', etc.
        """
        # Trim whitespace and split into lines
        lines = text.strip().splitlines()

        # Remove any line that looks like a header (first line)
        if lines and re.match(r"^\s*(Enhanced|Rewritten|Output|Result|Prompt)\s*[:\-]*", lines[0], re.IGNORECASE):
            lines = lines[1:]

        # Re-join the cleaned lines
        cleaned = "\n".join(line.strip() for line in lines if line.strip())

        return cleaned
    
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                "http://localhost:1234/v1/completions",
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
            return strip_llm_headers(raw_output)
        except requests.exceptions.RequestException as e:
            print(f"[⚠️ GPT Enhancement Failed - Attempt {attempt}] {e}")
            time.sleep(base_delay * attempt)
    print("⚠️ All LLM enhancement attempts failed. Returning original prompt.")
    return prompt
