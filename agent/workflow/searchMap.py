#该方法负责将大模型输出的搜索内容 转换成 playwright可以操作的内容，基本属于无状态的workflow
from litellm import completion
from dotenv import load_dotenv
import re
load_dotenv()

system_prompt="""

你是一位 Playwright 专家。请根据“招聘搜索需求（自然语言）”和以下 DOM/选择器信息，生成 **一段** 可执行的 Python 代码，且只能输出 **一个** 标注为 `python` 的代码块。代码需定义并实现：
1. 仅包含 page.click / page.fill / page.wait_for_timeout
2. 不得包含 import、browser/context/page 初始化、print、try/except、断言等
3. 所有“不限”的选项，都不需要生成操作代码，因为页面已经模式是不限的
4. 在开始任何操作前，都要清空筛选项，以防止多轮操作时已经存在选中项目导致干扰。清空方式是点击元素：#main-container > div > div.search-resume-wrap-v3 > div:nth-child(2) > div > div > div.wrap > form > section > div > span

【固定可操作项与选择器】
1) 直接填充：注意不要将关键词填充到公司名称或岗位名称中，除非显示提到了
   - 能力关键词：  #rc_select_1
   - 目标公司：  #rc_select_4
   - 目标岗位：  #rc_select_2

2) 学历下限（点击标签）：
   - 建议优先：.sfilter-edu .tag-label-group label:has-text("本科/硕士/博士/大专/中专/高中")
   - 兜底（仅当上面匹配不到时才用）：以下长选择器
     2.1 不限：
         #main-container > div:nth-child(2) > div > div:nth-child(2) > div > div > div.wrap > form > section > div > div.filter-box > section:nth-child(5) > div > div > div > label.tag-item.selected
     2.2 本科：
         #main-container > div:nth-child(2) > div > div:nth-child(2) > div > div > div.wrap > form > section > div > div.filter-box > section:nth-child(4) > div > div > div > div.tag-label-group > label:nth-child(2)
     2.3 硕士：
         #main-container > div:nth-child(2) > div > div:nth-child(2) > div > div > div.wrap > form > section > div > div.filter-box > section:nth-child(4) > div > div > div > div.tag-label-group > label:nth-child(3)
     2.4 博士/博士后：
         #main-container > div:nth-child(2) > div > div:nth-child(2) > div > div > div.wrap > form > section > div > div.filter-box > section:nth-child(4) > div > div > div > div.tag-label-group > label:nth-child(4)
     2.5 大专：
         #main-container > div:nth-child(2) > div > div:nth-child(2) > div > div > div.wrap > form > section > div > div.filter-box > section:nth-child(4) > div > div > div > div.tag-label-group > label:nth-child(5)
     2.6 中专/中技：
         #main-container > div:nth-child(2) > div > div:nth-child(2) > div > div > div.wrap > form > section > div > div.filter-box > section:nth-child(4) > div > div > div > div.tag-label-group > label:nth-child(6)
     2.7 高中及以下：
         #main-container > div:nth-child(2) > div > div:nth-child(2) > div > div > div.wrap > form > section > div > div.filter-box > section:nth-child(4) > div > div > div > div.tag-label-group > label:nth-child(7)

3) 工作年限：
   - 必须先执行点击：.sfilter-work-year .tag-label-group label:nth-child(7)   # 仅用于触发面板
   - 经验下限（年）：#workYearsLow
   - 经验上限（年）：#workYearsHigh
   - 说明：如 DOM 中实际为标签点击而非输入框，请按标签点击；若存在输入框则按输入框填充

4) 年龄要求（直接填充）：
   - 年龄下限（岁）：#ageLow
   - 年龄上限（岁）：#ageHigh

5) 性别要求（下拉后选择一项）：
   - 触发下拉：.sfilter-other-condition .ant-select-selector .ant-select-selection-item
   - 选项（优先）：div.ant-select-dropdown .ant-select-item-option:has-text("不限"|"男性"|"女性")
   - 兜底（仅当上面匹配不到时使用）：body > div:nth-child(27) ... （你提供的那些长链）

6) 目前城市：查找目标城市
   - 仅在各自 DOM 片段中查找对应城市文本（例如 label.tag-item:has-text("上海")）
    例如：使用 page.locator("#main-container > div > div.search-resume-wrap-v3 > div:nth-child(2) > div > div > div.wrap > form > section > div > div.filter-box > div:nth-child(1)").locator("label.tag-item:has-text('上海')").click()
7) 期望城市（从给定 DOM 内按文本点击）：
   - 仅在各自 DOM 片段中查找对应城市文本（例如 label.tag-item:has-text("上海")）
    例如：使用 page.locator("#main-container > div > div.search-resume-wrap-v3 > div:nth-child(2) > div > div > div.wrap > form > section > div > div.filter-box > div:nth-child(2)").locator("label.tag-item:has-text('上海')").click()

【工作流程与约束】
- 从“招聘搜索需求”中提取：岗位关键词、公司名称、岗位名称、院校（可多选）、工作年限上下限、年龄上下限、性别、目前城市、期望城市。未提及的一律不操作。
- 生成顺序（固定）：关键词 → 岗位名称 → 公司名称 → 院校 → 工作年限（低→高） → 年龄（低→高） → 性别 → 目前城市 → 期望城市。
- 每次操作，延迟500ms：page.wait_for_timeout(500)；
- 定位策略：优先“语义类 + 文本”选择器（如 .sfilter-edu .tag-label-group label:has-text('本科')）；不唯一时再加父级限定；最后才使用你提供的长链兜底。
- 仅使用：page.click / page.fill / page.wait_for_timeout。不得输出任何其他语句或解释性文字。
- 如果某项在 DOM 中无法定位或需求未提供，对该项**跳过**（不输出任何操作）。

【输出要求（强制）】
- 只输出 **一个** 代码块，且使用三反引号并标注 `python`。

"""

def generateCode(requirement):
    response = completion(
        model="gpt-4o",  # 填写需要调用的模型名称
        messages=[
            {
                "role": "system",
                "content": (system_prompt)
            },
            {
                "role": "user",
                "content": f"人才搜索的关键词如下：{requirement}"
            }
        ],
    )

    #去除大模型code生成结果中的markdown标记
    pattern = r"```python\n(.*?)\n```"
    pythonCode = re.findall(pattern, response.choices[0].message.content, re.DOTALL)[0]
    #查看代码生成结果
    print(pythonCode)

    return pythonCode

#generateCode("我要招聘一名本科毕业的希望在上海工作，责任心很强的35岁的java开发工程师")