#coding: utf-8

from flask import Flask, request
from markupsafe import escape
from flask import render_template, jsonify
from flask_cors import CORS
import random as rd
from collections import Counter
import numpy as np
import pandas as pd
import json
import os

from gpd import utils

app = Flask(__name__)
app.debug = True
#为了解决vue与jinja2的语法冲突，这里把jinja2的标志进行修改
#不过以后用jinja2的话，编码可能需要注意到这里的修改！
app.jinja_env.variable_start_string = '{['
app.jinja_env.variable_end_string = ']}'
CORS(app)

def label2num(label):
    if label == 'fix':
        return 0
    if label == 'other':
        return 1
    if label == 'feature':
        return 2
    
def num2label(num):
    if num == 0:
        return "fix"
    if num == 1:
        return "other"
    if num == 2:
        return "feature"

@app.route("/sample")
def sample():
    #函数功能：
    #按照时间（月份粒度）组织返回的数据
    #commit数量，有哪些重要commit（按照行数）
    #各个类型commit数量
    #各个类型commit的重要作者有谁

    #数据格式columns=['sha', 'message', 'author', 'time', 'line_count', 'label']
    try:
        df = pd.read_csv("/Users/apple/Downloads/项目dashboard/csv_data/chalk+++chalk.csv", encoding='gbk')
    except:
        df = pd.read_csv("/Users/apple/Downloads/项目dashboard/csv_data/chalk+++chalk.csv", encoding='utf8')
    #key: yyyy-mm
    #value是一个字典，字典中的内容如下
    #value: commit_count, important_commit(line_count最大), important_author, 
    #value: {label: commit_count, important_commit, important_author}

    month2dat = {}
    for i, row in df.iterrows():
        month = row.date[:len('2020-02')]
        #if month > "2021-01":
        #    continue
        label = row.label
        line_count = 0
        if not pd.isnull(row.path):
            temp = row.path.strip().split('\n')
            for i in temp:
                j = i.split(' ', 2)
                if j[0] != '-':
                    line_count += int(j[0]) + int(j[1])
        if month not in month2dat:
            month2dat[month] = {"commit_count":0, "important_commit":"", "message":"", "author_data": {},
                "line_count":-1, "important_author":""}
            month2dat[month]["fix"] = {"commit_count":0, "important_commit":"", "message":"", "author_data": {},
                "line_count":-1, "important_author":""}
            month2dat[month]["other"] = {"commit_count":0, "important_commit":"", "message":"", "author_data": {},
                "line_count":-1, "important_author":""}
            month2dat[month]["feature"] = {"commit_count":0, "important_commit":"", "message":"", "author_data": {},
                "line_count":-1, "important_author":""}
        month2dat[month]['commit_count'] += 1
        month2dat[month][label]['commit_count'] += 1
        if row.author not in month2dat[month]['author_data']:
            month2dat[month]['author_data'][row.author] = 0
            month2dat[month][label]['author_data'][row.author] = 0
        month2dat[month]['author_data'][row.author] += 1
        #month2dat[month][label]['author_data'][row.author] += 1
        if line_count > month2dat[month]['line_count']:
            month2dat[month]['line_count'] = line_count
            month2dat[month]['important_commit'] = row.sha
            month2dat[month]['message'] = row.message
        if line_count > month2dat[month][label]['line_count']:
            month2dat[month][label]['line_count'] = line_count
            month2dat[month][label]['important_commit'] = row.sha
            month2dat[month][label]['message'] = row.message
    response = {}
    months = list(month2dat.keys())
    months.sort()
    commit_count = []
    fix_count = []
    other_count = []
    feature_count = []
    #整理author_data信息。从而得到每个月重要的author是谁
    for m in months:
        """
        response[m] = {"commit_count": month2dat[m]["commit_count"],
            "important_commit": month2dat[m]["important_commit"],
            "message": month2dat[m]["message"],
            "line_count": month2dat[m]["line_count"], 
            "fix_count": month2dat[m]["fix"]['commit_count'],
            "other_count": month2dat[m]["other"]['commit_count'],
            "feature_count": month2dat[m]["feature"]['commit_count'],
        }
        maxi = -1
        author = ""
        for a, commit_count in month2dat[m]['author_data'].items():
            if commit_count > maxi:
                maxi = commit_count
                author = a
        response[m]['important_author'] = author
        """
        commit_count.append(month2dat[m]['commit_count'])
        fix_count.append(month2dat[m]['fix']['commit_count'])
        other_count.append(month2dat[m]['other']['commit_count'])
        feature_count.append(month2dat[m]['feature']['commit_count'])
    response['months'] = months
    response['commit_count'] = commit_count
    response['fix_count'] = fix_count
    response['other_count'] = other_count
    response['feature_count'] = feature_count
    return jsonify(response)


