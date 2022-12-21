

person = {'image':'1324443197.mp4_test_0390',
            'subcategory':'male',
              'keypoints':'{B_Head:(0.0,273.0.151.0.0.0,2)}'
        } 
# keypoint = ','.join(keypoint) 
# 

try:
    test='1324443197.mp4test0000.xml' 
    filename, person_id,a = test.split('_')
    print(filename,person_id,a)
except:   
    print('文件名错误') 
   

