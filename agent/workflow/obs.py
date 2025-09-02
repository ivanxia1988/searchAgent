from agent.workflow.matchJudge import matchJudgeBatch

def observe(amount, res_list,requirement):
    #result=matchJudgeBatch(res_list,requirement)
    #obs="搜索到的人选数量："+str(amount)+"符合的人选数量"+str(len(result))+"人选清单"+str(result)
    obs="搜索到的人选数量："+str(amount)
    return obs
