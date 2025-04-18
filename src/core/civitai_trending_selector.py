# CivitAI Trending Combo Selector
# This module fetches trending images from CivitAI API and selects combos that match local LORAs

import requests
import random
import json
import re
import os
from collections import defaultdict
from difflib import get_close_matches
from src.utils.config_loader import load_config
from src.utils.nomalize_loras import normalize_lora_name

# Load configuration
config = load_config()
LORA_DIR = config["paths"]["lora_folder"]

# CivitAI API endpoints
CIVITAI_API_BASE = "https://civitai.com/api/v1"
TRENDING_IMAGES_ENDPOINT = f"{CIVITAI_API_BASE}/images"
CIVITAI_WEB_BASE = "https://civitai.com"

# Cache for trending images to avoid repeated API calls
trending_cache = {
    "images": [],
    "last_updated": None,
    "cache_duration": 3600  # Cache for 1 hour
}

def fetch_trending_images(limit=100, nsfw=False):
    """
    Fetch trending images from CivitAI API
    
    Args:
        limit (int): Number of images to fetch (max 100)
        nsfw (bool): Whether to include NSFW images
        
    Returns:
        list: List of image data objects
    """
    import time
    from datetime import datetime, timedelta
    
    # Check if cache is valid
    now = datetime.now()
    if (trending_cache["last_updated"] and 
        trending_cache["images"] and 
        now - trending_cache["last_updated"] < timedelta(seconds=trending_cache["cache_duration"])):
        print(f"[CIVITAI] Using cached trending images ({len(trending_cache['images'])} items)")
        return trending_cache["images"]
    
    # Create a link to the web version for user reference
    trending_web_url = f"{CIVITAI_WEB_BASE}/images?period=Week&sort=Most Reactions&nsfw={str(nsfw).lower()}"
    print(f"[CIVITAI] Web link to trending images: {trending_web_url}")
    
    # Construct a very simple API URL to avoid any issues
    api_url = f"{TRENDING_IMAGES_ENDPOINT}"
    params = {
        "limit": limit,
        "sort": "Most Reactions",  # ✅ correct casing + spacing
        "nsfw": str(nsfw).lower()
    }
    
    # Add headers to make the request look more like a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://civitai.com/"
    }
    
    print(f"[CIVITAI] Fetching trending images from CivitAI API: {api_url}")
    
    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Update cache
        trending_cache["images"] = data.get("items", [])
        trending_cache["last_updated"] = now
        
        print(f"[CIVITAI] Successfully fetched {len(trending_cache['images'])} trending images")
        return trending_cache["images"]
    except Exception as e:
        print(f"[CIVITAI] Error fetching trending images: {e}")
        # Return cached data if available, otherwise empty list
        return trending_cache.get("images", [])

def filter_images_with_loras(images):
    """
    Filter images that include LORA resources
    
    Args:
        images (list): List of image data objects from CivitAI API
        
    Returns:
        list: Filtered list of images with LORA resources
    """
    filtered = []

    for image in images:
        meta = image.get("meta")
        if not isinstance(meta, dict):
            print(f"[CIVITAI] Skipping image {image.get('id')} with no valid meta field")
            continue

        prompt = meta.get("prompt", "")
        lora_matches = re.findall(r"<lora:([^:>]+):?([\d.]*)?>", prompt)
        
        if lora_matches:
            # Convert to resource-like dicts to keep compatibility
            image["lora_resources"] = [
                {"name": name, "weight": float(weight) if weight else 0.7}
                for name, weight in lora_matches
            ]
            filtered.append(image)

    print(f"[CIVITAI] Filtered {len(filtered)} images with LORA resources out of {len(images)} total")
    return filtered

def get_local_loras():
    """
    Get a list of locally available LORAs with normalized names
    
    Returns:
        dict: Dictionary mapping normalized LORA names to their full paths
    """
    from src.utils.raw_loader import load_models_and_loras
    
    _, _, all_loras = load_models_and_loras(model_dir="unused", lora_dir=LORA_DIR)
    
    # Create a mapping of normalized names to full paths
    local_loras = {}
    for lora in all_loras:
        lora_path = lora["name"]
        normalized_name = normalize_lora_name(lora_path)
        local_loras[normalized_name.lower()] = lora_path
    
    print(f"[CIVITAI] Found {len(local_loras)} local LORAs")
    return local_loras

def normalize_civitai_lora_name(name):
    """
    Normalize CivitAI LORA name for matching with local LORAs
    
    Args:
        name (str): LORA name from CivitAI
        
    Returns:
        str: Normalized LORA name
    """
    import re
    
    # Remove version numbers and common suffixes
    name = re.sub(r'v\d+(\.\d+)*$', '', name)
    name = re.sub(r'[-_\s]lora$', '', name, flags=re.IGNORECASE)
    
    # Replace special characters with underscores
    name = re.sub(r'[^\w\s]', '_', name)
    
    # Replace multiple spaces/underscores with a single underscore
    name = re.sub(r'[\s_]+', '_', name)
    
    return name.strip('_').lower()

def strip_author_from_name(name):
    # Remove patterns like -flux-by_author or _by_author
    return re.sub(r"[-_]?flux[-_]?by[_-]?[a-zA-Z0-9]+$", "", name, flags=re.IGNORECASE)

