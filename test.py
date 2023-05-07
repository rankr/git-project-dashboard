#coding: utf-8
import traceback

path = "C:\\Users\\Pit\\Downloads\\毕业相关\\dataset\\Java\\antlr4\\.gpd\\data\\commit_history.dat"
#path = "C:\\Users\\Pit\\Downloads\\check_commit.dat"
res = []

total = 0
cnt = 0
with open(path, 'r', newline='\r\n', encoding='utf-16') as f:
    while True:
        try:
            total += 1
            a = f.readline()
            if not a:
                break
                
            #print(a)
            #print(b)
            #break
            #res.append(a)
            if total % 1000 == 0:
                print(total)
        except:
            #res.append(a)
            traceback.print_exc()
            cnt += 1
            break
    
print(cnt, total)

print('===================================')
import codecs

total = 0
cnt = 0
with codecs.open(path, 'r', 'ISO-8859-1') as f:
    while True:
        try:
            total += 1
            a = f.readline()
            if not a:
                break
                
            #print(a)
            #print(b)
            #break
            #res.append(a)
            if total % 1000 == 0:
                print(total)
        except:
            #res.append(a)
            traceback.print_exc()
            cnt += 1
            break
    
print(cnt, total)