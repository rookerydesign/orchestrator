import os
import json
import streamlit as st

def sanitize_model_name(name: str) -> str:
    return name.replace("/", "_").replace("\\", "_")

def load_model_preset(model_choice: str) -> dict:
    preset_name = sanitize_model_name(model_choice)
    preset_path = os.path.join("config", "model_presets", f"{preset_name}.json")
    if os.path.exists(preset_path):
        with open(preset_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}