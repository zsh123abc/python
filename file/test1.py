# -*- coding:utf-8 -*-
import os
if __name__ == "__main__":
    rootdir = './'
    list = os.listdir(rootdir)  # 列出文件夹下所有的目录与文件
    for i in range(0, len(list)):
        path = os.path.join(rootdir, list[i])
        # if os.path.isfile(path):
        # # 你想对文件的操作
        print(path)