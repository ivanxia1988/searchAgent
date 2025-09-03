# 负责根据JD要求理解岗位的关键要求，核心是去掉不能通过简历匹配的要求、重复且能覆盖的要求、抽象要求的具像化
from litellm import completion
from dotenv import load_dotenv
import re
import json

load_dotenv()


prompt_for_summary="""
你需要对这一轮的匹配结果进行总结和评价，维度包括但不限于：
1. 值得进一步查看的人选数量比例高不高
2. 从中是否发现了一些新的线索，比如发现有高频出现的，定向去搜寻的目标公司

"""

prompt_for_precise="""
你是一位专业的HR，负责根据岗位要求和简历内容，判断简历是否符合岗位要求。如果是符合要求的，请输出“true”，否则输出“false”。

"""

prompt_for_abstract="""
你是一位资深HR助理，需要根据岗位要求和候选人的简历摘要，判断该候选人是否值得进入下一步详细简历查看。

请严格遵循以下原则：

1. 简历摘要信息有限，项目经历和细节可能没有完全体现，所以不能因为“没有提及”就认定候选人不符合。  
2. **主要排除规则**：只在发现明确的不符合条件时输出 false，例如：
   - 年龄明显不符（如要求 ≤35 岁，候选人 44 岁）
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

def matchJudge(res,requirement):
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
    #print(f"这是招聘要求：{requirement}\n这是简历内容：{res}")
    result=response.choices[0].message.content
    return result

def matchJudgeBatch(res_list,requirement):
    print("原始列表长度："+str(len(res_list)))
    result_list=[]
    short_list=[]

    for res in res_list:
        result=matchJudge(res,requirement)
        result_list.append(result)
        pattern = r"```json\n(.*?)\n```"
        json_result = re.findall(pattern, result, re.DOTALL)[0]
        try:
            result_dict = json.loads(json_result)
            if result_dict.get("result") == "true":
                short_list.append(res)
        except json.JSONDecodeError:
            print(f"无法解析 JSON: {result}")
    
    response = completion(
        model="gpt-4o",  # 填写需要调用的模型名称
        messages=[
            {
                "role": "system",
                "content": (prompt_for_summary)
            },
            {
                "role": "user",
                "content": f"请根据下面的匹配明细，对结果进行总结和评价：{result_list}"
            }
        ],
        top_p=0.7,
        temperature=0.1
    )

    summary=response.choices[0].message.content
    return short_list,summary

def matchJudgePrecise(res,requirement):
    response = completion(
        model="gpt-4o",  # 填写需要调用的模型名称
        messages=[
            {
                "role": "system",
                "content": (prompt)
            },
            {
                "role": "user",
                "content": f"这是招聘要求：{requirement}\n这是简历内容：{res}"
            }
        ],
        top_p=0.7,
        temperature=0.1
    )
    print(f"这是招聘要求：{requirement}\n这是简历内容：{res}")
    result=response.choices[0].message.content
    return result

def matchJudgeBatchPrecise(res_list,requirement):
    print("原始列表长度："+str(len(res_list)))
    result_list=[]
    for res in res_list:
        result=matchJudge(res,requirement)
        print(result)
        if(result=="true"):
            result_list.append(res)
    return result_list