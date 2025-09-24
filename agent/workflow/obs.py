from agent.workflow.matchJudge import matchJudgeBatch, matchJudgePrecise
from dotenv import load_dotenv
import json

load_dotenv()

def observe(amount, res_list, requirement, llm_response, page=None):
    short_list, summary = matchJudgeBatch(res_list, requirement, llm_response, page)

    obs = f"""
    搜索到的人选总数: {amount}
    首页人选数量：{len(res_list)}
    首页完美人选数量: {len(short_list)}
    对首页匹配结果总结: 
    {summary}

    """

    return obs

def observe_cts(response, requirement=None):
    """
    解析CTS搜索接口的响应结果并提取data部分信息
    
    Args:
        response: CTS搜索接口的响应数据，可能是字典或JSON字符串
        requirement: 可选，职位要求信息
    
    Returns:
        包含解析后信息的观察字符串
    """
    # 确保response是字典格式
    if isinstance(response, str):
        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError:
            return f"响应解析错误：{response}"
    else:
        response_dict = response
    
    # 提取data部分信息
    data = response_dict.get('data', {})
    total = data.get('total', 0)
    candidates = data.get('candidates', [])
    page = data.get('page', 1)
    page_size = data.get('pageSize', 10)
    
    # 构建观察字符串
    obs = f"""
    搜索结果状态: {'成功' if response_dict.get('code') == 200 else '失败'}
    消息: {response_dict.get('message', '')}
    搜索到的人选总数: {total}
    当前页码: {page}
    每页数量: {page_size}
    本页候选人数量: {len(candidates)}
    """
    
    # 如果有职位要求和候选人数据，可以添加更多分析
    if requirement and candidates:
        # 这里可以添加基于requirement对candidates的分析
        match_candidates = [c for c in candidates if matchJudgePrecise(c, requirement)]
        obs += f"符合职位要求的候选人数量: {len(match_candidates)}\n"
    
    return obs,candidates