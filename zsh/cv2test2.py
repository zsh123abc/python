import cv2


keys = ['B_Head','Neck','L_Shoulder','R_Shoulder','L_Elbow','R_Elbow','L_Wrist','R_Wrist','L_Hip',
        'R_Hip','L_Knee','R_Knee','L_Ankle','R_Ankle','Nose','L_Ear','L_Eye','R_Eye','R_Ear']
point_x = []
point_y = []
point_v = []

# 除了'Nose','L_Ear','L_Eye','R_Eye','R_Ear'，其他点都记录顺序
lines = [[530,231],[560,339],[1,3],[2,4],[3,5],[4,6],[5,7],[8,10],[9,11],[10,12],[11,13],[2,8],[3,9],[8,9]]


'''<keypoint name="B_Head" visible="1" x="530.00" y="231.46" z="0.00" zorder="0"/>
<keypoint name="L_Ankle" visible="1" x="560.07" y="339.55" z="126.54" zorder="0"/>
<keypoint name="L_Elbow" visible="1" x="528.23" y="281.18" z="71.50" zorder="0"/>
<keypoint name="L_Hip" visible="1" x="540.02" y="299.46" z="49.96" zorder="0"/>
<keypoint name="L_Knee" visible="1" x="526.85" y="327.57" z="93.56" zorder="0"/>
<keypoint name="L_Shoulder" visible="1" x="537.86" y="259.96" z="44.48" zorder="0"/>
<keypoint name="L_Wrist" visible="1" x="508.18" y="303.39" z="71.50" zorder="0"/>
<keypoint name="Neck" visible="1" x="532.36" y="248.76" z="0.00" zorder="0"/>
<keypoint name="R_Ankle" visible="1" x="533.53" y="353.12" z="157.45" zorder="0"/>
<keypoint name="R_Elbow" visible="1" x="525.67" y="280.99" z="25.09" zorder="0"/>
<keypoint name="R_Hip" visible="1" x="534.32" y="299.26" z="74.20" zorder="0"/>
<keypoint name="R_Knee" visible="1" x="522.33" y="328.16" z="117.62" zorder="0"/>
<keypoint name="R_Shoulder" visible="1" x="535.50" y="257.60" z="0.00" zorder="0"/>
<keypoint name="R_Wrist" visible="1" x="509.16" y="301.23" z="39.69" zorder="0"/>'''


'''
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
cv2处理图片
'''
# cv2读入图片
imgpath = 'D:/zsh/biaozhu/img/img/v.jpg'
img = cv2.imread(imgpath)

# 取出每一个关键点对应的数据
for line in lines:
    # [0,1]
    point1,point2 = line
    # 取出每个点对应的x，y
    # x1 = point_x[point1]
    # x2 = point_x[point2]
    # y1 = point_y[point1]
    # y2 = point_y[point2]
    # 开始点
    start_point = (int(point1), int(point1))
    # 结束点
    end_point = (int(point2), int(point2))
    # 判断开始点和结束点的坐标是否为（0,0）
    if start_point == (0,0) or end_point == (0,0):
        # 退出本次循环
        continue
    # 判断两个坐标点是否存在
    if point1 and point2:
        
        '''
        cv2.line 画线条
        五个参数
        img:要划的线所在的图像;
        pt1:直线起点
        pt2:直线终点  （坐标分别为宽、高,opencv中图像的坐标原点在左上角)
        color:直线的颜色
        thickness=1:线条粗细,默认是1.如果一个闭合图形设置为-1,那么整个图形就会被填充
        '''
        cv2.line(img, start_point, end_point, (0,255,0), 5)
        
for i in range(14):     
        cv2.circle(img,(point1, point2),3,(255,0,0),3)

ori_h, ori_w, _ = img.shape
dst = cv2.resize(img, (ori_w, ori_h))
cv2.imshow("dst: %d x %d" % (ori_w, ori_h),img)
# 图像显示的时间
cv2.waitKey(0)
# 删除任何建立的所有窗口
cv2.destroyAllWindows()

    # 处理14个关键点，鼻子，耳朵，眼睛不要        
# for i in range(14):
#     # if point_v[i]：[0,1]
#     # cv2.circle()-画圆,和cv2.line()的参数大致相同
#     cv2.circle(img,(int(point_x[i]),int(point_y[i])),3,(255,0,0),3)