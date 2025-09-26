#负责根据招聘要求生成搜索策略，例如搜索关键词等，这里就需要考虑到上下文工程了
import re
from litellm import completion
from dotenv import load_dotenv
from playwright.sync_api import Playwright
from agent.workflow.searchMap import generateCode
from playwright.sync_api import sync_playwright
from tool.resumeListExtract import extractResumeListWithID
from agent.workflow.obs import observe
from tool.logger import save_history_json,save_context_json
from tool.contextAssemble import assemble_context,assemble_history,assemble_react
from agent.prompt.system import SYSTEM_PROMPT
from tool.check import check

load_dotenv()

def call_llm(prompt: str) -> str:
    response = completion(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

system_prompt=SYSTEM_PROMPT


def searchAgent(cookies,requirement):# 初始化工作状态
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        browser_context = browser.new_context()
        browser_context.add_cookies(cookies)
        page = browser_context.new_page()
        page.goto("https://h.liepin.com/search/getConditionItem")  # 进入后台页面
        print(page.title())

        history=""
        reAct=""
        for step in range(2):
            # 组装当前轮次的上下文
            context = assemble_context(system_prompt, requirement, reAct)
            print(f"\n=== Step {step + 1} ===")
            llm_response = call_llm(context)
            print(llm_response)
            print(check(llm_response))

            # 生成playwright操作代码，获得搜索列表
            PlaywrightCode = generateCode(llm_response)
            exec(PlaywrightCode, {"page": page})

            page.wait_for_timeout(3000)

            # 返回总的搜索结果数量
            amount = page.locator("#resultList > div.result-list-bar.v2-resume-bar > div.result-list-bar-right > span").inner_text()
            print(amount)
            # 返回第一页的人选列表
            elements = page.query_selector_all("#resultList > div.table-box > table > tbody > tr")
            res_list = extractResumeListWithID(elements)
            #获得观察结果，传递page参数
            obs=observe(amount, res_list, requirement, llm_response, page)
            # 拼接上下文
            reAct = reAct+ "\n\n" + assemble_react(step+1, llm_response, "playwright在页面上执行完成", obs)
            # 记录轨迹
            history = history + "\n\n" + assemble_history(step+1, llm_response, PlaywrightCode, obs)
        
        # 循环结束后，组装包含所有轮次信息的最终上下文
        final_context = assemble_context(system_prompt, requirement, reAct)
        
        # 保存最终循环的上下文
        save_context_json(final_context)
        # 保存完整的轨迹
        save_history_json(history)

        page.wait_for_timeout(30000)
        browser.close()