
import os
import random
import re

WILDCARD_ROOT = os.path.join(os.path.dirname(__file__), "..", "wildcards")

WILDCARD_PATTERN = re.compile(r"(\d+\$\$)?\^\^(.+?)\^\^")
PIPE_PATTERN = re.compile(r"\{(.+?)\}")

def load_wildcard_file(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return lines

def resolve_pipes(text):
    def replacer(match):
        options = match.group(1).split("|")
        return random.choice(options).strip()
    return PIPE_PATTERN.sub(replacer, text)

def resolve_prompt(text, genre="fantasy", max_depth=10):
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
            # Try genre first, fallback to common
            genre_path = os.path.join(WILDCARD_ROOT, genre, inner + ".txt")
            common_path = os.path.join(WILDCARD_ROOT, "common", inner + ".txt")
            file_path = genre_path if os.path.exists(genre_path) else common_path
        else:
            file_path = os.path.join(WILDCARD_ROOT, *path_parts) + ".txt"

        if not os.path.exists(file_path):
            return f"[MISSING:{inner}]"

        options = load_wildcard_file(file_path)
        chosen = random.sample(options, min(weighted, len(options)))
        return ", ".join([resolve_prompt(resolve_pipes(c), genre, max_depth - 1) for c in chosen])

    # Replace nested wildcards and pipe sets
    result = resolve_pipes(text)
    result = WILDCARD_PATTERN.sub(wildcard_replacer, result)
    return result
