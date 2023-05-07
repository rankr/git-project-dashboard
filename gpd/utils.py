import os
import json
import pandas as pd
import numpy as np
import re
import hashlib
import Levenshtein

import nltk
from nltk.stem.porter import PorterStemmer
porter_stemmer = PorterStemmer()
from nltk.corpus import stopwords
eng_stop_words = stopwords.words('english')

def get_config_path():
    path = "C:\\Users\\Pit\\Downloads\\毕业相关\\项目dashboard\\code\\git-project-dashboard\\gpd.conf"
    
    ### if the config path not exists
    if not os.path.exists(path):
        print("Warning: in __init__.py, gpd.conf does not exist, creating it...")
        directory = os.getcwd()
        print("Adding gpd.conf in path \"%s\""%(directory))
        
        conf_path = os.path.join(directory, path)
        with open(conf_path, 'w') as f:
            conf = {'CONFIG_PATH': conf_path}
            json.dump(conf, f, indent=1)
        return conf_path
        
    ### if the config path exists
    with open(path) as f:
        temp = json.load(f)
    return temp['CONFIG_PATH']

CONFIG_PATH = get_config_path()
GPD_DATA_PATH = os.path.join(CONFIG_PATH[:-8], 'gpd', 'gpd_data')

def get_freq_feature_path():
    path = os.path.join(GPD_DATA_PATH, 'freq_feature.json')
    return path

'''
if the path is legal git path, return True
else return False
'''
def if_legal_git_path(path):
    if not os.path.exists(path):
        print("Path %s not exists"%(path))
        return False
    dot_git_path = os.path.join(path, '.git')
    if not os.path.exists(dot_git_path):
        print(dot_git_path)
        print("Path is not git repository, .git directory not exists")
        return False
    return True

'''
if the path has been added in gpd.conf, return True
else return False
'''
def if_path_in_gpd(path):
    with open(CONFIG_PATH) as f:
        config = json.load(f)
        
    PROJECT_PATH = config.get('PROJECT_PATH') or []
    if path in PROJECT_PATH:
        return True
    return False
    
def find_all(sub,s):
    index_list = []
    index = s.find(sub)
    while index != -1:
        index_list.append(index)
        index = s.find(sub,index+1)
    
    if len(index_list) > 0:
        return index_list
    else:
        return -1
    
def month_map(month):
    if month == 'Jan':
        return '1'
    elif month == 'Feb':
        return '2'
    elif month == 'Mar':
        return '3'
    elif month == 'Apr':
        return '4'
    elif month == 'May':
        return '5'
    elif month == 'Jun':
        return '6'
    elif month == 'Jul':
        return '7'
    elif month == 'Aug':
        return '8'
    elif month == 'Sep':
        return '9'
    elif month == 'Oct':
        return '10'
    elif month == 'Nov':
        return '11'
    elif month == 'Dec':
        return '12'
    else:
        assert(False)
    
### eng_words.json里是已经经过词干化的词，所以之后不再需要进一步处理了
def load_eng_words():
    path = os.path.join(GPD_DATA_PATH, 'eng_words.json')
    return set(json.load(open(path)))

dictionary = load_eng_words()
### sentence_filter对commit message进行处理。misc版本的这个函数仅对commit message的一个段落进行处理
def sentence_filter(s):
    global dictionary
    global porter_stemmer
    #在进行lower之前，先把驼峰命名法的变成token
    s = s.split(" ")
    s2 = []
    for i in s:
        if re.match("[a-z]+([A-Z][a-z]+)+$", i) or re.match("_*([a-zA-Z]+_)+[a-z]*$", i):
            s2.append("token")
        else:
            s2.append(i)
    s = " ".join(s2)
    
    s = s.lower()
    while "change-id" in s:
        #print("111")
        if len(s) <= len("Change-Id: Ic9a591fe739dd4ee3b0ad0130190e000404fb73a"):
            return ""
        else:
            posi = s.find('change-id')
            s = s[:posi] + s[posi + len("Change-Id: Ic9a591fe739dd4ee3b0ad0130190e000404fb73a"):]
    while "depends-on" in s:
        #print("222")
        if len(s) <= len("Depends-On: I4e08a97158dc4538c6f021c049c6e60fb7293459"):
            return ""
        else:
            posi = s.find('depends-on')
            s = s[:posi] + s[posi +len("Depends-On: I4e08a97158dc4538c6f021c049c6e60fb7293459"):]
    while "http" in s:
        #print(444)
        posi = s.find("http")
        left = s[:posi]
        right = s[posi:]
        posi_space = right.find(" ")
        if posi_space == -1:
            s = left
        else:
            s = left + right[posi_space + 1:]
    
    s = re.sub("\d+(\.\d+){1,2}", 'version', s)
    s = re.sub("\d+(\.\d+){3}", 'address', s)#ip addresss, for better pos-tag
    
    ### 删去常用符号，用来更精准分词
    s = re.sub(r"[!.,#\s]+", ' ', s)
    
    #number处理一定要在version、address等后面
    s = s.split(" ")
    s2 = []
    for i in s:
        if not i:
            continue
        if re.match("\d+", i):
            s2.append("number")
        else:
            s2.append(porter_stemmer.stem(i))
    s = " ".join(s2)
    
    s = s.split(" ")
    s2 = []
    for i in s:
        if i not in dictionary:
            s2.append("token")
        else:
            s2.append(i)
    
    s = []
    #多个token合并成一个
    for i, word in enumerate(s2):
        if i > 0 and s2[i] == 'token' and s2[i - 1] == "token":
            continue
        s.append(word)
    
    return s

### sentence_filter_simple更加简单，意图成为朴素的词袋模型，从而选取词汇特征
### 不会置换token，一些token可能对软件有特殊含义（比如）
### 不会根据dictionary删去词，这样也许会丢失重要关键词信息（如'doc'不在dictionary中）
### 会进行去除停用词，停用词对词袋模型没有意义
def sentence_filter_simple(s):
    global porter_stemmer
    s = s.lower()
    while "change-id" in s:
        #print("111")
        if len(s) <= len("Change-Id: Ic9a591fe739dd4ee3b0ad0130190e000404fb73a"):
            return ""
        else:
            posi = s.find('change-id')
            s = s[:posi] + s[posi + len("Change-Id: Ic9a591fe739dd4ee3b0ad0130190e000404fb73a"):]
    while "depends-on" in s:
        #print("222")
        if len(s) <= len("Depends-On: I4e08a97158dc4538c6f021c049c6e60fb7293459"):
            return ""
        else:
            posi = s.find('depends-on')
            s = s[:posi] + s[posi +len("Depends-On: I4e08a97158dc4538c6f021c049c6e60fb7293459"):]
    while "http" in s:
        #print(444)
        posi = s.find("http")
        left = s[:posi]
        right = s[posi:]
        posi_space = right.find(" ")
        if posi_space == -1:
            s = left
        else:
            s = left + right[posi_space + 1:]
    
    s = re.sub("\d+(\.\d+){1,2}", 'version', s)
    s = re.sub("\d+(\.\d+){3}", 'address', s)#ip addresss, for better pos-tag
    
    ### 删去常用符号，用来更精准分词
    s = re.sub(r"[!.:,#\s\[\]\(\)\{\}]+", ' ', s)
    
    #number处理一定要在version、address等后面
    s = s.split(" ")
    s2 = []
    for i in s:
        if not i or i in eng_stop_words or '@' in i:
            continue
        if re.match("\d+", i):
            s2.append("number")
        else:
            s2.append(porter_stemmer.stem(i))
    s = s2

    return s

