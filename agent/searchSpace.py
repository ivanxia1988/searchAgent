#负责根据招聘要求生成搜索策略，例如搜索关键词等，这里就需要考虑到上下文工程了
from litellm import completion
from dotenv import load_dotenv
from playwright.sync_api import Playwright
from agent.workflow.searchMap import generateCode
from playwright.sync_api import sync_playwright
from tool.resumeListExtract import extractResumeList
from agent.workflow.obs import observe
from tool.logger import save_history_json
from tool.contextAssemble import assemble_context,assemble_history
from agent.prompt.system import SYSTEM_PROMPT

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
        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()
        page.goto("https://h.liepin.com/search/getConditionItem")  # 进入后台页面
        print(page.title())
        # 获得期望城市和当前城市 因为里面的表单选项是动态变动的，所以需要每次都获得并试试生成操作代码
        ExpectCity = page.locator("#main-container > div > div.search-resume-wrap-v3 > div:nth-child(2) > div > div > div.wrap > form > section > div > div.filter-box > div:nth-child(2)").evaluate("el => el.outerHTML")
        CurrentCity = page.locator("#main-container > div > div.search-resume-wrap-v3 > div:nth-child(2) > div > div > div.wrap > form > section > div > div.filter-box > div:nth-child(1)").evaluate("el => el.outerHTML")

        history=""
        for step in range(2):
            # 组装当前轮次的上下文
            context = assemble_context(system_prompt, requirement, history)
            print(f"\n=== Step {step + 1} ===")
            llm_response = call_llm(context)
            print(llm_response)

            # 生成playwright操作代码，获得搜索列表
            PlaywrightCode = generateCode(llm_response,ExpectCity,CurrentCity)
            exec(PlaywrightCode, {"page": page})

            page.wait_for_timeout(3000)

            # 返回总的搜索结果数量
            amount = page.locator("#resultList > div.result-list-bar.v2-resume-bar > div.result-list-bar-right > span").inner_text()
            print(amount)
            # 返回第一页的人选列表
            elements = page.query_selector_all("#resultList > div.table-box > table > tbody > tr")
            res_list = extractResumeList(elements)
            #获得观察结果
            obs=observe(amount,res_list,requirement)
            # 拼接上下文
            history = history + "\n\n" + assemble_history(step+1, llm_response, PlaywrightCode, obs)
        
        # 循环结束后，组装包含所有轮次信息的最终上下文
        final_context = assemble_context(system_prompt, requirement, history)
        
        # 保存最终的完整上下文
        save_history_json(final_context)

        page.wait_for_timeout(30000)
        browser.close()