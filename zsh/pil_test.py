from PIL import Image
from PIL import ImageFilter
square = Image.open("D:/zsh/biaozhu/img/images/video_11.mp4_test_0909.jpg")
square1 = square.filter(ImageFilter.CONTOUR)  #选择轮廓效果
#square1.show()
square1.save("D:/zsh/biaozhu/img/video.jpg")
# square1.show()
