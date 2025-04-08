import openai
import anthropic
import os
import streamlit as st


def refresh_wildcards_claude(api_key, genre, category, wildcard_dir, n_entries=15):
    client = anthropic.Anthropic(api_key=api_key)

    from utils.wildcard_prompts import get_prompt_template
    prompt = get_prompt_template(genre, category, n=n_entries)


    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=600,
            temperature=1.0,
            system="You are a creative assistant helping generate prompt components for an AI art system.",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.content[0].text
        new_entries = [line.strip("-•* \n") for line in content.strip().split("\n") if line.strip()]
    except Exception as e:
        return [], f"⚠️ Claude API error: {e}"

    # Build wildcard file path
    category_file = os.path.join(wildcard_dir, genre, f"{category}.txt")
    os.makedirs(os.path.dirname(category_file), exist_ok=True)

    # Load existing entries
    if os.path.exists(category_file):
        with open(category_file, "r", encoding="utf-8") as f:
            existing = set(line.strip() for line in f if line.strip())
    else:
        existing = set()

    # Filter new entries
    added_entries = [e for e in new_entries if e not in existing]

    # Append to file
    if added_entries:
        with open(category_file, "a", encoding="utf-8") as f:
            for entry in added_entries:
                f.write(entry + "\n")

    return added_entries, None

def refresh_wildcards_openai(api_key, genre, category, wildcard_dir, n_entries=15):
    client = openai.OpenAI(api_key=api_key)

    prompt = (
        f"Generate {n_entries} unique wildcard entries for the '{category}' category in the '{genre}' genre. "
        f"Each should be 5–12 words long, highly visual, imaginative, and unusual. "
        f"These will be used in a creative prompt generator. Avoid repeating known tropes or clichés.\n\n"
        f"List them as a plain list with no explanations."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=1.1,
        )
        text = response.choices[0].message.content
        new_entries = [line.strip("-•* \n") for line in text.strip().split("\n") if line.strip()]
    except Exception as e:
        return [], f"⚠️ OpenAI error: {e}"

    # Build wildcard file path
    category_file = os.path.join(wildcard_dir, genre, f"{category}.txt")
    os.makedirs(os.path.dirname(category_file), exist_ok=True)

    # Load existing entries
    if os.path.exists(category_file):
        with open(category_file, "r", encoding="utf-8") as f:
            existing = set(line.strip() for line in f if line.strip())
    else:
        existing = set()

    # Filter new entries
    added_entries = [e for e in new_entries if e not in existing]

    # Append to file
    if added_entries:
        with open(category_file, "a", encoding="utf-8") as f:
            for entry in added_entries:
                f.write(entry + "\n")

    return added_entries, None