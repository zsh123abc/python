import os
import glob
import csv
import xml.etree.ElementTree as ET
from model import db_file
from app import app
from flask import jsonify, request
import json
from PIL import Image
from config import DIR
from . import database as db
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import time
import skimage.io as io
import asyncio
import cv2
from .ai_robot import convert
from ai_robot import *

# 获取xml文件的骨骼点信息
# xmlpath，xml文件存放的路径
# @app.route('/point/<path:localSystemFilePath>', methods=['GET'])
def get_point(xmlpath):
    # ET.parse 从文件读取xml文件信息，分为文件读入和字符串读入
    # xmlpath为上传的xml文件或xml文件路径，返回骨骼点
    tree = ET.parse(xmlpath)
    # 获取根节点
    root = tree.getroot() # annotation
    # 定义空字典
    person = {}
    # 循环对根节点中的数据进行操作
    for obj in root:
        # obj.tag 获取节点名字，str类型
        if obj.tag == "image":
            # obj.text 获取节点的文本值 str类型
            person["image"] = obj.text # <image>1324443197.mp4_test_0390</image>
        if obj.tag == "subcategory":
            person["subcategory"] = obj.text # <subcategory>male</subcategory>
        if obj.tag == "keypoints":
            person["keypoints"] = {}
            # 获取keypoints的子节点信息
            for child in obj:
                # child.attrib["name"] 获取节点中name属性值
                name = child.attrib["name"]
                # child.attrib 获取节点全部属性值，dict（字典）类型
                person["keypoints"][name] = child.attrib
    # 返回一个储存节点信息的字典
    # person = {'image':'1324443197.mp4_test_0390',
    #           'subcategory':'male',
    #           'keypoints':'{B_Head:(0.0,273.0.151.0.0.0,2)}'
    #     }       
    return person


# 获取节点类型
def get_dbtype_point(person):
    # 人体关节点
    person_keys = ['B_Head', 'Neck', 'L_Shoulder', 'R_Shoulder', 'L_Elbow', 'R_Elbow', 'L_Wrist', 'R_Wrist', 'L_Hip',
                   'R_Hip', 'L_Knee', 'R_Knee', 'L_Ankle', 'R_Ankle', 'Nose', 'L_Ear', 'L_Eye', 'R_Eye', 'R_Ear']
    # 定义空列表
    keypoint = []
    # keypoints':'{B_Head:(0.0,273.0.151.0.0.0,2)}
    for key in person['keypoints']:
        # index（）检测字符串中是否包含某子串，包含就返回首次出现的索引
        idx = person_keys.index(key) + 1 # 下标从0开始，所有+1，1
        # 循环取出每项数据
        for item in ['x', 'y', 'z', 'zorder', 'visible']:
            # 格式化字符串拼接
            # s = 'x1=0.0',记录下每个骨骼点的坐标
            s = '%s%d=%s' % (item, idx, person['keypoints'][key][item])
            # 拼接完添加进列表
            keypoint.append(s)
    # 所有数据添加完后返回keypoint列表     
    # 一次keypoint[]储存了一张图片的所有骨骼点的标注位置
    return keypoint


# 创建节点并且保存至数据库中
# @app.route('/createpoint/<path:localSystemFilePath>', methods=['GET'])
# 人，图片id，人id
def create_point(person, img_id, person_id):
    # 获取空的节点
    keypoint = get_dbtype_point(person)
    person_id = int(person_id)
    img_id = int(img_id)
    status = 0
    # 插入数据
    sql = '''insert into ai_label_skeleton set person_id=%d,img_id=%d,status=%d,%s''' % (
        person_id, img_id, status, ','.join(keypoint))
    print(sql)
    db_file(sql)
    # sql = '''select max(label_id) as id from ai_label_skeleton'''
    # 查询数据
    sql = '''select label_id from ai_label_skeleton where img_id={}'''.format(img_id)
    label_id = db_file(sql)[0]['label_id']
    try:
        tag = person['subcategory']
        sql = '''select tag_id from ai_tag where tag="{}"'''.format(tag)
        res = db_file(sql)
        if not res:
            sql = '''insert into ai_tag set tag="{}"'''.format(tag)
            db_file(sql)
            sql = '''select tag_id from ai_tag where tag="{}"'''.format(tag)
            res = db_file(sql)
        tag_id = res[0]['tag_id']
        sql = '''insert into ai_label_tag set tag_id={},label_id={}'''.format(tag_id, label_id)
        db_file(sql)
    except:
        pass


