import os
import glob
import csv
import xml.etree.ElementTree as ET
from model import db_file
from typing import List
from app import app
from flask import jsonify, request, render_template, make_response, send_from_directory
import json
from .keypoint import get_point,get_dbtype_point,create_point,get_db_points
import zipfile
import xml.dom.minidom
from config import DIR
import time
import base64

# 获取目录树
@app.route('/getdirtree')
def get_dir_tree():
    resp = {'code':0, 'msg': '成功'}
    try:
        # 获取所有参数
        filePath = request.values.get('filePath')
        fileType = request.values.get('fileType')
        # 判断文件类型
        if fileType == '1':
            sql_str = ' and isDir = 1'
        elif fileType == '2':
            sql_str = ' and isDir = 0'
        else:
            sql_str = ''
        # 空列表
        files = []
        # 查询数据
        sql = """select isDir, fileName, extendName,userFileId from userfile where filePath = '{}' {}""".format(filePath,sql_str)
        print(sql)
        result = db_file(sql)
        print(result)
        # 把result中每项数据取出来
        for res in result:
            # 空字典
            item = {}
            item['isDir'] = res['isDir']
            item['filename'] = res['fileName']
            item['userFileId'] = res['userFileId']
            # 判断数据是否为空，为空：false
            if res['extendName']:
                # 文件名+'.'+扩展名
                item['filename'] += '.' + res['extendName']
            # 没一次循环添加一次 
            files.append(item)
        # resp字典添加数据    
        resp['files'] = files
    except:
        resp['code'] = 1
        resp['msg'] = '失败'
    # 将python对象编码成Json字符串    
    return json.dumps(resp)

# 建立标签
def create_label(filePath, userFileId, person_id, person):
    # 数据库插入数据
    sql = '''insert into ai_image set file_id={},path="{}",type="jpg",status=0'''.format(userFileId, filePath)
    db_file(sql)
    # 数据库查询数据
    sql = '''select img_id from ai_image where file_id = {}'''.format(userFileId)
    res = db_file(sql)
    print(res)
    # res第0项中img_id对应的数据
    id = res[0]['img_id']
    print(id)
    # 创建节点并且保存至数据库中
    create_point(person, id, person_id)

# 获取标签
def get_label_tag(label_id):
    # 数据库查询
    sql = '''select ai_tag.tag as tag from ai_label_tag, ai_tag where ai_label_tag.tag_id = ai_tag.tag_id and ai_label_tag.label_id = {}'''.format(label_id)
    print(sql)
    result = db_file(sql)
    # 判断数据是否空，为空就false
    if result:
        # 不为空就返回result中第0项中tag对应的数据
        return result[0]['tag']
    else:
        # 为空就返回‘male’
        return 'male'

