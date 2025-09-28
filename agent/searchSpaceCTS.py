#负责根据招聘要求生成搜索策略，例如搜索关键词等，这里就需要考虑到上下文工程了
from multiprocessing import process
from litellm import completion
from dotenv import load_dotenv
from agent.workflow.obs import observe_cts
from tool.logger import save_history_json
from tool.contextAssemble import assemble_context,assemble_history
from agent.prompt.system import SYSTEM_PROMPT
from tool.searchCTS import search_with_payload_and_result
from tool.matchCache import clear_cache,get_qualified_candidate,search_long_term_policy
from tool.token_counter import add_tokens, get_total_tokens, reset_tokens
from agent.prompt.evaluate import PROMPT_FOR_EVAlUATE
import json

load_dotenv()

def call_llm(prompt: str) -> str:
    response = completion(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    add_tokens(response['usage']['total_tokens'])
    return response["choices"][0]["message"]["content"]

def searchAgent(requirement):# 初始化工作状态
        history=""
        #执行前清除所有缓存
        clear_cache()
        reset_tokens()
        policy_for_reference = search_long_term_policy(requirement)

        progress=0
        step = 1
        while step <= 2 and progress <= 1:
            # 组装当前轮次的上下文
            context = assemble_context(SYSTEM_PROMPT, policy_for_reference, requirement,progress, history)
            print(f"\n=== Step {step} ===")
            llm_response = call_llm(context)
            print(llm_response)
            # 调用CTS查询工具得到结果
            payload, search_result = search_with_payload_and_result(llm_response)

            #获得观察结果
            obs = observe_cts(step, search_result, requirement,llm_response)
            task_finished = len(get_qualified_candidate())
            #记录任务完成进度 0/20
            progress=task_finished/20

            # 拼接上下文
            history = history + "\n\n" + assemble_history(step, llm_response, "通过API完成检索，payload如下："+json.dumps(payload, ensure_ascii=False), obs)
            step+=1
        
        # 循环结束后，组装包含所有轮次信息的最终上下文
        final_context = assemble_context(SYSTEM_PROMPT, policy_for_reference, requirement, progress, history)
        
        # 保存最终的完整上下文
        save_history_json(final_context)
        total_tokens = get_total_tokens()

        # 打印最终成果：所用步数、合格人选数量、总token数量、费用（假设每百万token费用2.5美元）
        print(f"最终结果：\n所用步数：{step-1}\n合格人选数量：{task_finished}\ntoken数量：{total_tokens}\n费用（假设每百万token费用2.5美元）：{total_tokens /10000 * 0.025:.4f}美元")
        
        #对final context进行评级
        response = completion(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": PROMPT_FOR_EVAlUATE},
                    {"role": "user", "content": final_context}
                ]
            )
        print(response["choices"][0]["message"]["content"])
    