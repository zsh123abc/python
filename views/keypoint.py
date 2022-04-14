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

#@app.route('/point/<path:localSystemFilePath>', methods=['GET'])
def get_point(xmlpath):
    # xmlpath为上传的文件或文件路径，返回骨骼点
    tree = ET.parse(xmlpath)
    root = tree.getroot()
    person = {}
    for obj in root:
        if obj.tag == "image":
            person["image"] = obj.text
        if obj.tag == "subcategory":
            person["subcategory"] = obj.text
        if obj.tag == "keypoints":
            person["keypoints"] = {}
            for child in obj:
                name = child.attrib["name"]
                person["keypoints"][name] = child.attrib
    return person

def get_dbtype_point(person):
    person_keys = ['B_Head','Neck','L_Shoulder','R_Shoulder','L_Elbow','R_Elbow','L_Wrist','R_Wrist','L_Hip',
        'R_Hip','L_Knee','R_Knee','L_Ankle','R_Ankle','Nose','L_Ear','L_Eye','R_Eye','R_Ear']
    keypoint = []
    for key in person['keypoints']:
        idx = person_keys.index(key) + 1
        for item in ['x','y','z','zorder','visible']:
            s = '%s%d=%s'%(item, idx, person['keypoints'][key][item])
            keypoint.append(s)
    return keypoint

#@app.route('/createpoint/<path:localSystemFilePath>', methods=['GET'])
def create_point(person, img_id, person_id):
    keypoint = get_dbtype_point(person)
    person_id = int(person_id)
    img_id = int(img_id)
    status = 0
    sql = '''insert into ai_label_skeleton set person_id=%d,img_id=%d,status=%d,%s'''%(person_id, img_id, status, ','.join(keypoint))
    print(sql)
    db_file(sql)
    #sql = '''select max(label_id) as id from ai_label_skeleton'''
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
        sql = '''insert into ai_label_tag set tag_id={},label_id={}'''.format(tag_id,label_id)
        db_file(sql)
    except:
        pass

def get_db_point(userFileId):
    sql = '''select * from ai_image as img,ai_label_skeleton as label where img.file_id = {} and img.img_id = label.img_id'''.format(userFileId)
    result = db_file(sql)
    if not result:
        return None
    result = result[0]
    person_keys = ['B_Head','Neck','L_Shoulder','R_Shoulder','L_Elbow','R_Elbow','L_Wrist','R_Wrist','L_Hip',
        'R_Hip','L_Knee','R_Knee','L_Ankle','R_Ankle','Nose','L_Ear','L_Eye','R_Eye','R_Ear']
    data = {}
    keypoints = {}
    for i in range(19):
        keypoints[person_keys[i]] = {}
        keypoints[person_keys[i]]['x'] = result['x'+str(i+1)]
        keypoints[person_keys[i]]['y'] = result['y'+str(i+1)]
        #keypoints[person_keys[i]]['z'] = result['z'+str(i+1)]
        #keypoints[person_keys[i]]['zorder'] = result['zorder'+str(i+1)]
        keypoints[person_keys[i]]['visible'] = result['visible'+str(i+1)]
    data['person_id'] = result['person_id']
    data['keypoints'] = keypoints
    return data

def get_db_points(userFileIds):
    sql = '''select * from ai_image as img,ai_label_skeleton as label where img.file_id in ({}) and img.img_id = label.img_id'''.format(userFileIds)
    result = db_file(sql)
    if not result:
        return None
    person_keys = ['B_Head','Neck','L_Shoulder','R_Shoulder','L_Elbow','R_Elbow','L_Wrist','R_Wrist','L_Hip',
        'R_Hip','L_Knee','R_Knee','L_Ankle','R_Ankle','Nose','L_Ear','L_Eye','R_Eye','R_Ear']
    resp = []
    for res in result:
        sql = '''select fileName,filePath from userfile where userFileId={}'''.format(res['file_id'])
        img = db_file(sql)[0]['fileName']
        filepath = db_file(sql)[0]['filePath']
        data = {}
        keypoints = {}
        for i in range(19):
            keypoints[person_keys[i]] = {}
            keypoints[person_keys[i]]['x'] = res['x'+str(i+1)]
            keypoints[person_keys[i]]['y'] = res['y'+str(i+1)]
            keypoints[person_keys[i]]['z'] = res['z'+str(i+1)]
            keypoints[person_keys[i]]['zorder'] = res['zorder'+str(i+1)]
            keypoints[person_keys[i]]['visible'] = res['visible'+str(i+1)]
        data['person_id'] = res['person_id']
        data['image'] = img
        data['keypoints'] = keypoints
        data['filepath'] = filepath
        data['label_id'] = res['label_id']
        resp.append(data)
    return resp