# 从数据库获取单个节点
def get_db_point(userFileId):
    # 数据库获取节点
    sql = '''select * from ai_image as img,ai_label_skeleton as label where img.file_id = {} and img.img_id = label.img_id'''.format(
        userFileId)
    result = db_file(sql)
    # 节点不存在退出并且返回None
    if not result:
        return None
    # 能到这里就说明获取到节点了
    # 把第一位节点取出来
    # img_id:266590
    result = result[0]
    # 人体关节点
    person_keys = ['B_Head', 'Neck', 'L_Shoulder', 'R_Shoulder', 'L_Elbow', 'R_Elbow', 'L_Wrist', 'R_Wrist', 'L_Hip',
                   'R_Hip', 'L_Knee', 'R_Knee', 'L_Ankle', 'R_Ankle', 'Nose', 'L_Ear', 'L_Eye', 'R_Eye', 'R_Ear']
    # 定义两个空字典    
    data = {}
    keypoints = {}
    # 循环把每一个节点赋值上信息
    for i in range(19):
        keypoints[person_keys[i]] = {}
        keypoints[person_keys[i]]['x'] = result['x' + str(i + 1)]
        keypoints[person_keys[i]]['y'] = result['y' + str(i + 1)]
        keypoints[person_keys[i]]['z'] = result['z' + str(i + 1)]
        keypoints[person_keys[i]]['zorder'] = result['zorder' + str(i + 1)]
        keypoints[person_keys[i]]['visible'] = result['visible' + str(i + 1)]
    data['person_id'] = result['person_id']
    data['keypoints'] = keypoints
    # 返回储存节点信息的字典
    return data


# 从数据库获取多个节点
def get_db_points(userFileIds):
    # sql查询
    sql = '''select * from ai_image as img,ai_label_skeleton as label where img.file_id in 
    ({}) and img.img_id = label.img_id'''.format(
        userFileIds)
    result = db_file(sql)
    if not result:
        return None
    # 人体关节点
    person_keys = ['B_Head', 'Neck', 'L_Shoulder', 'R_Shoulder', 'L_Elbow', 'R_Elbow', 'L_Wrist', 'R_Wrist', 'L_Hip',
                   'R_Hip', 'L_Knee', 'R_Knee', 'L_Ankle', 'R_Ankle', 'Nose', 'L_Ear', 'L_Eye', 'R_Eye', 'R_Ear']
    resp = []
    for res in result:
        # sql查询,查询到
        # filename，video_1.mp4_test_0426
        # filepath,/zsh/videos/label_data/images/
        sql = '''select fileName,filePath from userfile where userFileId={}'''.format(res['file_id'])
        # 通过文件id查询图片名字
        img = db_file(sql)[0]['fileName'] # 17 (1)0011
        # 数据库查询图片路径
        filepath = db_file(sql)[0]['filePath']# /zsh/label_data/images/
        # 储存人体关节的数据
        data = {}
        # 储存人体关节点的顺序
        keypoints = {}
        # 19个关节点循环19次
        for i in range(19):
            # k:person_keys,v:{}
            keypoints[person_keys[i]] = {}
            # 字典嵌套字典
            # 记录人体关键点的 坐标(x,y,z)，下一张，可见度
            # k：x，v：res['x'+str(i+1)]
            # 记录每个关节点的顺序
            keypoints[person_keys[i]]['x'] = res['x' + str(i + 1)]
            keypoints[person_keys[i]]['y'] = res['y' + str(i + 1)]
            keypoints[person_keys[i]]['z'] = res['z' + str(i + 1)]
            # k:zorder, v:res['zorder'+str(i+1)]
            keypoints[person_keys[i]]['zorder'] = res['zorder' + str(i + 1)]
            keypoints[person_keys[i]]['visible'] = res['visible' + str(i + 1)]
        # 人体关节点对应的id
        data['person_id'] = res['person_id']
        # 图片
        data['image'] = img
        data['keypoints'] = keypoints
        # 文件存放路径
        data['filepath'] = filepath
        data['label_id'] = res['label_id']
        # 所有数据放进resp列表中
        resp.append(data)
    # 返回resp退出
    return resp


