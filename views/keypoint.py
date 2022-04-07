import aiofiles
import asyncio
import os
import glob
import csv
import numpy as np
import xml.etree.ElementTree as ET
from models import db_sport
from typing import List
from app import app
from flask import jsonify, request
import json
from PIL import Image
from config import DIR
from . import database as db
import shutil
import numpy as np
import skimage.io as io
import cv2
import matplotlib.pyplot as plt
import pylab
from pycocotools.coco import COCO
from io import BytesIO
import base64

#@app.route('/point/<path:localSystemFilePath>', methods=['GET'])
def get_point(xmlpath):
    print(xmlpath)
    tree = ET.parse(xmlpath)
    root = tree.getroot()
    print(root)
    person = {}
    for obj in root:
        if obj.tag == "image":
            person["image"] = obj.text
            
        if obj.tag == "keypoints":
            person["keypoints"] = {}
            for child in obj:
                name = child.attrib["name"]
                person["keypoints"][name] = child.attrib
    return person

@app.route('/createpoint/<path:localSystemFilePath>', methods=['GET'])
def create_point(imgpath):
    person = get_point(xmlpath)
    person_keys = ['B_Head','Neck','L_Shoulder','R_Shoulder','L_Elbow','R_Elbow','L_Wrist','R_Wrist','L_Hip',
        'R_Hip','L_Knee','R_Knee','L_Ankle','R_Ankle','Nose','L_Ear','L_Eye','R_Eye','R_Ear']
    keypoint = []
    print(person['image'])
    for key in person['keypoints']:
        idx = person_keys.index(key) + 1
        for item in ['x','y','z','zorder','visible']:
            s = '%s%d=%s'%(item, idx, person['keypoints'][key][item])
            keypoint.append(s)
    person_id = 0
    img_id = 0
    status = 0
    sql = '''insert into ai_label_skeleton set person_id=%d,img_id=%d,status=%d,%s'''%(person_id, img_id, status, ','.join(keypoint))
    print(sql)
    db_sport(sql)
    return 'ok'

@app.route('/get_labelimage', methods = ['GET'])
def get_labelimage():
    isMin = request.values.get('isMin')
    userFileId = request.values.get('userFileId')
    print(userFileId)
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
    data = get_point(xmlpath)
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
    data = base64.encodebytes(sio.getvalue()).decode()
    return data


        