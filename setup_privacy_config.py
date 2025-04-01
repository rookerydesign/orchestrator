
import os
import platform

def get_streamlit_config_path():
    if platform.system() == "Windows":
        return os.path.join(os.environ["USERPROFILE"], ".streamlit", "config.toml")
    else:
        return os.path.expanduser("~/.streamlit/config.toml")

def ensure_privacy_config():
    config_path = get_streamlit_config_path()
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    content = "[browser]\ngatherUsageStats = false\n"

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            existing = f.read()
        if "gatherUsageStats" in existing:
            print("Streamlit telemetry setting already configured.")
            return
        with open(config_path, "a") as f:
            f.write("\n" + content)
    else:
        with open(config_path, "w") as f:
            f.write(content)

    print(f"Streamlit telemetry disabled at {config_path}")

if __name__ == "__main__":
    ensure_privacy_config()