# 获取标签状态
def get_label_status(userFileId):
    # 根据id查询标签
    sql = '''select label.status as status from ai_label_skeleton as label,
        ai_image as image where image.file_id={} and image.img_id = label.img_id limit 1'''.format(userFileId)
    # status:0    
    result = db_file(sql)
    resp = {}
    # 判断是否查询到结果
    if result:
        # 记录标签状态
        status = result[0]['status'] # 0
        resp['status'] = status
        resp['code'] = 0
        resp['msg'] = '成功'
    else:
        resp['code'] = 1
        resp['msg'] = '没有标注数据'
    # 返回储存标签状态的resp字典    
    return resp


# 把预测的骨骼点显示出来
# 用cv2画出来，给定坐标 
@app.route('/get_labelimage', methods=['GET'])
def get_labelimage():
    # time1 = time.time()
    # 获取isMin的所有参数
    isMin = request.values.get('isMin')
    userFileId = request.values.get('userFileId')
    # 判断是否查询到结果，没有结果返回退出
    if not db_file('''select * from ai_image where file_id = {} limit 1'''.format(userFileId)):
        data = {}
        data['code'] = 1
        data['msg'] = '标注文件不存在'
        # 将python对象编码成Json字符串
        return json.dumps(data)
    # get_image_path() 根据id获取图片路径
    # /zsh/label_data/images/17 (1)0011.jpg
    filepath = db.get_image_path(userFileId)
    # 用'/'分割图片路径
    # ['', 'zsh', 'label_data', 'images', '17 (1)0011.jpg']
    filelist = filepath.split('/')
    # os.chdir(DIR)

    # 图片路径
    # 加上根目录路径
    # /data/dataset/zsh/label_data/images/17 (1)0011.jpg
    imgpath = DIR + filepath

    data = {}
    data['code'] = 1
    data['msg'] = '打开文件失败'


    # 判断路径或数据是否有错误
    # 文件路径必须是：label_data/images/图片
    if len(filelist) < 3 or filelist[-2] != 'images' or filelist[-3] != 'label_data' or isMin not in ('true', 'false'):
        data = {}
        data['status'] = 0
        data['code'] = 1
        data['msg'] = '文件非图片或请求参数错误'
        return data
    # 根据id从数据库获取单个节点
    # data['person_id':xxx,'keypoints':xxx]
    data = get_db_point(userFileId)
    # 判断是否取出数据
    if not data:
        data = {}
        data['code'] = 1
        data['msg'] = "没有标注文件"
        return data
    # 关节点
    keys = ['B_Head', 'Neck', 'L_Shoulder', 'R_Shoulder', 'L_Elbow', 'R_Elbow', 'L_Wrist', 'R_Wrist', 'L_Hip',
            'R_Hip', 'L_Knee', 'R_Knee', 'L_Ankle', 'R_Ankle', 'Nose', 'L_Ear', 'L_Eye', 'R_Eye', 'R_Ear']
    point_x = []
    point_y = []
    point_v = []
    # 除了'Nose','L_Ear','L_Eye','R_Eye','R_Ear'，其他点都记录顺序
    lines = [[0, 1], [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7], [8, 10], [9, 11], [10, 12], [11, 13], [2, 8],
             [3, 9], [8, 9]]
    # 取出每一个关节点
    for key in keys:
        # 判断关节点是否在data字典里
        if key in data['keypoints']:
            # 迭代到鼻，耳朵，眼睛这些关节点就跳过
            if key in ['Nose', 'L_Ear', 'L_Eye', 'R_Eye', 'R_Ear']:
                # 跳出本次循环
                continue
            # 把每个关键点对应的 x，y(坐标)，v(可见度)存放进对应的列表
            # float() 转换成浮点型
            point_x.append(float(data['keypoints'][key]['x']))
            point_y.append(float(data['keypoints'][key]['y']))
            # int() 转换成整型
            point_v.append(int(data['keypoints'][key]['visible']))
    # for line in lines:
    #     point1,point2 = line
    #     x1 = point_x[point1]
    #     x2 = point_x[point2]
    #     y1 = point_y[point1]
    #     y2 = point_y[point2]
    #     plt.plot([x1,x2],[y1,y2], linewidth=linewidth, color='black')

    # plt.plot(point_x,point_y,'.',markersize=size)
    # plt.show()

    '''
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    cv2处理图片
    '''
    # cv2读入图片
    img = cv2.imread(imgpath)

    # 取出每一个关键点对应的数据
    for line in lines:
        # [0,1]
        point1, point2 = line
        # 取出每个点对应的x，y
        x1 = point_x[point1]
        x2 = point_x[point2]
        y1 = point_y[point1]
        y2 = point_y[point2]

        # 开始点
        start_point = (int(x1), int(y1))
        # 结束点
        end_point = (int(x2), int(y2))
        # 判断开始点和结束点的坐标是否为（0,0）
        if start_point == (0, 0) or end_point == (0, 0):
            # 退出本次循环
            continue
        # 判断两个坐标点是否存在
        if point_v[point1] and point_v[point2]:
            '''
            cv2.line 画线条
            五个参数：
                img:要划的线所在的图像;
                pt1:直线起点
                pt2:直线终点  （坐标分别为宽、高,opencv中图像的坐标原点在左上角)
                color:直线的颜色
                thickness=1:线条粗细,默认是1.如果一个闭合图形设置为-1,那么整个图形就会被填充
            '''
            cv2.line(img, start_point, end_point, (0, 255, 0), 5)
    # 处理14个关键点，鼻子，耳朵，眼睛不要
    for i in range(14):
        # if point_v[i]：[0,1]
        if point_v[i]:
            # cv2.circle()-画圆,和cv2.line()的参数大致相同
            cv2.circle(img, (int(point_x[i]), int(point_y[i])), 3, (255, 0, 0), 3)
    if isMin == 'true':
        # img.shape 获取图片尺寸
        ori_h, ori_w, _ = img.shape
        # 等比例裁剪成150*150 
        if ori_h <= ori_w:
            h = 150
            # '//' 除完返回的是整型，'/'返回的是浮点型
            w = ori_w * 150 // ori_h
            # 扩展或缩小图片尺寸 img 读入的图片，(w, h) 指定图片的尺寸
            img = cv2.resize(img, (w, h))
            t = (w - 150) // 2
            # img.copy复制图像
            img = img[0:150, t:w - t].copy()
        else:
            h = ori_h * 150 // ori_w
            w = 150
            # 扩展或缩小图片尺寸 img 读入的图片，(w, h) 指定图片的尺寸
            img = cv2.resize(img, (w, h))
            t = (h - 150) // 2
            # img.copy复制图像
            img = img[t:h - t, 0:150].copy()
        # img = cv2.resize(img, (150,150))
        # cv2.imencode()函数是将图片格式转换(编码)成流数据，按 jpeg 格式编码
        # 赋值到内存缓存中;主要用于图像数据格式的压缩，方便网络传输。
        image = cv2.imencode('.jpeg', img)[1]
        
        src = 'data:image/jpeg;base64,'

    else:
        # img = cv2.resize(img, (450,450))
        '''
        cv2.imencode()函数是将图片格式转换(编码)成流数据，
        赋值到内存缓存中;主要用于图像数据格式的压缩，方便网络传输。
        对应的 cv2.imdecode()，用于解码
        返回的数据是长度2的元组
        '''
        image = cv2.imencode('.jpg', img)[1]

        src = 'data:image/jpg;base64,'
    # b64encode函数主要是使用Base64对bytes-like类型对象进行 编码(加密) 并返回bytes对象    
    # bytes类型：\x00\x00\x00\x00\x00
    # bytes 数据类型是utf-8格式的 二进制 形式的 不可变序列
    image = str(base64.b64encode(image))[2:-1]

    image = src + image
    # 获取指定id的标签状态，resp字典
    resp = get_label_status(userFileId)
    # 在resp字典中加入image图片数据
    resp['image'] = image
    return resp




