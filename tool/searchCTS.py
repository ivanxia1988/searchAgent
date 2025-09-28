# llm_cts_litellm.py
import os, uuid, json, requests
from typing import Dict, Any, Tuple
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
        "description": "把自然语言的规则转换为 CTS 搜索接口 payload。只填确定字段；不限/模糊不填。",
        "parameters": {
            "type": "object",
            "properties": {
                "jd": {"type": "string", "description": "职位描述通过语义去召回结果"},
                "keyword": {"type": "string", "description": "通用要求关键词"},
                "school": {"type": "string", "description": "学校名称关键词"},
                "company": {"type": "string", "description": "公司名称关键词"},
                "position": {"type": "string", "description": "职位名称关键词"},
                "workContent": {"type": "string", "description": "工作内容关键词"},
                "location": {"type": "array", "items": {"type": "string"}, "description": "期望城市城市名称list，示例：['北京','上海市','深圳']"},
                "degree": {"type": "integer", "enum": [1,2,3], "description": "学历要求枚举值：1. 大专及以上 2. 本科及以上 3. 硕士及以上"},
                "schoolType": {"type": "integer", "enum": [1,2,3,4,5,6], "description": "学校类型枚举值：1. 双一流 2. 211 3. 985 4. 强基计划 5. 双高计划 6. THE100"},
                "workExperienceRange": {"type": "integer", "enum": [1,3,4,5,6], "description": "工作年限枚举值：1. 1年以内 3. 1-3年 4. 3-5年 5. 5-10年 6. 10年以上"},
                "gender": {"type": "integer", "enum": [1,2], "description": "性别枚举值：1. 男 2. 女"},
                "age": {"type": "integer", "enum": [1,2,3,4,5], "description": "年龄范围枚举值：1. 20-25岁 2. 25-30岁 3. 35-40岁 4. 40-45岁 5. 45岁以上"},
                "active": {"type": "integer", "enum": [1,2,3,4], "description": "活跃度枚举值：1. 今日活跃 2. 近3天活跃 3. 近15天活跃 4. 近30天活跃"},
                "page": {"type": "integer", "default": 1, "description": "页数，默认为1"},
                "pageSize": {"type": "integer", "default": 10, "description": "每页数量，默认为10"}
            },
            "required": ["page","pageSize"],
            "additionalProperties": False
        }
    }
}]

SYS_PROMPT = """你是招聘搜索映射器。将输入的中文规则转成后端接口允许的 payload 字段。
硬性规则：
- 只有“明确且与枚举匹配”的字段才填写；“不限/无/模糊”不填。
- jd: 职位描述通过语义去召回结果
- keyword: 通用要求关键词
- school: 学校名称关键词
- company: 公司名称关键词
- position: 职位名称关键词
- workContent: 工作内容关键词
- location: 期望城市城市名称list，示例：["北京","上海市","深圳"]
- degree：1=大专及以上,2=本科及以上,3=硕士及以上
- schoolType：1=双一流,2=211,3=985,4=强基计划,5=双高计划,6=THE100
- workExperienceRange：1=1年以内,3=1-3年,4=3-5年,5=5-10年,6=10年以上；"5年以上"默认 5
- gender：男=1, 女=2；不限不填
- age：1=20-25岁,2=25-30岁,3=35-40岁,4=40-45岁,5=45岁以上；不在枚举范围不填
- active：1=今日活跃,2=近3天活跃,3=近15天活跃,4=近30天活跃
- 默认 page=1, pageSize=10
只调用 emit_payload 一次。"""

def llm_to_payload_with_litellm(keywords_block: str, page=1, page_size=10,
                                model: str = "openai/gpt-4o") -> Dict[str, Any]:
    """
    用 LiteLLM 的 function calling，把规则文本 → payload
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

def search_candidates(payload: Dict[str, Any], env: str = "prod") -> Dict[str, Any]:
    """调用 CTS 搜索接口，默认使用 prod 环境"""
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

def search_with_payload_and_result(keywords_block: str, page=1, page_size=10,
                                   model: str = "openai/gpt-4o", env: str = "prod") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    封装完整的搜索流程，同时返回 payload 和搜索结果
    
    Args:
        keywords_block: 包含搜索规则的文本
        page: 页码，默认为1
        page_size: 每页数量，默认为10
        model: 使用的 LLM 模型，默认为 "openai/gpt-4o"
        env: 环境，默认为 "prod"
    
    Returns:
        一个元组，包含 (payload, 搜索结果)
    """
    # 生成 payload
    payload = llm_to_payload_with_litellm(keywords_block, page, page_size, model)
    # 调用搜索接口并获取结果
    result = search_candidates(payload, env)
    # 返回 payload 和结果
    return payload, result

if __name__ == "__main__":
    kblock = """<keywords>
3. 年龄要求：不限
5. 性别要求：不限
6. 期望城市：杭州
工作经验：5年以上
7. 能力关键词：python
8. 公司关键词：无
</keywords>"""
    payload = llm_to_payload_with_litellm(kblock, page=1, page_size=10)
    print("LLM 映射 payload =>", json.dumps(payload, ensure_ascii=False))
    res = search_candidates(payload)  # 默认使用 prod 环境
    print(json.dumps(res, ensure_ascii=False)[:1200])
    
    # 使用新的封装函数示例
    print("\n使用封装函数:")
    payload, result = search_with_payload_and_result(kblock)
    print("封装函数返回的 payload =>", json.dumps(payload, ensure_ascii=False))
    print("封装函数返回的结果 =>", json.dumps(result, ensure_ascii=False)[:1200])

