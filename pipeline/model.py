from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Date, Enum, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from pipeline.config import URL, DATABASE_DEBUG

STATE_WAITING = 0
STATE_PENDING = 1
STATE_RUNNING = 2
STATE_SUCCEED = 3
STATE_FAILED = 4
STATE_FINISH = 5


Base = declarative_base()


class Graph(Base):
    __tablename__ = 'graph';
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(48), nullable=False, unique=True)
    desc = Column(String(200), nullable=True)
    checked = Column(Integer,nullable=False,default=0)
    sealed = Column(Integer,nullable=False,default=0)


    def __repr__(self):
        return '<Graph {} {}>'.format(self.id, self.name)

    __str__ = __repr__


class Vertex(Base):
    __tablename__ = 'vertex';
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(48), nullable=False)
    input = Column(Text, nullable=True)
    script = Column(Text, nullable=True)
    g_id = Column(Integer, ForeignKey('graph.id'))

    def __repr__(self):
        return '<Vertex {} {}>'.format(self.id, self.name)

    __str__ = __repr__


class Edge(Base):
    __tablename__ = 'edge';
    id = Column(Integer, primary_key=True, autoincrement=True)
    tail = Column(Integer, ForeignKey('vertex.id'), nullable=False)
    head = Column(Integer, ForeignKey('vertex.id'), nullable=False)
    g_id = Column(Integer, ForeignKey('graph.id'), nullable=False)

    def __repr__(self):
        return '<Edge {} {}>'.format(self.id, self.g_id)

    __str__ = __repr__


class Pipeline(Base):
    __tablename__ = 'pipeline';
    id = Column(Integer, primary_key=True, autoincrement=True)
    g_id = Column(Integer, ForeignKey('graph.id'), nullable=False)
    name = Column(String(48), nullable=False)
    desc = Column(String(200), nullable=True)
    state = Column(Integer, nullable=False,default=STATE_WAITING)

    tracks = relationship('Track',foreign_keys='Track.p_id')




    def __repr__(self):
        return '<Graph {} {}>'.format(self.id, self.g_id)

    __str__ = __repr__


class Track(Base):
    __tablename__ = 'track';

    id = Column(Integer, primary_key=True, autoincrement=True)
    p_id = Column(Integer, ForeignKey('pipeline.id'), nullable=False)
    v_id = Column(Integer, ForeignKey('vertex.id'), nullable=False)
    input = Column(Text, nullable=True)
    script = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    state = Column(Integer, nullable=False,default=STATE_WAITING)

    vertex = relationship('Vertex') # t.vertex.name
    pipeline = relationship('Pipeline') # t.pipeline.name

    def __repr__(self):
        return '<Graph {} {}>'.format(self.id, self.p_id, self.v_id)

    __str__ = __repr__


# 装饰器
from functools import wraps


def singleton(cls):
    instance = None

    @wraps(cls)
    def wrapper(*args, **kwargs):
        # 第一，两者的功能不同。global关键字修饰变量后标识该变量是全局变量，对该变量进行修改就是修改全局变量，而nonlocal关键字修饰变量后标识该变量是上一级函数中的局部变量，
        # 如果上一级函数中不存在该局部变量，nonlocal位置会发生错误（最上层的函数使用nonlocal修饰变量必定会报错）。
        # 第二，两者使用的范围不同。global关键字可以用在任何地方，包括最上层函数中和嵌套函数中，即使之前未定义该变量，global修饰后也可以直接使用，
        # 而nonlocal关键字只能用于嵌套函数中，并且外层函数中定义了相应的局部变量，否则会发生错误（见第一）
        nonlocal instance
        if not instance:
            instance = cls(*args, **kwargs)
        return instance

    return wrapper


@singleton
class Database:

    def __init__(self, *args, **kwargs):
        self._engine = create_engine(args[0], **kwargs)
        self._session = sessionmaker(bind=self._engine)()

    @property
    def session(self):
        return self._session

    @property
    def engine(self):
        return self._engine


    def create_all(self):
        Base.metadata.create_all(self._engine)

    def drop_all(self):
        Base.metadata.drop_all(self._engine)

    def __repr__(self):
        return "<{} {} {} {} >".format(self.__class__.__name__, id(self), id(self._engine), id(self._session))


db = Database(URL, echo=DATABASE_DEBUG)
# g_id = 1
#
# db.session.query(Vertex).filter(Vertex.g_id==g_id).filer(Vertex.id.notin_(
#     db.session.query(Edge.head).filter(Edge.g_id == g_id)
# )).all()