import cv2

img = cv2.imread('C:/Users/cwj/Desktop/v.jpg')
img_encode = cv2.imencode('.webp', img)

# 将数组中的数据以二进制格式写进文件
# img_encode[1].tofile('C:/Users/cwj/Desktop/v2.webp')


print(type(img_encode))
print(img_encode)

# shape 用来告知输出数据的形式
# img_shape=img_encode[1].shape
# print(img_shape)





