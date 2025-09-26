#负责根据招聘要求生成搜索策略，例如搜索关键词等，这里就需要考虑到上下文工程了
from multiprocessing import process
from litellm import completion
from dotenv import load_dotenv
from agent.workflow.obs import observe_cts
from tool.logger import save_history_json
from tool.contextAssemble import assemble_context,assemble_history
from agent.prompt.system import SYSTEM_PROMPT
from tool.searchCTS import search_with_payload_and_result
from tool.matchCache import clear_cache
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
        #执行前清除所有缓存
        clear_cache()

        for step in range(5):
            # 组装当前轮次的上下文
            context = assemble_context(system_prompt, requirement, history)
            print(f"\n=== Step {step + 1} ===")
            llm_response = call_llm(context)
            print(llm_response)

            # 调用CTS查询工具得到结果
            payload, search_result = search_with_payload_and_result(llm_response)

            #获得观察结果
            obs = observe_cts(step, search_result, requirement,llm_response)
           
            # 拼接上下文
            history = history + "\n\n" + assemble_history(step+1, llm_response, "通过API完成检索，payload如下："+json.dumps(payload, ensure_ascii=False), obs)
        
        # 循环结束后，组装包含所有轮次信息的最终上下文
        final_context = assemble_context(system_prompt, requirement, history)
        
        # 保存最终的完整上下文
        save_history_json(final_context)