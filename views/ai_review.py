from http.client import OK
from app import app
from flask import request
from model import db_file 
import math

# 算法二次评估/全部算法
@app.route('/label_check', methods = ['POST'])
def ai_review():
    '''
    机器评审,status:合格为3,不合格为2,没有检测的为0
    骨骼点之间的距离差距太大就是不合格
    '''
#    filePath = request.values.get('filePath', '')
    checkType = request.values.get('checkType', 'all') #undefined，没有传入数据的意思
    response = {'code':1}
#    if not filePath:
#        response['msg'] = '路径错误'
#        return response
#    if checkType not in ('all', 'line_filter', 'point_filter'):
#        response['msg'] = 'checkType参数错误'
#        return response
#
#    # 获取文件路径
#    sql = '''select filePath, fileName from userfile where userFileId in ({}) and isDir=1'''.format(filePath)
#    result = db_file(sql)
#    print(result)
#    filePaths = list()
#    for res in result:
#        file_name = "'{}{}/'".format(res.get('filePath'),res.get('fileName'))
#        print(file_name)
#        filePaths.append(file_name)
#    print(filePaths)
#    # 获取图片id
#    sql = '''select img_id from ai_image where path in ({}) and status = 0'''.format(','.join(filePaths))
#    print(sql)
#    result = db_file(sql)
#    if not result:
#        response['msg'] = '没有找到图片'
#        return response
#    result = [str(res.get('img_id')) for res in result]
#    img_ids = ','.join(result)

    fileIds = request.values.get('userFileIds','') # 1007935
    if not fileIds:
        # 没有选择图片就机器评审
        response['msg'] = 'fileIds不能为空'
        return response 
    sql = '''select img_id from ai_image where file_id in ({})'''.format(fileIds)
    print(sql)
    # img_id:266590
    result = db_file(sql)
    if not result:
        # 没有进行骨骼点预测的图片在数据库中没有img_id
        response['msg'] = '找不到对应的文件'
        return response
    # 有多个img_id就用逗号分隔开，一个的时候就是原样    
    img_ids = ','.join([str(res.get('img_id')) for res in result])

    # 根据查询到的img_id获取ai_label_skeleton表中的标注数据
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
            # 计算两点长度
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

    if not data:
        return response
    # 计算总骨骼点之间的平均值    
    mean_lines = mean_line(data.values())
    # var_lines = var_line(data, mean_lines)

    # 筛选设置骨骼点状态
    set_label_status(data, mean_lines, keypoints, checkType)
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



def set_label_status(data, mean_lines, keypoints, checkType):
    '''
    筛选设置骨骼点状态
    '''
    fail_img = list()
    fail_img_v1, fail_img_v2 = list(), list()
    pass_img = data.keys()
    if checkType in ('all', 'line_filter'):
        # 筛选出骨骼线不合格的标注
        pass_img, fail_img_v1 = error_line_filter(data, mean_lines)
        print('line filter')
    if checkType in ('all', 'point_filter'):
        # 筛选出骨骼点对称错乱标注
        pass_img, fail_img_v2 = error_keypoint_filter(keypoints, pass_img)
        print('point filter')
    fail_img = fail_img_v1 + fail_img_v2

    print(fail_img)
    print(pass_img)
    pass_img = [str(pass_id) for pass_id in pass_img]
    if fail_img:
        sql = '''update ai_label_skeleton set status = 1 where img_id in ({})'''.format(','.join(fail_img))
        print(sql)
        db_file(sql)
    if pass_img:
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
    
