# utils/wildcard_prompts.py

wildcard_prompt_templates = {
    "sci-fi": {
        "humanoids": (
            "Imagine a catalog of visionary sci-fi beings. Generate {n} unique humanoid concepts, each a singular subject or archetype. "
            "Limit to 2–4 words. No plurals, actions, settings, or full sentences — just rich, evocative character concepts like 'Bioplasmic avatar' or 'Temporal priest'."
        ),
        "garb": (
            "Create {n} short, futuristic clothing or wearable gear terms suitable for a sci-fi universe. Each should be under 12 words, singular, and visually unique. "
            "Avoid verbs or lengthy sentences "
        ),
        "holding": (
            "List {n} singular sci-fi handheld items, weapons, or relics. Make each imaginative and modular — e.g., 'plasma scepter', 'data wand', or 'gravity seed'. "
            "Avoid phrases or scenes. Each should be short and stand alone."
        ),
        "setting": (
            "Generate {n} vivid sci-fi setting fragments (5–15 words) like 'chrome ruins beneath twin suns' or 'orbital citadel over a dying world'. "
            "No full scenes — just mood-rich, location-style phrases suitable for use as wildcards. Dont number them, just return a line separated list."
        ),
        "classes": (
            "Invent {n} futuristic role or class titles. Keep them under 4 words, singular, and flavorful — e.g., 'Neural Exorcist', 'Temporal Cartographer'. "
            "Avoid tech babble or generic titles."
        ),
    },
    "fantasy": {
        "humanoids": (
            "Generate {n} poetic and mythical fantasy humanoid archetypes. Each should be a singular subject (e.g., 'Thornbound oracle', 'Runeblood knight'). "
            "No settings or actions. Keep them lyrical and under 5 words."
        ),
        "garb": (
            "List {n} fantasy clothing items or accessories — singular, rich in texture and era-specific mood. "
            "E.g., 'tattered mooncloak', 'runed mantle', 'bloodwoven tabard'. Avoid generic or modern terms."
        ),
        "holding": (
            "Create {n} short fantasy item names that evoke power or mystery — like 'soulglass dagger', 'ember lantern'. "
            "Keep entries 2–4 words, avoid actions or plurals."
        ),
        "setting": (
            "Generate {n} short, moody fantasy setting phrases — e.g., 'hallowed ruins in black mist'. "
            "No full scenes. Think in fragments rich with mood and symbolism."
        ),
        "classes": (
            "Invent {n} fantasy profession or class titles. Each should be singular and under 4 words. "
            "Examples: 'Witchhunter', 'Veilforged Bard', 'Cryptborn Alchemist'."
        ),
    },
    "horror": {
        "humanoids": (
            "Conjure {n} twisted, singular horror character types. Keep it uncanny, grotesque, or psychologically disturbing — e.g., 'hollow priest', 'scarred medium'. "
            "Avoid full phrases. No plurals or scenes."
        ),
        "garb": (
            "List {n} singular horror-themed garments or accessories. Each should hint at decay, ritual, or menace. "
            "E.g., 'charnel veil', 'stained cassock'. Max 4 words."
        ),
        "holding": (
            "Invent {n} eerie or arcane handheld items — short, mysterious, and chilling. Think 'withered totem', 'grinning key', 'whisperbox'."
        ),
        "setting": (
            "Generate {n} disturbing horror setting fragments — like 'asylum cellar beneath dripping stone'. Short, surreal, and atmospheric."
        ),
        "classes": (
            "List {n} singular horror occupations or archetypes — 'Flesh-scribe', 'Plague Whisperer'. Avoid heroic tropes. 1–3 words max."
        ),
    },
    "realism": {
        "humanoids": (
            "Create {n} grounded character roles suited for a realistic setting. Keep them singular and non-fantastical — e.g., 'railway worker', 'field medic'."
        ),
        "garb": (
            "List {n} realistic clothing items. Simple, singular, and era-appropriate — e.g., 'dust coat', 'military uniform'."
        ),
        "holding": (
            "Generate {n} handheld everyday or occupational objects — like 'toolbox', 'field notes', or 'worn radio'."
        ),
        "setting": (
            "List {n} short, realistic setting fragments — e.g., 'abandoned warehouse', 'snow-covered outpost'."
        ),
        "classes": (
            "Provide {n} grounded profession titles — e.g., 'Surveillance Officer', 'War Photographer'. Avoid sci-fi or fantasy flavor."
        ),
    },
    "default": {
        "default": (
            "Generate {n} creative and modular wildcard entries suitable for imaginative prompt construction. "
            "Each should be 2–6 words max, expressive, and standalone. No full scenes. No plurals. No explanations."
        )
    }
}

def get_prompt_template(genre, category, n=15):
    try:
        template = wildcard_prompt_templates[genre][category]
    except KeyError:
        template = wildcard_prompt_templates.get("default", {}).get("default", "")
    
    return template.format(n=n)
