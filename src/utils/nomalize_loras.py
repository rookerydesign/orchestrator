import os

def normalize_lora_name(raw_name):
    if not raw_name:
        return ""
    if isinstance(raw_name, str) and "/" in raw_name or "\\" in raw_name:
        return os.path.splitext(os.path.basename(raw_name))[0]
    return raw_name
