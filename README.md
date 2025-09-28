# searchAgent - 智能招聘搜索代理系统

## 项目概述
searchAgent是一个基于大语言模型的智能招聘搜索代理系统，能够自动分析招聘需求、生成搜索策略、检索候选人并评估匹配度，显著提升招聘效率和精准度。

## 系统架构

### 整体架构
searchAgent采用模块化设计，将招聘搜索流程分解为多个独立但协作的组件，主要包括Agent层、Tool层、Prompt层和Memory层。

```
searchAgent/
├── agent/
│   ├── workflow/       # 工作流模块（核心业务逻辑）
│   ├── prompt/         # 提示词模板（定义LLM交互模式）
│   └── memory/         # 记忆缓存数据（存储策略和匹配结果）
├── tool/               # 工具函数（提供通用功能支持）
├── main.py             # 项目入口（启动搜索代理）
└── requirements.txt    # 项目依赖（管理第三方库）
```

### 模块职责与交互关系

**Agent层**：
- `searchSpaceCTS.py`: 搜索代理核心，协调整个搜索流程
- `workflow/obs.py`: 结果观察模块，解析和评估搜索结果
- `workflow/matchJudge.py`: 匹配判断模块，评估候选人和岗位的匹配度

**Tool层**：
- `searchCTS.py`: 搜索工具，与CTS系统API交互
- `matchCache.py`: 缓存管理，存储和读取各种缓存数据
- `token_counter.py`: Token计数，监控LLM使用成本
- `candidateParser.py`: 候选人解析，格式化简历数据
- `contextAssemble.py`: 上下文组装，构建LLM输入

**Prompt层**：
- 提供各种预定义的提示词模板，指导LLM生成符合预期的响应

**Memory层**：
- 存储长期有效策略、人岗匹配结果、合格候选人信息等

### 核心数据流
1. `main.py`定义招聘需求并启动`searchAgent`
2. `searchAgent`调用LLM生成搜索策略，然后使用`searchCTS`执行搜索
3. 搜索结果通过`observe_cts`解析，调用`matchJudge`评估候选人
4. 评估结果被缓存到`matchCache`，同时更新搜索进度
5. 整个过程中`token_counter`统计LLM使用量
6. 最终输出搜索结果和统计信息

### 核心模块关系图
```
┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
│                    │    │                    │    │                    │
│  searchAgent核心   ├───>│  workflow工作流    ├───>│     tool工具库     │
│                    │    │                    │    │                    │
└────────────────────┘    └────────────────────┘    └────────────────────┘
         │                         │                         │
         ▼                         ▼                         ▼
┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐
│                    │    │                    │    │                    │
│   prompt提示词库   │    │   memory缓存层     │    │     外部服务       │
│                    │    │                    │    │   (CTS搜索接口)    │
└────────────────────┘    └────────────────────┘    └────────────────────┘
```

## 主要功能模块

### 1. 搜索代理核心 (searchSpaceCTS.py)
搜索代理的中央协调模块，负责管理整个招聘搜索流程，包括初始化环境、控制搜索步骤、调用各功能模块和汇总最终结果。
搜索代理的核心逻辑模块，负责协调整个搜索流程：
- 初始化工作状态和清除缓存
- 生成并执行搜索策略
- 管理搜索步骤和进度
- 统计和展示最终结果

```python
# 核心流程示例
def searchAgent(requirement):
    # 初始化
    clear_cache()
    reset_tokens()
    
    # 多轮搜索策略执行
    while step <= 2 and progress <= 1:
        # 组装上下文
        context = assemble_context(...)        
        # 调用LLM生成搜索策略
        llm_response = call_llm(context)
        # 执行搜索
        payload, search_result = search_with_payload_and_result(llm_response)
        # 分析结果
        obs = observe_cts(step, search_result, requirement, llm_response)
        # 更新进度和历史
        progress = task_finished/20
        history = assemble_history(...)
    
    # 统计结果
    print(f"最终结果：\n所用步数：{step-1}\n合格人选数量：{task_finished}\ntoken数量：{total_tokens}\n费用：{total_tokens/10000*0.025:.4f}美元")
```
<mcfile name="searchSpaceCTS.py" path="/Users/chengxia/project/searchAgent/agent/searchSpaceCTS.py"></mcfile>

### 2. 结果观察模块 (obs.py)
连接搜索结果和匹配判断的桥梁模块，负责解析CTS搜索结果、从策略中提取关键词、检测重复策略和候选人、并协调匹配评估过程。
- 提取搜索结果中的候选人信息
- 检测重复策略和重复候选人
- 评估候选人与岗位要求的匹配度
- 生成详细的观察报告
- 缓存合格候选人和长期有效策略

