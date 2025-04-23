import json
import os

CONFIG_PATH = os.path.expanduser("~/.config/autostash.json")

class ConfigManager:
    def __init__(self):
        if not os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'w') as f:
                json.dump({"folders": []}, f)
    
    def save_folders(self, folders):
        with open(CONFIG_PATH, 'r+') as f:
            data = json.load(f)
            data["folders"] = folders
            f.seek(0)
            json.dump(data, f)
    
    def get_folders(self):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)["folders"]
