import aiofiles
import asyncio
import os
import glob
import csv
import xml.etree.ElementTree as ET
from models import db_file,db_sport
from typing import List
from app import app
from flask import jsonify, request, render_template
import json

def check_file_path(url):
    result = {}
    if os.path.exists(url):
        if os.path.isfile(url):
            result = {'type': 'file', 'exist': True}
        if os.path.isdir(url):
            result = {'type': 'folder', 'exist': True}
    else:
        file_name = url.rsplit('.', 1)[1].lower()
        if file_name:
            result = {'type': 'file', 'exist': False}
    return result


async def get_file_data(file_path):
    # data = []
    async with aiofiles.open(file_path, encoding='utf-8', mode='r') as f:
        contents = await f.read()
        # await for line in f:
        #     data.append(line.strip())
        # f.close()
    await asyncio.sleep(1)
    return contents


async def get_folder_data(folder_path, folder_query):

    # if orderBy in ["lastModified", "size", "fileName"]:
    #     data.sort(key=os.path.getctime) orderBy or orderByDirection or filterByName:
    datas = {}
    if folder_query:
        orderBy = folder_query["orderBy"]
        orderByDirection = folder_query["orderByDirection"]
        filterByName = folder_query["filterByName"]
        if orderBy:
            if orderBy == "lastModified":
                if datas:
                    datas = sorted(datas, key=os.path.getmtime, reverse=True)
                else:
                    files = [os.path.join(folder_path, data) for data in os.listdir(folder_path)]
                    datas = sorted(files, key=os.path.getmtime, reverse=True)
            if orderBy == "size":
                if datas:
                    datas = sorted(datas, key=os.path.getsize, reverse=True)
                else:
                    files = [os.path.join(folder_path, data) for data in os.listdir(folder_path)]
                    datas = sorted(files, key=os.path.getsize, reverse=True)
            if orderBy == "fileName":
                if datas:
                    datas = sorted(datas, reverse=True)
                else:
                    files = [os.path.join(folder_path, data) for data in os.listdir(folder_path)]
                    datas = sorted(files, reverse=True)
        if orderByDirection:   
            if orderByDirection == "Ascending":
                if datas:
                    datas = sorted(datas, key=lambda t: os.stat(t).st_mtime)
                else:
                    files = [os.path.join(folder_path, data) for data in os.listdir(folder_path)]
                    datas = sorted(files, key=lambda t: os.stat(t).st_mtime)
            if orderByDirection == "Descending":
                if datas:
                    datas = sorted(datas, key=lambda t: -os.stat(t).st_mtime)
                else:
                    files = [os.path.join(folder_path, data) for data in os.listdir(folder_path)] 
                    datas = sorted(files, key=lambda t: -os.stat(t).st_mtime)
        if filterByName:
            if datas:
                datas = [data for data in datas if filterByName in data]
            else:
                files = [os.path.join(folder_path, data) for data in os.listdir(folder_path)]
                datas = [file for file in files if filterByName in file]
    else:
        datas = [os.path.join(folder_path, data) for data in os.listdir(folder_path)]
    datas = [data[15:] for data in datas]
    await asyncio.sleep(1)
    return datas


async def add_file(file_path, file_data):
    async with aiofiles.open(file_path, encoding='utf-8', mode='w') as file:
        if isinstance(file_data, List):
            await file.write('\n'.join(file_data))
        else:
            await file.write(file_data)
    await asyncio.sleep(1)
    return True if os.path.exists(file_path) else False


async def update_file(file_path, file_data):
    before_len = None
    async with aiofiles.open(file_path, encoding='utf-8', mode='r') as file:
        contents = await file.read()
        lines = contents.split('\n')
        before_len = len(lines)
        file.close()

    async with aiofiles.open(file_path, encoding='utf-8', mode='w') as sortedbooks:
        if isinstance(file_data, List) and len(file_data) > 0:
            lines.extend(file_data)
        else:
            if len(file_data) > 0:
                lines.append(file_data)
        await sortedbooks.write('\n'.join(lines))
        await sortedbooks.close()

    async with aiofiles.open(file_path, encoding='utf-8', mode='r') as file:
        contents = await file.read()
        update_lines = contents.split('\n')
    await asyncio.sleep(1)

    return True if len(update_lines) >= before_len else False


