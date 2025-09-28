# 负责根据JD要求理解岗位的关键要求，核心是去掉不能通过简历匹配的要求、重复且能覆盖的要求、抽象要求的具像化
from litellm import completion
from dotenv import load_dotenv
from tool.resumeExtract import resumeExtract
from agent.prompt.summary import PROMPT_FOR_SUMMARY
from tool.token_counter import add_tokens
import re
import json

load_dotenv()
from agent.prompt.precise import PROMPT_FOR_PRECISE,PROMPT_FOR_ABSTRACT



def matchJudgeV2(res,requirement, page=None):
    #res={id:xxx,ResumeSummary:xxx}
    response = completion(
        model="gpt-4o",  # 填写需要调用的模型名称
        messages=[
            {
                "role": "system",
                "content": (PROMPT_FOR_ABSTRACT)
            },
            {
                "role": "user",
                "content": f"这是招聘要求：{requirement}\n这是简历摘要：{res}"
            }
        ],
        top_p=0.7,
        temperature=0.1
    )
    result=response.choices[0].message.content
    try:
        # 尝试从返回内容中提取 JSON 部分
        pattern = r"```json\n(.*?)\n```"
        json_matches = re.findall(pattern, result, re.DOTALL)
        if not json_matches:
            # 如果没有找到JSON内容，使用原始结果
            return result
        
        json_result = json_matches[0]
        result_dict = json.loads(json_result)
        
        if result_dict.get("result") == "true":
            # 如果值得进一步查看，调用 resumeExtract 获取简历详情
            res_id = res.get('id')
            try:
                resume_detail = resumeExtract(res_id, page)
                # 进行精确对比
                result = matchJudgePrecise(resume_detail, requirement)
                return result
            except Exception as e:
                print(f"精确匹配时出错: {e}")
                # 出错时返回原始匹配结果
                return result

    except (json.JSONDecodeError, IndexError) as e:
        print(f"无法解析 JSON 或处理响应: {e}, 响应内容: {result}")

    return result

def matchJudgeBatch(res_list,requirement,llm_response, page=None):
    result_list = []
    short_list = []

    for res in res_list:
        result = matchJudgeV2(res, requirement, page)
        result_list.append({"简历": res, "匹配结果": result})
        
        try:
            pattern = r"```json\n(.*?)\n```"
            json_matches = re.findall(pattern, result, re.DOTALL)
            if json_matches:
                json_result = json_matches[0]
                result_dict = json.loads(json_result)
                if result_dict.get("result") == "true":
                    short_list.append(res)
        except json.JSONDecodeError:
            print(f"无法解析 JSON: {result}")
    print(result_list)
    response = completion(
        model="gpt-4o",  # 填写需要调用的模型名称
        messages=[
            {
                "role": "system",
                "content": (PROMPT_FOR_SUMMARY)
            },
            {
                "role": "user",
                "content": f"请根据下面的匹配明细，对结果进行总结和评价：{result_list};以下是本次使用的策略：{llm_response}"
            }
        ],
        top_p=0.7,
        temperature=0.1
    )

    summary=response.choices[0].message.content
    return short_list,summary

def matchJudgePrecise(res,requirement,policy):
    response = completion(
        model="gpt-4o",  # 填写需要调用的模型名称
        messages=[
            {
                "role": "system",
                "content": (PROMPT_FOR_PRECISE)
            },
            {
                "role": "user",
                "content": f"这是使用的搜索策略：{policy}\n这是招聘要求：{requirement}\n这是简历内容：{res}"
            }
        ],
        top_p=0.7,
        temperature=0.1
    )
    #print(f"这是招聘要求：{requirement}\n这是简历内容：{res}")
    result=response.choices[0].message.content
    add_tokens(response['usage']['total_tokens'])
    try:
        # 尝试从返回内容中提取 JSON 部分
        pattern = r"```json\n(.*?)\n```"
        json_matches = re.findall(pattern, result, re.DOTALL)
        if json_matches:
            return json.loads(json_matches[0])
        return json.loads(result)
    except json.JSONDecodeError:
        print(f"无法解析 JSON: {result}")
        return result