config_path = utils.get_config_path()
def get_repo_path(repo_name):
    with open(config_path) as f:
        a = json.load(f)
    for i in a['PROJECT_PATH']:
        if i.endswith(repo_name):
            return i
    return None
    
def get_repo_list():
    with open(config_path) as f:
        a = json.load(f)
    
    return a['PROJECT_PATH']

@app.route("/repo_list")
def repo_list():
    response = {}
    for path in get_repo_list():
        repo_name = path.split('\\')[-1]
        response[repo_name] = path
    return jsonify(response)

@app.route("/commit_state/<repo_name>", methods=['GET'])
def commit_state(repo_name):
    #repo_name = request.args.get('repo_name')
    repo_path = get_repo_path(repo_name)
    if repo_path is None:
        response['state'] = 'NO_REPO'
        return jsonify(response)
        
    monthly_commit_state_path = os.path.join(repo_path, '.gpd', 'data', 'monthly_commit_state.csv')
    if not os.path.exists(monthly_commit_state_path):
        response['state'] = 'NO_REPO'
        return jsonify(response)
        
    df = pd.read_csv(monthly_commit_state_path, index_col = 0)
    response = {}
    for i, row in df.iterrows():
        month = row['month']
        response[month] = {
            'feature': row['feature'],
            'fix': row['fix'],
            'other': row['other'],
            'add': row['add'],
            'remove': row['remove'],
            'total': row['total'],
        }
    # print(response)
    return jsonify(response)

@app.route("/file_state/<repo_name>", methods=['GET'])
def file_state(repo_name):
    #repo_name = request.args.get('repo_name')
    repo_path = get_repo_path(repo_name)
    if repo_path is None:
        response['state'] = 'NO_REPO'
        return jsonify(response)
        
    monthly_file_state_path = os.path.join(repo_path, '.gpd', 'data', 'monthly_file_state.csv')
    if not os.path.exists(monthly_file_state_path):
        response['state'] = 'NO_REPO'
        return jsonify(response)
        
    path2commit = {}
    df = pd.read_csv(monthly_file_state_path, index_col = 0)
    response = {}
    for i, row in df.iterrows():
        path = row['path']
        month = row['month']
        if path not in response:
            response[path] = {}
            path2commit[path] = 0
            
        path2commit[path] += row['total']
        core_developer = json.loads(row['core_developer'])
        response[path][month] = {
            'total': row['total'],
            'commit': row['fix'] + row['feature'] + row['other'],
            'core_developer': ', '.join(core_developer)
        }
    ## 选出最多commit的3个path作为默认展示的path
    a = list(path2commit.values())
    a.sort()
    if len(a) > 3:
        b = a[-3] ### commit阈值
    else:
        b = a[0]
    default_path = []
    for p, c in path2commit.items():
        if c >= b:
            default_path.append(p)
        if len(default_path) >= 3:
            break
    response['default_path'] = default_path
        
    return jsonify(response)
    

@app.route("/developer_state/<repo_name>", methods=['GET'])
def developer_state(repo_name):
    #repo_name = request.args.get('repo_name')
    repo_path = get_repo_path(repo_name)
    if repo_path is None:
        response['state'] = 'NO_REPO'
        return jsonify(response)
        
    monthly_developer_state_path = os.path.join(repo_path, '.gpd', 'data', 'monthly_developer_state.csv')
    if not os.path.exists(monthly_developer_state_path):
        response['state'] = 'NO_REPO'
        return jsonify(response)
        
    developer2commit = {}
    df = pd.read_csv(monthly_developer_state_path, index_col = 0)
    response = {}
    for i, row in df.iterrows():
        developer = row['developer']
        month = row['month']
        if developer not in response:
            response[developer] = {}
            developer2commit[developer] = 0
            
        temp = row['feature'] + row['fix'] + row['other']
        developer2commit[developer] += temp
        response[developer][month] = {
            'feature': row['feature'],
            'fix': row['fix'],
            'other': row['other'],
            'commit': temp
        }
    ## 选出最多commit的3个path作为默认展示的path
    a = list(developer2commit.values())
    a.sort()
    if len(a) > 3:
        b = a[-3] ### commit阈值
    else:
        b = a[0]
    default_developer = []
    for d, c in developer2commit.items():
        if c >= b:
            default_developer.append(d)
        if len(default_developer) >= 3:
            break
    response['default_developer'] = default_developer
    
    print('==============default_developer', default_developer)
        
    return jsonify(response)

if __name__ == "__main__":
    app.run(host = "127.0.0.1", port = 5000)

