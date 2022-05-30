from http.client import OK
from app import app
from flask import request
from model import db_file 
import math

@app.route('/ai_review', methods = ['POST'])
def ai_review():
    '''
    机器评审
    '''
    filePath = request.values.get('filePath', '')
    response = {'code':1}
    if not filePath:
        response['msg'] = '路径错误'
        return response

    # 获取图片id
    sql = '''select img_id from ai_image where path = "{}" and status = 0'''.format(filePath)
    print(sql)
    result = db_file(sql)
    if not result:
        response['msg'] = '没有找到图片'
        return response
    result = [str(res.get('img_id')) for res in result]
    img_ids = ','.join(result)

    # 获取标注数据
    sql = '''select * from ai_label_skeleton where img_id in ({})'''.format(img_ids)
    print(sql)
    result = db_file(sql)
    key_lines = [[0,1],[1,2],[1,3],[2,4],[3,5],[4,6],[5,7],[8,10],[9,11],[10,12],[11,13],[2,8],[3,9],[8,9]]

    data = {}
    for res in result:
        img_id = res.get('img_id')
        lines = []
        for key_line in key_lines:
            x1 = res.get('x{}'.format(key_line[0]+1))
            y1 = res.get('y{}'.format(key_line[0]+1))
            x2 = res.get('x{}'.format(key_line[1]+1))
            y2 = res.get('y{}'.format(key_line[1]+1))
            leng_lines = leng_line([x1,y1],[x2,y2])
            lines.append(leng_lines)
        data[img_id] = lines
    
    mean_lines = mean_line(data.values())
    set_label_status(data, mean_lines)
    response['code'] = 0
    response['msg'] = 'ok'
    return response



def leng_line(line1, line2):
    '''
    计算两点长度
    '''
    x1 = line1[0]
    y1 = line1[1]
    x2 = line2[0]
    y2 = line2[1]
    res = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    return res

def mean_line(lines):
    '''
    计算总骨骼点之间的平均值
    '''
    res_lines = [0] * 14
    leng = len(lines)
    for line in lines:
        for i in range(14):
            res_lines[i] += line[i]
    for i in range(14):
        res_lines[i] /= leng
    return res_lines


def set_label_status(data, mean_lines):
    '''
    筛选设置骨骼点状态
    '''
    pass_img = []
    fail_img = []
    for img_id in data:
        flag = 0
        lines = data.get(img_id)
        for i in range(14):
            if lines[i] > mean_lines[i] * 2:
                flag = 1
                break
        if flag:
            fail_img.append(str(img_id))
        else:
            pass_img.append(str(img_id))
    sql = '''update ai_label_skeleton set status = 1 where img_id in ({})'''.format(','.join(fail_img))
    print(sql)
    db_file(sql)
    sql = '''update ai_label_skeleton set status = 3 where img_id in ({})'''.format(','.join(pass_img))
    print(sql)
    db_file(sql)










