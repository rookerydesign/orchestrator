import requests
import time 
import anthropic
import os
import streamlit as st
import tiktoken  # optional, for accurate token count (or use estimate)
import re
from utils.wildcard_clean_prompts import wildcard_cleanup_templates



# def clean_wildcards_with_llm(entries, genre="sci-fi", category="humanoids", model="claude"):
#     prompt = (
#         f"You are a prompt enhancement assistant helping clean up a list of wildcards for a {genre} prompt generator.\n"
#         f"Category: {category}\n\n"
#         "Your task is to:\n"
#         "- Remove duplicates or similar entries\n"
#         "- Ensure each is 2–4 words, singular form, no verbs or full sentences\n"
#         "- Keep things creative and in-genre\n\n"
#         "Here is the list to clean:\n\n"
#         + "\n".join(entries) +
#         "\n\nReturn the cleaned list, one entry per line, no numbering or extra text."
#     )

#     # Example using Claude (Anthropic)
#     client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
#     try:
#         response = client.messages.create(
#             model="claude-3-sonnet-20240229",
#             max_tokens=600,
#             temperature=0.7,
#             system="You are a creative and precise wildcard cleaner for an AI prompt toolkit.",
#             messages=[{"role": "user", "content": prompt}]
#         )
#         content = response.content[0].text.strip()
#         cleaned = [line.strip("-•* \n") for line in content.split("\n") if line.strip()]
#         return cleaned
#     except Exception as e:
#         st.error(f"❌ LLM cleanup failed: {e}")
#         return []




# Tokenizer setup (OpenAI encoder)
enc = tiktoken.get_encoding("cl100k_base")

def estimate_token_count(text: str) -> int:
    return len(enc.encode(text))

def sanitize_entry(entry: str) -> str:
    entry = entry.strip()
    entry = entry.replace("\n", " ").replace("\r", "")
    entry = re.sub(r"[^\w\s\-\(\)']", "", entry)
    return entry[:250]

def chunk_by_token_limit(entries, max_tokens=2800):
    chunks = []
    current_chunk = []
    current_tokens = 0

    for entry in entries:
        cleaned = entry.strip()
        if not cleaned:
            continue

        token_count = len(enc.encode(cleaned))  # ← real token count

        # Skip single entries that are too large
        if token_count > max_tokens:
            st.warning(f"⚠️ Entry skipped (too large: {token_count} tokens): {cleaned[:80]}...")
            continue

        # Start a new chunk if limit exceeded
        if current_tokens + token_count > max_tokens:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = [cleaned]
            current_tokens = token_count
        else:
            current_chunk.append(cleaned)
            current_tokens += token_count

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def smart_clean_wildcards(entries, genre, category, token_limit=3000):
    all_cleaned = []
    chunks = chunk_by_token_limit(entries, max_tokens=token_limit)

    st.info(f"📦 Splitting {len(entries)} entries into {len(chunks)} token-aware chunks...")

    for idx, chunk in enumerate(chunks):
        st.info(f"🧠 Cleaning chunk {idx + 1} of {len(chunks)} ({len(chunk)} entries)...")

        try:
            cleaned = clean_wildcards_with_llm(
                chunk,
                genre=genre,
                category=category
            )
            if cleaned:
                all_cleaned.extend(cleaned)
            else:
                st.warning(f"⚠️ Chunk {idx + 1} returned no cleaned entries.")
        except Exception as e:
            st.error(f"❌ Chunk {idx + 1} failed: {e}")

    final_cleaned = sorted(set(e.strip() for e in all_cleaned if e.strip()))
    return final_cleaned



def clean_wildcards_with_llm(entries, genre, category, retries=3, base_delay=1.5, token_limit=3500):
    instruction = wildcard_cleanup_templates.get(category, wildcard_cleanup_templates["default"])
    instruction_text = instruction.format(genre=genre)

    prompt = (
        f"{instruction_text}\n\n"
        f"Wildcard List:\n" + "\n".join(entries) + "\n\nCleaned Wildcards:"
    )

    token_estimate = estimate_token_count(prompt)

    if token_estimate > token_limit:
        st.warning(
            f"⚠️ Skipped this chunk — estimated {token_estimate} tokens exceeds safe limit ({token_limit})."
        )
        return []

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                "http://localhost:1234/v1/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "prompt": prompt,
                    "max_tokens": 900,
                    "temperature": 0.7
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            cleaned_text = result["choices"][0]["text"].strip()
            cleaned = [line.strip("-•* \n") for line in cleaned_text.split("\n") if line.strip()]
            return cleaned
        except requests.exceptions.RequestException as e:
            st.warning(f"⚠️ Local LLM cleanup failed (attempt {attempt}): {e}")
            if attempt < retries:
                time.sleep(base_delay * attempt)
            else:
                st.error("❌ All local cleanup attempts failed.")
                return []
            
