# -*- coding:utf-8 -*-
from __future__ import print_function
from pycocotools.coco import COCO
import os, sys, zipfile
import urllib.request
import shutil
import numpy as np
import skimage.io as io
import cv2
import matplotlib.pyplot as plt
import pylab
import json
import argparse


parser = argparse.ArgumentParser(description='show bbox and keypoints in images.')
parser.add_argument('img_dir', metavar='img_dir', type=str,
                    help='path to input image directory.')
parser.add_argument('json_in_path', metavar='json_in_path', type=str,
                    help='path to input json path.')
parser.add_argument('bboxOutDir', metavar='bboxOutDir', type=str,
                    help='path to bbox output directory.')
parser.add_argument('keyPointOutDir', metavar='keyPointOutDir', type=str,
                    help='path to keypoint output directory.')

def show_keypoints(dataDir, annFile, outDir):
    if not os.path.exists(outDir):
        os.makedirs(outDir)

    pylab.rcParams['figure.figsize'] = (8.0, 10.0)
    coco = COCO(annFile)

    # display COCO categories and supercategories
    cats = coco.loadCats(coco.getCatIds())
    nms = [cat['name'] for cat in cats]
    print('COCO categories: \n{}\n'.format(' '.join(nms)))
    nms = set([cat['supercategory'] for cat in cats])
    print('COCO supercategories: \n{}'.format(' '.join(nms)))
    imgIds = coco.getImgIds()  # list

    for i in range(len(imgIds)):
        img = coco.loadImgs(imgIds[i])[0]  # list, len:1
        dataType = ''
        # print(img['file_name'])
        I = io.imread('%s/%s/%s' % (dataDir, dataType, img['file_name']))

        plt.axis('off')
        plt.imshow(I)
        plt.show()

        # load and display instance annotations
        # 加载实例掩膜
        # catIds = coco.getCatIds(catNms=['person','dog','skateboard']);
        # catIds=coco.getCatIds()
        catIds = []
        for ann in coco.dataset['annotations']:
            if ann['image_id'] == imgIds[0]:
                catIds.append(ann['category_id'])
        return json.dumps(catIds)
        # plt.imshow(I); plt.axis('off')
        annIds = coco.getAnnIds(imgIds=img['id'], catIds=catIds, iscrowd=None)
        ### filter by single person in a picture
        if(len(annIds) != 1):
            continue
        anns = coco.loadAnns(annIds)
        coco.showAnns(anns)

        # name = os.path.basename(os.path.join(dataDir, img['file_name'])) # 14个点
        # plt.savefig("{}/{}".format(outDir, name))

        save_path = "{}/{}".format(outDir, img['file_name'])
        save_dir = os.path.split(save_path)[0]
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        plt.savefig(save_path)  # 17个点
        plt.clf()  # 清除当前figure

def show_bbox(img_dir, json_file, outDir):
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    with open(json_file) as annos:
        raw_data = json.load(annos)
    images_id_num = len(raw_data['images'])
    annos_id_num = len(raw_data['annotations'])

    for i in range(annos_id_num):
        if raw_data['annotations'][i]['category_id'] != 1: # 1表示人这一类
            continue
        bbox = raw_data['annotations'][i]['bbox'] # (x1, y1, w, h)
        x, y, w, h = bbox
        img_id = raw_data['annotations'][i]['image_id']
        for k in range(images_id_num):
            if raw_data['images'][k]['id'] == img_id:
                img_name = raw_data['images'][k]['file_name']
                # if(img_name == '0300008.jpg'):
                #     print("img_id:{}".format(img_id))
                #     print("img_name:{}".format(img_name))
                #     print("x: {}, y: {}, w: {}, h:{}".format(x, y, w, h))
                #     return
                image_path = os.path.join(img_dir, img_name)  # 记得加上.jpg
                image = cv2.imread(image_path)
                # 参数为(图像，左上角坐标，右下角坐标，边框线条颜色，线条宽度)
                # 注意这里坐标必须为整数，还有一点要注意的是opencv读出的图片通道为BGR，所以选择颜色的时候也要注意
                anno_image = cv2.rectangle(image, (int(x), int(y)), (int(x + w), int(y + h)), (0, 255, 255), 2)
                # 保存图片
                path = os.path.join(outDir, img_name)
                save_dir = os.path.split(path)[0]
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                print(path)
                cv2.imwrite(path, anno_image)
                break

def main(args):
    # 在图片上显示bbox并保存, 显示关键点坐标并保存
    #if os.path.exists(args.bboxOutDir):
    #    shutil.rmtree(args.bboxOutDir)
    #show_bbox(args.img_dir, args.json_in_path, args.bboxOutDir)
    if os.path.exists(args.keyPointOutDir):
        shutil.rmtree(args.keyPointOutDir)
    show_keypoints(args.img_dir, args.json_in_path, args.keyPointOutDir)

if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
