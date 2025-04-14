# src/core/prompt_generator.py

import os
import random
import re
import json
from pathlib import Path
from src.utils.config_loader import load_config




# --- Constants & Regex Patterns ---
config = load_config()
WILDCARD_ROOT = Path(config["paths"]["wildcard_folder"])

LORA_TAGS_PATH = Path(__file__).parent / "lora_tags.json"

WILDCARD_PATTERN = re.compile(r"(\d+\$\$)?\^\^(.+?)\^\^")
PIPE_PATTERN = re.compile(r"\{(.+?)\}")
LORA_BLOCK_PATTERN = re.compile(r"\{+lora::([^\{\}]+?)\}+")

# --- Wildcard File Loader ---
def load_wildcard_file(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

# --- Pipe Syntax Handler: {option|option|option} ---
def resolve_pipes(text: str) -> str:
    return PIPE_PATTERN.sub(lambda m: random.choice(m.group(1).split("|")).strip(), text)

# --- Main Prompt Resolver ---
def resolve_prompt(text: str, genre: str = "fantasy", max_depth: int = 10, resolve_loras: bool = False) -> str:
    if max_depth <= 0:
        return text

    def wildcard_replacer(match):
        prefix, inner = match.groups()
        weighted = int(prefix.replace("$$", "")) if prefix else 1

        # Resolve file path based on genre/common
        path_parts = inner.split("/")
        if len(path_parts) == 1:
            genre_path = WILDCARD_ROOT / genre / f"{inner}.txt"
            file_path = genre_path if genre_path.exists() else None

            if not file_path:
                return f"[MISSING:{inner}]"

        else:
            file_path = WILDCARD_ROOT.joinpath(*path_parts).with_suffix(".txt")

        if not file_path.exists():
            print(f"[❌ Missing wildcard file] → {file_path}")
            return f"[MISSING:{inner}]"

        options = load_wildcard_file(file_path)
        chosen = random.sample(options, min(weighted, len(options)))

        return ", ".join(
            resolve_prompt(resolve_pipes(c), genre, max_depth - 1)
            for c in chosen
        )

    # 1. Resolve pipes ({} syntax)
    result = resolve_pipes(text)

    # 2. Resolve wildcards (^^ ^^ syntax)
    result = WILDCARD_PATTERN.sub(wildcard_replacer, result)

    # 3. LORA tag resolution
    if resolve_loras:
        result = resolve_lora_blocks(result)

    return result

# --- LORA Block Handler ---
def resolve_lora_blocks(prompt: str) -> str:
    if not LORA_BLOCK_PATTERN.search(prompt) or not LORA_TAGS_PATH.exists():
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
        parts = match.group(1).split("::")
        path = parts[0].strip()
        override_weight = parts[1].strip() if len(parts) == 2 else None

        wildcard_path = WILDCARD_ROOT / f"{path}.txt"
        if not wildcard_path.exists():
            return f"[MISSING:{path}]"

        candidates = load_wildcard_file(wildcard_path)
        if not candidates:
            return "[EMPTY_LORA_FILE]"

        activation = random.choice(candidates)
        json_key = path.replace("/", "\\\\") + "\\" + activation
        weight = parse_weight(override_weight, json_key)

        return f"<lora:{activation}:{weight}>"

    return LORA_BLOCK_PATTERN.sub(replace_block, prompt)

# --- Final Public Entry Point ---
def generate_prompts(template: str, genre: str = "fantasy", batch_size: int = 5) -> list[str]:
    return [resolve_prompt(template, genre=genre, resolve_loras=True) for _ in range(batch_size)]
