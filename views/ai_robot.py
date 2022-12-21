# -*- coding: utf-8 -*-
import tensorflow as tf
import cv2
import numpy as np
import os
import csv
import matplotlib.pyplot as plt
import argparse
# import torch
import time
from model import db_file
from config import tflite_path,DIR

'''
D:\project\data\dance_test_0630_img
D:\project\data\dance_test_tflite_img
D:\project\TNN_Model_result\blaze_pose\blaze_gpose.tflite
'''

def time_synchronized():
    # pytorch-accurate time
    # torch.cuda.synchronize() if torch.cuda.is_available() else None
    return time.time()


def padding_img(img, dest_size=None, color=(255, 255, 255)):
    ori_h, ori_w, _ = img.shape                                 #原图尺寸

    if dest_size is None:
        if ori_h >= ori_w:
            dest_size = (ori_h, ori_h)                        #fixme   按长边填充
        else:
            dest_size = (ori_w, ori_w)

    if dest_size[0] < ori_w and dest_size[1] < ori_h:
        raise Exception("The dest size must small than origin image")

    w_offset = max(0, int((dest_size[0] - ori_w) // 2))
    h_offset = max(0, int((dest_size[1] - ori_h) // 2))

    dest_img = cv2.copyMakeBorder(img, h_offset, h_offset, w_offset, w_offset, cv2.BORDER_CONSTANT,
                                  color)                         #填充目标图片    按边扩充
    dest_img = cv2.resize(dest_img, (int(dest_size[0]), int(dest_size[1])))
    return (dest_img, w_offset, h_offset)



class PoseEstimator:
    def __init__(self, model_path):
        self.interpreter = tf.lite.Interpreter(model_path)
        self.inp_len = self.interpreter.get_input_details()[0]['shape'][2]
        self.interpreter.allocate_tensors()
        # print('outputs:%s'%self.interpret.get_outputs()[0])
        self.out_len = 48

    def predict(self, frame):
        inp_frame, w_offset, h_offset = padding_img(frame)
        tmp_img = cv2.resize(inp_frame, (self.inp_len, self.inp_len))

        pad_h, pad_w, _ = inp_frame.shape
        h_scale, w_scale = pad_h / self.out_len, pad_w / self.out_len

        # tmp_img = tmp_img / 127.5 - 1
        tmp_img = tmp_img
        # img_transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])
        # tmp_img = img_transform(tmp_img).numpy()

        # inp_img = tmp_img.transpose((2, 0, 1))
        inp_img = tmp_img
        inp_img = inp_img[np.newaxis, :, :, :]
        inp_img = inp_img.astype(np.float32)

        input_details = self.interpreter.get_input_details()
        # print(input_details)
        output_details = self.interpreter.get_output_details()
        # print(output_details)

        self.interpreter.set_tensor(input_details[0]['index'], inp_img)
        t1 = time_synchronized()
        self.interpreter.invoke()
        pred = [self.interpreter.get_tensor(output_details[i]['index']) for i in range(len(output_details))]
        t2 = time_synchronized()
        FPS = 1/(t2-t1)
        # print(pred)
        coords = []
        pred = np.squeeze(pred)              #输出形状转换output: [17, 3]
        conf = []
        avg_conf = 0

        for i in range(pred.shape[0]):
            xy = pred[i,:]

            raw_x = xy[1]*self.out_len
            raw_y = xy[0]*self.out_len  # 找到最大位置所在行-->   x坐标值
            y = int(raw_y * h_scale - h_offset)  # 返回原图所在位置
            x = int(raw_x * w_scale - w_offset)
            coords.append([x, y])
            conf.append([x, y, xy[2]])
            avg_conf += xy[2]
        neck = [(coords[5][0]+coords[6][0])/2, (coords[5][1]+coords[6][1])/2]

        coords.insert(6,neck)
        # coords[6]
        avg_conf = avg_conf / pred.shape[0]

        return coords,pred, conf, avg_conf, FPS


def getPersonKeypoints(name, results):
    '''
        results forat
        "keypoints": {
            0: "nose",
            1: "left_eye",
            2: "right_eye",
            3: "left_ear",
            4: "right_ear",
            5: "left_shoulder",
            6: "neck",
            7: "right_shoulder",
            8: "left_elbow",
            9: "right_elbow",
            10: "left_wrist",
            11: "right_wrist",
            12: "left_hip",
            13: "right_hip",
            14:"left_knee",
            15:"right_knee",
            16:"left_ankle",
            17:"right_ankle"
        }
    '''
    person = {}
    person['image'] = name
    person['keypoints'] = {}
    person['keypoints']['R_Ankle'] = {}
    person['keypoints']['R_Ankle']['x'] = results[17][0]
    person['keypoints']['R_Ankle']['y'] = results[17][1]
    person['keypoints']['R_Ankle']['visible'] = '2'
    person['keypoints']['R_Knee'] = {}
    person['keypoints']['R_Knee']['x'] = results[15][0]
    person['keypoints']['R_Knee']['y'] = results[15][1]
    person['keypoints']['R_Knee']['visible'] = '2'
    person['keypoints']['R_Hip'] = {}
    person['keypoints']['R_Hip']['x'] = results[13][0]
    person['keypoints']['R_Hip']['y'] = results[13][1]
    person['keypoints']['R_Hip']['visible'] = '2'
    person['keypoints']['L_Hip'] = {}
    person['keypoints']['L_Hip']['x'] = results[12][0]
    person['keypoints']['L_Hip']['y'] = results[12][1]
    person['keypoints']['L_Hip']['visible'] = '2'
    person['keypoints']['L_Knee'] = {}
    person['keypoints']['L_Knee']['x'] = results[14][0]
    person['keypoints']['L_Knee']['y'] = results[14][1]
    person['keypoints']['L_Knee']['visible'] = '2'
    person['keypoints']['L_Ankle'] = {}
    person['keypoints']['L_Ankle']['x'] = results[16][0]
    person['keypoints']['L_Ankle']['y'] = results[16][1]
    person['keypoints']['L_Ankle']['visible'] = '2'

    person['keypoints']['R_Wrist'] = {}
    person['keypoints']['R_Wrist']['x'] = results[11][0]
    person['keypoints']['R_Wrist']['y'] = results[11][1]
    person['keypoints']['R_Wrist']['visible'] = '2'
    person['keypoints']['R_Elbow'] = {}
    person['keypoints']['R_Elbow']['x'] = results[9][0]
    person['keypoints']['R_Elbow']['y'] = results[9][1]
    person['keypoints']['R_Elbow']['visible'] = '2'
    person['keypoints']['R_Shoulder'] = {}
    person['keypoints']['R_Shoulder']['x'] = results[7][0]
    person['keypoints']['R_Shoulder']['y'] = results[7][1]
    person['keypoints']['R_Shoulder']['visible'] = '2'
    person['keypoints']['L_Shoulder'] = {}
    person['keypoints']['L_Shoulder']['x'] = results[5][0]
    person['keypoints']['L_Shoulder']['y'] = results[5][1]
    person['keypoints']['L_Shoulder']['visible'] = '2'
    person['keypoints']['L_Elbow'] = {}
    person['keypoints']['L_Elbow']['x'] = results[8][0]
    person['keypoints']['L_Elbow']['y'] = results[8][1]
    person['keypoints']['L_Elbow']['visible'] = '2'
    person['keypoints']['L_Wrist'] = {}
    person['keypoints']['L_Wrist']['x'] = results[10][0]
    person['keypoints']['L_Wrist']['y'] = results[10][1]
    person['keypoints']['L_Wrist']['visible'] = '2'

    person['keypoints']['B_Head'] = {}
    person['keypoints']['B_Head']['x'] = results[0][0]
    person['keypoints']['B_Head']['y'] = results[0][1]
    person['keypoints']['B_Head']['visible'] = '2'
    person['keypoints']['Neck'] = {}
    person['keypoints']['Neck']['x'] = results[6][0]
    person['keypoints']['Neck']['y'] = results[6][1]
    person['keypoints']['Neck']['visible'] = '2'

    return person


def convert(img_dir, userFileIds='', onnx_path=tflite_path):
    # yd pose keypoint order        
    # KP_Names = ['R_Ankle', 'R_Knee', 'R_Hip', 'L_Hip', 'L_Knee', 'L_Ankle', '', '', 'Neck', 'B_Head', 'R_Wrist',
    #             'R_Elbow', 'R_Shoulder', 'L_Shoulder', 'L_Elbow', 'L_Wrist']  
    # 集合记录需要标注的人体关节点名字              
    person_keys = ['B_Head','Neck','L_Shoulder','R_Shoulder','L_Elbow','R_Elbow','L_Wrist','R_Wrist','L_Hip',
        'R_Hip','L_Knee','R_Knee','L_Ankle','R_Ankle','Nose','L_Ear','L_Eye','R_Eye','R_Ear']
    # csv_output_rows = []
    p = PoseEstimator(model_path=onnx_path)
    userfile_str = ''
    if userFileIds:
        userfile_str = 'and userFileId in ({})'.format(userFileIds)
    # 查询，从userfile表中获取 userFileId,filename 两列内容
    # 条件：filePath = img_dir 并且 extendName = jpg 并且 userFileId 要在userFileIds集合里
    sql = '''select userFileId,fileName from userfile where filePath="{}" and extendName="jpg" {}'''.format(img_dir, userfile_str)
    #print(sql)
    result = db_file(sql)

    # 循环取出数据
    for res in result:
        print(res)
        # 文件名加上后缀
        name = res['fileName'] + '.jpg'
        # 用户文件id
        userFileId = res['userFileId']
        # 查询ai_image表中所有列的内容
        # 条件 file_id=userFileId
        sql = '''select * from ai_image where file_id={}'''.format(userFileId)
        flag = True
        # 没有查询到数据就插入数据之后在查询
        if not db_file(sql):
            # insert into ai_image set 
            # set 一次插入多条数据
            sql = '''insert into ai_image set file_id={}, path="{}",type="jpg",status=0'''.format(userFileId, img_dir)
            db_file(sql)
            # 查询 ai_image 表中img_id列中 file_id = userFileId 的数据
            sql = '''select img_id from ai_image where file_id={}'''.format(userFileId)
            flag = False
        # 数据第一条中img_id对应的值
        img_id = db_file(sql)[0]['img_id']
        print(flag)
        # 文件所在的绝对路径
        file = DIR+img_dir+name
        print(file)
        # 根据路径读入图片
        img = cv2.imread(file)
        # 没有数据就跳过本次循环
        if img is None:
            continue

        predict = p.predict(img)
        person = getPersonKeypoints(name, predict[0])

        #print(person)
        # data = person["image"]

        # 空列表
        kps = []
        # 循环取出person中keypoints对应的数据
        for keypoint in person['keypoints']:
            # index() 判断字符串是否包含另一个字符串，返回第一次出现的地址，没有就抛出异常
            idx = person_keys.index(keypoint) + 1
            for k in person['keypoints'][keypoint]:
                # (k, idx, person['keypoints'][keypoint][k]) 数据所在的集合，id，数据
                # 用= 为了后面直接给sql语句使用
                str_point = '%s%s=%s' % (k, idx, person['keypoints'][keypoint][k])
                #print(str_point)
                # 列表添加数据
                kps.append(str_point)
        # 用','分开kps，并且组成一个新的字符串   
        keypoints = ','.join(kps)
        #print(keypoints)

        # 查询ai_label_skeleton表中label_id列的内容
        # 条件 img_id = img_id
        sql = '''select label_id from ai_label_skeleton where img_id={}'''.format(img_id)
        label_result = db_file(sql)

        # 判断label_result是否为空，为空else
        # 有数据修改已有数据，没有插入新数据
        if label_result:
            # 修改ai_label_skeleton表中的person_id,status数据，set:修改多条数据，where：只修改img_id=img_id的数据
            sql = '''update ai_label_skeleton set person_id=0,status=0,{} where img_id={}'''.format(keypoints, img_id)
            db_file(sql)
        else:
            # ai_label_skeleton表插入多条数据
            sql = '''insert into ai_label_skeleton set person_id=0,status=0,img_id={},{}'''.format(img_id, keypoints)
            db_file(sql)
            # 查询ai_label_skeleton表中label_id列的数据，条件 img_id相等
            sql = '''select label_id from ai_label_skeleton where img_id={}'''.format(img_id)
            label_id = db_file(sql)[0]['label_id']
            # ai_label_skeleton表插入多条数据
            sql = '''insert into ai_label_tag set tag_id = 1,label_id={}'''.format(label_id)
            db_file(sql)
        

        

        # xmin = 0
        # ymin = 0
        # xmax = 0
        # ymax = 0

        # print(person["keypoints"].keys())
        # for kp_name in KP_Names:
        #     if kp_name == "" or not kp_name in person["keypoints"]:
        #         data.extend([0, 0, 0])
        #         continue
        #     kp = person["keypoints"][kp_name]
        #     # if kp["visible"] == "0":
        #     #    data.extend([0, 0, 1])
        #     #    continue
        #     x = float(kp["x"])
        #     y = float(kp["y"])
        #     visible = 1 if kp["visible"] == "0" else 2
        #     data.extend([x, y, visible])

        #     if visible > 0:
        #         if xmin > x or xmin == 0:
        #             xmin = x
        #         if xmax < x:
        #             xmax = x
        #         if ymin > y or ymin == 0:
        #             ymin = y
        #         if ymax < y:
        #             ymax = y

        # imgPath = os.path.join(img_dir, person["image"])
        # print(imgPath)
        # image_bgr = cv2.imread(imgPath, cv2.IMREAD_COLOR)
        # if image_bgr.size == 0:
        #     print('read fail:', imgPath)
        #     continue

        # width = xmax - xmin + 1
        # height = ymax - ymin + 1

        # bbox = np.zeros((4))
        # # corrupted bounding box
        # if width <= 0 or height <= 0:
        #     continue
        # # 20% extend
        # else:
        #     width_ratio = 1.3 if width > height else 1.5
        #     height_ratio = 1.5 if width > height else 1.3
        #     bbox[0] = (xmin + xmax) / 2. - width / 2 * width_ratio
        #     if bbox[0] < 0:
        #         bbox[0] = 0
        #     bbox[1] = (ymin + ymax) / 2. - height / 2 * height_ratio
        #     if bbox[1] < 0:
        #         bbox[1] = 0
        #     bbox[2] = width * width_ratio
        #     if bbox[2] > image_bgr.shape[0]:
        #         bbox[2] = image_bgr.shape[0] - bbox[0]
        #     bbox[3] = height * height_ratio
        #     if bbox[3] > image_bgr.shape[1]:
        #         bbox[3] = image_bgr.shape[1] - bbox[1]

        # data.extend(bbox)
        # csv_output_rows.append(data)

    # headers = ["frame"]
    # for i in range(len(KP_Names)):
    #     headers.extend(["%s_x" % KP_Names[i].lower(), "%s_y" % KP_Names[i].lower(), "%s_v" % KP_Names[i].lower()])
    # headers.extend(["bbox_top_x", "bbox_top_y", "bbox_bottom_x", "bbox_bottom_y"])

    # par_dir = os.path.abspath(os.path.dirname(img_dir))
    # with open(os.path.join(par_dir, "pose-data_blaze.csv"), 'w', newline='') as csvfile:
    #     csvwriter = csv.writer(csvfile)
    #     csvwriter.writerow(headers)
    #     csvwriter.writerows(csv_output_rows)
    #     csvfile.close()