# 获取xml文件
def get_xml_file(zipFileCnt, person):
    filepath = DIR+'/yd_pose/test/test.zip'
    # 新建zip对象，后面用write()方法添加文件到这个压缩包中
    f = zipfile.ZipFile(filepath,'w',zipfile.ZIP_STORED)
    # 空列表
    paths = []
    names = []
    # 循环拿出person的每一项
    for item in person:
        #在内存中创建一个空的文档
        doc = xml.dom.minidom.Document()
        #创建一个根节点Managers对象
        root = doc.createElement('annotation')
        #将根节点添加到文档对象中
        doc.appendChild(root)
        # 创建叶子节点
        nodeimage = doc.createElement('image')
        nodecategory = doc.createElement('category')
        nodesubcategory = doc.createElement('subcategory')
        nodekeypoints = doc.createElement('keypoints')
        '''
        在nodeimage节点后面添加新创建的文本节点
            appendChild() 向节点的子节点列表的末尾添加新的子节点。
            doc.createTextNode() 创建文本节点
        '''
        nodeimage.appendChild(doc.createTextNode(item['image']))
        # 在nodecategory节点后面添加新创建的文本节点
        nodecategory.appendChild(doc.createTextNode('person'))
        # item字典中label_id对应的值
        label_id = item['label_id']
        # 获取id对应的标签
        tag = get_label_tag(label_id)
        # 在nodesubcategory节点后面添加新创建的文本节点
        nodesubcategory.appendChild(doc.createTextNode(tag))
        # 取出item中keypoints对应的值
        items = item['keypoints']
        # 循环取出keypoints里面的数据
        for name in item['keypoints']:
            # 判断三个坐标x,y,z是否为0
            if items[name]['x'] == items[name]['y'] == items[name]['z'] == 0:
                # 为0退出本此循环
                continue
            # 创建节点
            nodekeypoint = doc.createElement('keypoint')
            #设置根节点的属性
            nodekeypoint.setAttribute('name', name)
            nodekeypoint.setAttribute('zorder', str(items[name]['zorder']))
            nodekeypoint.setAttribute('x', str(items[name]['x']))
            nodekeypoint.setAttribute('y', str(items[name]['y'])) 
            nodekeypoint.setAttribute('z', str(items[name]['z']))
            nodekeypoint.setAttribute('visible', str(items[name]['visible']))
            # 添加节点到文档对象
            nodekeypoints.appendChild(nodekeypoint)
        # 添加节点到根节点
        root.appendChild(nodeimage)
        root.appendChild(nodecategory)
        root.appendChild(nodesubcategory)
        root.appendChild(nodekeypoints)
        # 路径
        path = DIR + '/yd_pose/test/' + str(item['image']) + '.xml'
        # 以写的方式打开，但是需要注意的是： 若文件存在，则文件会被清空
        fp = open(path, 'w')
        print(path)
        # writexml()第一个参数是目标文件对象，第二个参数是根节点的缩进格式，第三个参数是其他子节点的缩进格式，
        # 第四个参数制定了换行格式，第五个参数制定了xml内容的编码。  
        doc.writexml(fp, indent='\t', addindent='\t', newl='\n', encoding="utf-8")
        # 把路径添加到列表
        paths.append(path)
        names.append(str(item['image'])+'.xml')
        # 关闭文件
        fp.close()
        
    # 判断zipFileCnt是否为空，不为空：false
    if not zipFileCnt:
        for i in range(len(paths)):
            print(paths[i])
            print(names[i])
            # 在文件中写入数据
            f.write(paths[i],'/' + names[i])
            os.remove(paths[i])
    else:
    ###打包成多个zip，再将所有zip压缩成一个总压缩包
        index = 0
        file_sum = len(paths)
        file_cnt = int(zipFileCnt)
        zip_cnt = (file_sum - 1) // file_cnt + 1
        zip_path = DIR+'/yd_pose/test/file_zip.zip'
        for i in range(zip_cnt):
            file_zip = zipfile.ZipFile(zip_path,'w',zipfile.ZIP_STORED)
            for j in range(file_cnt):
                if index >= file_sum:
                    break
                print(paths[index])
                print(names[index])
                file_zip.write(paths[index],'/' + names[index])
                os.remove(paths[index])
                index += 1
            zip_name = '/{}.zip'.format(i + 1)
            file_zip.close()
            # 在文件中写入数据
            f.write(zip_path, zip_name)
            # 用于删除指定路径下的文件，如果指定的路径是一个目录，将抛出OsError
            os.remove(zip_path)
    # 关闭文件        
    f.close()
    return [DIR+'/yd_pose/test/', 'test.zip']
    #os.remove(DIR+'/yd_pose/test/test.zip')
    # with open(DIR+'/yd_pose/test/test.zip','rb') as f1:
    #     base64_str = base64.b64encode(f1.read())
    # return base64_str

# 获取图片的长宽    
def get_image_wh(userFileId):
    sql = '''select imageHeight,imageWidth from userfile,image where userfile.userFileId={} and userfile.fileId=image.fileId'''.format(userFileId)
    res = db_file(sql)
    return (res[0]['imageHeight'], res[0]['imageWidth'])