def get_label_status(userFileId):
    sql = '''select label.status as status from ai_label_skeleton as label,
        ai_image as image where image.file_id={} and image.img_id = label.img_id limit 1'''.format(userFileId)
    result = db_file(sql)
    resp = {}
    if result:
        status = result[0]['status']
        resp['status'] = status
        resp['code'] = 0
        resp['msg'] = '成功'
    else:
        resp['code'] = 1
        resp['msg'] = '没有标注数据'
    return resp

@app.route('/get_labelimage', methods = ['GET'])
def get_labelimage():
    time1 = time.time()
    isMin = request.values.get('isMin')
    userFileId = request.values.get('userFileId')
    if not db_file('''select * from ai_image where file_id = {} limit 1'''.format(userFileId)):
        data = {}
        data['code'] = 1
        data['msg'] = '标注文件不存在'
        return json.dumps(data)
    filepath = db.get_image_path(userFileId)
    filelist = filepath.split('/')
    #os.chdir(DIR)
    imgpath = DIR + filepath
    # linewidth = 5
    # size = 12
    # if isMin == 'true':
    #     plt.rcParams['figure.figsize'] = (1.5, 1.5)
    #     linewidth = 2
    #     size = 3
    # else:
    #     plt.rcParams['figure.figsize'] = (8.0, 10.0)
    # plt.axis('off')
    data = {}
    data['code'] = 1
    data['msg'] = '打开文件失败'
    #data = get_point(xmlpath)
    #I = io.imread(imgpath)
    #I = plt.imread(imgpath)
    # while(0):
    #     try:
    #         plt.imshow(I)
    #         break
    #     except:
    #         time.sleep(0.5)
    # plt.imshow(I)
    #plt.show()
    if len(filelist)<3 or filelist[-2]!='images' or filelist[-3]!='label_data' or isMin not in ('true','false'):
        data = {}
        #image = base64.encodebytes(sio.getvalue()).decode()
        #data['image'] = image
        data['status'] = 0
        data['code'] = 1
        data['msg'] = '文件非图片或请求参数错误'
        return data
    data = get_db_point(userFileId)
    if not data:
        #sio = BytesIO()
        #plt.savefig(sio, format='png')
        #plt.clf()
        #plt.close()
        data = {}
        #image = base64.encodebytes(sio.getvalue()).decode()
        #data['image'] = image
        #data['status'] = 0
        data['code'] = 1
        data['msg'] = "没有标注文件"
        return data
    
    keys = ['B_Head','Neck','L_Shoulder','R_Shoulder','L_Elbow','R_Elbow','L_Wrist','R_Wrist','L_Hip',
        'R_Hip','L_Knee','R_Knee','L_Ankle','R_Ankle','Nose','L_Ear','L_Eye','R_Eye','R_Ear']
    point_x = []
    point_y = []
    point_v = []
    lines = [[0,1],[1,2],[1,3],[2,4],[3,5],[4,6],[5,7],[8,10],[9,11],[10,12],[11,13],[2,8],[3,9],[8,9]]
    for key in keys:
        if key in data['keypoints']:
            if key in ['Nose','L_Ear','L_Eye','R_Eye','R_Ear']:
                continue
            point_x.append(float(data['keypoints'][key]['x']))
            point_y.append(float(data['keypoints'][key]['y']))
            point_v.append(int(data['keypoints'][key]['visible']))
    # for line in lines:
    #     point1,point2 = line
    #     x1 = point_x[point1]
    #     x2 = point_x[point2]
    #     y1 = point_y[point1]
    #     y2 = point_y[point2]
    #     plt.plot([x1,x2],[y1,y2], linewidth=linewidth, color='black')
    
    # plt.plot(point_x,point_y,'.',markersize=size)
    #plt.show()
    
    '''
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    cv2处理图片
    '''
    img = cv2.imread(imgpath)

    
    for line in lines:
        point1,point2 = line
        x1 = point_x[point1]
        x2 = point_x[point2]
        y1 = point_y[point1]
        y2 = point_y[point2]
        start_point = (int(x1), int(y1))
        end_point = (int(x2), int(y2))
        if start_point == (0,0) or end_point == (0,0):
            continue
        if point_v[point1] and point_v[point2]:
            cv2.line(img, start_point, end_point, (0,255,0), 5)
    for i in range(14):
        if point_v[i]:
            cv2.circle(img,(int(point_x[i]),int(point_y[i])),3,(255,0,0),3)
    if isMin == 'true':
        img = cv2.resize(img, (150,150))
        image = cv2.imencode('.jpeg',img)[1]
        src = 'data:image/jpeg;base64,'

    else:
        img = cv2.resize(img, (450,450))
        image = cv2.imencode('.jpg',img)[1]
        src = 'data:image/jpg;base64,'
    image = str(base64.b64encode(image))[2:-1]

    image = src + image
    resp = get_label_status(userFileId)
    resp['image'] = image
    return resp
    '''
    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    '''


    # sio = BytesIO()
    # if isMin == 'true':
    #     plt.savefig(sio, format='jpeg')
    #     src = 'data:image/jpeg;base64,'
    # else:
    #     plt.savefig(sio, format='png')
    #     src = 'data:image/png;base64,'
    # plt.clf()
    # plt.close() 
    # resp = {}  
    
    # try:     
    #     image = base64.encodebytes(sio.getvalue()).decode()
    #     #print(1)
    #     #print(image)
        
    #     sql = '''select label.status as status from ai_label_skeleton as label,
    #     ai_image as image where image.file_id={} and image.img_id = label.img_id limit 1'''.format(userFileId)
    #     result = db_file(sql)
    #     time2 = time.time()
    #     print(time2-time1)
    #     #print(result)
    #     status = result[0]['status']
    #     resp['image'] = '<img src="%s"/>' % (src + image)
    #     resp['status'] = status
    #     resp['code'] = 0
    #     resp['msg'] = '成功'
    #     #print(resp)
    # except Exception as e:
    #     resp['code'] = 1
    #     resp['msg'] = str(e)
    #     #print(e)
    # return resp['image']
    # return resp

