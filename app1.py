from pipeline.executor import showpipeline
from pipeline.executor import finish_params, finish_script
import simplejson
from pipeline.executor import EXECUTOR
# 为了给用户提供友好的界面效果，在网页往往需要
ps = showpipeline(1)  # 返回运行节点列表 print('-' * 30)
print(ps)
print('-' * 30)
for p_id, p_name, p_state, t_id, v_id, t_state, inp, script in ps:
    print(p_id, p_name, p_state, t_id, v_id, t_state, inp, script)
    d = {}  # 如果参数是必须，则交互，让用户提交
    if inp:
        inp = simplejson.loads(inp)
        for k in inp.keys():
            if inp[k].get('required', False):
                d[k] = input('{}= '.format(k))
        print(d)
    result = finish_params(t_id, d)
    print(script, '+++++++++')
    script = finish_script(t_id, *result)
    print(script)  # 拿到替换好的脚本，准备执行
    EXECUTOR.execute(t_id, script)  # 异步执行行
