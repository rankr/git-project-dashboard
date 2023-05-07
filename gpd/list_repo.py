import os
import json

from gpd.utils import get_config_path

CONFIG_PATH = get_config_path()

def list_path():
    print("In list_path")
    with open(CONFIG_PATH) as f:
        config = json.load(f)
        
    PROJECT_PATH = config.get('PROJECT_PATH') or []
    
    for path in PROJECT_PATH:
        print(path)