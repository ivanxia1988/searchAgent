# 负责从搜索列表中提取出简历列表结构体

import json
import urllib.parse
from bs4 import BeautifulSoup

def extractResumeList(elements):
    resume_list = []
    for element in elements:
        resume_list.append(element.inner_text())
    return resume_list

# 负责从搜索列表中提取出简历列表结构体，包含id
def extractResumeListWithID(elements):
    resume_list = []
    for element in elements:
        html = element.inner_html() 
        soup = BeautifulSoup(html, "html.parser")
        tr = soup.find("tr") or soup

        id_val = ""
        inp = tr.select_one('input[name="res_id_encode"]')
        if inp and inp.has_attr("value"):
            id_val = inp["value"].strip()
        else:
            scm = tr.get("data-tlg-scm", "") or ""
            m = re.search(r"cid=([^&]+)", scm)
            if m:
                id_val = m.group(1)
        content = tr.get_text(" ", strip=True)
        resume_list.append({"id": id_val, "ResumeSummary": content})

    return resume_list

def extractIDList(elements):
    res_id_encode_list = []
    for element in elements:
            # 获取 data_info 属性值
            data_info = element.get_attribute('data_info')
            # 解码并解析 data_info 属性值为 JSON 对象
            data_info_json = json.loads(urllib.parse.unquote(data_info))
            # 提取 res_id_encode 的值
            print(data_info_json)
            res_id_encode = data_info_json.get('res_id_encode')   
 
            if res_id_encode:
                res_id_encode_list.append(res_id_encode)
    return res_id_encode_list