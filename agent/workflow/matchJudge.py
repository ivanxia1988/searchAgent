# 负责根据JD要求理解岗位的关键要求，核心是去掉不能通过简历匹配的要求、重复且能覆盖的要求、抽象要求的具像化

from unittest import result
from litellm import completion
from dotenv import load_dotenv
import re
load_dotenv()

prompt="""
你是一位专业的HR，负责根据岗位要求和简历内容，判断简历是否符合岗位要求。如果是符合要求的，请输出“true”，否则输出“false”。

"""

def matchJudge(res,requirement):
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

def matchJudgeBatch(res_list,requirement):
    print("原始列表长度："+str(len(res_list)))
    result_list=[]
    for res in res_list:
        result=matchJudge(res,requirement)
        print(result)
        if(result=="true"):
            result_list.append(res)
    return result_list

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