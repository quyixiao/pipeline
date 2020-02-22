# 开启一个流程，获取参数后需要验证，验证失败抛出异常，验证成功就用来替换执行脚本，生成可运行的脚本
# 然后将参数，脚本存储数据库的track表
# 在track表中添加script 字段，存储执行的脚本
# required 是否必须，True 则用户必须输入值，default 缺失值忽略
# default 缺省值，如果非必须值，用户没有填写了，使用缺省值
# 占位符，用户提供了参数后，使用名称ip进行替换
# 特别注意，如果使用ping命令测试，window默认的ping4 下，Linux会一直ping下去，所以如果使用Linux 测试项目脚本
# 流转
# 手动流转以后实现，实现自动流转
# 如何知道该某个节点该轮到它执行了
# 间隔着反复的track表查询什么节点可以执行了吗？
# 为了减少对数据库的查询，最好的方式应该是由前一个节点成功完成后触发下一个查询
# 查询完成的节点的一个节点是否存在，是否具备执行条件等
# 查询 完成的节点的一个节点是否存在，是否具备执行条件等
# 首先，需要在pipeline中查看当前任务状态是否已经失败，如果存在，则不再继续查找下一个节点，否则成功执行，继续下面的操作
# 本节点成功执行置为成功
# 首先，需要在pipeline中查看当前任务状态是否已经失败，如果失败，则不再执行一个个节点，否则成功执行下一个节点，
# 本节点成功执行置为成功，在track表中查询 一一个本任务流队自己之外的还有没有其它的节点在运行中，遍历所有其他的节点
# 首先判断如果有一个失败，就立即置pipeline的state 为STATE_FAILED
# 如果其它的节点都是成功，则置为成功，pipeline的state为STATE_FINISHED
# 如果碰到一个STATE_WAITING,STATE_RUNNING，则将搜索下一个结点
# 下一个结点
# 没有下一级结点，说明该节点是终点，是终点，不代表没有其它的终点，本节点没有一级它就不用管其它的结点了，只需要把自己的状态置为成功就行了
# 如果节点没有执行失败，一定会成功执行，其它的节点继续执行，如果最后一个终点执行完成，会发现其他的节点是成功状态，所以它将pipeline
# 的state置为

from subprocess import Popen, PIPE
from tempfile import TemporaryFile

tf = TemporaryFile('w+')
#p = Popen('echo "magedu" \n ping www.baidu.com -c 4 ', shell=True, stdout=tf)
p = Popen('/Users/quyixiao/ttg/xxx', shell=True, stdout=tf)
code = p.wait(5)
print(code)

tf.seek(0)
text = tf.read()
print(11111111, text)
