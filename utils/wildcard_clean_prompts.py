wildcard_cleanup_templates = {
    "garb": (
        "You're a creative assistant helping clean a wildcard list for image prompt generation.\n"
        "Clean this list of clothing-related wildcard entries for the '{genre}' genre using the following rules. \n"
        "These can be a bit descriptive — up to 12 words max — but should still be modular and not full sentences.\n"
        "- Remove exact duplicates.\n"
        "- Keep variety and creative phrasing.\n"
        "- Avoid punctuation, plurals, or full actions.\n"
        "- Return only the cleaned list — one wildcard per line. No extra commentary or formatting.\n"
    ),
    "setting": (
         "You're a creative assistant helping clean a wildcard list for image prompt generation.\n"
        "You are cleaning short fantasy setting fragments — each one is a phrase or sentence describing a location or vibe.\n"
        "Some entries may be 8–12 words. This is okay as long as they are evocative and visual.\n"
        "- Remove duplicates.\n"
        "- Keep creative descriptions intact.\n"
        "- Avoid full narrative sentences or dialogue.\n"
        "- Return one entry per line.\n"
    ),
    "classes": (
        "You're a creative assistant helping clean a wildcard list for image prompt generation.\n"
        "Clean this list of character class names for an RPG-style generator.\n"
        "- Remove **only exact duplicates**. Keep similar entries unless they are truly redundant.\n"
        "- Preserve entries that are imaginative, unusual, or specific, even if stylistically similar.\n"
        "- Do NOT merge entries unless they're clearly the same. Avoid over-trimming.\n"
        "- Keep everything singular (not plural), 1–6 words max, no punctuation.\n"
        "- Remove full sentences or obvious verbs/actions — but retain vivid phrasing.\n"
        "- Return only the cleaned list — one wildcard per line. No extra commentary or formatting.\n\n"
    ),
    "default": (
        "You're a creative assistant helping clean a wildcard list for image prompt generation.\n"
        "Please clean this list with the following rules:\n"
        "- Remove **only exact duplicates**. Keep similar entries unless they are truly redundant.\n"
        "- Preserve entries that are imaginative, unusual, or specific, even if stylistically similar.\n"
        "- Do NOT merge entries unless they're clearly the same. Avoid over-trimming.\n"
        "- Keep everything singular (not plural), 1–6 words max, no punctuation.\n"
        "- Remove full sentences or obvious verbs/actions — but retain vivid phrasing.\n"
        "- Return only the cleaned list — one wildcard per line. No extra commentary or formatting.\n\n"
    )
}
