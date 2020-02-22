

USERNAME = 'ldd_biz'
PASSWORD = 'Hello1234'
HOST = '172.16.157.238'
PORT = '3306'
DATABASE = 'test_mimi'

DATABASE_DEBUG = True


URL = "mysql+pymysql://{}:{}@{}:{}/{}?{}".format(USERNAME, PASSWORD,
            HOST, PORT, DATABASE,
            'charset=utf8')




