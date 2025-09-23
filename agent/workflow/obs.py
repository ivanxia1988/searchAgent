from agent.workflow.matchJudge import matchJudgeBatch
from dotenv import load_dotenv

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