async def drop_file(file_path):
    os.remove(file_path)
    await asyncio.sleep(1)
    return False if os.path.exists(file_path) else True


@app.route('/')
def hello():
    return render_template('commit.html')
    try:
        return render_template('commit.html')
    except Exception as e:
        print(e)

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



@app.route('/getpath')
async def get_filepath():
    userfile_title = ['userFileId','deleteBatchNum', ]
    filePath = request.values.get('filePath')
    print(filePath)
    sql = """select * from userfile where filePath='%s'""" % (filePath)
    #sql = '''select * from userfile'''
    print(sql)
    result = db_file(sql)
    for i in result:
        print(i)
    resp = {}
    data = {}
    list = []
    for res in result:
        item = res
        list.append(item)
    data['list'] = list
    resp['data'] = data
    resp['code'] = 0
    resp['message'] = '成功'
    resp['success'] = True
    return resp
    return json.dumps(result)




@app.route('/api/file/getfilelist', methods=['GET'])
async def get_path():
    try:
        filePath = request.values.get('filePath')
        print(filePath)
        _result = None
        _json_data = request.json
        _path = f'./file' + filePath
        _path_info = check_file_path(_path)
        if _path_info['type'] == 'file' and _path_info['exist'] == True:
            _result = await get_file_data(_path)
            _result = {
                'data':_result
            }
        elif _path_info['type'] == 'folder' and _path_info['exist'] == True:
            data = await get_folder_data(_path, _json_data)
            _result = {
                'isDirectory': True,
                'data': data,
                'code': 0,
                'message': '成功',
                'success': True
            }
        else:
            return not_found()
        resp = jsonify(_result)
        resp.status_code = 200
        return resp

    except Exception as e:
        print(e)


@app.route('/uploadfile', methods=['POST'])
async def create_file():
    try:
        _result = None
        _json = request.values
        _data = _json['files']
        _filepath = _json['filepath']
        _filename = _json['filename']
        _path = f'./file' + _filepath + _filename
        print(_path)
        _path_info = check_file_path(_path)
        if _path_info['type'] == 'file' and _path_info['exist'] == False:
            _result = await add_file(_path, _data)
            if _result == True:
                message = {'status': 200,
                           'message': f'Create {_path} success!!'}
                #database.add_file(_path)
                resp = jsonify(message)
                resp.status_code = 200
                return resp
            else:
                message = {
                    'status': 400, 'message': f'{_path} create fail, please check file data!'}
        else:
            message = {'status': 400, 'message': f'{_path} has been exist!'}
        resp = jsonify(message)
        resp.status_code = 400
        return resp

    except Exception as e:
        print(e)


@app.route('/file/<path:localSystemFilePath>', methods=['PATCH'])
async def edit_file(localSystemFilePath):
    try:
        _result = None
        _json = request.json
        _data = _json['files']
        _path = f'./file/{localSystemFilePath}'
        _path_info = check_file_path(_path)
        if _path_info['type'] == 'file' and _path_info['exist'] == True:
            _result = await update_file(_path, _data)
            if _result == True:
                message = {'status': 200,
                           'message': f'Update {_path} success!!'}
                resp = jsonify(message)
                resp.status_code = 200
                return resp
            else:
                message = {
                    'status': 400, 'message': f'{_path} update fail, please check file data!'}
                resp = jsonify(message)
                resp.status_code = 400
                return resp
        else:
            return not_found()

    except Exception as e:
        print(e)


@app.route('/file/<path:localSystemFilePath>', methods=['DELETE'])
async def delete_file(localSystemFilePath):
    try:
        _result = None
        _path = f'./file/{localSystemFilePath}'
        _path_info = check_file_path(_path)
        if _path_info['type'] == 'file' and _path_info['exist'] == True:
            _result = await drop_file(_path)
            print('delete result: ', _result)
            if _result == True:
                message = {'status': 200,
                           'message': f'Delete file {_path} success!!'}
                resp = jsonify(message)
                resp.status_code = 200
                return resp
        else:
            return not_found()

    except Exception as e:
        print(e)


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404
    return resp


@app.errorhandler(500)
def server_error(error=None):
    message = {
        'status': 500,
        'message': 'server or network error: ',
    }
    resp = jsonify(message)
    resp.status_code = 500
    return resp