def xmlsave():
    n = 0
    sql = "select filePath, fileName from userfile where extendName='xml' and filePath like '%/label_data/info/'"
    result = db_file(sql)
    for res in result:
        path = res['filePath'][:-5] + 'images/'
        name = res['fileName'][:-2]
        sql = "select userFileId,extendName from userfile where filePath='{}' and fileName='{}'".format(path,name)
        ans = db_file(sql)
        if not ans:
            continue
        userFileId = ans[0]['userFileId']
        extendName = ans[0]['extendName']
        try:
            sql = """insert into ai_image set file_id={},path='{}',type='{}',status=0""".format(userFileId, path, extendName)
            db_file(sql)
            sql = """select max(img_id) as id from ai_image"""
            img_id = db_file(sql)[0]['id']
            filePath = DIR + res['filePath'] + res['fileName'] + '.xml'
            person_id = res['fileName'][-1]
            create_point(filePath, img_id, person_id)
        except:
            pass
        n += 1
        if n > 1000:
            time.sleep(2)
            n = 0

@app.route('/get_label_info')
def get_label_info():
    img_id = request.values.get('img_id')
    resp = {}
    resp['code'] = 0
    data = get_db_point(img_id)
    if not data:
        resp['code'] = 0
    resp['data'] = data
    return json.dumps(resp)


@app.route('/file/set_label_status', methods=['POST'])
def set_label_status():
    status = request.form['status']
    files = request.form['userFileIds']
    status = int(status)
    resp = {}
    resp['code'] = 0
    resp['msg'] = '成功'
    if status not in (0,1,2,3):
        resp['code'] = 1
        resp['msg'] = 'status is not in (0,1,2,3)'
        return json.dumps(resp)
    try:
        sql = '''select img_id from ai_image where file_id in ({})'''.format(files)
        result = db_file(sql)
        img_ids = []
        for res in result:
            img_ids.append(str(res['img_id']))
        img_ids = ','.join(img_ids)
        print(img_ids)
        sql = '''update ai_label_skeleton set status={} where img_id in ({})'''.format(status, img_ids)
        print(sql)
        db_file(sql)
        
    except:
        resp['code'] = 1
        resp['msg'] = 'files error'
    return json.dumps(resp)