# 获取coco文件
def get_coco_file(userFileIds,person):
    # 生成coco文件
    db_type = 'push-up-1'
    if person:
        db_type = person[0]['filepath'][9:]
    userFileIds = userFileIds.split(',')
    save_path = DIR + '/annotations/'
    respath = save_path
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    jsonname = db_type.split('/')[0]
    save_path = os.path.join(save_path, jsonname + '.json')
    resname = jsonname + '.json'
    joint_num = 17
    aid = 0
    # coco文件格式
    coco = {'images':[], 'categories':[], 'annotations':[]}
    # category格式
    category = {
        'supercategory':'person',
        'id':1,
        'name':'person',
        'keypoints':['body_head','neck','left_shoulder','right_shoulder','left_elbow','right_elbow','left_wrist','right_wrist','left_hip',
        'right_hip','left_knee','right_knee','left_ankle','right_ankle','nose','left_ear','left_eye','right_eye','right_ear'],
        'skeleton':[[0,1],[1,2],[1,3],[2,4],[3,5],[4,6],[5,7],[8,10],[9,11],[10,12],[11,13],[2,8],[3,9],[8,9],[1,14],[14,16],[16,15],[14,17],[17,18]]
        }
    for item in person:
        filename = str(item['image']) + '.jpg'
        filepath = db_type
        # 获取图片高和宽
        h, w = get_image_wh(userFileIds[aid])
        # images格式
        img_dic = {'id': aid, 'file_name': filepath+filename, 'coco_url':'http://images.cocodataset.org/'+filepath+filename, 'width': w, 'height': h}
        coco['images'].append(img_dic)
        # 获取关键点数据和数量
        kps = []
        numkeypoints = 0
        items = item['keypoints']
        bbox = [0,0,0,0]
        xmin = 0
        ymin = 0
        xmax = 0
        ymax = 0
        for keypoint in item['keypoints']:
            x = items[keypoint]['x']
            y = items[keypoint]['y']
            v = 2 if items[keypoint]['visible'] else 1
            if not (x == y == 0):
                numkeypoints += 1
                kps += [x,y,v]
                if v > 0:
                    if xmin > x or xmin == 0:
                        xmin = x
                    if xmax < x:
                        xmax = x
                    if ymin > y or ymin == 0:
                        ymin = y
                    if ymax < y:
                        ymax = y
        width = xmax - xmin + 1
        height = ymax - ymin + 1
        if width <= 0 or height <= 0:
            continue
        else:
            if width > height:
                if height/width < 0.15:
                    height = width * 0.15
            else:
                if width/height < 0.15:
                    width = height * 0.15
            width_ratio = 1.3 if width > height else 1.5
            height_ratio = 1.5 if width > height else 1.3
            bbox[0] = (xmin + xmax)/2. - width/2*width_ratio
            bbox[0] = max(bbox[0], 0)
            bbox[1] = (ymin + ymax)/2. - height/2*height_ratio
            bbox[1] = max(bbox[1], 0)
            bbox[2] = width*width_ratio
            if bbox[2] >= w - bbox[0]:
                bbox[2] = w - bbox[0] - 1
            bbox[3] = height*height_ratio
            if bbox[3] >= h - bbox[1]:
                bbox[3] = h - bbox[1] - 1

        # annotations格式
        person_dict = {'id':aid,'image_id':aid, 'category_id': 1, 'area': bbox[2]*bbox[3], 'bbox':bbox, 'iscrowd':0, 'keypoints': kps, 'numkeypoints': numkeypoints}
        coco['annotations'].append(person_dict)
        aid += 1
    category['keypoints'] = category['keypoints']
    category['skeleton'] = category['skeleton']
    # categories格式
    coco['categories'] = [category] 
    with open(save_path, 'w') as f:
        json.dump(coco, f)
    return [respath, resname]        

# 获取自定义文件
def get_custom_file(cocopath):
    output_name = '{}_custom.json'.format(cocopath[1][:-5])
    output_file = DIR + '/annotations/' + output_name
    input_file = DIR + '/annotations/' + cocopath[1]
    order_map = {0: 13, 1: 11, 2: 9, 3: 8, 4: 10, 5: 12, 6: 1, 7: 0, 8: 7, 9: 5, 10: 3, 11: 2, 12: 4, 13: 6}

    # 使用with的话，能够减少冗长，还能自动处理上下文环境产生的异常
    # 只读模式打开文件，读文件内容的指针会放在文件的开头，操作的文件必须存在
    with open(input_file, 'r', encoding='utf-8') as f:
        # json.load()从json文件中读取数据
        data = json.load(f)

    input_anno = data['annotations']
    input_img = data['images']
    print('annotations:', len(input_anno), 'images:', len(input_img))
    dict_img = {}
    for img in input_img:
        dict_img[img['id']] = img['file_name']
    res = []
    for i in input_anno:
        image = dict_img[i['image_id']]
        ## 训练时会重新计算visibility，此处结果可不管
        #visibility = [1 if j == 2 else 0 for j in i['keypoints'][2::3]]
        #bbox = [i['bbox'][:2], i['bbox'][2:]]

        points = []
        for x, y, v in zip(i['keypoints'][0::3], i['keypoints'][1::3], i['keypoints'][2::3]):
            if v != 0:
                points.append([x, y])
            else:
                points.append([-1, -1])
        print(points)
        #points = sorted([i for i in zip(order_map.values(), points)], key=lambda k: k[0])
        #points = [i[1] for i in points]

        # print({'image': image, 'points': points, 'visibility': visibility, 'bbox': bbox})
        # 列表中嵌套字典
        res.append({'image': image, 'points': points})
    print('输出数量：', len(res))

    with open(output_file, 'w', encoding='utf-8') as f:
        # 将python对象编码成Json字符串  
        json.dump(res, f)
    return output_name


