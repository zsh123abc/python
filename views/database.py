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

'''
对于数据库的操作
'''

# 根据id获取图片路径
def get_image_path(userFileId):
    # 获取图片路径
    sql = '''select filePath, fileName, extendName from userfile where userFileId = {} limit 1'''.format(userFileId)
    result = db_file(sql)
    for res in result:
        # /zsh/label_data/images/17 (1)0011.jpg
        path = res['filePath'] + res['fileName'] + '.' + res['extendName']
    return path

 # 摘要算法 防止篡改
def get_file_md5(filename):
    # os.path.isfile() 判断是否是文件
    if not os.path.isfile(filename):
        # 不是文件直接退出
        return 
    # hashlib.md5() 把任意长度的数据转换为一个长度固定的数据串（通常用16进制的字符串表示）
    myhash = hashlib.md5()
    # open() 打开文件，’rb‘以二进制打开图片视频等
    f = open(filename,'rb')
    while True:
        # read() 读取文件，二进制文件逐个字节读取
        b = f.read(8096)
        # 判断文件是否存在
        if not b:
            break
        # update() 增加内容
        myhash.update(b)
    # close()关闭文件     
    f.close()
    # hexdigest() 返回摘要，十六进制数据字符串值
    return myhash.hexdigest()

# 保存图片到数据库
# id，高，宽 
def image_save(fileid, height, width):
    sql = '''insert into image set fileId={}, imageHeight={}, imageWidth={}'''.format(fileid, height, width)
    db_file(sql)

# 插入文件
# filepath 视频帧储存的路径 filename 视频帧名字 ext 文件类型（后缀）
def insert_file(filepath, filename, ext):
    # fileUrl 视频帧路径+视频帧名字+类型后缀
    fileUrl = '%s%s.%s' % (filepath, filename,ext)
    # md5 加密，identifier 十六进制数据字符串值
    identifier = get_file_md5(DIR+fileUrl)
    # os.stat() 获取指定路径文件的状态信息
    file_stats = os.stat(DIR+fileUrl)
    # 获取文件的大小信息 .st_size 大小，单位是bytes
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
    # 支持的几种图片格式
    if ext in ['bmp','jpg','png','tif','gif','jpeg']:
        # Image.open() 根据路径读取的图像
        img = Image.open(DIR+fileUrl)
        # 图片的大小
        width = img.width
        height = img.height
        # 保存图片对应的id和图片的大小进数据库
        image_save(fileid, height, width)

# 插入文件夹
def insert_folder(filepath,filename):
    # .format() 格式化字符串
    sql = '''insert into userfile set deleteFlag=0, fileName='{}', filePath='{}',
        isDir=1,userId=3, uploadTime=now()'''.format(filename,filepath)
    # 插入数据到数据库    
    db_file(sql)