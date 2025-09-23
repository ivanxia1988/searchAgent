# llm_cts_litellm.py
import os, uuid, json, requests
from typing import Dict, Any
from dotenv import load_dotenv
from litellm import completion  # pip install litellm

load_dotenv()

# —— 环境密钥：从 .env 读取 ——
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # LiteLLM 会自动读取
# 可选：如果你走自建 LiteLLM 代理，配置 LITELLM_API_BASE，例如 http://localhost:4000
# os.environ["LITELLM_API_BASE"] = os.getenv("LITELLM_API_BASE", "")

TENANT_KEY = os.getenv("TENANT_KEY")
TENANT_SECRET = os.getenv("TENANT_SECRET")

BASE = {"test": "https://link-test.hewa.cn", "prod": "https://link.hewa.cn"}
PATH = "/thirdCooperate/search/candidate/cts"

# —— 定义“函数调用”schema：让模型输出 payload ——
TOOLS = [{
    "type": "function",
    "function": {
        "name": "emit_payload",
        "description": "把自然语言的<keywords>规则转换为 CTS 搜索接口 payload。只填确定字段；不限/模糊不填。",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "能力关键词，例如：Python、Java、前端"},
                "company": {"type": "string", "description": "目标公司"},
                "position": {"type": "string", "description": "目标岗位"},
                "degree": {"type": "integer", "enum": [1,2,3]},
                "schoolType": {"type": "integer", "enum": [1,2,3,4,5,6]},
                "workExperienceRange": {"type": "integer", "enum": [1,3,4,5,6]},
                "gender": {"type": "integer", "enum": [1,2]},
                "age": {"type": "integer", "enum": [1,2,3,4,5]},
                "page": {"type": "integer", "default": 1},
                "pageSize": {"type": "integer", "default": 10}
            },
            "required": ["page","pageSize"],
            "additionalProperties": False
        }
    }
}]

SYS_PROMPT = """你是招聘搜索映射器。将<keywords>块里的中文规则转成后端接口允许的 payload 字段。
硬性规则：
- 只有“明确且与枚举匹配”的字段才填写；“不限/无/模糊”不填。
- 城市（现居/期望等）不能用 location 字段，请并入 keyword。
- degree：1=大专及以上,2=本科及以上,3=硕士及以上。
- workExperienceRange：1=<1年,3=1-3,4=3-5,5=5-10,6=10+；“5年以上”默认 5。
- gender：男=1, 女=2；不限不填。
- age：1=20-25,2=25-30,3=35-40,4=40-45,5=45+；不在枚举范围不填。
- 能力/技术词 + 城市 → 合并到 keyword；去重；用空格分隔。
- 默认 page=1, pageSize=10。
只调用 emit_payload 一次。"""

def llm_to_payload_with_litellm(keywords_block: str, page=1, page_size=10,
                                model: str = "openai/gpt-4o") -> Dict[str, Any]:
    """
    用 LiteLLM 的 function calling，把 <keywords> → payload
    model 可换成你代理里映射的任何模型标识
    """
    messages = [
        {"role": "system", "content": SYS_PROMPT},
        {"role": "user", "content": f"{keywords_block}\n\n默认 page={page}, pageSize={page_size}。"}
    ]
    resp = completion(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice={"type": "function", "function": {"name": "emit_payload"}},
        temperature=0
    )
    msg = resp.choices[0].message
    # LiteLLM 对齐 OpenAI 响应结构
    tool_call = msg.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    args.setdefault("page", page)
    args.setdefault("pageSize", page_size)
    # 清理空值
    clean = {k: v for k, v in args.items() if v not in (None, "", [])}
    return clean

def search_candidates(env: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """调用 CTS 搜索接口"""
    url = BASE[env] + PATH
    headers = {
        "tenant_key": TENANT_KEY,
        "tenant_secret": TENANT_SECRET,
        "trace_id": uuid.uuid4().hex,
        "Content-Type": "application/json"
    }
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=12)
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 200:
        raise RuntimeError(f"API错误: {data}")
    return data

if __name__ == "__main__":
    kblock = """<keywords>
1. 学历下限：本科
2. 年龄要求：不限
3. 工作年限：5年以上
4. 性别要求：不限
5. 目标公司：无
6. 目标岗位：技术负责人
7. 能力关键词：Python
8. 目前城市：杭州
9. 期望城市：杭州
</keywords>"""
    payload = llm_to_payload_with_litellm(kblock, page=1, page_size=10)
    print("LLM 映射 payload =>", json.dumps(payload, ensure_ascii=False))
    res = search_candidates(env="test", payload=payload)
    print(json.dumps(res, ensure_ascii=False)[:1200])