import os
import glob
import csv
import xml.etree.ElementTree as ET
from models import db_file
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

#@app.route('/point/<path:localSystemFilePath>', methods=['GET'])
def get_point(xmlpath):
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

#@app.route('/createpoint/<path:localSystemFilePath>', methods=['GET'])
def create_point(xml_path, img_id, person_id):
    person = get_point(xml_path)
    person_keys = ['B_Head','Neck','L_Shoulder','R_Shoulder','L_Elbow','R_Elbow','L_Wrist','R_Wrist','L_Hip',
        'R_Hip','L_Knee','R_Knee','L_Ankle','R_Ankle','Nose','L_Ear','L_Eye','R_Eye','R_Ear']
    keypoint = []
    for key in person['keypoints']:
        idx = person_keys.index(key) + 1
        for item in ['x','y','z','zorder','visible']:
            s = '%s%d=%s'%(item, idx, person['keypoints'][key][item])
            keypoint.append(s)
    person_id = int(person_id)
    img_id = int(img_id)
    status = 0
    sql = '''insert into ai_label_skeleton set person_id=%d,img_id=%d,status=%d,%s'''%(person_id, img_id, status, ','.join(keypoint))
    db_file(sql)
    sql = '''select max(label_id) as id from ai_label_skeleton'''
    label_id = db_file(sql)[0]['id']
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
        keypoints[person_keys[i]]['z'] = result['z'+str(i+1)]
        keypoints[person_keys[i]]['zorder'] = result['zorder'+str(i+1)]
        keypoints[person_keys[i]]['visible'] = result['visible'+str(i+1)]
    data['person_id'] = result['person_id']
    data['keypoints'] = keypoints
    return data

@app.route('/get_labelimage', methods = ['GET'])
def get_labelimage():
    isMin = request.values.get('isMin')
    userFileId = request.values.get('userFileId')
    filepath = db.get_image_path(userFileId)
    os.chdir(DIR)
    userList = filepath.split('/')
    userList[-2] = 'info'
    userList[-1] = userList[-1].split('.')[0] + '_0.xml'
    imgpath = DIR + filepath
    xmlpath = DIR + '/'.join(userList)
    # display COCO categories and supercategories
    #cats = coco.loadCats(coco.getCatIds())
    #nms = [cat['name'] for cat in cats]
    #print('COCO categories: \n{}\n'.format(' '.join(nms)))
    #nms = set([cat['supercategory'] for cat in cats])
    #print('COCO supercategories: \n{}'.format(' '.join(nms)))
    #imgIds = coco.getImgIds()  # list
    #return json.dumps(imgIds)
    
    linewidth = 5
    size = 12
    if isMin == 'true':
        plt.rcParams['figure.figsize'] = (1.5, 1.5)
        linewidth = 2
        size = 3
    else:
        plt.rcParams['figure.figsize'] = (8.0, 10.0)
    I = io.imread(imgpath)
    plt.axis('off')
    plt.imshow(I)
    plt.show()
    #data = get_point(xmlpath)
    data = get_db_point(userFileId)
    if not data:
        sio = BytesIO()
        plt.savefig(sio, format='png')
        plt.clf()
        plt.close()
        #if isMin:
        #    plt.thumbnail((150,150))
        data = {}
        image = base64.encodebytes(sio.getvalue()).decode()
        data['image'] = image
        data['status'] = 0
        return data
    keys = ['B_Head','Neck','L_Shoulder','R_Shoulder','L_Elbow','R_Elbow','L_Wrist','R_Wrist','L_Hip',
        'R_Hip','L_Knee','R_Knee','L_Ankle','R_Ankle','Nose','L_Ear','L_Eye','R_Eye','R_Ear']
    point_x = []
    point_y = []
    point_v = []
    lines = [[0,1],[1,2],[1,3],[2,4],[3,5],[4,6],[5,7],[8,10],[9,11],[10,12],[11,13]]
    for key in keys:
        if key in data['keypoints']:
            if key in ['Nose','L_Ear','L_Eye','R_Eye','R_Ear']:
                continue
            point_x.append(float(data['keypoints'][key]['x']))
            point_y.append(float(data['keypoints'][key]['y']))
            point_v.append(int(data['keypoints'][key]['visible']))
    for line in lines:
        point1,point2 = line
        x1 = point_x[point1]
        x2 = point_x[point2]
        y1 = point_y[point1]
        y2 = point_y[point2]
        plt.plot([x1,x2],[y1,y2], linewidth=linewidth, color='black')
    plt.plot(point_x,point_y,'.',markersize=size)
    plt.show()
    sio = BytesIO()
    plt.savefig(sio, format='png')
    plt.clf()
    plt.close()
    #if isMin:
    #    plt.thumbnail((150,150))
    data = {}
    image = base64.encodebytes(sio.getvalue()).decode()
    sql = '''select label.status as status from ai_label_skeleton as label,
     ai_image as image where image.file_id={} and image.img_id = label.img_id'''.format(userFileId)
    result = db_file(sql)
    status = result[0]['status']
    data['image'] = image
    data['status'] = status
    #return image
    return data

def xmlsave():
    n = 0
    sql = "select filePath, fileName from userfile where extendName='xml' and filePath like '%/label_data/info/' and userFileId>293751"
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