# 保存xml文件到数据库
def xmlsave():
    n = 0
    # 查询
    sql = "select filePath, fileName from userfile where extendName='xml' and filePath like '%/label_data/info/'"
    result = db_file(sql)
    for res in result:
        # 在文件路径中加入images/
        path = res['filePath'][:-5] + 'images/'
        # 文件名字
        name = res['fileName'][:-2]
        # 数据库查询
        sql = "select userFileId,extendName from userfile where filePath='{}' and fileName='{}'".format(path, name)
        ans = db_file(sql)
        # 判断是否查询到数据
        if not ans:
            # 没有数据退出本次循环
            continue
        # 取出ans第0位中userFileId对应的数据
        userFileId = ans[0]['userFileId']
        # 取出ans第0位中extendName对应的数据
        extendName = ans[0]['extendName']
        try:
            # sql插入数据
            sql = """insert into ai_image set file_id={},path='{}',type='{}',status=0""".format(userFileId, path,
                                                                                                extendName)
            db_file(sql)
            # 查询
            sql = """select max(img_id) as id from ai_image"""
            # 图片id
            img_id = db_file(sql)[0]['id']
            # 文件路径
            filePath = DIR + res['filePath'] + res['fileName'] + '.xml'
            # 取出res中fileName对应的数据中的最后一位
            person_id = res['fileName'][-1]
            # 创建节点并且保存至数据库中
            create_point(filePath, img_id, person_id)
        except:
            pass
        # 每一次循环记一次数
        n += 1
        # 循环次数>1000次停两秒
        if n > 1000:
            # 睡眠两秒
            time.sleep(2)
            # 重置计数
            n = 0


