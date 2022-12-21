import logging
import os
# abspath 获取脚本路径，dirname 去掉文件名，返回目录 
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:  # 基本配置类
    # os.getenv 获取环境变量键SECRET_KEY的只（存在），否则返回默认值some secret words
    SECRET_KEY = os.getenv('SECRET_KEY', 'some secret words')
    ITEMS_PER_PAGE = 10
    level = logging.DEBUG

class DevelopmentConfig(BaseConfig):  #  开发环境
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:yd_db_pass@192.168.100.109:3306/file?charset=utf8'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    

class TestingConfig(BaseConfig):  # 测试环境
    TESTING = True
    # os.path.join拼接路径
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite'))
    WTF_CSRF_ENABLED = False

class ProductionConfig(BaseConfig):  # 生产环境
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite'))
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'product': ProductionConfig,
    'default': DevelopmentConfig
}

# 根目录
DIR = '/data/dataset'
# 模型路径
tflite_path = './model_float32.tflite'