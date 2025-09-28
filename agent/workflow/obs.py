from agent.workflow.matchJudge import matchJudgePrecise
from dotenv import load_dotenv
from agent.prompt.summary import PROMPT_FOR_SUMMARY
import json
from litellm import completion
from tool.candidateParser import parse_candidates_to_text
from tool.matchCache import save_qualified_candidate,save_match_result_jd2cv,get_match_result_jd2cv,save_search_result,get_search_result
from tool.token_counter import add_tokens
import re
import time
load_dotenv()

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
    
    keywords_match = re.search(r'<keywords>(.*?)</keywords>', policy, re.DOTALL)

    if keywords_match:
        keywords = keywords_match.group(1)

    #如果keyword在kyeword_record里面出现过，那么认为是生成了重复策略，则不进行后续的分析
    if get_search_result(keywords):
        obs=f"关键词在keyword_record中出现过，认为是重复策略，不进行后续分析"
        save_search_result(step,keywords,obs)
        return obs
    else:
        # 提取data部分信息
        data = response_dict.get('data', {})
        total = data.get('total', 0)
        candidates = data.get('candidates', [])
        page = data.get('page', 1)
        page_size = data.get('pageSize', 10)
        
        list=[]
        # 如果有职位要求和候选人数据，可以添加更多分析
        if candidates:
            # 使用工具模块中的方法将候选人从JSON格式转为优化后的文本格式
            candidates_with_id_and_text_only = parse_candidates_to_text(candidates)
            rep_candidate_num=0
            qualified_candidate_num=0
            for candidate in candidates_with_id_and_text_only:
                cv_id = candidate['cv_id']
                text = candidate['candidate_text']
                # 如果cv_id在缓存中，跳过
                if get_match_result_jd2cv(cv_id):
                    #记录重复出现的人的数
                    rep_candidate_num+=1
                    continue
                else:
                    # 缓存中没有结果，执行匹配并保存结果
                    result = matchJudgePrecise(text, requirement,policy)
                    # 并发控制以防超出openai的api调用的rate limit
                    time.sleep(0.5)
                    print(f"result: {result}")
                    list.append(result)
                    #在jd2cv中缓存新结果
                    save_match_result_jd2cv(cv_id,result)
                    #在qualified candidate中缓存合格人选详情
                    if result.get("result") == "true":
                        save_qualified_candidate(text)
                        qualified_candidate_num

        #重复率
        review_num=len(candidates)
        rep_rate = rep_candidate_num / review_num if review_num != 0 else 0
        # 构建观察字符串，如果没有候选人，不展示重复与合格相关信息

        obs = f"""
        搜索到的人选总数: {total}，其中对第一页候选人进行合格检查，数量为: {review_num}
        """
        if candidates:
            obs += f"""
        重复出现的人选数量: {rep_candidate_num}
        重复出现的人选占比: {rep_rate}
        合格人选数量：{qualified_candidate_num}
        合格人选命中率（1即为100%）：{qualified_candidate_num/review_num if review_num != 0 else 0}
        """
        
        print(obs)

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
            add_tokens(response['usage']['total_tokens'])
            obs += f"\n对观察结果的分析摘要: {summary}\n"
            #把记录保存到keyword record下
            # 提取policy中的<keyword>标签内的内容
            save_search_result(step, keywords,obs)

        except Exception as e:
            obs += f"\n使用OpenAI API生成分析摘要时出错: {str(e)}\n"
        
        return obs