# 获取标签信息
@app.route('/get_label_info')
def get_label_info():
    # 获取img_id对应的所有参数
    img_id = request.values.get('img_id')
    # 定义空字典
    resp = {}
    # code=0，正常
    resp['code'] = 0
    # 获取到节点信息
    data = get_db_point(img_id)
    if not data:
        resp['code'] = 0
    resp['data'] = data
    # 将python对象编码成Json字符串
    return json.dumps(resp)

# 置位合格/置位不合格
# 设置标签状态并保存至数据库,
# 手动判断标注文件是否合格，并将status修改，0没有检测过，2不合格，3合格
@app.route('/file/set_label_status', methods=['POST'])
def set_label_status():
    # 获取指定的表单数据
    # status 状态码 （0,1,2,3）
    status = request.form['status'] #3
    files = request.form['userFileIds'] #1007935
    # 字符串'3'转换为整型3
    status = int(status)
    resp = {}
    resp['code'] = 0
    resp['msg'] = '成功'
    # 不是0,1,2,3就说明没有状态
    if status not in (0, 1, 2, 3):
        resp['code'] = 1
        resp['msg'] = 'status is not in (0,1,2,3)'
        # 将python对象编码成Json字符串
        return json.dumps(resp)
    try:
        # sql查询
        # 根据userFileIds查到img_id
        sql = '''select img_id from ai_image where file_id in ({})'''.format(files)
        # img_id:266590
        result = db_file(sql)
        img_ids = []
        for res in result:
            img_ids.append(str(res['img_id']))
        img_ids = ','.join(img_ids)
        print(img_ids)
        # sql修改
        # 根据img_id 查到要修改的status
        # 修改ai_label_skeleton表中img_id对应的status，3为合格，2为不合格
        sql = '''update ai_label_skeleton set status={} where img_id in ({})'''.format(status, img_ids)
        print(sql)
        db_file(sql)

    except:
        # 异常处理，文件错误,
        # 没有选择图片或选择到没有骨骼点预测的图片
        resp['code'] = 1
        resp['msg'] = 'files error'
    # 将python对象编码成Json字符串    
    return json.dumps(resp)


