#负责根据招聘要求生成搜索策略，例如搜索关键词等，这里就需要考虑到上下文工程了
from multiprocessing import process
from litellm import completion
from dotenv import load_dotenv
from agent.workflow.obs import observe_cts
from tool.logger import save_history_json
from tool.contextAssemble import assemble_context,assemble_history
from agent.prompt.system import SYSTEM_PROMPT
from tool.searchCTS import search_with_payload_and_result
import json

load_dotenv()

def call_llm(prompt: str) -> str:
    response = completion(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

system_prompt=SYSTEM_PROMPT

def searchAgent(requirement):# 初始化工作状态
        history=""
        all_candidates = []  # 用于存储所有候选人的列表
        for step in range(10):
            # 组装当前轮次的上下文
            progress=len(all_candidates)
            context = assemble_context(system_prompt, requirement, progress, history)
            print(f"\n=== Step {step + 1} ===")
            llm_response = call_llm(context)
            print(llm_response)

            # 调用CTS查询工具得到结果
            payload, search_result = search_with_payload_and_result(llm_response)

            #获得观察结果
            obs, match_candidates = observe_cts(search_result, requirement)
            print(f"匹配的候选人数量: {len(match_candidates) if isinstance(match_candidates, list) else 0}")
            
            # 处理空列表情况
            if not match_candidates:
                print("没有找到匹配的候选人")
            # 将匹配的候选人添加到总列表中
            elif isinstance(match_candidates, list):
                all_candidates.extend(match_candidates)  # 使用extend添加列表中的元素
                print(f"本轮添加了{len(match_candidates)}个候选人")
            elif isinstance(match_candidates, dict):
                # 如果是字典，可能需要提取具体的候选人数组
                if 'candidates' in match_candidates:
                    nested_candidates = match_candidates['candidates']
                    if isinstance(nested_candidates, list):
                        all_candidates.extend(nested_candidates)
                        print(f"本轮从嵌套结构中添加了{len(nested_candidates)}个候选人")
                else:
                    print("收到非预期的字典结构，未添加候选人")
            else:
                print(f"收到非列表类型的候选数据: {type(match_candidates)}")

            # 拼接上下文
            history = history + "\n\n" + assemble_history(step+1, llm_response, "通过API完成检索，payload如下："+json.dumps(payload, ensure_ascii=False), obs)
        
        # 循环结束后，组装包含所有轮次信息的最终上下文
        final_context = assemble_context(system_prompt, requirement, len(all_candidates), history)
        
        # 保存最终的完整上下文
        save_history_json(final_context, all_candidates)
        
        print(f"\n搜索完成。总共找到{len(all_candidates)}个匹配的候选人。")
        return all_candidates