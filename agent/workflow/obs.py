from pydoc import plain
from agent.workflow.matchJudge import matchJudgeBatch, matchJudgePrecise
from dotenv import load_dotenv
from agent.prompt.summary import PROMPT_FOR_SUMMARY
import json
from litellm import completion
from tool.candidateParser import parse_candidates_to_text
from tool.matchCache import save_qualified_candidate,save_match_result_jd2cv,get_match_result_jd2cv,save_search_result
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

def observe_cts(step,response, requirement, policy):
    """
    解析CTS搜索接口的响应结果并提取data部分信息
    
    Args:
        response: CTS搜索接口的响应数据，可能是字典或JSON字符串
        requirement: 可选，职位要求信息
    
    Returns:
        包含解析后信息的观察字符串和候选人列表
    """
    # 确保response是字典格式
    if isinstance(response, str):
        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError:
            return f"响应解析错误：{response}", []
    else:
        response_dict = response
    
    # 提取data部分信息
    data = response_dict.get('data', {})
    total = data.get('total', 0)
    candidates = data.get('candidates', [])
    page = data.get('page', 1)
    page_size = data.get('pageSize', 10)

    list=[]
    # 如果有职位要求和候选人数据，可以添加更多分析
    if requirement and candidates:
        # 使用工具模块中的方法将候选人从JSON格式转为优化后的文本格式
        candidates_with_id_and_text_only = parse_candidates_to_text(candidates)
        rep_candidate_num=0
        for candidate in candidates_with_id_and_text_only:
            cv_id = candidate['id']
            text = candidate['text']
            # 如果cv_id在缓存中，跳过
            if get_match_result_jd2cv(cv_id):
                #记录重复出现的人的数
                rep_candidate_num+=1
                continue
            else:
                # 缓存中没有结果，执行匹配并保存结果
                result = matchJudgePrecise(text, requirement,policy)
                list.append(result)
                #在jd2cv中缓存新结果
                save_match_result_jd2cv(cv_id,result)
                #在qualified candidate中缓存合格人选详情
                result_dict = json.loads(result)
                if result_dict.get("result") == "true":
                    save_qualified_candidate(text)

    # 构建观察字符串
    obs = f"""
    搜索结果状态: {'成功' if response_dict.get('code') == 200 else '失败'}
    消息: {response_dict.get('message', '')}
    搜索到的人选总数: {total}
    当前页码: {page}
    每页数量: {page_size}
    本页候选人数量: {len(candidates)}
    """
    
    # 使用litellm调用OpenAI API对obs进行分析
    temp=obs+"\n"+f"人选情况: {list}"

    try:
        response = completion(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": PROMPT_FOR_SUMMARY},
                {"role": "user", "content": temp}
            ]
        )
        summary = response['choices'][0]['message']['content']
        obs += f"\n对观察结果的分析摘要: {summary}\n"
        #把记录保存到keyword record下
        save_search_result(step, policy, obs)

    except Exception as e:
        obs += f"\n使用OpenAI API生成分析摘要时出错: {str(e)}\n"
    
    return obs