### 从commit的修改路径提取特征 
### 后缀作为特征
### 相反，路径中包含'_'的目录名，会被舍弃（这种文件往往是项目上下文相关的，不能作为普适特征）
def paths_filter(paths):
    ret = set()
    for path in paths.split('\n'):
        temp = re.split(r'[/]', path)
        if '.' in temp[-1]: # 后缀也作为潜在特征考虑
            a = temp[-1].split('.')
            temp[-1] = a[0]
            for u in a[1:]:
                temp.append(u)
        for i in temp:
            if not i:
                continue
            if '_' not in i:
                ret.add(porter_stemmer.stem(i))
    return ret
    
### 从commit的修改路径提取特征 
### 后缀作为特征
### 相反，路径中包含'_'的目录名，会被舍弃（这种文件往往是项目上下文相关的，不能作为普适特征）
### 相比函数paths_filter，这个只提取“重要的”路径名
### 大部分修改都会涉及多个路径，如果一个词出现在threshold比例或以上的路径中，那么这个词才会被当做这个路径的潜在特征
def paths_filter_important(paths, threshold = 0.5):
    ret = {}
    for path in paths.split('\n'):
        temp = re.split(r'[/]', path)
        if '.' in temp[-1]: # 后缀也作为潜在特征考虑
            a = temp[-1].split('.')
            temp[-1] = a[0]
            for u in a[1:]:
                temp.append(u)
        for i in temp:
            if not i:
                continue
            if '_' not in i:
                w = porter_stemmer.stem(i)
                if w not in ret:
                    ret[w] = 0
                ret[w] += 1
    L = paths.count('\n')
    ret = set([w for w,c in ret.items() if ret[w]/L >= threshold])
    return ret
    
### commit中如果path名称改变，那么会有xxx/{xxx => xxx}/xxx格式出现
### 由于这种修改出于重构、文件名称优化、名称修正等等，所以修改后的名称更加正确、反应commit目的
### 所以这里处理用改正后的名称替代该位置
### 在最后分类前，需要用这个函数处理路径后，再喂给上面的paths_filter提取特征
def deal_path_change(path):
    temp = path.split('\n')
    ret = ''
    for i in temp:
        if not i:
            continue
        if '{' in i:
            a = i.find('{')
            b = i.find('=> ')
            c = i.find('}')
            if c < len(i)-1:
                i = i[:a] + i[b+3:c] + i[c+1:]
            else:
                i = i[:a] + i[b+3:c]
        ret += i + "\n"
    return ret

"""
return: 
    'H': Harder to access
    'E': Easier to access
    'N': No change
"""
def detect_java_method_accessibility(modifier_add, modifier_delete):
    if 'private' in modifier_add:
        if 'private' not in modifier_delete:
            return 'H'
        else:
            return 'N'
    elif 'protected' in modifier_add:
        if 'private' in modifier_delete:
            return 'E'
        elif 'protected' in modifier_delete:
            return 'N'
        return 'H'
    elif 'public' in modifier_add:
        if 'private' in modifier_delete or 'protected' in modifier_delete:
            return 'E'
        return 'N'
        
"""
return: 
    'H': Harder to access
    'E': Easier to access
    'N': No change
"""
def detect_python_method_accessibility(name_add, name_delete):
    if name_add.startswith('__'):
        if not name_delete.startswith('__'):
            return 'H'
        else:
            return 'N'
    elif name_add.startswith('_'):
        if name_delete.startswith('__'):
            return 'E'
        elif name_delete.startswith('_'):
            return 'N'
        else:
            return 'H'
    else:
        if name_delete.startswith('_'):
            return 'E'
        return 'N'
           
"""
return: 
    'H': Harder to access
    'E': Easier to access
    'N': No change
"""
def detect_js_method_accessibility(name_add, name_delete):
    if name_add.startswith('#'):
        if not name_delete.startswith('#'):
            return 'H'
        else:
            return 'N'
    elif name_add.startswith('_'):
        if name_delete.startswith('#'):
            return 'E'
        elif name_delete.startswith('_'):
            return 'N'
        else:
            return 'H'
    else:
        if name_delete.startswith('_') or name_delete.startswith('#'):
            return 'E'
        return 'N'
    
"""
return: 
    'H': Harder to access
    'E': Easier to access
    'N': No change
"""
def detect_ts_method_accessibility(modifier_add, modifier_delete):
    if 'private' in modifier_add:
        if 'private' not in modifier_delete:
            return 'H'
        else:
            return 'N'
    elif 'protected' in modifier_add:
        if 'private' in modifier_delete:
            return 'E'
        elif 'protected' in modifier_delete:
            return 'N'
        return 'H'
    elif 'public' in modifier_add:
        if 'private' in modifier_delete or 'protected' in modifier_delete:
            return 'E'
        return 'N'
        
    
debug = False

