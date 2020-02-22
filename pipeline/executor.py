import re
from collections import defaultdict
from tempfile import TemporaryFile

import simplejson

from pipeline.model import db, Vertex, Edge, Graph, Pipeline, STATE_WAITING, Track, STATE_RUNNING, STATE_PENDING, \
    STATE_FAILED, STATE_FINISH, STATE_SUCCEED
from pipeline.service import transactional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import threading, time
from subprocess import Popen
import uuid
from queue import Queue

TYPES = {
    'str': str,
    'int': int,
    'string': str,
}


def start(g_id, name: str, desc='desc'):
    #
    g = db.session.query(Graph).filter((Graph.id == g_id) & (Graph.checked == 1)).first()
    if not g:
        return

    # 找到所有的顶点，
    query = db.session.query(Vertex).filter(Vertex.g_id == g_id)
    vertexes = query.all()
    if not vertexes:
        return
    # 起点， 状态PENDING
    starts = query.filter(Vertex.id.notin_(
        db.session.query(Edge.head).filter(Edge.g_id == g_id)
    )).all()

    zds = [v.id for v in starts]
    print(zds, '~~~~~~~~~~~~')

    # 新建一个任务流
    p = Pipeline()
    p.g_id = g_id
    p.name = name
    p.desc = desc
    p.state = STATE_RUNNING
    db.session.add(p)

    for v in vertexes:
        t = Track()
        t.v_id = v.id
        t.pipeline = p
        t.state = STATE_PENDING if v.id in zds else STATE_WAITING
        db.session.add(t)

    # 封闭graph ,sealed
    if g.sealed == 0:
        g.sealed = 1
        db.session.add(g)

    try:
        db.session.commit()
        print('start ok~~~~~~~~')
    except Exception as e:
        print(e)
        db.session.rollback()


def showpipeline(p_id, states=[STATE_PENDING], exclude=[STATE_FAILED]):
    # 显示所有流程的相关信息,顶点的信息，顶点里面的input,script
    # tracks
    # ret = []
    # query = db.session.query(Track).filter(Track.p_id == p_id).filter(Track.state == state)
    # for track in query:
    #     ret.append((track.pipeline.id,track.pipeline.name,track.pipeline.state,
    #                 track.id,track.v_id,track.state,
    #                 track.vertex.input,track.vertex.script))
    query = db.session.query(Pipeline.id, Pipeline.name, Pipeline.state,
                             Track.id, Track.v_id, Track.state,
                             Vertex.input, Vertex.script) \
        .join(Track, Pipeline.id == Track.p_id). \
        join(Vertex, Vertex.id == Track.v_id) \
        .filter(Pipeline.state.notin_(exclude)) \
        .filter(Track.p_id == p_id) \
        .filter(Track.state.in_(states))
    return query.all()


def finish_params(v_id, d: dict):
    ret = {}
    value = db.session.query(Vertex.input, Vertex.script).filter(Vertex.id == v_id).first()
    print(value)
    inp, script = value
    if inp:
        inp = simplejson.loads(inp)
        for k, v in inp.items():
            if k in d.keys():
                ret[k] = TYPES[inp[k].get('type', 'str')](d[k])
            elif inp[k].get('default') is not None:
                ret[k] = TYPES[inp[k].get('type', 'str')](inp[k].get('default'))
            else:
                raise TypeError()

    return ret, script


@transactional
def finish_script(t_id, params, script):
    newline = ''
    print(params, type(params))
    print(script, type(script))
    if script:
        script = simplejson.loads(script).get('script',
                                              '')  # {"script": "echo \"test1.A\"\nping {ip} -w 4", "next": "B"}
        print(script)
        regex = re.compile(r'{([^{}]+)}')
        start = 0
        for matcher in regex.finditer(script):
            newline += script[start:matcher.
                start()]
            print(matcher, matcher.group(1))
            key = matcher.group(1)
            tmp = params.get(key, '')
            newline += str(tmp)
            start = matcher.end()
        else:
            newline += script[start:]

        # 入库track input script
        t = db.session.query(Track).filter(Track.id == t_id).first()
        if t:
            t.input = simplejson.dumps(params)
            t.script = newline
            db.session.add(t)

    return newline


