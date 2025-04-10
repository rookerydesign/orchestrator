wildcard_cleanup_templates = {
    "garb": (
        "You're a creative assistant helping clean a wildcard list for image prompt generation.\n"
        "These are clothing-related wildcard entries for the '{genre}' genre. They can be descriptive — up to ~20 words — but should still be modular and not full scenes.\n"
        "Your goals:\n"
        "- Keep each entry modular and evocative — up to 20 words max.\n"
        "- If an entry is **too long or too verbose**, **rewrite** it into a shorter, punchier phrase (do not delete).\n"
        "- Only delete true duplicates or full narrative sentences.\n"
        "- Do NOT merge distinct variations — similar items with different details should remain.\n"
        "- Keep imaginative phrases — poetic, eerie, textured, strange.\n"
        "\n"
        "Return only the cleaned or rewritten list — one entry per line. No commentary, no formatting, no numbering.\n"
    ),
    "setting": (
         "You're a creative assistant helping clean a wildcard list for image prompt generation.\n"
        "You are cleaning short '{genre}' setting fragments — They can be descriptive — up to ~20 words — but should still be modular and not full scenes.\n"
        "Instructions:\n"
        "- Keep each entry modular and evocative — up to 20 words max.\n"
        "- If an entry is **too long or too verbose**, **rewrite** it into a shorter, punchier phrase (do not delete).\n"
        "- Only delete true duplicates or full narrative sentences.\n"
        "- Do NOT merge distinct variations — similar items with different details should remain.\n"
        "- Preserve evocative, strange, or eerie descriptions, even if abstract.\n"
        "\n"
        "Return only the cleaned or rewritten list — one entry per line. No commentary, no formatting, no numbering.\n"
    ),
    "classes": (
        "You're a creative assistant helping clean a wildcard list for image prompt generation.\n"
        "Clean this list of '{genre}' character class names for an RPG-style generator.\n"
        "Instructions:\n"
        "- Keep each entry modular and evocative — up to 5 words max.\n"
        "- If an entry is **too long or too verbose**, **rewrite** it into a shorter, punchier phrase (do not delete).\n"
        "- Only delete true duplicates or full narrative sentences.\n"
        "- Do NOT merge distinct variations — similar items with different details should remain.\n"
        "- Preserve evocative, strange, or eerie descriptions, even if abstract.\n"
        "\n"
        "Return only the cleaned or rewritten list — one entry per line. No commentary, no formatting, no numbering.\n"
    ),    
    "default": (
        "You're a creative assistant helping clean a wildcard list for image prompt generation.\n"
        "Please clean this list with the following rules:\n"
        "- Keep each entry modular and evocative — up to 5 words max.\n"
        "- If an entry is **too long or too verbose**, **rewrite** it into a shorter, punchier phrase (do not delete).\n"
        "- Only delete true duplicates or full narrative sentences.\n"
        "- Do NOT merge distinct variations — similar items with different details should remain.\n"
        "- Preserve evocative, strange, or eerie descriptions, even if abstract.\n"
        "\n"
        "Return only the cleaned or rewritten list — one entry per line. No commentary, no formatting, no numbering.\n"
    )
}
