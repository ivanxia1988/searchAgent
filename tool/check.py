#检查大模型的回答是否遵循了推理过程
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

prompt="""
请检查大模型返回中的think与keyword是否相符
"""

def check(response):
    response = completion(
        model="gpt-4o",  # 填写需要调用的模型名称
        messages=[
            {
                "role": "system",
                "content": (prompt)
            },
            {
                "role": "user",
                "content": f"大模型的反馈结果：{response}"
            }
        ],
        top_p=0.7,
        temperature=0.1
    )
    result=response.choices[0].message.content
    return result
