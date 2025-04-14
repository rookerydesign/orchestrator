
import os
import random
import re
import json
import yaml

WILDCARD_ROOT = os.path.join(os.path.dirname(__file__), "..", "wildcards")

WILDCARD_PATTERN = re.compile(r"(\d+\$\$)?\^\^(.+?)\^\^")
PIPE_PATTERN = re.compile(r"\{(.+?)\}")

LORA_TAGS_PATH = os.path.join(os.path.dirname(__file__), "lora_tags.json")
LORA_BLOCK_PATTERN = re.compile(r"\{+lora::([^\{\}]+?)\}+")


def load_wildcard_file(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return lines

def resolve_pipes(text):
    def replacer(match):
        options = match.group(1).split("|")
        return random.choice(options).strip()
    return PIPE_PATTERN.sub(replacer, text)

def resolve_prompt(text, genre="fantasy", max_depth=10, resolve_loras=False):
    if max_depth <= 0:
        return text  # prevent infinite recursion

    def wildcard_replacer(match):
        prefix, inner = match.groups()
        weighted = 1
        if prefix:
            try:
                weighted = int(prefix.replace("$$", ""))
            except ValueError:
                pass

        # Resolve path
        path_parts = inner.split("/")
        if len(path_parts) == 1:
            genre_path = os.path.join(WILDCARD_ROOT, genre, inner + ".txt")
            common_path = os.path.join(WILDCARD_ROOT, "common", inner + ".txt")
            file_path = genre_path if os.path.exists(genre_path) else common_path
        else:
            file_path = os.path.join(WILDCARD_ROOT, *path_parts) + ".txt"

        if not os.path.exists(file_path):
            return f"[MISSING:{inner}]"

        options = load_wildcard_file(file_path)
        chosen = random.sample(options, min(weighted, len(options)))

        return ", ".join(
    filter(None, map(str, [
        resolve_prompt(resolve_pipes(c), genre, max_depth - 1)
        for c in chosen
    ]))
)

    # 1. Pipes
    result = resolve_pipes(text)

    # 2. Wildcards
    result = WILDCARD_PATTERN.sub(wildcard_replacer, result)

    # 3. LORA resolution only if allowed
    if resolve_loras:
        result = resolve_lora_blocks(result)

    return result


def resolve_lora_blocks(prompt):
    """
    Process {{lora::path::weight}} blocks in prompts:
    1. Extract the path to a wildcard file
    2. Select a random entry from that file
    3. Process optional weight or weight range
    4. Return formatted <lora:name:weight> tags
    """

    if not LORA_BLOCK_PATTERN.search(prompt):
        
        return prompt

    if not os.path.exists(LORA_TAGS_PATH):
       
        return prompt

    with open(LORA_TAGS_PATH, "r", encoding="utf-8") as f:
        tags = json.load(f)

    def parse_weight(raw_weight, json_key):
        if raw_weight == "?":
            return round(random.uniform(0.35, 0.75), 2)

        if "-" in raw_weight:
            try:
                low, high = map(float, raw_weight.split("-"))
                return round(random.uniform(low, high), 2)
            except:
                
                return 0.7

        try:
            return float(raw_weight)
        except:
            return tags.get(json_key, {}).get("preferred_weight", 0.7)

    def replace_block(match):
        raw = match.group(1)
        parts = raw.split("::")

        if len(parts) < 1:
            print("[❌ BAD_LORA_BLOCK]:", raw)
            return "[BAD_LORA_BLOCK]"

        path = parts[0].strip()
        override_weight = parts[1].strip() if len(parts) == 2 else None

        wildcard_path = os.path.join(WILDCARD_ROOT, path + ".txt")

        if not os.path.exists(wildcard_path):
            return f"[MISSING:{path}]"

        with open(wildcard_path, "r", encoding="utf-8") as f:
            candidates = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        if not candidates:
            return "[EMPTY_LORA_FILE]"

        activation = random.choice(candidates)
        json_key = path.replace("/", "\\\\") + "\\" + activation
        weight = parse_weight(override_weight, json_key)

        print(f"[✅ LORA SELECTED]: {activation} @ {weight}")
        return f"<lora:{activation}:{weight}>"

    return LORA_BLOCK_PATTERN.sub(replace_block, prompt)