re_java_class = re.compile(r"(\w+\s+)*class\s+(\w+\s+)*{")
re_java_method = re.compile(r"\s*([\w\[\]<>]+\s+)+\w+\s*[(]")
re_java_var = re.compile(r"\s*([\w\[\]<>?]+\s+)+\w+\s*(=.+)?;")
def extract_java_change(add_path, remove_path, location, diff):
    global re_java_class
    global re_java_method
    global re_java_var
    global debug

    add_lines = {}
    remove_lines = {}
    
    add_method = {}
    remove_method = {}
    var_declaratoin_order = 0
    add_var = []
    remove_var = []
    
    ### vector
    add_class_cnt = 0           # 0
    remove_class_cnt = 0        # 1
    rename_class_cnt = 0        # 2
    move_method_cnt = 0         # 3
    add_method_cnt = 0          # 4
    remove_method_cnt = 0       # 5
    rename_method_cnt = 0       # 6
    accessibility_up_cnt = 0    # 7
    accessibility_down_cnt = 0  # 8
    add_arg_cnt = 0             # 9
    remove_arg_cnt = 0          # 10
    move_arg_cnt = 0            # 11
    change_arg_type_cnt = 0     # 12
    rename_arg_cnt = 0          # 13
    add_return_cnt = 0          # 14
    remove_return_cnt = 0       # 15
    update_return_cnt = 0       # 16
    add_var_cnt = 0             # 17
    remove_var_cnt = 0          # 18
    rename_var_cnt = 0          # 19
    change_var_type_cnt = 0     # 20
    add_statement_cnt = 0       # 21
    remove_statement_cnt = 0    # 22
    update_statement_cnt = 0    # 23
    move_statement_cnt = 0      # 24
    condition_change_cnt = 0    # 25
    add_else_cnt = 0            # 26
    remove_else_cnt = 0         # 27
    
    class_name_state = [set(), set()] ### [add_class_name, remove_class_name]
    return_state = [False, False] ### [if_return_add, if_return_remove]
    
    for line in diff.split('\n'):
        flag = 'c' # default: context
        if line.startswith('+'):
            flag = '+'
            line = line[1:]
        elif line.startswith('-'):
            flag = '-'
            line = line[1:]
        else:
            ### context 把diff分成更小的多个块，所以每次context都检查一下各种更改，能在更细粒度上生成代码变更情况
            
            ### dealing with return change
            if all(return_state):
                update_return_cnt += 1
            elif return_state[0]:
                add_return_cnt += 1
            elif return_state[1]:
                remove_return_cnt += 1
            return_state = [False, False]
            
            ### dealing with class name change
            #if any(class_name_state):
            #    print("&&&&&&&&&&&&&&&&&&&&&& class_name_state", class_name_state)
            if all(class_name_state) and len(class_name_state[0]) == len(class_name_state[1]) and \
                class_name_state[0] != class_name_state[1]:
                rename_class_cnt += len(class_name_state[0] - class_name_state[1])
            elif len(class_name_state[0]) > len(class_name_state[1]):
                add_class_cnt += 1
            elif len(class_name_state[0]) < len(class_name_state[1]):
                remove_class_cnt += 1
            class_name_state = [set(), set()]
            
            ### dealing with var change: add, remove, rename, type-change
            if len(add_var) == 0:
                if remove_var:
                    remove_var_cnt += sum([len(x[1]) for x in remove_var])
            elif len(remove_var) == 0:
                add_var_cnt += sum([len(x[1]) for x in add_var])
            else:
                add_posi = 0
                remove_posi = 0
                while add_posi < len(add_var) and remove_posi < len(remove_var):  
                    add_order, add_dict = add_var[add_posi]
                    remove_order, remove_dict = remove_var[remove_posi]
                    if add_order == remove_order: ### 同一批变量声明
                        if len(add_dict) < len(remove_dict):
                            remove_var_cnt += len(remove_dict) - len(add_dict)
                        elif len(add_dict) > len(remove_dict):
                            add_var_cnt += len(add_dict) - len(remove_dict)
                        else:
                            temp0 = set(add_dict.keys())
                            temp1 = set(remove_dict.keys())
                            temp2 = temp0 - temp1
                            temp3 = temp1 - temp0
                            rename_var_cnt += len(temp2)
                            for i in temp0.intersection(temp1):
                                if add_dict[i] != remove_dict[i]:
                                    change_var_type_cnt += 1
                        remove_posi += 1
                        add_posi += 1
                    elif add_order > remove_order:
                        remove_var_cnt += len(remove_dict)
                        remove_posi += 1
                    else: ### add_order < remove_order
                        add_var_cnt += len(add_dict)
                        add_posi += 1
                
                if add_posi < len(add_var):
                    add_var_cnt += sum([len(x[1]) for x in add_var[add_posi:]])
                if remove_posi < len(remove_var):
                    remove_var_cnt += sum([len(x[1]) for x in remove_var[remove_posi:]])
                
            var_declaratoin_order = 0
            add_var = []
            remove_var = []
            
            continue
        
        if debug:
            print("####### flag", flag)
            print(line, '\n')

        line = line.strip()
        if not line:
            continue
        
        if re.match(re_java_class, line):
            temp = line.find('{')
            if temp == -1:
                continue
            temp = line[:temp].split()
            #print("&&&&&&&&&&&&&In class, temp", temp)
            
            class_name = temp[-1]
            if flag == '+':
                class_name_state[0].add(class_name)
            elif flag == '-':
                class_name_state[1].add(class_name)
                
        elif re.match(re_java_method, line) and not line.startswith('return'):
            if debug:
                print("============= in method condition")
        
            temp = line.find('(')
            if temp == -1:
                continue
            line_elements = line[:temp].split()
            
            modifier = ' '.join(line_elements[:-2])
            return_type = line_elements[-2]
            method_name = line_elements[-1]
            
            temp = line[temp:]
            temp2 = temp.find(')')
            if temp2 == -1: ### cannot get args
                method_args = {}
            else:
                args_string = temp[:temp2].strip()
                method_args = {}
                order = 0
                for i in args_string.split(','):
                    i = i.strip().split()
                    if not i:
                        continue
                    method_args[i[-1]] = {'order': order, 'type': ' '.join(i[:-1])} ### arg_name: {order: , type}
                    order += 1
                    
            method_info = {
                'args': method_args, 
                'modifier': modifier, 
                'return_type': return_type
            }
            if flag == '+':
                add_method[method_name] = method_info
            else:
                remove_method[method_name] = method_info
        
        elif re.match(re_java_var, line): ### variable declaration
            line = line.replace('=', ' = ')
            
            var_info = {} ### var_name: var_type
            var_type = ""
            prev2 = ""
            prev1 = ""
            for i in line.split():
                if i == '=':
                    if not var_type:
                        var_type = prev2
                    var_info[prev1] = var_type
                else:
                    prev1 = i
                    
            if flag == '+':
                add_var.append((var_declaratoin_order, var_info))
            else:
                remove_var.append((var_declaratoin_order, var_info))
                var_declaratoin_order += 1
                
        elif line.startswith('return'):
            if flag == '+':
                return_state[0] = True
            else:
                return_state[1] = True
                
                
        elif 'else' in line:
            if flag == '+':
                add_else_cnt += 1
            else:
                remove_else_cnt += 1
                
        elif 'while' in line or 'if' in line or 'for' in line:
            condition_change_cnt += 1
            
        else: ### other statements change
            md5 = hashlib.md5(line.encode()).digest()
            if flag == '+':
                add_lines[md5] = line
            elif flag == '-':
                remove_lines[md5] = line
                
            
    temp0 = set(add_method.keys())
    temp1 = set(remove_method.keys())
    ### detect moving-method change, and method accessibility change, and args change
    for name in temp0.intersection(temp1):
        i = add_method[name]
        j = remove_method[name]
        if i == j:
            move_method_cnt += 1
            
        ac = detect_java_method_accessibility(i['modifier'], j['modifier'])
        if ac == 'H':
            accessibility_down_cnt += 1
        elif ac == 'E':
            accessibility_up_cnt += 1
        
        add_args = i['args']
        remove_args = j['args']
        
        arg_set0 = set(add_args.keys())
        arg_set1 = set(remove_args.keys())
        if len(arg_set0) != len(arg_set1):
            for arg_name in arg_set0.intersection(arg_set1):
                a = add_args[arg_name]
                r = remove_args[arg_name]
                ### arg order change
                if a['order'] != r['order']:
                    move_arg_cnt += 1
                ### arg type change
                if a['type'] != r['type']:
                    change_arg_type_cnt += 1
                    
            
        arg_set2 = arg_set0 - arg_set1
        arg_set3 = arg_set1 - arg_set0
        rename_arg_cnt_temp = 0
        for arg_name0 in arg_set2:
            for arg_name1 in arg_set3:
                if add_args[arg_name0] == remove_args[arg_name1]:
                    rename_arg_cnt_temp += 1
        add_arg_cnt += len(arg_set2) - rename_arg_cnt_temp
        remove_arg_cnt += len(arg_set3) - rename_arg_cnt_temp
        rename_arg_cnt += rename_arg_cnt_temp
        
            
    temp2 = temp0 - temp1
    temp3 = temp1 - temp0
    rename_method_cnt_temp = 0
    ### detect renaming-method change
    for name_add in temp2:
        for name_remove in temp3:
            if add_method[name_add] == remove_method[name_remove]:
                rename_method_cnt_temp += 1
        
    add_method_cnt += len(temp2) - rename_method_cnt_temp
    remove_method_cnt += len(temp3) - rename_method_cnt_temp
    rename_method_cnt += rename_method_cnt_temp
    
    ### detect statement-change
    temp = set(add_lines.keys()).intersection(remove_lines.keys())
    move_statement_cnt += len(temp)
    for add_md5, add_line in add_lines.items():
        if add_md5 in temp:
            continue
        ### find similar statements
        for remove_line in remove_lines.values():
            if len(add_line) >= 100 or len(remove_line) >= 100: ### 如果太长，会太慢，所以这里做个过滤
                continue
            a = Levenshtein.distance(add_line, remove_line)
            b = min(len(add_line), len(remove_line))
            if debug:
                print('add_line', add_line)
                print('remove_line', remove_line)
            if a / b <= 0.2:
                update_statement_cnt += 1
    add_statement_cnt += max(len(add_lines) - move_statement_cnt - update_statement_cnt, 0)
    remove_statement_cnt += max(len(remove_lines) - move_statement_cnt - update_statement_cnt, 0)
    
    return [
            add_class_cnt, remove_class_cnt, rename_class_cnt, move_method_cnt, add_method_cnt, 
            remove_method_cnt, rename_method_cnt, accessibility_up_cnt, accessibility_down_cnt, add_arg_cnt, 
            remove_arg_cnt, move_arg_cnt, change_arg_type_cnt, rename_arg_cnt, add_return_cnt, 
            remove_return_cnt, update_return_cnt, add_var_cnt, remove_var_cnt, rename_var_cnt, 
            change_var_type_cnt, add_statement_cnt, remove_statement_cnt, update_statement_cnt, move_statement_cnt, 
            condition_change_cnt, add_else_cnt, remove_else_cnt
           ]
    
    
