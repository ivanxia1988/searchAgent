# 人岗匹配结果缓存管理工具
from operator import truediv
import os
import json
import hashlib
from datetime import datetime
from tool.candidateParser import generate_candidate_id

JD2CV_CACHE_FILE = "agent/memory/jd2cv_cache.json"
QULIFIED_CANDIDATE_FILE = "agent/memory/qulified_candidate.json"
SEARCH_CACHE_FILE = "agent/memory/keyword_record.json"
LONG_TERM_POLICY_FILE = "agent/memory/long_term_policy.json"



def _load_cache(file_path):
    """从缓存文件加载数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)



def _save_cache(data, file_path):
    """将数据保存到缓存文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_long_term_policy(requirement, policy):
    """保存长期策略到缓存"""
    hashkey = hashlib.md5(requirement.encode('utf-8')).hexdigest()
    cache = _load_cache(LONG_TERM_POLICY_FILE)
    cache.append({"hashkey": hashkey, "policy": policy})
    
    _save_cache(cache, LONG_TERM_POLICY_FILE)
    print(f"✅ 长期策略已保存到缓存")


def get_long_term_policy():
    """从缓存获取长期策略"""
    cache = _load_cache(LONG_TERM_POLICY_FILE)
    return cache

def search_long_term_policy(requirement):
    """从缓存获取长期策略"""
    hashkey = hashlib.md5(requirement.encode('utf-8')).hexdigest()
    cache = _load_cache(LONG_TERM_POLICY_FILE)
    for item in cache:
        if item.get('hashkey') == hashkey:
            return item.get('policy')
    return None

def save_qualified_candidate(candidate):
    """保存符合条件的候选人到缓存"""
    cache = _load_cache(QULIFIED_CANDIDATE_FILE)
    cache.append(candidate)
    
    _save_cache(cache, QULIFIED_CANDIDATE_FILE)
    print(f"✅ 符合条件的候选人已保存到缓存")


def get_qualified_candidate():
    """保存符合条件的候选人到缓存"""
    cache = _load_cache(QULIFIED_CANDIDATE_FILE)
    return cache


def save_match_result_jd2cv(cv_id, match_result):
    """保存人岗匹配结果到jd2cv_cache.json
    
    结构:
        [
            {
            "cv_id": "123",
            "result": "true",
            "reason": "不满足的原因",
            "root_cause": "失败是否是搜索关键词有关系",
            "clue": "通过阅读简历，发现新的挖掘方向"
            },
            {
            "cv_id": "1231",
            "result": "false",
            "reason": "不满足的原因",
            "root_cause": "失败是否是搜索关键词有关系",
            "clue": "通过阅读简历，发现新的挖掘方向"
            }
        ]
    """
    cache = _load_cache(JD2CV_CACHE_FILE)
    
    new_record = {
        'cv_id': cv_id,
        'result': match_result['result'],
        'reason':match_result['reason'],
        "root_cause": match_result['root_cause'],
        "clue": match_result['clue']
    }
    
    cache.append(new_record)
    _save_cache(cache, JD2CV_CACHE_FILE)


def get_match_result_jd2cv(cv_id):
    """从jd2cv_cache.json获取人岗匹配结果
    
    Args:
        cv_id: 候选人ID
        
    Returns:
        dict: 包含match和reason的匹配结果字典，如果不存在则返回None
    """
    cache = _load_cache(JD2CV_CACHE_FILE)
    
    for record in cache:
        if record.get('cv_id') == cv_id:
            print(f"✅ 从jd2cv_cache.json获取到人岗匹配结果")
            return True
    
    return False

def save_search_result(step, policy, obs):
    """
    保存搜索结果到缓存
    保存样例
    [
    {
        "step": 1,
        "keyword": "年龄大于10岁",
        "obs": "跟之前重复比较高，命中率比较差，建议增加筛选条件",
    },
    {
        "step": 2,
        "Keyword": "年龄大于10岁",
        "obs": "跟之前重复比较高，命中率比较差，建议增加筛选条件",
    }
]
    
    
    """

    cache = _load_cache(SEARCH_CACHE_FILE)
    
    new_record = {
        'step': step,
        'keyword': policy,
        'obs': obs
    }
    
    cache.append(new_record)
    _save_cache(cache, SEARCH_CACHE_FILE)


def get_search_result(keyword):
    """
    从缓存中获取搜索结果
    """
    cache = _load_cache(SEARCH_CACHE_FILE)
    
    for record in cache:
        if record.get('keyword') == keyword:
            print(f"✅ 从keyword_record.json获取到搜索结果,step={record.get('step')}")
            return True
    
    return False

def clear_cache():
    """清除所有缓存文件"""
    for filename in [JD2CV_CACHE_FILE, QULIFIED_CANDIDATE_FILE, SEARCH_CACHE_FILE]:
        _save_cache([], filename)
        print(f"✅ 已清除 {filename} 缓存")