def match_civitai_loras_with_local(image, local_loras):
    """
    Match CivitAI LORAs with locally available LORAs
    """
    lora_resources = image.get("lora_resources", [])
    matched_loras = []

    for resource in lora_resources:
        name = resource.get("name", "")
        cleaned = strip_author_from_name(name)
        normalized = normalize_civitai_lora_name(cleaned)

        variations = [
            normalized,
            normalized.replace("_", ""),
            normalized.replace("_", " "),
            cleaned.lower(),
        ]

        matched = False
        for variation in variations:
            if variation in local_loras:
                matched = True
                local_path = local_loras[variation]
                break
            else:
                # Try fuzzy match
                close = get_close_matches(variation, local_loras.keys(), n=1, cutoff=0.7)
                if close:
                    matched = True
                    local_path = local_loras[close[0]]
                    print(f"[CIVITAI] Fuzzy matched '{variation}' -> '{close[0]}'")
                    break

        if matched:
            weight = resource.get("weight", 0.7)
            matched_loras.append({
                "name": local_path,
                "weight": weight,
                "civitai_name": name
            })
        else:
            print(f"[CIVITAI] No local match found for LORA: {name} (normalized: {normalized})")

    return len(matched_loras), len(lora_resources), matched_loras

def select_trending_combo(genre=None, nsfw=False, limit=50, model_name=None):
    """
    Select a trending combo from CivitAI that matches local LORAs
    
    Args:
        genre (str, optional): Genre preference for filtering
        nsfw (bool, optional): Whether to include NSFW images
        limit (int, optional): Number of images to fetch (default: 50)
        model_name (str, optional): Model name to filter by
        
    Returns:
        tuple: (selected_loras, debug_log, original_image, prompt, trending_web_url)
    """
    # Fetch trending images
    trending_images = fetch_trending_images(limit=limit, nsfw=nsfw)
    
    # Filter images with LORA resources
    filtered_images = filter_images_with_loras(trending_images)
    random.shuffle(filtered_images)
    # Create a link to the web version for user reference
    trending_web_url = f"{CIVITAI_WEB_BASE}/images?period=Week&sort=most_reactions&nsfw={str(nsfw).lower()}"
    
    if not filtered_images:
        print("[CIVITAI] No trending images with LORA resources found")
        return [], [{
            "name": "No trending images found",
            "weight": "-",
            "category": "error",
            "reasons": ["No trending images with LORA resources found"]
        }], None, "", trending_web_url
    
    # Get local LORAs
    local_loras = get_local_loras()
    
    # Match CivitAI LORAs with local LORAs
    valid_combos = []
    
    for image in filtered_images:
        # Check if the image was generated with the selected model
        meta = image.get("meta", {})
        if not isinstance(meta, dict):
            continue  # skip this image if meta is missing or malformed
        image_model = meta.get("Model", "")
        
        # Skip if model_name is specified and doesn't match
        if model_name and model_name.lower() not in image_model.lower():
            continue
            
        matched_count, total_count, matched_loras = match_civitai_loras_with_local(image, local_loras)
        
        # Consider combos with at least 50% matching LORAs
        match_ratio = matched_count / total_count if total_count > 0 else 0
        
        MATCH_THRESHOLD = 0.4  # Was 0.5
        if matched_count > 0 and match_ratio >= MATCH_THRESHOLD:
            valid_combos.append({
                "image": image,
                "matched_loras": matched_loras,
                "match_ratio": match_ratio,
                "prompt": image.get("meta", {}).get("prompt", ""),
                "model": image_model
            })
    
    if not valid_combos:
        print("[CIVITAI] No valid combos found with matching local LORAs")
        return [], [{
            "name": "No valid combos found",
            "weight": "-",
            "category": "error",
            "reasons": ["No trending combos with matching local LORAs found"]
        }], None, "", trending_web_url
    
    # Sort by match ratio (highest first)
    valid_combos.sort(key=lambda x: x["match_ratio"], reverse=True)
    
    # Select a random combo from the top 10 (or all if less than 10)
    top_combos = valid_combos[:min(10, len(valid_combos))]
    selected_combo = random.choice(top_combos)
    
    # Prepare the result
    selected_loras = selected_combo["matched_loras"]
    original_image = selected_combo["image"]
    prompt = selected_combo["prompt"]
    
    # Create a link to the web version for user reference
    trending_web_url = f"{CIVITAI_WEB_BASE}/images?period=Week&sort=most_reactions&nsfw={str(nsfw).lower()}"
    
    # Create debug log
    debug_log = []
    for lora in selected_loras:
        debug_log.append({
            "name": normalize_lora_name(lora["name"]),
            "weight": lora["weight"],
            "category": "trending",
            "reasons": [f"From trending image on CivitAI (original: {lora['civitai_name']})"]
        })
    
    return selected_loras, debug_log, original_image, prompt, trending_web_url

def get_trending_combo_with_preview(genre=None, nsfw=False, limit=50, model_name=None):
    """
    Get a trending combo with preview image URL
    
    Args:
        genre (str, optional): Genre preference for filtering
        nsfw (bool, optional): Whether to include NSFW images
        limit (int, optional): Number of images to fetch (default: 50)
        model_name (str, optional): Model name to filter by
        
    Returns:
        dict: Dictionary with selected_loras, debug_log, preview_url, prompt, generation_params, and trending_web_url
    """
    selected_loras, debug_log, original_image, prompt, trending_web_url = select_trending_combo(
        genre=genre,
        nsfw=nsfw,
        limit=limit,
        model_name=model_name
    )
    
    preview_url = None
    if original_image:
        preview_url = original_image.get("url")
        
        # Get additional generation parameters if available
        meta = original_image.get("meta")
        if not isinstance(meta, dict):
            meta = {}
        generation_params = {}
        
        # Extract common parameters
        for param in ["steps", "sampler", "cfgScale", "seed", "width", "height", "Model"]:
            if param in meta:
                generation_params[param] = meta[param]
    
    return {
        "selected_loras": selected_loras,
        "debug_log": debug_log,
        "preview_url": preview_url,
        "prompt": prompt,
        "generation_params": generation_params if 'generation_params' in locals() else {},
        "trending_web_url": trending_web_url
    }