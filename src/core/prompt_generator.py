# src/core/prompt_generator.py

import os
import re
import random
from pathlib import Path

from typing import List

# Constants
WILDCARD_ROOT = Path(__file__).parent.parent / "wildcards"
LORA_TAGS_PATH = Path(__file__).parent / "lora_tags.json"

# Patterns
WILDCARD_PATTERN = re.compile(r"(\d+\$\$)?\^\^(.+?)\^\^")
PIPE_PATTERN = re.compile(r"\{(.+?)\}")
LORA_BLOCK_PATTERN = re.compile(r"\{+lora::([^\{\}]+?)\}+")


def convert_custom_tokens(prompt: str) -> str:
    return re.sub(r"\^\^([a-zA-Z0-9_\-/ ]+)\^\^", r"__\1__", prompt)


def load_wildcard_file(path: Path) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def resolve_pipes(text: str) -> str:
    def replacer(match):
        options = match.group(1).split("|")
        return random.choice(options).strip()
    return PIPE_PATTERN.sub(replacer, text)


def resolve_prompt(text: str, genre: str = "fantasy", max_depth: int = 10, resolve_loras: bool = False) -> str:
    if max_depth <= 0:
        return text

    def wildcard_replacer(match):
        prefix, inner = match.groups()
        weighted = int(prefix.replace("$$", "")) if prefix else 1

        path_parts = inner.split("/")
        file_path = (
            WILDCARD_ROOT / genre / f"{inner}.txt"
            if len(path_parts) == 1 and (WILDCARD_ROOT / genre / f"{inner}.txt").exists()
            else WILDCARD_ROOT / "/".join(path_parts)
        ).with_suffix(".txt")

        if not file_path.exists():
            return f"[MISSING:{inner}]"

        options = load_wildcard_file(file_path)
        chosen = random.sample(options, min(weighted, len(options)))

        return ", ".join(
            resolve_prompt(resolve_pipes(c), genre, max_depth - 1)
            for c in chosen
        )

    result = resolve_pipes(text)
    result = WILDCARD_PATTERN.sub(wildcard_replacer, result)

    if resolve_loras:
        result = resolve_lora_blocks(result)

    return result


def resolve_lora_blocks(prompt: str) -> str:
    if not LORA_BLOCK_PATTERN.search(prompt) or not LORA_TAGS_PATH.exists():
        return prompt

    import json
    with open(LORA_TAGS_PATH, "r", encoding="utf-8") as f:
        tags = json.load(f)

    def parse_weight(raw_weight, json_key):
        try:
            if raw_weight == "?":
                return round(random.uniform(0.35, 0.75), 2)
            if "-" in raw_weight:
                low, high = map(float, raw_weight.split("-"))
                return round(random.uniform(low, high), 2)
            return float(raw_weight)
        except:
            return tags.get(json_key, {}).get("preferred_weight", 0.7)

    def replace_block(match):
        parts = match.group(1).split("::")
        path = parts[0].strip()
        override_weight = parts[1].strip() if len(parts) > 1 else None

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


def generate_prompts(template: str, genre: str = "fantasy", batch_size: int = 5) -> List[str]:
    return [resolve_prompt(template, genre=genre, resolve_loras=True) for _ in range(batch_size)]


# 🧪 Dev testing
if __name__ == "__main__":
    test_template = "A ^^Character^^ in a ^^Setting^^ with a {cool|eerie} vibe and {lora::genre_faces::?}"
    results = generate_prompts(test_template, genre="fantasy", batch_size=5)
    for p in results:
        print(p)
