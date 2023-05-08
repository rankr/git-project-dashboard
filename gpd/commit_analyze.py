import pandas as pd
import numpy as np
import os
import json
import codecs
import re

from gpd.utils import paths_filter, deal_path_change, sentence_filter_simple, \
    extract_code_change_pattern, get_freq_feature_path, find_all, month_map
#from utils import paths_filter, deal_path_change, sentence_filter_simple, \
#    extract_code_change_pattern, get_freq_feature_path, find_all, month_map

'''
function in this file is used to analyzing commit code change, and classify them
'''

def commit_analyze(path, limit=float('inf')):
    ### check data under path/.gpd/data
    gpd_path = os.path.join(path, '.gpd')
    gpd_data_path = os.path.join(gpd_path, 'data')
    gpd_raw_commit_path = os.path.join(gpd_data_path, 'commit_history.dat')

    if not os.path.exists(gpd_raw_commit_path):
        print("commit_analyze failed due to lack data file when dealing path %s"%(gpd_raw_commit_path))
        return
        
    res_path = os.path.join(gpd_data_path, 'commit_feature.csv')
    if os.path.exists(res_path):
        #print("The git project %s has been \"commit_analyze\" before, skipping it"%(res_path))
        return
        
    ret = [] ### format: [{'hash': , 'author': , 'date': , 'message': , 'path_summary': , 'code_change': }, {}, ...]
    with codecs.open(gpd_raw_commit_path, 'r', 'ISO-8859-1') as f:
        commit_hash = ""
        author = ""
        date = ""
        message = ""
        add_path = ""    ### the path where lines are added
        remove_path = "" ### the path where lines are removed
        path_summary = []
        location = ""    ### where the code change happened (in which function, class)
        diff = ""
        code_change = []
        
        bad_add_path = False
        read_state = ""
        history = ""
        printed = set()
        while limit>0:
            if limit != float('inf') and limit % 100 == 0 and limit not in printed:
                print("In commit_analyze, limit is %s"%(limit))
                printed.add(limit)
            a = f.readline()
            if not a:
                if commit_hash: ### 把已有的commit信息存起来
                    limit -= 1
                    code_change.append([add_path, remove_path, location, diff])
                    res = {
                        'hash': commit_hash, 
                        'author': author, 
                        'date': date, 
                        'message': message, 
                        'path_summary': json.dumps(path_summary), 
                        'code_change': json.dumps(code_change)
                    }
                    ret.append(res)
                break
            elif a.startswith("commit"):
                if commit_hash: ### 把已有的commit信息存起来
                    limit -= 1
                    if not bad_add_path:
                        code_change.append([add_path, remove_path, location, diff])
                        res = {
                            'hash': commit_hash, 
                            'author': author, 
                            'date': date, 
                            'message': message, 
                            'path_summary': json.dumps(path_summary), 
                            'code_change': json.dumps(code_change)
                        }
                        ret.append(res)
                commit_hash = a.strip().split()[1]
                author = ""
                date = ""
                message = ""
                add_path = ""    ### the path where lines are added
                remove_path = "" ### the path where lines are removed
                path_summary = []
                location = ""    ### where the code change happened (in which function, class)
                diff = ""
                code_change = []
                bad_add_path = False
                continue
            elif bad_add_path:
                continue
            elif a.startswith('Author:'):
                author = a.strip().split(' ', 1)[1]
                continue
            elif a.startswith('Date:   '):
                date = a.strip()[len('Date:   '):]
                read_state = "after_date"
                continue
            elif re.match("[\d]+\t[\d]+\t", a): ### changed file summary
                a = a.strip().split('\t', 2)
                path_summary.append(a) ### added line count, removed line count, path
                continue
            elif re.match("-\t-\t", a): ### changed file summary (binary file, meaningless)
                a = a.strip().split('\t', 2)
                path_summary.append(a) ### added line count, removed line count, path
                continue
            elif a.startswith("diff"):
                read_state = "after_diff"
                if location: ### 如果已经有diff存在，先存储
                    if not bad_add_path:
                        code_change.append([add_path, remove_path, location, diff])
                    location = ""
                    diff = ""
                continue
            elif a.startswith("index"):
                continue
            elif a.startswith("+++"):
                add_path = a.strip()[5:]
                if add_path.endswith('.java') or \
                    add_path.endswith('.py') or \
                    add_path.endswith('.ts') or \
                    add_path.endswith('.js'):
                    bad_add_path = False
                else:
                    bad_add_path = True
                    
                continue
            elif a.startswith("---"):
                remove_path = a.strip()[5:]
                continue
            elif re.match("@@[ ].+[ ]@@", a):
                if location: ### 如果已经有diff存在，先存储
                    if not bad_add_path:
                        code_change.append([add_path, remove_path, location, diff])
                    location = ""
                    diff = ""
                start_position = max([i.start() for i in re.finditer('@@', a)][:2]) + 3
                location = a.strip()[start_position:]
                continue
            else:
                if read_state == 'after_date':
                    message += a
                    continue
                elif read_state == 'after_diff':
                    diff += a
                    continue
                else:
                    print("Error: in commit %s, dont know how to deal with line %s"%(commit_hash, a))
                    break
    
    df = pd.DataFrame(ret)
    df.to_csv(res_path)
    return
   
    
