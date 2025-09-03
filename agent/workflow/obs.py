from agent.workflow.matchJudge import matchJudgeBatch
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

def observe(amount, res_list,requirement):
    short_list,summary=matchJudgeBatch(res_list,requirement)

    obs = f"""
    搜索到的人选总数: 
    {amount}
    首页值得进一步查看的人选数量: {len(short_list)}
    对首页匹配结果总结: 
    {summary}

    """

    return obs
