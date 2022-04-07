import os#适应python
from collections import defaultdict
file_type = defaultdict(int)  #创建一个空的字典，用来存储我们的结果
#os.chdir(r'F:\\python_code ')   #更改当前工作目录,其实不用更改，一直是这个路径
# current_work_dir = os.curdir： 指代当前目录，在windows系统下是'.'
current_work_dir = os.getcwd()   #当前工作目录
#filepath = current_work_dir
def get_file_list(filepath):
    try:
        current_work_dir = os.chdir(filepath)
        all_file = os.listdir(current_work_dir)  #用列表列举当前目录中的文件名
    except:
        print('error')
        return
    #print(all_file )
    queue = []
    for each_file in all_file:   #依次提取这个列表中的每一个元素（路径）
        if os.path.isdir(filepath+each_file) == True:   #判断这个路径是否表示文件夹,如果这是文件夹，就==True,如果不是文件夹就跳到else          
            path = filepath + each_file + '/'
            if each_file == 'path':
                path+='to/'
            print(path)
            if each_file[0] == '.':
                continue
            get_file_list(path)
        else:  # 如果不是文件夹，即是有后缀的那些文件
            #ext = os.path.splitext(each_file)[1]   #分离文件名与扩展名，返回元组(f_name, f_extension)[1]这里的意思是元组中第二个名字即扩展名
            #file_type.setdefault(ext, 0)   #将这个拓展名放置在字典中
            #file_type[ext] +=1#如果没有这个扩展名就添加，如果有这个扩展名就+1
            print(filepath + each_file)

get_file_list('./')