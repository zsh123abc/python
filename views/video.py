import cv2 
import os 
from config import DIR
from models import db_file
from app import app
from flask import request
from .database import insert_file,insert_folder

# outPutDir 视频路径 videoName 视频名字    
def get_frame_name(outPutDir, videoName, times):
    #命名视频帧
    n = len(videoName)
    # '0'*(3-n) 表示有几个0
    videoName = '0'*(3-n) + videoName
    n = len(str(times))
    times = '0'*(4-n) + times
    # filename 视频帧名字
    # /data/dataset/zsh/videos/label_data/images/17(1)0001.jpg
    filename = outPutDir + videoName + times + '.jpg'
    # 服务器存放图片的路径，图片名字无后缀：17(1)0001
    return [filename,videoName+times]

# 提取视频帧，并且保存到指定文件里
# videopath 视频文件路径，/zsh/videos/
# videoName 视频名字，17(1)
# outPutDir 视频文件抽帧后图片存放路径，/zsh/videos/label_data/images/
# fileurl 从数据库拿到的服务器存放视频的路径，/data/dataset/yd_pose/dance/k-pop/maria/ori_data/round_1/videos/17.mp4
# frame_cnt 表单数据，无
def get_frame(videoPath, videoName, outPutDir, fileurl, frame_cnt):
    #要提取视频的文件名
    sourceFileName=videoName
    #把后缀接上,服务器存放视频的路径
    # /data/dataset/zsh/videos/17.mp4
    video_path = DIR + videoPath + sourceFileName+'.mp4'
    print(video_path)
    # 计数用，多少帧截一张
    times=0
    #输出图片到当前目录vedio文件夹下
    # os.path.exists 文件夹存在返回True，反之返回false
    # /data/dataset/zsh/videos/label_data/images/
    if not os.path.exists(DIR+outPutDir):
        #如果文件目录不存在则创建目录
        # os.makedirs 递归生成文件夹，用来创建多层目录（单层用os.mkdir)
        # /data/dataset/zsh/videos/label_data/images/
        os.makedirs(DIR+outPutDir)
        # 插入文件夹，outPutDir[:-18]：文件名字，'label_data'：文件路径
        # 把数据插入数据库
        insert_folder(outPutDir[:-18], 'label_data')
        insert_folder(outPutDir[:-7],outPutDir[-7:-1])
    # n 给视频帧命名用的
    n = 1
    # cv2.VideoCapture() 视频抽帧，视频图像化
    camera = cv2.VideoCapture(fileurl)
    # 获取视频的帧率
    fps = camera.get(cv2.CAP_PROP_FPS)
    #提取视频的频率，每50帧提取一个
    if frame_cnt:
        frameFrequency=int(frame_cnt)
    else:
        frameFrequency=int(fps)
    print(frameFrequency)
    print(frame_cnt)
    # 取出所有的图片和图片名字并且存放进数据库
    while True:
        # 取帧，从1开始
        times+=1
        # read() 读取名字和图片
        res, image = camera.read()
        print(res)
        # 判断res是否为None
        if not res:
            print('not res , not image')
            break
        # 每50帧提取一个，times从1-50，51取模不等于0
        if times%frameFrequency==0:
            # get_frame_name() 命名视频帧
            # /data/dataset/zsh/videos/label_data/images/
            # 服务器存放图片路径，视频名字，计数n
            res = get_frame_name(DIR+outPutDir, videoName, str(n))
            # res：服务器存放图片的路径，图片名字无后缀：17(1)0001
            n += 1
            # 取出视频帧路径，有名字后缀
            # /data/dataset/zsh/videos/label_data/images/17(1)0001.jpg
            filename = res[0]
            # 取出加上数字后的视频名字，，无后缀
            # 17(1)0001
            name = res[1]
            print(filename)
            print(name)
            # cv2.imwrite() 用于将图像保存到指定的文件，视频帧和视频帧对应的图片，
            # filename：要保存的文件的路径和名称，image：保存的图片
            cv2.imwrite(filename, image)
            sql = '''select * from userfile where filePath="{}" and fileName="{}"'''.format(outPutDir, name)
            # 判断是否从数据库拿到数据，db_file(sql) 从数据库拿数据
            if not db_file(sql):
                insert_file(outPutDir, name,'jpg')
    print('图片提取结束')
    # 释放资源
    camera.release()

