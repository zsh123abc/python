import aiofiles
import asyncio
import os
import glob
import csv
import numpy as np
import xml.etree.ElementTree as ET
from models import db_file,db_sport
from typing import List
from app import app
from flask import jsonify, request,render_template
from PIL import Image
from config import DIR

def get_thumbnail(path, filename):
    # 生成缩略图
    filepath = DIR + path + filename
    #image = glob.glob(filepath)
    img = Image.open(filepath)
    img.thumbnail((150,150))
    return img

def get_image_path(userFileId):
    sql = '''select filePath, fileName, extendName from userfile where userFileId = {}'''.format(userFileId)
    result = db_file(sql)
    for res in result:
        path = res['filePath'] + res['fileName'] + '.' + res['extendName']
    return path