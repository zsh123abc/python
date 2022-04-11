#import aiofiles
import asyncio
import os
import glob
import csv
import numpy as np
import xml.etree.ElementTree as ET
from model import db_file
from typing import List
from app import app
from flask import jsonify, request,render_template
from PIL import Image
from config import DIR
import hashlib

def get_image_path(userFileId):
    # 获取图片真实路径
    sql = '''select filePath, fileName, extendName from userfile where userFileId = {}'''.format(userFileId)
    print(sql)
    result = db_file(sql)
    for res in result:
        path = res['filePath'] + res['fileName'] + '.' + res['extendName']
    return path


def get_file_md5(filename):
    # 路径加密
    if not os.path.isfile(filename):
        return
    myhash = hashlib.md5()
    f = open(filename,'rb')
    while True:
        b = f.read(8096)
        if not b:
            break
        myhash.update(b)
    f.close()
    return myhash.hexdigest()

def image_save(fileid, height, width):
    sql = '''insert into image set fileId={}, imageHeight={}, imageWidth={}'''.format(fileid, height, width)
    db_file(sql)

def insert_file(filepath, filename, ext):
    # 插入文件
    fileUrl = '%s%s.%s' % (filepath, filename,ext)
    identifier = get_file_md5(DIR+fileUrl)
    file_stats = os.stat(DIR+fileUrl)
    file_size = file_stats.st_size
    sql = '''insert into file (createUserId,fileSize,fileStatus,fileUrl,identifier,storageType, createTime)
         values ({0},{1},{2},'{3}','{4}',{5}, now())'''.format(3,file_size,1,fileUrl[1:],identifier,0) 
    db_file(sql)
    sql = '''select max(fileId) as id from file'''
    result = db_file(sql)
    fileid = result[0]['id']
    sql = '''insert into userfile (deleteFlag, extendName, fileId, fileName, filePath, isDir,userId,uploadTime)
         values ({0},'{1}',{2},'{3}','{4}',{5},{6},now())'''.format(0,ext,fileid,filename,filepath,0,3)
    db_file(sql)
    if ext in ['bmp','jpg','png','tif','gif','jpeg']:
        img = Image.open(DIR+fileUrl)
        width = img.width
        height = img.height
        image_save(fileid, height, width)

def insert_folder(filepath,filename):
    # 插入文件夹
    sql = '''insert into userfile set deleteFlag=0, fileName='{}', filePath='{}',
        isDir=1,userId=3, uploadTime=now()'''.format(filename,filepath)
    db_file(sql)