# #获取视频文件信息
def get_video_info(userFileIds):
    #获取视频文件信息
    sql = '''select fileName,filePath,extendName,fileId from userfile where userFileId in ({})'''.format(userFileIds)
    print(sql)
    #数据库操作
    result = db_file(sql)
    # 空列表
    videopath = []
    videolist = []
    videoextend = []
    videofileid = []
    for res in result:
        # 视频文件路径
        # 列表中添加数据
        videopath.append(res['filePath'])# /zsh/videos/
        # 视频文件名字
        videolist.append(res['fileName'])# 17(1)
        # lower() 大写字母转小写
        videoextend.append(res['extendName'].lower())#mp4
        videofileid.append(res['fileId'])#10161
    print(videopath)
    print(videoextend)
    # set() 转成一个集合{}
    videopath = set(videopath)
    videoextend = set(videoextend)
    # 判断视频文件路径是否存在
    if len(videopath) != 1:
        return 0
    # 判断视频文件名字是否存在    
    elif len(videoextend) != 1:
        return 1
    # list(videopath)[0] 视频文件路径集合中的第一个，/zsh/videos/
    # list(videoextend)[0] 视频文件名字后缀的第一个，mp4
    # videolist 存放视频文件名字的集合，17(1)
    # videofileid 视频文件Id，10161
    res = [list(videopath)[0], list(videoextend)[0], videolist, videofileid]
    return res

# 批量抽取视频帧
# 装饰器@ methods=['POST'] 代表这个url地址允许POST请求方式
# post 客户端使用响应码来确定应用程序的操作是否成功
# 通过route()装饰器的方法将函数连接到请求的URL上 ’/get_video_frame‘
@app.route('/get_video_frame', methods=['POST'])
def get_video_frame():
    # 定义一个空字典
    resp = {}
    # 执行正确，后面碰到错误就之后退出
    resp['code'] = 0
    resp['msg'] = 'ok'
    # Request.Form：获取以POST方式提交的数据
    # request.form['userFileIds'] 获取表单中userFileIds对应的值
    userFileIds = request.form['userFileIds']
    frame_cnt = ''
    # 判断'frame_cnt'是否在表单中
    if 'frame_cnt' in request.form:
        # 如果存在就取出对应的值
        frame_cnt = request.form['frame_cnt']
    print(userFileIds)
    # get_video_info() 从数据库中取出视频文件的数据：
    # 没有取到数据就是0或1
    # 路径，后缀，名字，fileId
    video_info = get_video_info(userFileIds)
    # ==0：视频文件路径错误，==1：视频文件类型错误
    if video_info == 0:
        # 执行出错
        resp['code'] = 1
        # 视频路径错误
        resp['msg'] = 'Video Path Error'
        return resp
    elif video_info == 1:
        # 执行出错
        resp['code'] = 1
        # 视频类型错误
        resp['msg'] = 'Video Type Error'
        return resp    
    # 视频文件路径
    videopath = video_info[0]# 路径 /zsh/videos/
    # 视频文件名字
    videolist = video_info[2]# 名字 17
    # 视频文件对应的fileId
    videofileid = video_info[3]# fileId 10161
    print(videopath)
    print(videolist)
    # 字符串切片判断路径是否是指定路径，否：文件路径错误
    # 当前路径是否是/videos/
    if videopath[-8:] != '/videos/':
        # 执行出错
        resp['code'] = 1
        # 视频路径错误
        resp['msg'] = 'Video Path Error'
        # 返回退出
        return resp
    # 如果是指定路径就在后面加上新路径拼凑成完整路径
    # outPutDir 视频抽帧后图片存放位置
    # /zsh/label_data/images/
    outPutDir=videopath[:-7]+'label_data/images/'
    # 视频文件名字长度
    n = len(videolist)
    # 视频名字对应的下标
    for i in range(n):
        # 循环把视频名字一个一个赋值过去
        video = videolist[i] # 17(1)
        # fileId 
        fileid = videofileid[i] # 10161
        # 数据库查询id
        sql = '''select fileUrl from file where fileId={}'''.format(fileid)
        # 拿到的所有数据的第一条中和’fileUrl‘对应的数据
        #yd_pose/dance/k-pop/maria/ori_data/round_1/videos/17.mp4
        fileurl = db_file(sql)[0]['fileUrl'] 
        # 把根目录路径加上，完整路径,服务器储存视频的绝对路径
        # /data/dataset/yd_pose/dance/k-pop/maria/ori_data/round_1/videos/17.mp4
        fileurl = DIR + '/' + fileurl
        # videopath 视频路径，/zsh/videos/
        # video 视频名字，17
        # outPutDir 视频文件抽帧后图片存放路径,/zsh/videos/label_data/images/
        # fileUrl 从数据库拿到的需要抽帧视频的路径，在服务器里，
            # /data/dataset/yd_pose/dance/k-pop/maria/ori_data/round_1/videos/17.mp4
        # frame_cnt 表单数据，无
        # 提取视频帧，并且保存到指定文件里
        get_frame(videopath, video, outPutDir, fileurl, frame_cnt)
    # 返回集合，里面存放code，msg，是否正确
    return resp