# 标注文件下载
@app.route('/label_download', methods=['GET','POST'])
def label_download():
    userFileIds = request.values.get('userFileIds')
    fileType = request.values.get('fileType')
    zipFileCnt = request.values.get('zipFileCnt', '')
    resp = {}
    resp['code'] = 1
    resp['msg'] = '未知原因'
    # 文件类型错误
    if fileType not in ['coco','xml','custom']:
        resp['code'] = 1
        resp['msg'] = '文件类型错误'
    # 从数据库获取多个节点
    person = get_db_points(userFileIds)
    # 用逗号分割
    idList = userFileIds.split(',')
    # 判断是否获取到所有标注文件
    if len(person) != len(idList):
        resp['code'] = 1
        resp['msg'] = '部分文件未存在标注文件'
    # 判断文件类型是否为xml类型    
    if fileType == 'xml':
        filepath = get_xml_file(zipFileCnt, person)
        respath = filepath[0]
        resname = filepath[1]
    # 判断文件类型是否为coco类型        
    elif fileType == 'coco':
        filepath = get_coco_file(userFileIds, person)
        respath = filepath[0]
        resname = filepath[1]
    # 判断文件类型是否为custom类型      
    elif fileType == 'custom':
        cocopath = get_coco_file(userFileIds, person)
        resname = get_custom_file(cocopath)
        respath = cocopath[0]
    #file = make_response(send_from_directory(respath, resname, as_attachment=True))
    #resp['file'] = file
    try:
        # make_response() 自定义响应内容
        # 在视图内部掌控响应对象的结果

        # send_from_directory() 文件下载
        # respath：文件的绝对路径，不包含文件名
        # resname：文件名称
        # as_attachment：是否显示文件名称
        return make_response(send_from_directory(respath, resname, as_attachment=True))
    except:    
        # 将python对象编码成Json字符串    
        return json.dumps(resp)


# xml文件上传接口
@app.route('/upload_label_file', methods=['GET','POST'])
def uploadlabelfile():
    # request.method 获取当前请求方式
    if request.method == 'GET':
        # render_template 模板,引入html文件
        return render_template('commit.html')
    if request.method == 'POST':
        # request.files[]就表示原先的 file控件名,获取传到后端的file文件
        file = request.files['file']
        # request.form 获取指定的表单数据
        filename = request.form['filename']
        filePath = request.form['filePath']
        resp = {}
        resp['code'] = 1
        # 判断是否获取到文件
        if not file:
            resp['msg'] = '上传失败'
            return resp
        # 获取节点
        person = get_point(file)
        # 获取节点类型
        keypoint = get_dbtype_point(person)
        # 用逗号分隔后在组成字符串
        keypoint = ','.join(keypoint)
        try:
            # 用‘_’分割成两个字符串
            filename, person_id = filename.split('_')
        except:
            resp['msg'] = '文件名错误'
            return resp
        # 数据库查询
        sql = '''select userFileId from userfile where filePath="{}" and fileName="{}"'''.format(filePath, filename)
        result = db_file(sql)
        # 判断result是否为None
        if result:
            userFileId = result[0]['userFileId']
            sql = '''select img_id from ai_image where file_id={}'''.format(userFileId)
            result = db_file(sql)
            # 判断result是否不为None
            if not result:
                # 建立标签创建节点保存到数据库中
                create_label(filePath, userFileId, person_id, person)
                resp['code'] = 0
                resp['msg'] = '标注文件已生成'
                return resp
            img_id = result[0]['img_id']
        else:
            resp['msg'] = '文件不存在'
            return resp
        if not keypoint:
            resp['msg'] = '失败'
            return resp
        # 修改数据库中数据
        sql = 'update ai_label_skeleton set status=0,{} where img_id={}'.format(keypoint,img_id)
        print(sql)
        db_file(sql)
        sql = 'select label_id from ai_label_skeleton where img_id={}'.format(img_id)
        result = db_file(sql)
        if result:
            label_id = result[0]['label_id']
            sql = '''select * from ai_tag,ai_label_tag where ai_label_tag.label_id={} and ai_label_tag.tag_id=ai_tag.tag_id
                and tag_id.tag={}'''.format(label_id, person['subcategory'])
        resp['code'] = 0
        resp['msg'] = '标注文件已更改'
        return resp