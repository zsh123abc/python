
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:  # 基本配置类
    SECRET_KEY = os.getenv('SECRET_KEY', 'some secret words')
    ITEMS_PER_PAGE = 10


class DevelopmentConfig(BaseConfig):  #  开发环境
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:yd_db_pass@192.168.100.109:3306/file?charset=utf8'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    

class TestingConfig(BaseConfig):  # 测试环境
    TESTING = True
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

DIR = '/data/dataset'