```python
def observe_cts(step, response, requirement, policy):
    # 解析搜索响应
    response_dict = json.loads(response) if isinstance(response, str) else response
    
    # 提取关键词并检查重复策略
    keywords_match = re.search(r'<keywords>(.*?)</keywords>', policy, re.DOTALL)
    if keywords_match:
        keywords = keywords_match.group(1)
        if get_search_result(keywords):
            return "关键词在keyword_record中出现过，认为是重复策略，不进行后续分析"
    
    # 提取候选人信息并评估匹配度
    data = response_dict.get('data', {})
    candidates = data.get('candidates', [])
    # 对每个候选人进行匹配评估
    for candidate in candidates_with_id_and_text_only:
        if not get_match_result_jd2cv(cv_id):
            result = matchJudgePrecise(text, requirement, policy)
            # 缓存结果并统计合格人数
            if result.get("result") == "true":
                save_qualified_candidate(text)
    
    # 生成观察报告
    obs = f"搜索到的人选总数: {total}，其中对第一页候选人进行合格检查，数量为: {review_num}"
    # ...添加更多统计信息
```
<mcfile name="obs.py" path="/Users/chengxia/project/searchAgent/agent/workflow/obs.py"></mcfile>

### 3. 匹配判断模块 (matchJudge.py)
基于LLM的智能评估模块，通过精确和抽象两种方式评估候选人和岗位的匹配度，并提供详细的匹配分析。

```python
# 匹配判断核心功能示例
def matchJudgeV2(res, requirement, page=None):
    # 第一步：使用抽象匹配进行初步筛选
    response = completion(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": PROMPT_FOR_ABSTRACT},
            {"role": "user", "content": f"这是招聘要求：{requirement}\n这是简历摘要：{res}"}
        ]
    )
    
    # 解析LLM响应，提取JSON结果
    result = response.choices[0].message.content
    pattern = r"```json\n(.*?)\n```"
    json_matches = re.findall(pattern, result, re.DOTALL)
    if json_matches:
        result_dict = json.loads(json_matches[0])
        
        # 如果初步筛选通过，获取简历详情进行精确匹配
        if result_dict.get("result") == "true":
            res_id = res.get('id')
            resume_detail = resumeExtract(res_id, page)
            result = matchJudgePrecise(resume_detail, requirement)
```
- 支持两级筛选机制：先通过摘要快速筛选，再对匹配度高的简历进行精确评估
- 输出结构化的匹配结果，包含result(是否匹配)、reason(不满足原因)、root_cause(失败根因)和clue(改进线索)
- 基于预定义的提示词模板，确保评估标准的一致性和准确性

<mcfile name="matchJudge.py" path="/Users/chengxia/project/searchAgent/agent/workflow/matchJudge.py"></mcfile>

### 4. 搜索工具模块 (searchCTS.py)
对外交互模块，定义搜索参数结构、处理与CTS系统的API通信、并从LLM响应中提取结构化的搜索参数。
- 定义搜索参数和函数调用schema
- 处理搜索请求和响应
- 从LLM响应中提取搜索payload

<mcfile name="searchCTS.py" path="/Users/chengxia/project/searchAgent/tool/searchCTS.py"></mcfile>

### 5. 缓存管理模块 (matchCache.py)
性能优化模块，通过缓存长期有效策略、人岗匹配结果和合格候选人信息，避免重复劳动，提高系统效率。
- 保存和读取长期有效策略
- 缓存人岗匹配结果
- 存储合格候选人信息
- 记录搜索关键词

```python
# 缓存相关函数示例
def save_long_term_policy(requirement, policy):
    hashkey = hashlib.md5(requirement.encode('utf-8')).hexdigest()
    cache = _load_cache(LONG_TERM_POLICY_FILE)
    cache.append({"hashkey": hashkey, "policy": policy})
    _save_cache(cache, LONG_TERM_POLICY_FILE)

# 其他缓存函数：get_qualified_candidate, save_match_result_jd2cv, get_search_result等
```
<mcfile name="matchCache.py" path="/Users/chengxia/project/searchAgent/tool/matchCache.py"></mcfile>

### 6. Token计数器模块 (token_counter.py)
统计LLM调用的token使用量，用于成本计算：
- 累加每次LLM调用的token数量
- 提供获取总token数和重置功能

```python
total_tokens = 0

def add_tokens(tokens):
    global total_tokens
    total_tokens += tokens
    
def get_total_tokens():
    return total_tokens
    
def reset_tokens():
    global total_tokens
    total_tokens = 0
```
<mcfile name="token_counter.py" path="/Users/chengxia/project/searchAgent/tool/token_counter.py"></mcfile>

## 提示词模板系统
项目采用模块化的提示词模板系统，存储在`agent/prompt/`目录下：
- `system.py`: 系统级提示词，定义招聘搜索策略专家角色
- `precise.py`: 精确匹配评估的提示词模板
- `abstract.py`: 摘要匹配评估的提示词模板
- `evaluate.py`: 结果评估的提示词模板

