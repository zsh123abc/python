import os
import glob
import csv
import xml.etree.ElementTree as ET
from models import db_file
from typing import List
from app import app
from flask import jsonify, request, render_template
import json
from .keypoint import get_point

@app.route('/getdirtree')
def get_dir_tree():
    resp = {'code':0, 'msg': '成功'}
    try:
        filePath = request.values.get('filePath')
        files = []
        sql = """select isDir, fileName, extendName from userfile where filePath = '{}'""".format(filePath)
        print(sql)
        result = db_file(sql)
        print(result)
        for res in result:
            item = {}
            item['isDir'] = res['isDir']
            item['filename'] = res['fileName']
            if res['extendName']:
                item['filename'] += '.' + res['extendName']
            files.append(item)
        resp['files'] = files
    except:
        resp['code'] = 1
        resp['msg'] = '失败'
    return json.dumps(resp)

def get_xml_file(userFileIds):
    pass


def label_download():
    userFileIds = request.values.get('userFileIds')
    fileType = request.values.get('fileType')
    if fileType == 'xml':
        get_xml_file(userFIleIds)

@app.route('/upload_label_file', methods=['GET','POST'])
def uploadlabelfile():
    if request.method == 'GET':
        return render_template('commit.html')
    if request.method == 'POST':
        file = request.files['file']
        if file:
            person = get_point(file)
            return person