re_python_class = re.compile(r"\s*class\s+(.+)?:")
re_python_method = re.compile(r"(\w*\s+)?def\s+\w+\s*[(]")
re_python_var = re.compile(r"\s*\w+\s*=(.+)?")
def extract_python_change(add_path, remove_path, location, diff):
    global re_python_class
    global re_python_method
    global re_python_var
    global debug

    add_lines = {}
    remove_lines = {}
    
    add_method = {}
    remove_method = {}
    var_declaratoin_order = 0
    add_var = []
    remove_var = []
    
    ### vector
    add_class_cnt = 0           # 0
    remove_class_cnt = 0        # 1
    rename_class_cnt = 0        # 2
    move_method_cnt = 0         # 3
    add_method_cnt = 0          # 4
    remove_method_cnt = 0       # 5
    rename_method_cnt = 0       # 6
    accessibility_up_cnt = 0    # 7
    accessibility_down_cnt = 0  # 8
    add_arg_cnt = 0             # 9
    remove_arg_cnt = 0          # 10
    move_arg_cnt = 0            # 11
    change_arg_type_cnt = 0     # 12
    rename_arg_cnt = 0          # 13
    add_return_cnt = 0          # 14
    remove_return_cnt = 0       # 15
    update_return_cnt = 0       # 16
    add_var_cnt = 0             # 17
    remove_var_cnt = 0          # 18
    rename_var_cnt = 0          # 19
    change_var_type_cnt = 0     # 20
    add_statement_cnt = 0       # 21
    remove_statement_cnt = 0    # 22
    update_statement_cnt = 0    # 23
    move_statement_cnt = 0      # 24
    condition_change_cnt = 0    # 25
    add_else_cnt = 0            # 26
    remove_else_cnt = 0         # 27
    
    class_name_state = [set(), set()] ### [add_class_name, remove_class_name]
    return_state = [False, False] ### [if_return_add, if_return_remove]
    
    for line in diff.split('\n'):
        flag = 'c' # default: context
        if line.startswith('+'):
            flag = '+'
            line = line[1:]
        elif line.startswith('-'):
            flag = '-'
            line = line[1:]
        else:
            ### context 把diff分成更小的多个块，所以每次context都检查一下各种更改，能在更细粒度上生成代码变更情况
            
            ### dealing with return change
            if all(return_state):
                update_return_cnt += 1
            elif return_state[0]:
                add_return_cnt += 1
            elif return_state[1]:
                remove_return_cnt += 1
            return_state = [False, False]
            
            ### dealing with class name change
            #if any(class_name_state):
            #    print("&&&&&&&&&&&&&&&&&&&&&& class_name_state", class_name_state)
            if all(class_name_state) and len(class_name_state[0]) == len(class_name_state[1]) and \
                class_name_state[0] != class_name_state[1]:
                rename_class_cnt += len(class_name_state[0] - class_name_state[1])
            elif len(class_name_state[0]) > len(class_name_state[1]):
                add_class_cnt += 1
            elif len(class_name_state[0]) < len(class_name_state[1]):
                remove_class_cnt += 1
            class_name_state = [set(), set()]
            
            ### dealing with var change: add, remove, rename, type-change
            if len(add_var) == 0:
                if remove_var:
                    remove_var_cnt += sum([len(x[1]) for x in remove_var])
            elif len(remove_var) == 0:
                add_var_cnt += sum([len(x[1]) for x in add_var])
            else:
                add_posi = 0
                remove_posi = 0
                while add_posi < len(add_var) and remove_posi < len(remove_var):  
                    add_order, add_arr = add_var[add_posi]
                    remove_order, remove_arr = remove_var[remove_posi]
                    if add_order == remove_order: ### 同一批变量定义
                        if len(add_arr) < len(remove_arr):
                            remove_var_cnt += len(remove_arr) - len(add_arr)
                        elif len(add_arr) > len(remove_arr):
                            add_var_cnt += len(add_arr) - len(remove_arr)
                        else:
                            temp0 = set(add_arr)
                            temp1 = set(remove_arr)
                            temp2 = temp0 - temp1
                            temp3 = temp1 - temp0
                            rename_var_cnt += len(temp2)
                        remove_posi += 1
                        add_posi += 1
                    elif add_order > remove_order:
                        remove_var_cnt += len(remove_arr)
                        remove_posi += 1
                    else: ### add_order < remove_order
                        add_var_cnt += len(add_arr)
                        add_posi += 1
                
                if add_posi < len(add_var):
                    add_var_cnt += sum([len(x[1]) for x in add_var[add_posi:]])
                if remove_posi < len(remove_var):
                    remove_var_cnt += sum([len(x[1]) for x in remove_var[remove_posi:]])
                
            var_declaratoin_order = 0
            add_var = []
            remove_var = []
            
            continue
        
        if debug:
            #print("####### flag", flag)
            #print(line, '\n')
            pass

        line = line.strip()
        if not line:
            continue
        
        if re.match(re_python_class, line):
            temp = line.find('class')
            if temp == -1:
                continue
            temp = line[temp+5:].split()
            #print("&&&&&&&&&&&&&In class, temp", temp)
            
            class_name = temp[0]
            if flag == '+':
                class_name_state[0].add(class_name)
            elif flag == '-':
                class_name_state[1].add(class_name)
                
        elif re.match(re_python_method, line) and not line.startswith('return'):
            if debug:
                #print("============= in method condition")
                pass
        
            temp = line.find('(')
            if temp == -1:
                continue
            line_elements = line[:temp].split()
            
            modifier = ' '.join(line_elements[:-2])
            method_name = line_elements[-1]
            
            temp = line[temp:]
            temp2 = temp.find(')')
            if temp2 == -1: ### cannot get args
                method_args = {}
            else:
                args_string = temp[:temp2].strip()
                method_args = {}
                order = 0
                for i in args_string.split(','):
                    i = i.strip().split()
                    if not i:
                        continue
                    method_args[i[-1]] = {'order': order} ### arg_name: order
                    order += 1
                    
            method_info = {  
                'args': method_args, 
                'modifier': modifier
            }
            if flag == '+':
                add_method[method_name] = method_info
            else:
                remove_method[method_name] = method_info
        
        elif re.match(re_python_var, line): ### variable declaration
            line = line.replace('=', ' = ')
            
            var_info = [] ### var_name
            prev1 = ""
            for i in line.split():
                if i == '=':
                    var_info.append(prev1)
                else:
                    prev1 = i
                    
            if flag == '+':
                add_var.append((var_declaratoin_order, var_info))
            else:
                remove_var.append((var_declaratoin_order, var_info))
                var_declaratoin_order += 1
                
        elif line.startswith('return'):
            if flag == '+':
                return_state[0] = True
            else:
                return_state[1] = True
                
                
        elif 'else' in line:
            if flag == '+':
                add_else_cnt += 1
            else:
                remove_else_cnt += 1
                
        elif 'while' in line or 'if' in line or 'for' in line:
            condition_change_cnt += 1
            
        else: ### other statements change
            md5 = hashlib.md5(line.encode()).digest()
            if flag == '+':
                add_lines[md5] = line
            elif flag == '-':
                remove_lines[md5] = line
                
            
    temp0 = set(add_method.keys())
    temp1 = set(remove_method.keys())
    ### detect moving-method change, and method accessibility change, and args change
    for name in temp0.intersection(temp1):
        i = add_method[name]
        j = remove_method[name]
        if i == j:
            move_method_cnt += 1
        
        add_args = i['args']
        remove_args = j['args']
        
        arg_set0 = set(add_args.keys())
        arg_set1 = set(remove_args.keys())
        if len(arg_set0) != len(arg_set1):
            for arg_name in arg_set0.intersection(arg_set1):
                a = add_args[arg_name]
                r = remove_args[arg_name]
                ### arg order change
                if a['order'] != r['order']:
                    move_arg_cnt += 1
                    
            
        arg_set2 = arg_set0 - arg_set1
        arg_set3 = arg_set1 - arg_set0
        rename_arg_cnt_temp = 0
        for arg_name0 in arg_set2:
            for arg_name1 in arg_set3:
                if add_args[arg_name0] == remove_args[arg_name1]:
                    rename_arg_cnt_temp += 1
        add_arg_cnt += len(arg_set2) - rename_arg_cnt_temp
        remove_arg_cnt += len(arg_set3) - rename_arg_cnt_temp
        rename_arg_cnt += rename_arg_cnt_temp
        
            
    temp2 = temp0 - temp1
    temp3 = temp1 - temp0
    rename_method_cnt_temp = 0
    ### detect renaming-method change
    for name_add in temp2:
        for name_remove in temp3:
            if add_method[name_add] == remove_method[name_remove]:
                rename_method_cnt_temp += 1
                a = detect_python_method_accessibility(name_add, name_remove)
                if a == 'E':
                    accessibility_up_cnt += 1
                elif a == 'H':
                    accessibility_down_cnt += 1
        
    add_method_cnt += len(temp2) - rename_method_cnt_temp
    remove_method_cnt += len(temp3) - rename_method_cnt_temp
    rename_method_cnt += rename_method_cnt_temp
    
    ### detect statement-change
    temp = set(add_lines.keys()).intersection(remove_lines.keys())
    move_statement_cnt += len(temp)
    for add_md5, add_line in add_lines.items():
        if add_md5 in temp:
            continue
        ### find similar statements
        for remove_line in remove_lines.values():
            if len(add_line) >= 100 or len(remove_line) >= 100: ### 如果太长，会太慢，所以这里做个过滤
                continue
            a = Levenshtein.distance(add_line, remove_line)
            b = min(len(add_line), len(remove_line))
            if debug:
                print('add_line', add_line)
                print('remove_line', remove_line)
            if a / b <= 0.2:
                update_statement_cnt += 1
    add_statement_cnt += max(len(add_lines) - move_statement_cnt - update_statement_cnt, 0)
    remove_statement_cnt += max(len(remove_lines) - move_statement_cnt - update_statement_cnt, 0)
    
    return [
            add_class_cnt, remove_class_cnt, rename_class_cnt, move_method_cnt, add_method_cnt, 
            remove_method_cnt, rename_method_cnt, accessibility_up_cnt, accessibility_down_cnt, add_arg_cnt, 
            remove_arg_cnt, move_arg_cnt, change_arg_type_cnt, rename_arg_cnt, add_return_cnt, 
            remove_return_cnt, update_return_cnt, add_var_cnt, remove_var_cnt, rename_var_cnt, 
            change_var_type_cnt, add_statement_cnt, remove_statement_cnt, update_statement_cnt, move_statement_cnt, 
            condition_change_cnt, add_else_cnt, remove_else_cnt
           ]
  
