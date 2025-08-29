# 负责从搜索列表中提取出简历列表结构体

import json
import urllib.parse

def extractResumeList(elements):
    resume_list = []
    for element in elements:
        resume_list.append(element.inner_text())
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