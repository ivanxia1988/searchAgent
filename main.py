import copy
from playwright.sync_api import sync_playwright
import json
from tool.cookieTransfer import format_cookie
from agent.workflow.JDunderstd import coreRequire
from agent.searchSpaceCTS import searchAgent

# 取得可用的有效登陆状态
with open("cookie.json", 'r') as f:
    cookies = format_cookie(json.load(f))
# 加载岗位要求
with open("./jdExample/jd_real_1.txt", 'r') as f:
    requirement = f.read()
# 岗位要求预处理，只返回消除重复、消除歧义、消除初筛阶段无法判断的要点后的核心岗位需求
#coreRequirement = coreRequire(requirement)

requirement = """
我要找到20个符合条件的人选，岗位要求如下：

AI方向技术负责人
2. 五年以上相关工作经验
3. 主导过至少2个完整AI项目落地
4. 熟练掌握Python、C++、Java等至少一种编程语言
5. 精通Transformer、CNN等架构
6. 有LVM多模态大模型实战经验
7. 熟悉PyTorch/TensorFlow框架及分布式训练
9. 人选要求在杭州

"""

requirement1 = """
我要找到20个符合条件的人选，岗位要求如下：

2. 五年以上相关工作经验
7. 熟悉PyTorch/TensorFlow框架及分布式训练
9. 人选要求在杭州

"""

searchAgent(requirement1)
