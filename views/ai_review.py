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

    data = dict()
    keypoints = dict()
    for res in result:
        img_id = res.get('img_id')
        lines = []
        keypoint = []
        for key_line in key_lines:
            x1 = res.get('x{}'.format(key_line[0]+1))
            y1 = res.get('y{}'.format(key_line[0]+1))
            x2 = res.get('x{}'.format(key_line[1]+1))
            y2 = res.get('y{}'.format(key_line[1]+1))
            leng_lines = leng_line([x1,y1],[x2,y2])
            lines.append(leng_lines)
        for i in range(1,15):
            x = res.get('x{}'.format(i+1))
            y = res.get('y{}'.format(i+1))
            point = dict()
            point['x'] = x
            point['y'] = y
            keypoint.append(point)
        data[img_id] = lines
        keypoints[img_id] = keypoint

    mean_lines = mean_line(data.values())
    # var_lines = var_line(data, mean_lines)
    set_label_status(data, mean_lines, keypoints)
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



def set_label_status(data, mean_lines, keypoints):
    '''
    筛选设置骨骼点状态
    '''
    pass_img_v1, fail_img_v1 = error_line_filter(data, mean_lines)
    print('error line')
    pass_img, fail_img_v2 = error_keypoint_filter(keypoints, pass_img_v1)
    print('error point')
    fail_img_v1 += fail_img_v2
    fail_img = fail_img_v1

    sql = '''update ai_label_skeleton set status = 1 where img_id in ({})'''.format(','.join(fail_img))
    print(sql)
    db_file(sql)
    sql = '''update ai_label_skeleton set status = 3 where img_id in ({})'''.format(','.join(pass_img))
    print(sql)
    db_file(sql)


def error_line_filter(data, mean_lines):
    """
    筛选出骨骼线不合格的标注
    """
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
    return pass_img, fail_img

def error_keypoint_filter(keypoints, pass_img_v1):
    """
    筛选出骨骼点对称错乱标注
    """
    fail_img_v2 = []
    pass_img_v2 = []
    for img_id in pass_img_v1:
        keypoint = keypoints.get(int(img_id))
        l_shoulder = keypoint[2]
        r_shoulder = keypoint[3]
        l_hip = keypoint[8]
        r_hip = keypoint[9]
        l_ankle = keypoint[10]
        r_ankle = keypoint[11]
        l_foot = keypoint[12]
        r_foot = keypoint[13]

        need_keypoints = [l_shoulder, l_hip, l_ankle, l_foot, r_shoulder, r_hip, r_ankle, r_foot]
        ### 忽略躺着的状态
        x_min, x_max, y_min, y_max = l_shoulder['x'], l_shoulder['y'], l_shoulder['y'], l_shoulder['y']
        for keypoint in need_keypoints:
            x_min = min(keypoint['x'], x_min)
            x_max = max(keypoint['x'], x_max)
            y_min = min(keypoint['y'], y_min)
            y_max = max(keypoint['y'], y_max)
        if x_max - x_min >= y_max - y_min:
            continue
        print('ddd')
        ### 筛选骨骼点错乱标注
        shoulder = 1 if need_keypoints[0]['x'] > need_keypoints[4]['x'] else 0
        hip = 1 if need_keypoints[1]['x'] > need_keypoints[5]['x'] else 0
        ankle = 1 if need_keypoints[2]['x'] > need_keypoints[6]['x'] else 0
        foot = 1 if need_keypoints[3]['x'] > need_keypoints[7]['x'] else 0
        if (shoulder ^ hip) + (hip ^ ankle) + (ankle ^ foot) > 1:
            fail_img_v2.append(str(img_id))
        else:
            pass_img_v2.append(str(img_id))
        print(img_id)
    return pass_img_v2, fail_img_v2
    