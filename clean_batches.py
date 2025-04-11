# This script processes batch files in a specified directory, cleaning up the <lora:...> tags
# by removing the path prefix and ensuring the format is consistent. It can also create backup files    


import os
import json
import re

BATCH_DIR = "saved_batches"  # or wherever your batch files live
BACKUP = True  # Set to True to save modified versions to new files

# Pattern to strip path prefix from <lora:...> blocks
LORA_TAG_RE = re.compile(r"<lora:(.*?/)+(.*?)>")

def clean_lora_paths(prompt: str) -> str:
    def replace_lora(match):
        parts = match.group(1).split("/")
        name = parts[-1]
        weight = match.group(2)
        return f"<lora:{name}:{weight}>"

    return re.sub(r"<lora:([^:]+):([\d.]+)>", replace_lora, prompt)


def process_batch_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        batch = json.load(f)

    modified = False
    for job in batch:
        prompt = job["payload"]["data"][1]
        cleaned_prompt = clean_lora_paths(prompt)
        if cleaned_prompt != prompt:
            job["payload"]["data"][1] = cleaned_prompt
            modified = True

    if modified:
        if BACKUP:
            new_path = file_path.replace(".json", "_fixed.json")
        else:
            new_path = file_path

        with open(new_path, "w", encoding="utf-8") as f:
            json.dump(batch, f, indent=2)
        print(f"✅ Fixed: {os.path.basename(file_path)}")
    else:
        print(f"➖ No changes needed: {os.path.basename(file_path)}")

def run():
    files = [f for f in os.listdir(BATCH_DIR) if f.endswith(".json")]
    if not files:
        print("No batch files found.")
        return

    for filename in files:
        full_path = os.path.join(BATCH_DIR, filename)
        process_batch_file(full_path)

if __name__ == "__main__":
    run()
