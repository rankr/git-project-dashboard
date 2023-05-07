import os
import json

from gpd.utils import if_legal_git_path, if_path_in_gpd, get_config_path
from gpd.calculate_repo import calculate

CONFIG_PATH = get_config_path()

def add_path(path):
    if not if_legal_git_path(path):
        #print('========= Add failed')
        return 1
    
    if if_path_in_gpd(path):
        #print("Warning: PATH %s already exists!"%(path))
        return 2
    
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    PROJECT_PATH = config.get('PROJECT_PATH') or []
    
    ### add path
    PROJECT_PATH.append(path)
    config['PROJECT_PATH'] = PROJECT_PATH
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=1)
    
    calculate(path)
    #print('Add %s achieved'%(path))
    return 0
    