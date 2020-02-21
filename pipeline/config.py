


DATABASE_DEBUG = True

URL = '{}://{}:{}@{}:{}/{}?charset=utf8'.format(
    'mysql+pymysql',
    'ldd_biz', 'Hello1234',
    '172.16.157.238', 3306,
    'test_mimi',
)