re_js_class = re.compile(r"\s*class\s+(.+)?{")
re_js_method = re.compile(r"\s*(\w+\s+)?\s+\w+\s*[(]")
re_js_var = re.compile(r"\s*((var)|(let)|(const))?\s*\w+\s*=(.+)?;")
def extract_js_change(add_path, remove_path, location, diff):
    global re_js_class
    global re_js_method
    global re_js_var
    global debug

    add_lines = {}
    remove_lines = {}
    
    add_method = {}
    remove_method = {}
    var_declaratoin_order = 0
    add_var = []
    remove_var = []
    
    ### vector
    add_class_cnt = 0           # 0
    remove_class_cnt = 0        # 1
    rename_class_cnt = 0        # 2
    move_method_cnt = 0         # 3
    add_method_cnt = 0          # 4
    remove_method_cnt = 0       # 5
    rename_method_cnt = 0       # 6
    accessibility_up_cnt = 0    # 7
    accessibility_down_cnt = 0  # 8
    add_arg_cnt = 0             # 9
    remove_arg_cnt = 0          # 10
    move_arg_cnt = 0            # 11
    change_arg_type_cnt = 0     # 12
    rename_arg_cnt = 0          # 13
    add_return_cnt = 0          # 14
    remove_return_cnt = 0       # 15
    update_return_cnt = 0       # 16
    add_var_cnt = 0             # 17
    remove_var_cnt = 0          # 18
    rename_var_cnt = 0          # 19
    change_var_type_cnt = 0     # 20
    add_statement_cnt = 0       # 21
    remove_statement_cnt = 0    # 22
    update_statement_cnt = 0    # 23
    move_statement_cnt = 0      # 24
    condition_change_cnt = 0    # 25
    add_else_cnt = 0            # 26
    remove_else_cnt = 0         # 27
    
    class_name_state = [set(), set()] ### [add_class_name, remove_class_name]
    return_state = [False, False] ### [if_return_add, if_return_remove]
    
    for line in diff.split('\n'):
        flag = 'c' # default: context
        if line.startswith('+'):
            flag = '+'
            line = line[1:]
        elif line.startswith('-'):
            flag = '-'
            line = line[1:]
        else:
            ### context 把diff分成更小的多个块，所以每次context都检查一下各种更改，能在更细粒度上生成代码变更情况
            
            ### dealing with return change
            if all(return_state):
                update_return_cnt += 1
            elif return_state[0]:
                add_return_cnt += 1
            elif return_state[1]:
                remove_return_cnt += 1
            return_state = [False, False]
            
            ### dealing with class name change
            #if any(class_name_state):
            #    print("&&&&&&&&&&&&&&&&&&&&&& class_name_state", class_name_state)
            if all(class_name_state) and len(class_name_state[0]) == len(class_name_state[1]) and \
                class_name_state[0] != class_name_state[1]:
                rename_class_cnt += len(class_name_state[0] - class_name_state[1])
            elif len(class_name_state[0]) > len(class_name_state[1]):
                add_class_cnt += 1
            elif len(class_name_state[0]) < len(class_name_state[1]):
                remove_class_cnt += 1
            class_name_state = [set(), set()]
            
            ### dealing with var change: add, remove, rename, type-change
            if len(add_var) == 0:
                if remove_var:
                    remove_var_cnt += sum([len(x[1]) for x in remove_var])
            elif len(remove_var) == 0:
                add_var_cnt += sum([len(x[1]) for x in add_var])
            else:
                add_posi = 0
                remove_posi = 0
                while add_posi < len(add_var) and remove_posi < len(remove_var):  
                    add_order, add_arr = add_var[add_posi]
                    remove_order, remove_arr = remove_var[remove_posi]
                    if add_order == remove_order: ### 同一批变量定义
                        if len(add_arr) < len(remove_arr):
                            remove_var_cnt += len(remove_arr) - len(add_arr)
                        elif len(add_arr) > len(remove_arr):
                            add_var_cnt += len(add_arr) - len(remove_arr)
                        else:
                            temp0 = set(add_arr)
                            temp1 = set(remove_arr)
                            temp2 = temp0 - temp1
                            temp3 = temp1 - temp0
                            rename_var_cnt += len(temp2)
                        remove_posi += 1
                        add_posi += 1
                    elif add_order > remove_order:
                        remove_var_cnt += len(remove_arr)
                        remove_posi += 1
                    else: ### add_order < remove_order
                        add_var_cnt += len(add_arr)
                        add_posi += 1
                
                if add_posi < len(add_var):
                    add_var_cnt += sum([len(x[1]) for x in add_var[add_posi:]])
                if remove_posi < len(remove_var):
                    remove_var_cnt += sum([len(x[1]) for x in remove_var[remove_posi:]])
                
            var_declaratoin_order = 0
            add_var = []
            remove_var = []
            
            continue
        
        if debug:
            #print("####### flag", flag)
            #print(line, '\n')
            pass

        line = line.strip()
        if not line:
            continue
        
        if re.match(re_js_class, line):
            temp = line.find('class')
            if temp == -1:
                continue
            temp = line[temp+5:].split()
            #print("&&&&&&&&&&&&&In class, temp", temp)
            
            class_name = temp[0]
            if flag == '+':
                class_name_state[0].add(class_name)
            elif flag == '-':
                class_name_state[1].add(class_name)
                
        elif re.match(re_js_method, line) and not line.startswith('return') \
            and not line.startswith('if') and not line.startswith('for') and not line.startswith('while'):
            if debug:
                #print("============= in method condition")
                pass
        
            temp = line.find('(')
            if temp == -1:
                continue
            line_elements = line[:temp].split()
            
            modifier = ' '.join(line_elements[:-2])
            method_name = line_elements[-1]
            
            temp = line[temp:]
            temp2 = temp.find(')')
            if temp2 == -1: ### cannot get args
                method_args = {}
            else:
                args_string = temp[:temp2].strip()
                method_args = {}
                order = 0
                for i in args_string.split(','):
                    i = i.strip().split()
                    if not i:
                        continue
                    method_args[i[-1]] = {'order': order} ### arg_name: order
                    order += 1
                    
            method_info = {  
                'args': method_args, 
                'modifier': modifier
            }
            if flag == '+':
                add_method[method_name] = method_info
            else:
                remove_method[method_name] = method_info
        
        elif re.match(re_js_var, line): ### variable declaration
            line = line.replace('=', ' = ')
            
            var_info = [] ### var_name
            prev1 = ""
            for i in line.split():
                if i == '=':
                    var_info.append(prev1)
                else:
                    prev1 = i
                    
            if flag == '+':
                add_var.append((var_declaratoin_order, var_info))
            else:
                remove_var.append((var_declaratoin_order, var_info))
                var_declaratoin_order += 1
                
        elif line.startswith('return'):
            if flag == '+':
                return_state[0] = True
            else:
                return_state[1] = True
                
                
        elif 'else' in line:
            if flag == '+':
                add_else_cnt += 1
            else:
                remove_else_cnt += 1
                
        elif 'while' in line or 'if' in line or 'for' in line:
            condition_change_cnt += 1
            
        else: ### other statements change
            md5 = hashlib.md5(line.encode()).digest()
            if flag == '+':
                add_lines[md5] = line
            elif flag == '-':
                remove_lines[md5] = line
                
            
    temp0 = set(add_method.keys())
    temp1 = set(remove_method.keys())
    ### detect moving-method change, and method accessibility change, and args change
    for name in temp0.intersection(temp1):
        i = add_method[name]
        j = remove_method[name]
        if i == j:
            move_method_cnt += 1
        
        add_args = i['args']
        remove_args = j['args']
        
        arg_set0 = set(add_args.keys())
        arg_set1 = set(remove_args.keys())
        if len(arg_set0) != len(arg_set1):
            for arg_name in arg_set0.intersection(arg_set1):
                a = add_args[arg_name]
                r = remove_args[arg_name]
                ### arg order change
                if a['order'] != r['order']:
                    move_arg_cnt += 1
                    
            
        arg_set2 = arg_set0 - arg_set1
        arg_set3 = arg_set1 - arg_set0
        rename_arg_cnt_temp = 0
        for arg_name0 in arg_set2:
            for arg_name1 in arg_set3:
                if add_args[arg_name0] == remove_args[arg_name1]:
                    rename_arg_cnt_temp += 1
        add_arg_cnt += len(arg_set2) - rename_arg_cnt_temp
        remove_arg_cnt += len(arg_set3) - rename_arg_cnt_temp
        rename_arg_cnt += rename_arg_cnt_temp
        
            
    temp2 = temp0 - temp1
    temp3 = temp1 - temp0
    rename_method_cnt_temp = 0
    ### detect renaming-method change
    for name_add in temp2:
        for name_remove in temp3:
            if add_method[name_add] == remove_method[name_remove]:
                rename_method_cnt_temp += 1
                a = detect_js_method_accessibility(name_add, name_remove)
                if a == 'E':
                    accessibility_up_cnt += 1
                elif a == 'H':
                    accessibility_down_cnt += 1
        
    add_method_cnt += len(temp2) - rename_method_cnt_temp
    remove_method_cnt += len(temp3) - rename_method_cnt_temp
    rename_method_cnt += rename_method_cnt_temp
    
    ### detect statement-change
    temp = set(add_lines.keys()).intersection(remove_lines.keys())
    move_statement_cnt += len(temp)
    for add_md5, add_line in add_lines.items():
        if add_md5 in temp:
            continue
        ### find similar statements
        for remove_line in remove_lines.values():
            if len(add_line) >= 100 or len(remove_line) >= 100: ### 如果太长，会太慢，所以这里做个过滤
                continue
            a = Levenshtein.distance(add_line, remove_line)
            b = min(len(add_line), len(remove_line))
            if debug:
                print('add_line', add_line)
                print('remove_line', remove_line)
            if a / b <= 0.2:
                update_statement_cnt += 1
    add_statement_cnt += max(len(add_lines) - move_statement_cnt - update_statement_cnt, 0)
    remove_statement_cnt += max(len(remove_lines) - move_statement_cnt - update_statement_cnt, 0)
    
    return [
            add_class_cnt, remove_class_cnt, rename_class_cnt, move_method_cnt, add_method_cnt, 
            remove_method_cnt, rename_method_cnt, accessibility_up_cnt, accessibility_down_cnt, add_arg_cnt, 
            remove_arg_cnt, move_arg_cnt, change_arg_type_cnt, rename_arg_cnt, add_return_cnt, 
            remove_return_cnt, update_return_cnt, add_var_cnt, remove_var_cnt, rename_var_cnt, 
            change_var_type_cnt, add_statement_cnt, remove_statement_cnt, update_statement_cnt, move_statement_cnt, 
            condition_change_cnt, add_else_cnt, remove_else_cnt
           ]
   
   

