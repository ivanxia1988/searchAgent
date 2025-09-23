#负责从HTML简历中提取结构化个人信息
from playwright.sync_api import sync_playwright
import json
from tool.cookieTransfer import format_cookie

# 修改resumeExtract函数以接受现有页面实例或创建新实例
def resumeExtract(id, existing_page=None):
    # 如果提供了现有页面实例，直接使用它
    if existing_page:
        page = existing_page
        # 保存当前URL以便稍后恢复
        original_url = page.url
        try:
            page.goto(f"https://h.liepin.com/resume/showresumedetail/?showsearchfeedback=1&res_id_encode={id}")
            # 等待元素出现
            page.wait_for_selector("#rc-tabs-0-panel-1 > div", timeout=10000)
            
            # 获取 innerText
            text = page.locator("#rc-tabs-0-panel-1 > div").inner_text()
            page.wait_for_timeout(1000)
            return text
        except Exception as e:
            print(f"提取简历详情时出错: {e}")
            return f"简历内容无法提取，无法确认任何硬性条件。错误: {str(e)}"
        finally:
            # 恢复原始URL
            try:
                page.goto(original_url)
            except:
                pass
    
    # 如果没有提供页面实例，创建新的实例（用于单独测试）
    with sync_playwright() as p:
        with open("cookie.json", 'r') as f:
            cookies = format_cookie(json.load(f))
        browser = p.chromium.launch(headless=False)
        browser_context = browser.new_context()
        browser_context.add_cookies(cookies)
        page = browser_context.new_page()
        
        try:
            page.goto(f"https://h.liepin.com/resume/showresumedetail/?showsearchfeedback=1&res_id_encode={id}")
            # 等待元素出现
            page.wait_for_selector("#rc-tabs-0-panel-1 > div", timeout=10000)
            
            # 获取 innerText
            text = page.locator("#rc-tabs-0-panel-1 > div").inner_text()
            return text
        except Exception as e:
            print(f"提取简历详情时出错: {e}")
            return f"简历内容无法提取，无法确认任何硬性条件。错误: {str(e)}"
        finally:
            # 清理资源
            page.wait_for_timeout(1000)
            browser.close()

# 示例调用（如果需要单独测试）
# result = resumeExtract("76808f2f7cdbQfb92efbdf0a5")
# print(result)
