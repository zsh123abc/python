import os
import glob
import csv
import xml.etree.ElementTree as ET
from model import db_file
from typing import List
from app import app
from flask import jsonify, request, render_template
import json
from .keypoint import get_point,get_dbtype_point,create_point

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

def create_label(filePath, userFileId, person_id, person):
    sql = '''insert into ai_image set file_id={},path="{}",type="jpg",status=0'''.format(userFileId, filePath)
    db_file(sql)
    sql = '''select img_id from ai_image where file_id = {}'''.format(userFileId)
    res = db_file(sql)
    print(res)
    id = res[0]['img_id']
    print(id)
    create_point(person, id, person_id)

def label_download():
    userFileIds = request.values.get('userFileIds')
    fileType = request.values.get('fileType')
    if fileType == 'xml':
        get_xml_file(userFIleIds)

@app.route('/upload_label_file', methods=['GET','POST'])
def uploadlabelfile():
    # xml文件上传接口
    if request.method == 'GET':
        return render_template('commit.html')
    if request.method == 'POST':
        file = request.files['file']
        filename = request.form['filename']
        filePath = request.form['filePath']
        resp = {}
        resp['code'] = 1
        if not file:
            resp['msg'] = '上传失败'
            return resp
        person = get_point(file)
        keypoint = get_dbtype_point(person)
        keypoint = ','.join(keypoint)
        try:
            filename, person_id = filename.split('_')
        except:
            resp['msg'] = '文件名错误'
            return resp
        sql = '''select userFileId from userfile where filePath="{}" and fileName="{}"'''.format(filePath, filename)
        result = db_file(sql)
        if result:
            userFileId = result[0]['userFileId']
            sql = '''select img_id from ai_image where file_id={}'''.format(userFileId)
            result = db_file(sql)
            if not result:
                create_label(filePath, userFileId, person_id, person)
                resp['code'] = 0
                resp['msg'] = '标注文件已生成'
                return resp
            img_id = result[0]['img_id']
        else:
            resp['msg'] = '文件不存在'
            return resp
        sql = 'update ai_label_skeleton set status=0,{} where img_id={}'.format(keypoint,img_id)
        db_file(sql)
        sql = 'select label_id from ai_label_skeleton where img_id={}'.format(img_id)
        result = db_file(sql)
        label_id = result[0]['label_id']
        sql = '''select * from ai_tag,ai_label_tag where ai_label_tag.label_id={} and ai_label_tag.tag_id=ai_tag.tag_id 
            and tag_id.tag={}'''.format(label_id, person['subcategory'])
        resp['code'] = 0
        resp['msg'] = '标注文件已更改'
        return resp

