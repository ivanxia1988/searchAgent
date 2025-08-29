# 负责根据JD要求理解岗位的关键要求，核心是去掉不能通过简历匹配的要求、重复且能覆盖的要求、抽象要求的具像化

from unittest import result
from litellm import completion
from dotenv import load_dotenv
import re
load_dotenv()

prompt="""
你是一位专业的 JD 理解器，擅长从复杂的岗位描述中提炼出真正可以通过简历进行匹配的“核心要求”。

请遵循以下标准：
1. 去除无法通过简历判断的软性要求（如责任心、沟通能力等）；
2. 合并或去除重复、能被包含的要求；
3. 将模糊要求具象化（如“熟悉业务” → 有 xxx 项目经验）；

请以如下格式输出（不要添加任何额外说明）：

Core：
1. ...
2. ...
3. ...

 Cropped：
- 要求内容A ：原因：无法通过简历判断
- 要求内容B ：原因：重复或被包含
- 要求内容C ：原因：抽象，需具象化后处理
"""

def coreRequire(requirement):
    response = completion(
        model="gpt-4o",  # 填写需要调用的模型名称
        messages=[
            {
                "role": "system",
                "content": (prompt)
            },
            {
                "role": "user",
                "content": f"这是原始的招聘要求：{requirement}"
            }
        ],
        top_p=0.7,
        temperature=0.1
    )
    result=response.choices[0].message.content
    print(f"\n=== 岗位要求理解结果 ===")
    print(result)
    core_match = re.search(r'Core：\s*((?:\d+\.\s?.+\n?)+)', result)
    core_items = re.findall(r'\d+\.\s*(.+)', core_match.group(1)) if core_match else []

    return core_items

#coreRequire("我要招聘一名本科毕业的希望在上海工作，责任心很强的35岁的java开发工程师")