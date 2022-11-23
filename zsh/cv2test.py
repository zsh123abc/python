import numpy as np
import cv2 as cv

img = cv.imread("D:/zsh/biaozhu/img/images/video_1.mp4_test_0378.jpg")

# 缩放图像，后面的其他程序都是在这一行上改动
ori_h, ori_w, _ = img.shape
if ori_h<=ori_w:
    h = 150
    w = ori_w*150//ori_h
    dst = cv.resize(img, (w, h))
else:
    h = ori_h*150//ori_w
    w = 150
    img = cv.resize(img, (w, h))
# cv.startWindowThread()    
# 显示图像
cv.imshow("dst: %d x %d" % (dst.shape[0], dst.shape[1]), dst)
# 图像显示的时间
cv.waitKey(0)
# 删除任何建立的所有窗口
cv.destroyAllWindows()

