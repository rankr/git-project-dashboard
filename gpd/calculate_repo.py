#coding: utf-8
import os
import json
import subprocess
import platform

from gpd.utils import if_legal_git_path, if_path_in_gpd, get_config_path
from gpd.commit_analyze import commit_analyze, commit_vector, commit_classification

CONFIG_PATH = get_config_path()

def execute_cmd(cmd):
    # 如果stderr是subprocess.PIPE会出现返回status始终不为0的情况
    # 如果stderr是subprocess.STDOUT会出现文件传输进度条覆盖正常信息的情况
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True) 
    # p.wait() # 等待执行完
    output, err = p.communicate()
    # 判断命令是否执行成功
    status = 1 if err else 0
    if status == 0:
        #print('[SUCCESS] %s' % cmd)
        pass
    else:
        print('[ERROR] %s' % cmd)
        print(err)
    return status, output

def calculate(path):
    if not if_legal_git_path(path):
        print("gpd calculate failed because path not exists")
        return
    if not if_path_in_gpd(path):
        print("gpd calculate failed because no .git directory exists")
    
    #print("Start calculating project information...")
    
    ### put data under path/.gpd/data
    gpd_path = os.path.join(path, '.gpd')
    gpd_data_path = os.path.join(gpd_path, 'data')
    gpd_raw_commit_path = os.path.join(gpd_data_path, 'commit_history.dat')
    
    if os.path.exists(gpd_raw_commit_path):
        print("The git project %s has been calculated before, skipping it"%(path))
        return
    
    if not os.path.exists(gpd_path):
        os.mkdir(gpd_path)
    if not os.path.exists(gpd_data_path):
        os.mkdir(gpd_data_path)
        
    ### 默认从2020-01-01开始，三年数据
    os.chdir(path)
    status, output= execute_cmd('git log --no-merges --numstat --since=2020-01-01 -p > %s'%(gpd_raw_commit_path))
    '''
    platform_name = platform.platform().lower()
    if 'windows' in platform_name:
        status, output= execute_cmd('Get-Content -encoding UTF8 %s > %s'%(gpd_raw_commit_path, gpd_raw_commit_path+'2'))
    else:
        status, output= execute_cmd('cat -encoding UTF8 %s > %s'%(gpd_raw_commit_path, gpd_raw_commit_path+'2'))
    '''
    #print("Calculate %s achieved"%(path))
    commit_analyze(path)
    commit_vector(path)
    commit_classification(path)
    