# 负责根据JD要求理解岗位的关键要求，核心是去掉不能通过简历匹配的要求、重复且能覆盖的要求、抽象要求的具像化
from litellm import completion
from dotenv import load_dotenv
from tool.resumeExtract import resumeExtract
import re
import json

load_dotenv()


prompt_for_summary="""
你需要对这一轮的检索结果进行总结和评价，目标是为下一步搜索提供指导。
以下建议的现象的归因：
1. 当没有结果集时，可能存在关键词过多导致出现问题，因为检索框是And模式，所以建议大幅减少关键词进行试探。特别要注意目标岗位的关键词设置复杂，特别容易造成无结果
2. 当结果集超大时，可能存在关键词过少的请
3. 策略结果适中（100以内）、但是首页命中率低，可能是：
3.1 关键词选择不够核心，不足以区分人才的特殊性：例如搜索AI人才但是启用了python关键词
3.2 关键词不足以表达出对人才的要求全面性：例如AI人才需要transform没错，但是要亲自训练过就不满足
3.3 关键词方向没有问题，但是应该要找他的父集or子集：例如B端项目，应该尝试检索自集-CRM系统等
3.4 关键词方向没有问题，自然语言导致无法输出正确回答：例如做过B端项目，应该鼓励名词而非包含动词

另外请不要：
1. 轻易建议跨城市找人的策略
2. 轻易用超多关键词去检索
3. 关键词设置过长导致无法匹配，例如“AI方向负责人”在岗位关键词里应写成AI



请用 Markdown 格式输出，结构如下：

## 本轮检索整体评价
- 对整体结果的简短总结（例如：结果数量适中，但精准命中率偏低）。

## 命中率与质量
- 值得进一步查看的人选比例：高 / 中 / 低
- 是否存在明显的噪音候选人？噪音集中在哪些维度（学历、城市、技能等）

## 新线索发现（仅针对合格人选）
- 高频出现的目标公司：
- 高频出现的职位头衔：
- 高频出现的技能关键词：
- 可以作为下一轮定向搜索的新方向：

## 检索策略反馈
- 关键词是否过宽或过窄：
- 哪些条件起到有效筛选作用：
- 哪些条件可能需要调整或放宽：

## 下一步建议
- 建议保留的条件：
- 建议放宽的条件：
- 建议新增的线索：

"""

prompt_for_precise="""
你是一位资深人力资源专家，负责严格的人岗匹配筛选。

输入：
1. 岗位要求（包含硬性条件和加分条件）
2. 候选人简历内容（完整文本）
3. 搜索策略（包含关键词等）


任务：
- 逐条对比岗位要求和简历内容。
- 只依据简历中明确体现的信息，不做臆测或补充。
- 硬性条件（如学历、年限、技能、城市等）必须完全满足。
- 任何缺失、模糊或无法确认的硬性条件，都判定为“不符合”。
- 输出必须是严格 JSON，格式如下：
   {
       "result": "true",
       "reason": "不满足的原因",
       "root_cause": "失败是否是搜索关键词有关系",
       "clue": "通过阅读简历，发现新的挖掘方向"
   }

注意：
- 禁止输出解释或理由，只能输出 `true` 或 `false`。
- 判断必须完全基于简历中出现的明确信息，不能主观推断。

root_cause：
例如 搜索关键词是python，但是岗位要求是AI方向，python的关键词并不能有效检索到AI方向的人才

clue：
学习可扩展的关键词，提升召回能力：
技能词扩展：从检索到符合条件的简历中的，与当前检索条件对应的子集（要求B端项目，发现简历中很多提到了CRM系统等）
岗位词扩展：从检索到符合条件的简历中的岗位自称，去思考拓展思路（JD 叫“AI方向技术负责人”，简历可能自称“算法总监”或“CTO助理”，总经理助理，可能简历是行长助理）

学习人选聚集特征，提升精准定位能力：
公司特征：从检索到符合条件的简历中，发现杭州的视觉AI人才很多都来自海康威视，那么海康是一个好公司
行业特征：从检索到符合条件的简历中，发现机器人行业会用到视觉方向，那么这类行业会有很多人才聚集


"""

