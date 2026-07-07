import json
import os

CONFIG_FILE = "raze_autoclick_config.json"

DEFAULT_CONFIG = {
    "cps": 10.0,
    "click_type": "left",
    "mode": "toggle",
    "hotkey": {"type": "keyboard", "key": "f6"},
    "antikick": True,
    "antikick_max": 20
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