freq_feature = None
with open(get_freq_feature_path()) as f:
    freq_feature = json.load(f)
    
'''
extract vector to represent commit
input:
    message: commit message
    paths: [[added_line_count, removed_line_count, path_of_file], ...]
    code_changes: [[path1, path2, location, diff], ...]
'''
def extract_commit_vector(message, paths, code_changes):
    message_path_vec = []
    code_change_vec = None
    
    message_words = set(sentence_filter_simple(message))
    paths = '\n'.join([x[-1] for x in paths])
    paths = deal_path_change(paths)
    path_words = paths_filter(paths)
    total_words = message_words.union(path_words)
    for word in freq_feature:
        if word not in total_words:
            message_path_vec.append(0)
        else:
            message_path_vec.append(1)
    
    code_change_vec = extract_code_change_pattern(code_changes)
    
    message_path_vec.extend(code_change_vec)
    
    return message_path_vec
    
'''
get commit vector to classify, store related data in .gpd/data
'''
def commit_vector(path, limit=float('inf')):
    ### check data under path/.gpd/data
    gpd_path = os.path.join(path, '.gpd')
    gpd_data_path = os.path.join(gpd_path, 'data')
    gpd_commit_csv_path = os.path.join(gpd_data_path, 'commit_feature.csv')

    if not os.path.exists(gpd_commit_csv_path):
        print("commit_vector failed due to lack data file when dealing path %s"%(gpd_commit_csv_path))
        return
        
    gpd_commit_vec_path = os.path.join(gpd_data_path, 'commit_vector.csv')
    if os.path.exists(gpd_commit_vec_path):
        #print("The git project %s has been \"commit_vector\" before, skipping it"%(res_path))
        #return
        pass
        
    result = []
    df = pd.read_csv(gpd_commit_csv_path, index_col = 0)
    for index, row in df.iterrows():
        if index >= limit:
            break
        vec = extract_commit_vector(row['message'], json.loads(row['path_summary']), json.loads(row['code_change']))
        
        path_summary = json.loads(row['path_summary'])
        modified_path_num = len(path_summary)
        add_line_num = 0
        remove_line_num = 0
        for arr in path_summary:
            if arr[0].isdigit():
                add_line_num += int(arr[0])
            if arr[1].isdigit():
                remove_line_num += int(arr[1])
        add_remove_rate = 1
        if remove_line_num > 0:
            add_remove_rate = add_line_num/remove_line_num
            
        result.append([row['hash'], vec + [modified_path_num, add_line_num, remove_line_num, add_remove_rate]])
        
    new_df = pd.DataFrame(result)
    new_df.to_csv(gpd_commit_vec_path)
    return new_df
    
import pickle
with open(os.path.join("C:\\Users\\Pit\\Downloads\\毕业相关\\项目dashboard\\code\\git-project-dashboard\\gpd\\gpd_data", 
                       "clf_freq.model"), 'rb') as f:
    temp = f.read()
    model = pickle.loads(temp)
    
def commit_classification(path):
    ### check data under path/.gpd/data
    gpd_path = os.path.join(path, '.gpd')
    gpd_data_path = os.path.join(gpd_path, 'data')
    gpd_commit_vec_path = os.path.join(gpd_data_path, 'commit_vector.csv')

    if not os.path.exists(gpd_commit_vec_path):
        print("commit_classification failed due to lack data file when dealing path %s"%(gpd_commit_vec_path))
        return
        
    gpd_commit_class_path = os.path.join(gpd_data_path, 'commit_classification.json')
    if os.path.exists(gpd_commit_class_path):
        #print("The git project %s has been \"commit_vector\" before, skipping it"%(res_path))
        #return
        pass
        
    vec_df = pd.read_csv(gpd_commit_vec_path)
    sha2label = {}
    for i, row in vec_df.iterrows():
        sha = row['0']
        vec = json.loads(row['1'])
        label = model.predict([vec])[0]
        sha2label[sha] = int(label)
    
    with open(gpd_commit_class_path, 'w') as f:
        json.dump(sha2label, f)
    