class Executor:
    def __init__(self, workers=5):
        self.__tasks = {}
        self.__executor = ThreadPoolExecutor(max_workers=workers)
        self.__event = threading.Event()
        self.__queue = Queue()
        threading.Thread(target=self._run).start()
        threading.Thread(target=self._save_track).start()

    def _execute(self, script, key):
        codes = 0
        with TemporaryFile('a+') as f:
            for line in script.splitlines():
                p = Popen(line, shell=True, stdout=f)
                code = p.wait()
                codes += code
                f.flush()
                f.seek(0)
                text = f.read()
        return key, codes, text

    def execute(self, t_id, script):
        try:
            t = db.session.query(Track).filter(Track.id == t_id).one()
            key = uuid.uuid4().hex
            self.__tasks[self.__executor.submit(self._execute, script, key)] = key, t_id
            t.state = STATE_RUNNING
            db.session.add(t)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)

    def _run(self):
        while not self.__event.wait(1):
            for future in as_completed(self.__tasks):  # 有可能阻塞
                key, t_id = self.__tasks[future]
                try:
                    key, code, text = future.result()
                    print(key, code, text)
                    # 拿到结果干什么？ 异步处理方案
                    self.__queue.put((t_id, code, text))  # 推送到第三方queue

                except Exception as e:
                    print(e)
                    print(key, t_id, 'failed')
                finally:
                    del self.__tasks[future]

    def _save_track(self):
        # 存储结果
        # 从Q里面拿数据存储
        while True:
            t_id, code, text = self.__queue.get()  # 阻塞拿
            print(t_id, code, text)

            track = db.session.query(Track).filter(Track.id == t_id).one()
            track.state = STATE_SUCCEED if code == 0 else STATE_FAILED
            track.output = text

            if code != 0:
                track.pipeline.state = STATE_FAILED
            else:
                # 流转代码， 隐含 自己成功，看别的顶点
                # pipeline是否失败 ， track表中查找是否有失败的
                tracks = db.session.query(Track).filter((Track.p_id == track.p_id) & (Track.id != t_id)).all()

                states = {STATE_WAITING: 0, STATE_PENDING: 0, STATE_RUNNING: 0, STATE_FAILED: 0, STATE_SUCCEED: 0}

                for t in tracks:
                    states[t.state] += 1

                if states[STATE_FAILED] > 0:
                    track.pipeline.state = STATE_FAILED
                elif len(tracks) == states[STATE_SUCCEED]:  # 说明除去自己之外全是成功的，你当然就是最后的那一个顶点，也就是终点
                    track.pipeline.state = STATE_FINISH
                else:  # 还有节点没有做完，判断自己有没有下一级
                    # heads = db.session.query(Edge.head).filter(Edge.tail == track.v_id).all()
                    # if len(heads) == 0:
                    #     pass # 什么都不做，因为你没下一级，就是其中一个先做完的终点
                    # else:
                    query = db.session.query(Edge).filter(Edge.g_id == track.pipeline.g_id)

                    t2h = defaultdict(list)
                    h2t = defaultdict(list)

                    for e in query:
                        t2h[e.tail].append(e.head)
                        h2t[e.head].append(e.tail)

                    if track.v_id in t2h.keys():
                        nexts = t2h[track.v_id]
                        for n in nexts:
                            tails = h2t[n]  # n pending 条件是tails所有状态都必须是成功
                            # 统计tails是否都是成功的，可以pending,
                            # select count(state) from track where track.v_id in (1,2,4)
                            # and track.state = STATE_SUCCEED  and pid
                            s_count = db.session.query(Track).filter(Track.p_id == track.p_id) \
                                .filter(Track.v_id.in_(tails)) \
                                .filter(Track.state == STATE_SUCCEED).count()
                            if s_count == len(tails):
                                # pending
                                nx = db.session.query(Track).filter(Track.v_id == n).one()
                                nx.state = STATE_PENDING
                                db.session.add(nx)
                            else:
                                pass  # 什么都不做

                    else:
                        pass  # 什么都不做，因为你没下一级，就是其中一个先做完的终点

            db.session.add(track)
            try:
                db.session.commit()
                pass  # TODO
            except Exception as e:
                db.session.rollback()
                print(e)


EXECUTOR = Executor()