# 骨骼点预测
# 整个目录/所选图片
# 具体实现算法在grpc服务器端
@app.route('/skeleton_calculate', methods=['GET'])
def skeleton_calculate():
    # request.values.get("key") 获取img_dir所有参数
    img_dir = request.values.get('img_dir') #/zsh/label_data/images/
    # 获取userFileIds所有参数
    userFileIds = request.values.get('userFileIds')#1007935
    # 定义一个空字典
    resp = {}
    # 数据不存在或者目录不存在，os.path.isdir()函数 判断某一路径是否为目录
    # 1007935，/zsh/label_data/images/，/data/dataset/zsh/label_data/images/
    if not userFileIds or not img_dir or not os.path.isdir(DIR + img_dir):
        resp['code'] = 1
        resp['msg'] = '输入参数错误'
        # 返回退出
        return resp

    # 导入客户端包
    from file import client
    from config import tflite_path,DIR

    # from ..file import client
    # convert(img_dir, userFileIds)
    # 通过grpc调用服务器端骨骼点预测代码
    # img_dir 图片目录，userFileIds 用户文件id
    client.skeleton_calculate(img_dir, userFileIds)

    # 集合记录需要标注的人体关节点名字
    userFileIds=''
    onnx_path=tflite_path      
    person_keys = ['B_Head','Neck','L_Shoulder','R_Shoulder','L_Elbow','R_Elbow','L_Wrist','R_Wrist','L_Hip',
        'R_Hip','L_Knee','R_Knee','L_Ankle','R_Ankle','Nose','L_Ear','L_Eye','R_Eye','R_Ear']
    # csv_output_rows = []

    p = PoseEstimator(model_path=onnx_path)

    userfile_str = ''
    if userFileIds:
        userfile_str = 'and userFileId in ({})'.format(userFileIds)

    # 查询，从userfile表中获取 userFileId,filename 两列内容
    # 条件：filePath = img_dir 并且 extendName = jpg 并且 userFileId 要在userFileIds集合里
    sql = '''select userFileId,fileName from userfile where filePath="{}" and extendName="jpg" {}'''.format(img_dir, userfile_str)
    #print(sql)
    # userFileId:1007935，fileName:17(1)0011
    result = db_file(sql)

    # 循环取出数据
    for res in result:
        print(res)
        # 文件名加上后缀,17(1)0011.jpg
        name = res['fileName'] + '.jpg'
        # userFileId,1007935
        userFileId = res['userFileId']
        # 查询ai_image表中所有列的内容
        # 条件 file_id=userFileId
        sql = '''select * from ai_image where file_id={}'''.format(userFileId)
        flag = True
        # 没有查询到数据就先插入数据，然后在查询
        if not db_file(sql):
            # insert into ai_image set 
            # set 一次插入多条数据
            sql = '''insert into ai_image set file_id={}, path="{}",type="jpg",status=0'''.format(userFileId, img_dir)
            db_file(sql)
            # 查询 ai_image 表中img_id列中 file_id = userFileId 的数据
            sql = '''select img_id from ai_image where file_id={}'''.format(userFileId)
            flag = False
        # 数据第一条中img_id对应的值，266590
        img_id = db_file(sql)[0]['img_id']
        print(flag)
        # 图片所在的绝对路径
        # /data/dataset/zsh/label_data/images/17(1)0011.jpg
        file = DIR+img_dir+name
        print(file)
        # 根据路径读入图片
        img = cv2.imread(file)
        # 没有数据就跳过本次循环
        if img is None:
            continue

        predict = p.predict(img)
        person = getPersonKeypoints(name, predict[0])

        # 空列表
        kps = []
        # 循环取出person中keypoints对应的数据
        for keypoint in person['keypoints']:
            # index() 判断字符串是否包含另一个字符串，返回第一次出现的地址，没有就抛出异常
            idx = person_keys.index(keypoint) + 1
            for k in person['keypoints'][keypoint]:
                # (k, idx, person['keypoints'][keypoint][k]) 数据所在的集合，id，数据
                # 用= 为了后面直接给sql语句使用
                str_point = '%s%s=%s' % (k, idx, person['keypoints'][keypoint][k])
                #print(str_point)
                # 列表添加数据
                kps.append(str_point)
        # 用','分开kps，并且组成一个新的字符串   
        keypoints = ','.join(kps)
        #print(keypoints)

        # 查询ai_label_skeleton表中label_id列的内容
        # 条件 img_id = img_id
        sql = '''select label_id from ai_label_skeleton where img_id={}'''.format(img_id)
        # label_id:266565
        label_result = db_file(sql)

        # 判断label_result是否为空，为空else
        # 有数据修改已有数据，没有插入新数据,骨骼点预测的坐标
        if label_result:
            # 修改ai_label_skeleton表中的person_id,status数据，set:修改多条数据，where：只修改img_id=img_id的数据
            sql = '''update ai_label_skeleton set person_id=0,status=0,{} where img_id={}'''.format(keypoints, img_id)
            db_file(sql)
        else:
            # ai_label_skeleton表插入多条数据
            sql = '''insert into ai_label_skeleton set person_id=0,status=0,img_id={},{}'''.format(img_id, keypoints)
            db_file(sql)
            # 查询ai_label_skeleton表中label_id列的数据，条件 img_id相等
            sql = '''select label_id from ai_label_skeleton where img_id={}'''.format(img_id)
            label_id = db_file(sql)[0]['label_id']
            # ai_label_skeleton表插入多条数据
            sql = '''insert into ai_label_tag set tag_id = 1,label_id={}'''.format(label_id)
            db_file(sql)

    resp['code'] = 0
    resp['msg'] = '成功'
    return resp
