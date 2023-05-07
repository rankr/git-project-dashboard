
import os
import json

'''
remove data of repository
deep: 
    if True, remove all data in gpd
    if False, remove from gpd.conf
'''
def remove_path(path, deep=False):
    if not if_path_in_gpd(path):
        print("Warning: PATH %s not exist in gpd.conf!"%(path))
        return
    
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    PROJECT_PATH = config.get('PROJECT_PATH') or []
    
    ### remove path
    PROJECT_PATH = [x for x in PROJECT_PATH if x != path]
    config['PROJECT_PATH'] = PROJECT_PATH
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=1)
        
    ### TODO: add deep removing
    if deep:
        pass