"""
if new - old > one year, return True
else return False
"""
def more_than_year(old, new):
    old_y, old_m = old.split('_')
    old_y = int(old_y)
    old_m = int(old_m)
    new_y, new_m = new.split('_')
    new_y = int(new_y)
    new_m = int(new_m)
    
    if old_y >= new_y:
        return False
    elif old_y < new_y - 1:
        return True
    else:
        if new_m >= old_m:
            return True
        return False

"""
if a > b:
    return 1
if a == b:
    return 0
if a < b:
    return -1
"""
def ym_compare(a, b):
    ya, ma = a.split('_')
    yb, mb = b.split('_')
    ya, ma, yb, mb = int(ya), int(ma), int(yb), int(mb)
    if ya > yb:
        return 1
    elif ya < yb:
        return -1
    else:
        if ma > mb:
            return 1
        elif ma < mb:
            return -1
        return 0

'''
for each month, extract project state from commits, 
including: 
    cloud of important word from commit message, 
    
    for frequently modified file in project, add lines and remove lines, and developer who frequently modify it
    
    important (commits much) developers and their add/remove/modify lines in commit
    important (commits specific type much) developers and their add/remove/modify lines in commit
    
    for each time zone, count of developers, add lines, remove lines, modify lines, feature/fix/other/total amount
    
write file:
    monthly_commit_state.csv    : month, (types of)commit amount, (types of)lines
    monthly_file_state.csv      : (top 80% modified file) month, file_path, (types of)commit amount, (types of)lines, core developers
    monthly_father_path_state.csv:(top 80% modified file) month, file_path, (types of)commit amount, (types of)lines, core developers
    monthly_developer_state.csv : month, author, (types of)commit amount, (types of)lines
    monthly_newcomer_state.csv  : month, author, (types of)commit amount, (types of)lines
    monthly_timezone_state.csv  : month, timezone, (types of)commit amount, (types of)lines, developers
    
'''
def extract_commit_monthly_state(path):
    ### check data under path/.gpd/data
    gpd_path = os.path.join(path, '.gpd')
    gpd_data_path = os.path.join(gpd_path, 'data')
    gpd_commit_csv_path = os.path.join(gpd_data_path, 'commit_feature.csv')
    gpd_commit_vec_path = os.path.join(gpd_data_path, 'commit_vector.csv')
    gpd_commit_class_path = os.path.join(gpd_data_path, 'commit_classification.json')

    if not os.path.exists(gpd_commit_csv_path) or not os.path.exists(gpd_commit_vec_path) \
        or not os.path.exists(gpd_commit_class_path):
        print("extract_commit_monthly_state failed due to lack data file when dealing path %s"%(gpd_commit_csv_path))
        return
        
    monthly_commit_state_path = os.path.join(gpd_data_path, 'monthly_commit_state.csv')
    if os.path.exists(monthly_commit_state_path):
        #print("The git project %s has been \"commit_vector\" before, skipping it"%(res_path))
        return
        pass
    
    ### read existing info
    with open(gpd_commit_class_path) as f:
        hash2label = json.load(f)
    commit_feature_df = pd.read_csv(gpd_commit_csv_path, index_col = 0)
    commit_vec_df = pd.read_csv(gpd_commit_csv_path, index_col = 0)
    
    re_email = re.compile('<.*@.*>')
    
    assert(len(commit_feature_df) == len(commit_vec_df))
    
    to_save_commit = []
    to_save_file = []
    to_save_father = []
    to_save_developer = []
    to_save_newcomer = []
    to_save_timezone = [] 
    
    existed_developer = set()
    first_month = None
    this_month = None
    commit_state = {'fix': 0, 'feature': 0, 'other': 0, 'add': 0, 'remove': 0, 'total': 0}
    file_state = {} ### path: path_state
    developer_state = {} ### developer: developer_state
    newcomer_state = set()
    timezone_state = {} ### time_zone: timezone_state
    
    for i in range(len(commit_feature_df)-1, -1, -1):
        r1 = commit_feature_df.iloc[i]
        r2 = commit_vec_df.iloc[i]
        sha = r1['hash']
        label = hash2label[sha]
        if label == 0:
            label = 'fix'
        elif label == 1:
            label = 'other'
        elif label == 2:
            label = 'feature'
        else:
            assert(False)
        
        author_str = r1['author']
        temp = re.search(re_email, 'author_str')
        if temp:
            email = temp.group(0)[1:-1]
            author = author_str[:-(len(email)+3)]
        else:
            arr = find_all(' ', author_str)
            if arr == -1: ### worst situation
                author = author_str
                email = ""
                #print("arr == -1", author_str, r1)
                #return
            else:
                author = author_str[:arr[-1]]
                email = author_str[arr[-1]+1:]
        existed_developer.add(author)
            
        date_str = r1['date']
        temp = date_str.split()
        assert(len(temp) >= 6)
        weekday, month, day, time, year, time_zone = temp[:6]
        month = month_map(month)
        ym = "%s_%s"%(year, month)
        if this_month is None:
            first_month = this_month = ym
        elif ym_compare(this_month, ym) == -1: ### data of one month is end, save it
            ### commit state save
            to_save_commit.append([this_month, 
                commit_state['feature'], commit_state['fix'], commit_state['other'], 
                commit_state['add'], commit_state['remove'], commit_state['total']
            ])
                    
            ### only save file which modified most (top 80% commits)
            file_modified_arr = [x['commit'] for x in file_state.values()]
            file_modified_arr.sort(reverse = True)
            total_commit = sum(file_modified_arr)
            if total_commit:
                now_total_commit = 0
                commit_amount_limit = 0 ### file path whose commits amount less than the limit, will not be saved
                for j, k in enumerate(file_modified_arr):
                    now_total_commit += k
                    if now_total_commit >= total_commit * 0.8:
                        commit_amount_limit = k
                        break
                        
                for modified_path, path_data in file_state.items():
                    if path_data['commit'] < commit_amount_limit:
                        continue
                    author_most_commit_num = max(path_data['author'].values())
                    core_author = [x for x, y in path_data['author'].items() if y == author_most_commit_num]
                    to_save_file.append([this_month, modified_path, 
                        path_data['feature'], path_data['fix'], path_data['other'], 
                        path_data['add'], path_data['remove'], path_data['total'], 
                        json.dumps(core_author)
                    ])
                    
                ### find 5 most modified father path
                father2data = {}
                for modified_path, path_data in file_state.items():
                    if '/' not in modified_path:
                        father = "__ROOT__"
                    else:
                        temp = modified_path.split('/')
                        father = "__ROOT__/" + '/'.join(temp[:-1])
                    if father not in father2data:
                        father2data[father] = {'fix': 0, 'feature': 0, 'other': 0, 'add': 0, 'remove': 0, 'total': 0, 'author': {} }
                        
                    father2data[father]['fix'] += path_data['fix']
                    father2data[father]['feature'] += path_data['feature']
                    father2data[father]['other'] += path_data['other']
                    father2data[father]['add'] += path_data['add']
                    father2data[father]['remove'] += path_data['remove']
                    father2data[father]['total'] += path_data['total']
                    
                    for developer, author_data in path_data['author'].items():
                        if developer not in father2data[father]['author']:
                            father2data[father]['author'][developer] = 0
                        father2data[father]['author'][developer] += author_data
                ### get top 5 modified father path
                temp = [x['total'] for x in father2data.values()]
                if len(temp) >= 5:
                    father_commit_limit = temp[4]
                else:
                    father_commit_limit = 0
                for father, fdata in father2data.items():
                    if fdata['total'] < father_commit_limit:
                        continue
                    ### get core author
                    temp = max(fdata['author'].values())
                    core_author = [x for x, y in fdata['author'].items() if y == temp]
                    to_save_father.append([this_month, father, 
                        fdata['feature'], fdata['fix'], fdata['other'], 
                        fdata['add'], fdata['remove'], fdata['total'], 
                        json.dumps(core_author)
                    ])
            
            
            ### developer state save
            for developer, author_data in developer_state.items():
                to_save_developer.append([this_month, developer, 
                    author_data['feature'], author_data['fix'], author_data['other'], 
                    author_data['add'], author_data['remove'], author_data['total']
                ])
                
            ### newcomer state save
            for developer in newcomer_state:
                author_data = developer_state[developer]
                to_save_newcomer.append([this_month, developer, 
                    author_data['feature'], author_data['fix'], author_data['other'], 
                    author_data['add'], author_data['remove'], author_data['total']
                ])
                
            ### timezone state save
            for timezone, tz_data in timezone_state.items():
                to_save_timezone.append([this_month, timezone, 
                    tz_data['feature'], tz_data['fix'], tz_data['other'], 
                    tz_data['add'], tz_data['remove'], tz_data['total']
                ])
            
            this_month = ym
            commit_state = {'fix': 0, 'feature': 0, 'other': 0, 'add': 0, 'remove': 0, 'total': 0}
            file_state = {} ### path: path_state
            developer_state = {} ### developer: developer_state
            newcomer_state = set()
            timezone_state = {} ### time_zone: timezone_state
            
        if author not in existed_developer and more_than_year(first_month, ym):
            newcomer_state.add(author)
            existed_developer.add(author)
        
        path_summary = json.loads(r1['path_summary'])
        add_line_num = 0
        remove_line_num = 0
        for arr in path_summary:
            add_line = 0
            remove_line = 0
            if arr[0].isdigit():
                add_line = int(arr[0])
                add_line_num += add_line
            if arr[1].isdigit():
                remove_line = int(arr[0])
                remove_line_num += remove_line
                
            modified_path = arr[2]
            
            if modified_path not in file_state:
                file_state[modified_path] = { 'fix': 0, 'feature': 0, 'other': 0, 'commit': 0, 
                    'add': 0, 'remove': 0, 'total': 0, 'author': {} }
            file_state[modified_path]['commit'] += 1
            file_state[modified_path][label] += 1
            file_state[modified_path]['add'] += add_line
            file_state[modified_path]['remove'] += remove_line
            file_state[modified_path]['total'] += (add_line + remove_line)
            if author not in file_state[modified_path]['author']:
                file_state[modified_path]['author'][author] = 0
            file_state[modified_path]['author'][author] += 1
            
        total_modified_num = add_line_num + remove_line_num
        commit_state[label] += 1
        commit_state['add'] += add_line_num
        commit_state['remove'] += remove_line_num
        commit_state['total'] += total_modified_num
        
        if author not in developer_state:
            developer_state[author] = {'fix': 0, 'feature': 0, 'other': 0, 'add': 0, 'remove': 0, 'total': 0}
        developer_state[author][label] += 1
        developer_state[author]['add'] += add_line_num
        developer_state[author]['remove'] += remove_line_num
        developer_state[author]['total'] += total_modified_num
        
        if time_zone not in timezone_state:
            timezone_state[time_zone] = {'fix': 0, 'feature': 0, 'other': 0, 'add': 0, 'remove': 0, 'total': 0}
        timezone_state[time_zone] = {'fix': 0, 'feature': 0, 'other': 0, 'add': 0, 'remove': 0, 'total': 0}
        timezone_state[time_zone][label] += 1
        timezone_state[time_zone]['add'] += add_line_num
        timezone_state[time_zone]['remove'] += remove_line_num
        timezone_state[time_zone]['total'] += total_modified_num
          
    ### 循环结束后，也需要进行下面的这些存储，不然会丢掉最后一个月信息
    
    ### commit state save
    to_save_commit.append([this_month, 
        commit_state['feature'], commit_state['fix'], commit_state['other'], 
        commit_state['add'], commit_state['remove'], commit_state['total']
    ])
            
    ### only save file which modified most (top 80% commits)
    file_modified_arr = [x['commit'] for x in file_state.values()]
    file_modified_arr.sort(reverse = True)
    total_commit = sum(file_modified_arr)
    if total_commit:
        now_total_commit = 0
        commit_amount_limit = 0 ### file path whose commits amount less than the limit, will not be saved
        for j, k in enumerate(file_modified_arr):
            now_total_commit += k
            if now_total_commit >= total_commit * 0.8:
                commit_amount_limit = k
                break
                
        for modified_path, path_data in file_state.items():
            if path_data['commit'] < commit_amount_limit:
                continue
            author_most_commit_num = max(path_data['author'].values())
            core_author = [x for x, y in path_data['author'].items() if y == author_most_commit_num]
            to_save_file.append([this_month, modified_path, 
                path_data['feature'], path_data['fix'], path_data['other'], 
                path_data['add'], path_data['remove'], path_data['total'], 
                json.dumps(core_author)
            ])
            
        ### find 5 most modified father path
        father2data = {}
        for modified_path, path_data in file_state.items():
            if '/' not in modified_path:
                father = "__ROOT__"
            else:
                temp = modified_path.split('/')
                father = "__ROOT__/" + '/'.join(temp[:-1])
            if father not in father2data:
                father2data[father] = {'fix': 0, 'feature': 0, 'other': 0, 'add': 0, 'remove': 0, 'total': 0, 'author': {} }
                
            father2data[father]['fix'] += path_data['fix']
            father2data[father]['feature'] += path_data['feature']
            father2data[father]['other'] += path_data['other']
            father2data[father]['add'] += path_data['add']
            father2data[father]['remove'] += path_data['remove']
            father2data[father]['total'] += path_data['total']
            
            for developer, author_data in path_data['author'].items():
                if developer not in father2data[father]['author']:
                    father2data[father]['author'][developer] = 0
                father2data[father]['author'][developer] += author_data
        ### get top 5 modified father path
        temp = [x['total'] for x in father2data.values()]
        if len(temp) >= 5:
            father_commit_limit = temp[4]
        else:
            father_commit_limit = 0
        for father, fdata in father2data.items():
            if fdata['total'] < father_commit_limit:
                continue
            ### get core author
            temp = max(fdata['author'].values())
            core_author = [x for x, y in fdata['author'].items() if y == temp]
            to_save_father.append([this_month, father, 
                fdata['feature'], fdata['fix'], fdata['other'], 
                fdata['add'], fdata['remove'], fdata['total'], 
                json.dumps(core_author)
            ])
    
    ### developer state save
    for developer, author_data in developer_state.items():
        to_save_developer.append([this_month, developer, 
            author_data['feature'], author_data['fix'], author_data['other'], 
            author_data['add'], author_data['remove'], author_data['total']
        ])
        
    ### newcomer state save
    for developer in newcomer_state:
        author_data = developer_state[developer]
        to_save_newcomer.append([this_month, developer, 
            author_data['feature'], author_data['fix'], author_data['other'], 
            author_data['add'], author_data['remove'], author_data['total']
        ])
        
    ### timezone state save
    for timezone, tz_data in timezone_state.items():
        to_save_timezone.append([this_month, timezone, 
            tz_data['feature'], tz_data['fix'], tz_data['other'], 
            tz_data['add'], tz_data['remove'], tz_data['total']
        ])
        
    new_df = pd.DataFrame(to_save_commit, columns=['month', 'feature', 'fix', 'other', 'add', 'remove', 'total'])
    new_df.to_csv(monthly_commit_state_path)
    
    monthly_file_state_path = os.path.join(gpd_data_path, 'monthly_file_state.csv')
    new_df = pd.DataFrame(to_save_file, columns=['month', 'path', 'feature', 'fix', 'other', 'add', 'remove', 'total', 'core_developer'])
    new_df.to_csv(monthly_file_state_path)
    
    monthly_father_path_state_path = os.path.join(gpd_data_path, 'monthly_father_path_state.csv')
    new_df = pd.DataFrame(to_save_father, columns=['month', 'path', 'feature', 'fix', 'other', 'add', 'remove', 'total', 'core_developer'])
    new_df.to_csv(monthly_father_path_state_path)
        
    monthly_developer_state_path = os.path.join(gpd_data_path, 'monthly_developer_state.csv')
    new_df = pd.DataFrame(to_save_developer, columns=['month', 'developer', 'feature', 'fix', 'other', 'add', 'remove', 'total'])
    new_df.to_csv(monthly_developer_state_path)
    
    monthly_newcomer_state_path = os.path.join(gpd_data_path, 'monthly_newcomer_state.csv')
    new_df = pd.DataFrame(to_save_newcomer, columns=['month', 'developer', 'feature', 'fix', 'other', 'add', 'remove', 'total'])
    new_df.to_csv(monthly_newcomer_state_path)
    
    monthly_timezone_state_path = os.path.join(gpd_data_path, 'monthly_timezone_state.csv')
    new_df = pd.DataFrame(to_save_timezone, columns=['month', 'timezone', 'feature', 'fix', 'other', 'add', 'remove', 'total'])
    new_df.to_csv(monthly_timezone_state_path)
    
        
if __name__ == "__main__":
    #commit_vector("C:\\Users\\Pit\\Downloads\\毕业相关\\dataset\\Java\\error-prone", limit=10)
    #commit_vector("C:\\Users\\Pit\\Downloads\\毕业相关\\dataset\\Python\\autokeras", limit=10)
    #commit_vector("C:\\Users\\Pit\\Downloads\\毕业相关\\dataset\\JavaScript\\charts", limit=10)
    commit_vector("C:\\Users\\Pit\\Downloads\\毕业相关\\dataset\\TypeScript\\core", limit=10)