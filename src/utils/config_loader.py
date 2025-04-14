# src/utils/config_loader.py

import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.yaml"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Optional quick test
if __name__ == "__main__":
    config = load_config()
    print(config)