re_ts_class = re.compile(r"\s*class\s+(.+)?{")
re_ts_method = re.compile(r"\s*(\w+\s+)*\w+\s*[(]")
re_ts_var = re.compile(r"\s*((public|private|protected)\s+)?((var|let|const)\s+)?([\w <>,]+:\s+)?[\w <>,]+\s*=(.+)?")
def extract_ts_change(add_path, remove_path, location, diff):
    global re_js_class
    global re_js_method
    global re_js_var
    global debug

    add_lines = {}
    remove_lines = {}
    
    add_method = {}
    remove_method = {}
    var_declaratoin_order = 0
    add_var = []
    remove_var = []
    
    ### vector
    add_class_cnt = 0           # 0
    remove_class_cnt = 0        # 1
    rename_class_cnt = 0        # 2
    move_method_cnt = 0         # 3
    add_method_cnt = 0          # 4
    remove_method_cnt = 0       # 5
    rename_method_cnt = 0       # 6
    accessibility_up_cnt = 0    # 7
    accessibility_down_cnt = 0  # 8
    add_arg_cnt = 0             # 9
    remove_arg_cnt = 0          # 10
    move_arg_cnt = 0            # 11
    change_arg_type_cnt = 0     # 12
    rename_arg_cnt = 0          # 13
    add_return_cnt = 0          # 14
    remove_return_cnt = 0       # 15
    update_return_cnt = 0       # 16
    add_var_cnt = 0             # 17
    remove_var_cnt = 0          # 18
    rename_var_cnt = 0          # 19
    change_var_type_cnt = 0     # 20
    add_statement_cnt = 0       # 21
    remove_statement_cnt = 0    # 22
    update_statement_cnt = 0    # 23
    move_statement_cnt = 0      # 24
    condition_change_cnt = 0    # 25
    add_else_cnt = 0            # 26
    remove_else_cnt = 0         # 27
    
    class_name_state = [set(), set()] ### [add_class_name, remove_class_name]
    return_state = [False, False] ### [if_return_add, if_return_remove]
    
    for line in diff.split('\n'):
        flag = 'c' # default: context
        if line.startswith('+'):
            flag = '+'
            line = line[1:]
        elif line.startswith('-'):
            flag = '-'
            line = line[1:]
        else:
            ### context 把diff分成更小的多个块，所以每次context都检查一下各种更改，能在更细粒度上生成代码变更情况
            
            ### dealing with return change
            if all(return_state):
                update_return_cnt += 1
            elif return_state[0]:
                add_return_cnt += 1
            elif return_state[1]:
                remove_return_cnt += 1
            return_state = [False, False]
            
            ### dealing with class name change
            #if any(class_name_state):
            #    print("&&&&&&&&&&&&&&&&&&&&&& class_name_state", class_name_state)
            if all(class_name_state) and len(class_name_state[0]) == len(class_name_state[1]) and \
                class_name_state[0] != class_name_state[1]:
                rename_class_cnt += len(class_name_state[0] - class_name_state[1])
            elif len(class_name_state[0]) > len(class_name_state[1]):
                add_class_cnt += 1
            elif len(class_name_state[0]) < len(class_name_state[1]):
                remove_class_cnt += 1
            class_name_state = [set(), set()]
            
            ### dealing with var change: add, remove, rename, type-change
            if len(add_var) == 0:
                if remove_var:
                    remove_var_cnt += sum([len(x[1]) for x in remove_var])
            elif len(remove_var) == 0:
                add_var_cnt += sum([len(x[1]) for x in add_var])
            else:
                add_posi = 0
                remove_posi = 0
                while add_posi < len(add_var) and remove_posi < len(remove_var):  
                    add_order, add_arr = add_var[add_posi]
                    remove_order, remove_arr = remove_var[remove_posi]
                    if add_order == remove_order: ### 同一批变量定义
                        if len(add_arr) < len(remove_arr):
                            remove_var_cnt += len(remove_arr) - len(add_arr)
                        elif len(add_arr) > len(remove_arr):
                            add_var_cnt += len(add_arr) - len(remove_arr)
                        else:
                            temp0 = set(add_arr)
                            temp1 = set(remove_arr)
                            temp2 = temp0 - temp1
                            temp3 = temp1 - temp0
                            rename_var_cnt += len(temp2)
                        remove_posi += 1
                        add_posi += 1
                    elif add_order > remove_order:
                        remove_var_cnt += len(remove_arr)
                        remove_posi += 1
                    else: ### add_order < remove_order
                        add_var_cnt += len(add_arr)
                        add_posi += 1
                
                if add_posi < len(add_var):
                    add_var_cnt += sum([len(x[1]) for x in add_var[add_posi:]])
                if remove_posi < len(remove_var):
                    remove_var_cnt += sum([len(x[1]) for x in remove_var[remove_posi:]])
                
            var_declaratoin_order = 0
            add_var = []
            remove_var = []
            
            continue
        
        if debug:
            #print("####### flag", flag)
            #print(line, '\n')
            pass

        line = line.strip()
        if not line:
            continue
        
        if re.match(re_ts_class, line):
            temp = line.find('class')
            if temp == -1:
                continue
            temp = line[temp+5:].split()
            #print("&&&&&&&&&&&&&In class, temp", temp)
            
            class_name = temp[0]
            if flag == '+':
                class_name_state[0].add(class_name)
            elif flag == '-':
                class_name_state[1].add(class_name)
                
        elif re.match(re_ts_method, line) and not line.startswith('return') \
            and not line.startswith('if') and not line.startswith('for') and not line.startswith('while'):
            if debug:
                #print("============= in method condition")
                pass
        
            temp = line.find('(')
            if temp == -1:
                continue
            line_elements = line[:temp].split()
            
            modifier = ' '.join(line_elements[:-2])
            method_name = line_elements[-1]
            
            temp = line[temp:]
            temp2 = temp.find(')')
            if temp2 == -1: ### cannot get args
                method_args = {}
            else:
                args_string = temp[:temp2].strip()
                method_args = {}
                order = 0
                for i in args_string.split(','):
                    i = i.strip().split()
                    if not i:
                        continue
                    method_args[i[-1]] = {'order': order} ### arg_name: order
                    order += 1
                    
            method_info = {  
                'args': method_args, 
                'modifier': modifier
            }
            if flag == '+':
                add_method[method_name] = method_info
            else:
                remove_method[method_name] = method_info
        
        elif re.match(re_ts_var, line): ### variable declaration
            line = line.replace('=', ' = ')
            
            var_info = [] ### var_name
            prev1 = ""
            for i in line.split():
                if i == '=':
                    var_info.append(prev1)
                else:
                    prev1 = i
                    
            if flag == '+':
                add_var.append((var_declaratoin_order, var_info))
            else:
                remove_var.append((var_declaratoin_order, var_info))
                var_declaratoin_order += 1
                
        elif line.startswith('return'):
            if flag == '+':
                return_state[0] = True
            else:
                return_state[1] = True
                
                
        elif 'else' in line:
            if flag == '+':
                add_else_cnt += 1
            else:
                remove_else_cnt += 1
                
        elif 'while' in line or 'if' in line or 'for' in line:
            condition_change_cnt += 1
            
        else: ### other statements change
            md5 = hashlib.md5(line.encode()).digest()
            if flag == '+':
                add_lines[md5] = line
            elif flag == '-':
                remove_lines[md5] = line
                
            
    temp0 = set(add_method.keys())
    temp1 = set(remove_method.keys())
    ### detect moving-method change, and method accessibility change, and args change
    for name in temp0.intersection(temp1):
        i = add_method[name]
        j = remove_method[name]
        if i == j:
            move_method_cnt += 1
            
        ac = detect_java_method_accessibility(i['modifier'], j['modifier'])
        if ac == 'H':
            accessibility_down_cnt += 1
        elif ac == 'E':
            accessibility_up_cnt += 1
        
        add_args = i['args']
        remove_args = j['args']
        
        arg_set0 = set(add_args.keys())
        arg_set1 = set(remove_args.keys())
        if len(arg_set0) != len(arg_set1):
            for arg_name in arg_set0.intersection(arg_set1):
                a = add_args[arg_name]
                r = remove_args[arg_name]
                ### arg order change
                if a['order'] != r['order']:
                    move_arg_cnt += 1
                    
            
        arg_set2 = arg_set0 - arg_set1
        arg_set3 = arg_set1 - arg_set0
        rename_arg_cnt_temp = 0
        for arg_name0 in arg_set2:
            for arg_name1 in arg_set3:
                if add_args[arg_name0] == remove_args[arg_name1]:
                    rename_arg_cnt_temp += 1
        add_arg_cnt += len(arg_set2) - rename_arg_cnt_temp
        remove_arg_cnt += len(arg_set3) - rename_arg_cnt_temp
        rename_arg_cnt += rename_arg_cnt_temp
        
            
    temp2 = temp0 - temp1
    temp3 = temp1 - temp0
    rename_method_cnt_temp = 0
    ### detect renaming-method change
    for name_add in temp2:
        for name_remove in temp3:
            if add_method[name_add] == remove_method[name_remove]:
                rename_method_cnt_temp += 1
        
    add_method_cnt += len(temp2) - rename_method_cnt_temp
    remove_method_cnt += len(temp3) - rename_method_cnt_temp
    rename_method_cnt += rename_method_cnt_temp
    
    ### detect statement-change
    temp = set(add_lines.keys()).intersection(remove_lines.keys())
    move_statement_cnt += len(temp)
    for add_md5, add_line in add_lines.items():
        if add_md5 in temp:
            continue
        ### find similar statements
        for remove_line in remove_lines.values():
            if len(add_line) >= 100 or len(remove_line) >= 100: ### 如果太长，会太慢，所以这里做个过滤
                continue
            a = Levenshtein.distance(add_line, remove_line)
            b = min(len(add_line), len(remove_line))
            if debug:
                #print('add_line', add_line)
                #print('remove_line', remove_line)
                pass
            if a / b <= 0.2:
                update_statement_cnt += 1
    add_statement_cnt += max(len(add_lines) - move_statement_cnt - update_statement_cnt, 0)
    remove_statement_cnt += max(len(remove_lines) - move_statement_cnt - update_statement_cnt, 0)
    
    return [
            add_class_cnt, remove_class_cnt, rename_class_cnt, move_method_cnt, add_method_cnt, 
            remove_method_cnt, rename_method_cnt, accessibility_up_cnt, accessibility_down_cnt, add_arg_cnt, 
            remove_arg_cnt, move_arg_cnt, change_arg_type_cnt, rename_arg_cnt, add_return_cnt, 
            remove_return_cnt, update_return_cnt, add_var_cnt, remove_var_cnt, rename_var_cnt, 
            change_var_type_cnt, add_statement_cnt, remove_statement_cnt, update_statement_cnt, move_statement_cnt, 
            condition_change_cnt, add_else_cnt, remove_else_cnt
           ]
           