prompt_for_abstract="""
你是一位资深HR助理，需要根据岗位要求和候选人的简历摘要，判断该候选人是否值得进入下一步详细简历查看。

请严格遵循以下原则：

1. 简历摘要信息有限，项目经历和细节可能没有完全体现，所以不能因为“没有提及”就认定候选人不符合。  
2. **主要排除规则**：只在发现明确的不符合条件时输出 false，例如：
   - 年龄明显不符
   - 求职期望与岗位要求冲突（城市或方向完全不一致）
   - 学历明显低于岗位要求
   - 工作年限严重不足
   - 曾担任职位与岗位方向完全无关  
3. 如果候选人的 **职位名称 / 职业方向** 与岗位相关，即使简历摘要里没有提到具体项目经历，也应认为值得进一步查看 → 输出 true。  
4. 输出必须是严格 JSON，格式如下：
   {
       "result": "true",
       "reason": "职位方向相关，值得进一步查看"
   }

"""


def matchJudgeV2(res,requirement, page=None):
    #res={id:xxx,ResumeSummary:xxx}
    response = completion(
        model="gpt-4o",  # 填写需要调用的模型名称
        messages=[
            {
                "role": "system",
                "content": (prompt_for_abstract)
            },
            {
                "role": "user",
                "content": f"这是招聘要求：{requirement}\n这是简历摘要：{res}"
            }
        ],
        top_p=0.7,
        temperature=0.1
    )
    result=response.choices[0].message.content
    try:
        # 尝试从返回内容中提取 JSON 部分
        pattern = r"```json\n(.*?)\n```"
        json_matches = re.findall(pattern, result, re.DOTALL)
        if not json_matches:
            # 如果没有找到JSON内容，使用原始结果
            return result
        
        json_result = json_matches[0]
        result_dict = json.loads(json_result)
        
        if result_dict.get("result") == "true":
            # 如果值得进一步查看，调用 resumeExtract 获取简历详情
            res_id = res.get('id')
            try:
                resume_detail = resumeExtract(res_id, page)
                # 进行精确对比
                result = matchJudgePrecise(resume_detail, requirement)
                return result
            except Exception as e:
                print(f"精确匹配时出错: {e}")
                # 出错时返回原始匹配结果
                return result

    except (json.JSONDecodeError, IndexError) as e:
        print(f"无法解析 JSON 或处理响应: {e}, 响应内容: {result}")

    return result

def matchJudgeBatch(res_list,requirement,llm_response, page=None):
    result_list = []
    short_list = []

    for res in res_list:
        result = matchJudgeV2(res, requirement, page)
        result_list.append({"简历": res, "匹配结果": result})
        
        try:
            pattern = r"```json\n(.*?)\n```"
            json_matches = re.findall(pattern, result, re.DOTALL)
            if json_matches:
                json_result = json_matches[0]
                result_dict = json.loads(json_result)
                if result_dict.get("result") == "true":
                    short_list.append(res)
        except json.JSONDecodeError:
            print(f"无法解析 JSON: {result}")
    print(result_list)
    response = completion(
        model="gpt-4o",  # 填写需要调用的模型名称
        messages=[
            {
                "role": "system",
                "content": (prompt_for_summary)
            },
            {
                "role": "user",
                "content": f"请根据下面的匹配明细，对结果进行总结和评价：{result_list};以下是本次使用的策略：{llm_response}"
            }
        ],
        top_p=0.7,
        temperature=0.1
    )

    summary=response.choices[0].message.content
    return short_list,summary

def matchJudgePrecise(res,requirement,policy):
    response = completion(
        model="gpt-4o",  # 填写需要调用的模型名称
        messages=[
            {
                "role": "system",
                "content": (prompt_for_precise)
            },
            {
                "role": "user",
                "content": f"这是使用的搜索策略：{policy}\n这是招聘要求：{requirement}\n这是简历内容：{res}"
            }
        ],
        top_p=0.7,
        temperature=0.1
    )
    #print(f"这是招聘要求：{requirement}\n这是简历内容：{res}")
    result=response.choices[0].message.content
    return result