## 关键工作流程

### 1. 启动流程
1. 加载环境变量和配置
2. 定义招聘需求(requirement)
3. 调用searchAgent函数启动搜索代理

### 2. 搜索策略生成
1. 组装上下文（系统提示词、历史策略、招聘需求等）
2. 调用LLM生成搜索策略
3. 从LLM响应中提取搜索关键词和参数

### 3. 候选人检索与评估
1. 使用生成的搜索策略调用CTS接口
2. 解析搜索结果，提取候选人信息
3. 检查关键词是否重复，避免无效搜索
4. 对每个候选人，检查是否已评估过，避免重复劳动
5. 对未评估的候选人，调用matchJudge进行匹配评估
6. 缓存匹配结果，统计合格候选人数量
7. 生成详细的观察报告，包括搜索数量、重复率、合格率等
8. 如果合格率较高，保存当前策略为长期有效策略

### 4. 多轮优化
系统支持多轮搜索策略优化，默认执行最多2轮搜索：
1. 第一轮搜索生成初始结果和观察报告
2. 基于第一轮结果分析，动态调整搜索策略
3. 第二轮搜索进一步精化结果，提高合格率

### 5. 结果统计与输出
1. 统计合格候选人数量
2. 计算总token使用量和预估费用
3. 输出最终搜索结果报告，包括所用步数、合格人数、token数量和费用

## 使用示例

以下是一个简单的使用示例，展示如何通过main.py启动搜索代理：

```python
# main.py示例代码
from agent.searchSpaceCTS import searchAgent
from tool.contextAssemble import load_cookie

# 定义招聘需求
requirement1 = """
岗位职责：
1. 负责公司软件产品的后端开发工作
2. 参与系统架构设计和技术选型
3. 解决开发过程中的技术难题

任职要求：
1. 本科及以上学历，计算机相关专业
2. 3-5年后端开发经验，熟悉Python或Java
3. 熟悉分布式系统设计和微服务架构
4. 具有良好的沟通能力和团队协作精神
"""

# 加载cookie（如果需要）
load_cookie()

# 启动搜索代理
searchAgent(requirement1)
```

## 项目依赖
- Python 3.8+
- litellm 1.76.0+ (用于LLM调用)
- python-dotenv (环境变量管理)
- requests (API请求)
- 其他依赖见requirements.txt

### requirements.txt示例内容
```
litellm==1.76.0
python-dotenv>=1.0.0
requests>=2.31.0
# 其他可能的依赖
# pandas>=2.0.0  # 如果需要数据处理
# numpy>=1.24.0  # 如果需要数值计算
```

## 配置与部署

### 环境变量配置
在项目根目录创建`.env`文件，配置以下环境变量：
```
OPENAI_API_KEY=your_openai_api_key
TENANT_KEY=your_tenant_key
TENANT_SECRET=your_tenant_secret
# 可选配置 - 如果使用自定义LiteLLM代理
#LITELLM_API_BASE=http://localhost:4000
```

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行项目
```bash
# 确保.env文件已正确配置
python main.py
```

### 缓存文件管理
项目使用多个JSON文件存储缓存数据，位于`agent/memory/`目录：
- `jd2cv_cache.json`: 人岗匹配结果缓存
- `qulified_candidate.json`: 合格候选人缓存
- `keyword_record.json`: 搜索关键词记录
- `long_term_policy.json`: 长期有效策略缓存

*注意：定期清理这些文件可以释放存储空间，但会导致缓存失效。*

## 主要优化点
1. **策略复用机制**：通过缓存长期有效策略，避免重复生成相似搜索策略
2. **重复候选人检测**：通过缓存已评估的候选人信息，避免重复评估
3. **Token使用监控**：实时统计LLM调用的token使用量，进行成本控制
4. **多轮搜索优化**：基于前一轮搜索结果动态调整搜索策略

## 注意事项
1. 系统默认使用gpt-4o模型，可在代码中修改为其他支持的模型
2. 缓存文件存储在`agent/memory/`目录下，定期清理可释放空间
3. 系统包含并发控制机制，避免超出API调用速率限制
4. Token费用计算基于假设的每百万token费用2.5美元，实际费用以API提供商报价为准

## 未来改进方向
1. **多模型支持**：增加更多LLM模型支持和动态模型选择功能
2. **策略优化**：改进搜索策略生成算法，提高搜索精准度和效率
3. **可视化界面**：开发Web界面，方便结果查看、策略调整和数据分析
4. **需求扩展**：支持更多类型的招聘需求和更复杂的搜索条件
5. **异常处理**：完善系统的异常处理和容错机制
6. **性能优化**：进一步优化系统性能，减少响应时间
7. **自动化**：增加自动学习和优化功能，持续提高搜索效果
8. **集成扩展**：支持与更多招聘平台和系统的集成