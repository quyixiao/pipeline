# 开启一个流程，获取参数后需要验证，验证失败抛出异常，验证成功就用来替换执行脚本，生成可运行的脚本
# 然后将参数，脚本存储数据库的track表
# 在track表中添加script 字段，存储执行的脚本
# required 是否必须，True 则用户必须输入值，default 缺失值忽略
# default 缺省值，如果非必须值，用户没有填写了，使用缺省值
# 占位符，用户提供了参数后，使用名称ip进行替换
# 特别注意，如果使用ping命令测试，window默认的ping4 下，Linux会一直ping下去，所以如果使用Linux 测试项目脚本
#

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
