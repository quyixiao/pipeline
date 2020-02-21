import simplejson as simplejson

from pipeline.config import URL, DATABASE_DEBUG
from pipeline.executor import start, showpipeline, finish_params, finish_script
from pipeline.model import Database, STATE_WAITING,STATE_PENDING

import sys

db = Database(URL, echo=DATABASE_DEBUG)

# db.create_all()

import json
from pipeline.service import Graph, Vertex, db
from pipeline.service import create_graph, add_vertex, add_edge


# 测试数据
def test_create_dag():
    try:
        # 创建DAG
        g = create_graph('test1')  # 成功则返回一个Graph对象
        # 增加顶点
        input = {
            "ip": {
                "type": "str",
                "required": True,
                "default": '127.0.0.1'
            }
        }
        if sys.platform in ['dos', 'win32', 'win16']:
            script = {
                'script': 'echo "test1.A"\nping {ip}',
                'next': 'B'
            }
        else:
            script = {
                'script': 'echo "test1.A"\nping {ip} -w 4',
                'next': 'B'
            }

        # 这里为了让用户方便，next可以接收2种类型，数字表示顶点的id，字符串表示同一个DAG中该名称的节点，不能重复
        a = add_vertex(g, 'A', json.dumps(input), json.dumps(script))  # next顶点验证可以在定义时，也可以在使用时
        b = add_vertex(g, 'B', None, '{"script":"echo B"}')
        c = add_vertex(g, 'C', None, '{"script":"echo C"}')
        d = add_vertex(g, 'D', None, '{"script":"echo D"}')
        # 增加边
        ab = add_edge(g, a, b)
        ac = add_edge(g, a, c)
        cb = add_edge(g, c, b)
        bd = add_edge(g, b, d)

        # 创建环路
        g = create_graph('test2')  # 环路
        # 增加顶点
        a = add_vertex(g, 'A', None, '{"script":"echo A"}')
        b = add_vertex(g, 'B', None, '{"script":"echo B"}')
        c = add_vertex(g, 'C', None, '{"script":"echo C"}')
        d = add_vertex(g, 'D', None, '{"script":"echo D"}')
        # 增加边, abc之间的环
        ba = add_edge(g, b, a)
        ac = add_edge(g, a, c)
        cb = add_edge(g, c, b)
        bd = add_edge(g, b, d)

        # 创建DAG
        g = create_graph('test3')  # 多个终点
        # 增加顶点
        a = add_vertex(g, 'A', None, '{"script":"echo A"}')
        b = add_vertex(g, 'B', None, '{"script":"echo B"}')
        c = add_vertex(g, 'C', None, '{"script":"echo C"}')
        d = add_vertex(g, 'D', None, '{"script":"echo D"}')
        # 增加边
        ba = add_edge(g, b, a)
        ac = add_edge(g, a, c)
        bc = add_edge(g, b, c)
        bd = add_edge(g, b, d)

        # 创建DAG
        g = create_graph('test4')  # 多入口
        # 增加顶点
        a = add_vertex(g, 'A', None, '{"script":"echo A"}')
        b = add_vertex(g, 'B', None, '{"script":"echo B"}')
        c = add_vertex(g, 'C', None, '{"script":"echo C"}')
        d = add_vertex(g, 'D', None, '{"script":"echo D"}')
        # 增加边
        ab = add_edge(g, a, b)
        ac = add_edge(g, a, c)
        cb = add_edge(g, c, b)
        db = add_edge(g, d, b)
    except Exception as e:
        print(e)


from pipeline.service import Graph, db
from pipeline.service import check_graph


def test_check_all_graph():
    query = db.session.query(Graph).filter(Graph.checked == 0).all()
    for g in query:
        if check_graph(g):
            g.checked = 1
            db.session.add(g)
    try:
        db.session.commit()
        print('done')
    except Exception as e:
        print(e)
        db.session.rollback()


# db.drop_all()
# db.create_all()
# test_create_dag()
# test_check_all_graph()
#
# start(1,'测试流程1')


ret = showpipeline(1); # p_id   = 1
print(ret)
p_id,p_name,p_state,t_id,v_id,t_state,inp,script = ret[0]
print(p_id,p_name,p_state,t_id,v_id,t_state,inp,script)

# input 处理 交互
#
if inp:
    try:
        inp = simplejson.loads(inp)
        if not isinstance(inp,dict):
            inp = {}
    except:
        inp = {}
    d = {}

    for k,v in inp.items():
        if v.get('required',False):
            i = input('{}='.format(k))
            d[k] = i

    print(d)



result = finish_params(v_id, d)
print(result)


newline = finish_script(*result)
print('newline is ',newline)