
import os
import json
import requests
from pathlib import Path
import re
from bs4 import BeautifulSoup

# Configuration
LORA_DIR = "F:/03_Gen AI tools/webui_forge_cu121_torch231/webui/models/Lora"  # Adjust this path if needed 
OUTPUT_FILE = "lora_tags.json"
LLM_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_NAME = "gryphe.mythomax-l2-13b"
MAX_PROMPTS = 3

HEADERS = {
    "Content-Type": "application/json"
}

SYSTEM_PROMPT = "You are a visual style tagging assistant for AI art models. Always respond in JSON format only."

USER_TEMPLATE = """
LORA Metadata Summary:

- Description: "{description}"
- Notes: "{notes}"
- Trained Words: {trained_words}
- Example Prompts:
{example_prompts}

Please return:
{{
  "genre": [],
  "style": [],
  "subject": [],
  "tone": []
}}
"""

def clean_html(text):
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()

def extract_prompts_from_dict(data, found=None):
    if found is None:
        found = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                extract_prompts_from_dict(v, found)
            elif isinstance(v, str) and "prompt" in k.lower():
                found.append(v.strip())
    elif isinstance(data, list):
        for item in data:
            extract_prompts_from_dict(item, found)
    return found

def extract_metadata(json_path, info_path):
    # Load both files
    with open(json_path, "r", encoding="utf-8", errors="ignore") as f:
        json_data = json.load(f)

    with open(info_path, "r", encoding="utf-8", errors="ignore") as f:
        info_data = json.load(f)

    # Pull and clean
    description = clean_html(info_data.get("description", "") or json_data.get("description", ""))
    notes = clean_html(json_data.get("notes", ""))
    trained_words = info_data.get("trainedWords", [])

    # Extract prompts
    raw_prompts = extract_prompts_from_dict(info_data)
    unique_prompts = []
    seen = set()
    for p in raw_prompts:
        cleaned = re.sub(r"<lora:[^>]+>", "", p).strip()
        if cleaned not in seen and len(cleaned) > 15:
            unique_prompts.append(f'- "{cleaned}"')
            seen.add(cleaned)
        if len(unique_prompts) >= MAX_PROMPTS:
            break

    return {
        "description": description,
        "notes": notes,
        "trained_words": trained_words,
        "example_prompts": "\n".join(unique_prompts)
    }

def send_to_llm_chat(prompt):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }

    print(f"[🧠] Sending prompt to LLM (first 500 chars):\n{prompt[:500]}...\n")

    response = requests.post(LLM_API_URL, headers=HEADERS, json=payload, timeout=60)

    if not response.ok:
        print(f"[!] LLM API Error {response.status_code}: {response.text}")
        response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"].strip()

def find_lora_pairs(base_path):
    lora_pairs = []
    for root, dirs, files in os.walk(base_path):
        json_map = {}
        info_map = {}

        for f in files:
            if f.endswith(".json") and not f.endswith(".civitai.info"):
                base = f[:-5]  # strip .json
                json_map[base] = f
            elif f.endswith(".civitai.info"):
                base = f[:-13]  # strip .civitai.info
                info_map[base] = f

        matched_stems = set(json_map.keys()) & set(info_map.keys())

        for stem in matched_stems:
            json_path = os.path.join(root, json_map[stem])
            info_path = os.path.join(root, info_map[stem])
            lora_pairs.append((stem, Path(root), json_path, info_path))

    print(f"[🧪] Found {len(lora_pairs)} LORA pairs:")
    for stem, folder, _, _ in lora_pairs:
        print(f" - {folder / stem}")

    return lora_pairs


def main():
    # Load existing tag data if available
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            lora_tags = json.load(f)
    else:
        lora_tags = {}

    print(f"[📂] Loaded {len(lora_tags)} existing tags.")

    lora_items = find_lora_pairs(LORA_DIR)
    current_keys = []
    new_tags = 0
    skipped = 0

    print(f"[🔎] Found {len(lora_items)} LORA pairs to check...")

    for stem, folder, json_path, info_path in lora_items:
        key = str(folder.relative_to(LORA_DIR) / stem)
        current_keys.append(key)

        if key in lora_tags:
            print(f"[⏩] Skipping already-tagged LORA: {key}")
            skipped += 1
            continue

        print(f"[🔍] Tagging new LORA: {key}")
        meta = extract_metadata(json_path, info_path)

        user_prompt = USER_TEMPLATE.format(
            description=meta["description"],
            notes=meta["notes"],
            trained_words=meta["trained_words"],
            example_prompts=meta["example_prompts"]
        )

        try:
            tag_json = send_to_llm_chat(user_prompt)
            tags = json.loads(tag_json)
            lora_tags[key] = tags
            new_tags += 1
            print(f"[✓] Tagged {key}")
        except Exception as e:
            print(f"[!] Error tagging {stem}: {e}")

    # Clean out any tags for LORAs that no longer exist
    cleaned_tags = {k: v for k, v in lora_tags.items() if k in current_keys}
    removed = len(lora_tags) - len(cleaned_tags)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        json.dump(cleaned_tags, out, indent=2)

    print("✅ Tagging session complete.")
    print(f"   • Total scanned  : {len(lora_items)}")
    print(f"   • Skipped        : {skipped}")
    print(f"   • Newly tagged   : {new_tags}")
    print(f"   • Removed stale  : {removed}")
    print(f"   • Final tag count: {len(cleaned_tags)}")

if __name__ == "__main__":
    main()