'''
extract code change type of commit, e.g. delete_class, add_argument, update_statement
input:
    code_change: [[path1, path2, location, diff], ...]
'''
def extract_code_change_pattern(code_change, limit=float('inf')):
    global debug
    
    total_code_change_vec = np.array([0]*28)
    for arr in code_change:
        path = arr[0]
        if arr[0].endswith('.java'):
            if debug:
                print('===================diff\n', arr[3])
            vec = extract_java_change(arr[0], arr[1], arr[2], arr[3])
            total_code_change_vec += vec
            if debug:
                print('=================== vec\n', vec)
        elif arr[0].endswith('.py'):
            if debug:
                print('===================diff\n', arr[3])
            vec = extract_python_change(arr[0], arr[1], arr[2], arr[3])
            total_code_change_vec += vec
            if debug:
                print('=================== vec\n', vec)
        elif arr[0].endswith('.js'):
            if debug:
                print('===================diff\n', arr[3])
            vec = extract_js_change(arr[0], arr[1], arr[2], arr[3])
            total_code_change_vec += vec
            if debug:
                print('=================== vec\n', vec)
        elif arr[0].endswith('.ts'):
            if debug:
                print('===================diff\n', arr[3])
            vec = extract_ts_change(arr[0], arr[1], arr[2], arr[3])
            total_code_change_vec += vec
            if debug:
                print('=================== vec\n', vec)
    return total_code_change_vec
    
