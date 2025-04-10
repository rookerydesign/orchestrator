# utils/wildcard_prompts.py

wildcard_prompt_templates = {
    "sci-fi": {
        "humanoids": (
            "Imagine a catalog of visionary sci-fi beings. Generate {n} unique humanoid concepts, each a singular subject or archetype. "
            "Limit to 2–4 words. No plurals, actions, settings, or full sentences — just rich, evocative character ideas like 'Bioplasmic avatar' or 'Temporal priest'. "
            "Respond with a plain, line-separated list — no numbering, no titles, no formatting. Be unusual and original."
        ),
        "garb": (
            "Create {n} futuristic clothing or wearable gear concepts suitable for a sci-fi universe. Each should be visually unique, singular, and under 20 words. "
            "Think modular armor, biotech robes, neon shrouds — richly descriptive yet concise. Avoid verbs or full sentences. "
            "Return a plain list only — no formatting or numbering."
        ),
        "holding": (
            "List {n} imaginative sci-fi handheld items, relics, or tools. Each should be a singular concept like 'plasma scepter', 'data wand', or 'gravity seed'. "
            "Avoid phrases or scenes. Make them feel modular and futuristic. Output only a plain, unnumbered list."
        ),
        "setting": (
            "Generate {n} vivid sci-fi setting fragments, each between 5–15 words — like 'chrome ruins beneath twin suns' or 'orbital citadel over a dying world'. "
            "Focus on mood, texture, and location. No full scenes or actions. Output only a raw, line-separated list — no numbering or headers."
        ),
        "classes": (
            "Invent {n} futuristic role or class titles — each under 4 words, singular, and flavorful. "
            "Examples: 'Neural Exorcist', 'Temporal Cartographer'. Avoid tech babble or generic roles. "
            "Respond only with a plain list — no numbers or formatting."
        ),
    },
    "fantasy": {
        "humanoids": (
            "Generate {n} poetic and mythical fantasy humanoid archetypes. Each should be a singular subject like 'Thornbound oracle', 'Runeblood knight'. "
            "No settings or actions. Keep them lyrical and under 5 words. Output only a line-separated list — no formatting."
        ),
        "garb": (
            "List {n} fantasy clothing items or accessories — singular and richly described in texture and mood. "
            "Examples: 'tattered mooncloak stitched with silver runes', 'bloodwoven tabard soaked in spell-ink'. "
            "Avoid modern terms or plain items. Output a line-separated list with no numbering or extra formatting."
        ),
        "holding": (
            "Create {n} short fantasy item names that evoke power or mystery — like 'soulglass dagger', 'ember lantern'. "
            "Keep entries 2–4 words. Avoid plurals or full phrases. Return a plain, line-separated list only — no formatting or extra explanation."
        ),
        "setting": (
            "Generate {n} short, moody fantasy setting fragments (5–15 words), e.g., 'hallowed ruins in black mist', 'sunken crypt beneath cursed orchard'. "
            "Focus on mood, mysticism, and setting. Output only the raw list — no numbering or formatting."
        ),
        "classes": (
            "Invent {n} fantasy profession or class titles. Each should be singular and under 4 words. "
            "Examples: 'Witchhunter', 'Veilforged Bard', 'Cryptborn Alchemist'. Output a plain, unnumbered list only."
        ),
    },
    "horror": {
        "humanoids": (
            "Conjure {n} twisted, singular horror character types. Keep it uncanny, grotesque, or psychologically disturbing — like 'hollow priest', 'scarred medium'. "
            "Avoid scenes or plurals. Use rich, unsettling wording. Only return a line-separated list, no formatting or headers."
        ),
        "garb": (
            "List {n} horror-themed garments or accessories. Each should suggest decay, ritual, or menace — e.g., 'charnel veil soaked in whispers', 'stained cassock stitched with teeth'. "
            "Keep them short but richly disturbing. No modern fashion. Output only the raw list — no numbering, formatting or extras."
        ),
        "holding": (
            "Invent {n} eerie or arcane handheld items — short, mysterious, and chilling. Examples: 'withered totem', 'grinning key', 'whisperbox'. "
            "Keep entries 2–4 words. Return a plain list only — no formatting, no numbers."
        ),
        "setting": (
            "Generate {n} disturbing horror setting fragments (5–15 words) — like 'asylum cellar beneath dripping stone'. "
            "Short, surreal, and atmospheric. Respond only with a plain, unnumbered list."
        ),
        "classes": (
            "List {n} singular horror occupations or archetypes — e.g., 'Flesh-scribe', 'Plague Whisperer'. Avoid heroic tropes. Max 3 words. "
            "Respond with a plain list only — no headers or numbering. Embrace the eerie."
        ),
    },
    "realism": {
        "humanoids": (
            "Create {n} grounded female character portrayals for a realism-based universe. "
            "Each entry should describe a person with rich, visual traits or emotional tone — like 'Moody and pensive attractive woman with glasses'. "
            "Entries should be singular, 5–12 words, and evoke mood, age, or condition. "
            "Do not use fantasy or sci-fi language. Avoid job titles only — these should feel like vivid, realistic mini-character descriptions. "
            "Return only a line-separated list. No numbering or extra formatting."
        ),
        "garb": (
            "List {n} realistic complete female clothing outfits. Each should be singular and simply described — e.g., 'High-top Sneakers, Sporty Striped Socks, Skater Skirt, Cropped Hoodie'. "
            "Avoid fantasy or surreal elements. No actions or adjectives beyond function. Return a clean, unnumbered list."
        ),
        "holding": (
            "Generate {n} handheld everyday or occupational objects — like 'toolbox', 'field notes', or 'worn radio'. "
            "Avoid modern brand names or tech. Output only a plain list, no numbering."
        ),
        "setting": (
            "Generate {n} short, atmospheric setting fragments grounded in realism. "
            "Each should evoke mood, time, and place — like 'snow-drifted checkpoint at dawn' or 'abandoned diner under buzzing light'. "
            "Think cinematic and emotionally charged — locations with texture, weather, decay, isolation, tension, or routine. "
            "Keep each under 15 words. Avoid fantasy or surreal elements. "
            "Return a raw, line-separated list with no numbering or formatting."
        ),
        "classes": (
            "Provide {n} grounded profession titles — e.g., 'Surveillance Officer', 'War Photographer'. Avoid sci-fi or fantasy flavor. "
            "Output a clean, unnumbered list only."
        ),
    },
    "default": {
        "default": (
            "Generate {n} creative and modular wildcard entries suitable for imaginative prompt construction. "
            "Each should be 2–6 words max, expressive, and standalone. No full scenes. No plurals. "
            "Only return a plain line-separated list — no formatting, no numbering, no titles."
        )
    }
}

def get_prompt_template(genre, category, n=15):
    try:
        template = wildcard_prompt_templates[genre][category]
    except KeyError:
        template = wildcard_prompt_templates.get("default", {}).get("default", "")
    
    return template.format(n=n)
