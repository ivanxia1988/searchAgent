# 测试candidateParser.py中的parse_candidates_to_text函数

from tool.candidateParser import parse_candidates_to_text

# 创建一个简单的测试候选人数据
test_candidates = [
    {
        "gender": "男",
        "age": "30",
        "workYear": "5-10年",
        "nowLocation": "北京",
        "educationList": [
            {
                "sortNum": 1,
                "education": "本科",
                "school": "北京大学",
                "speciality": "计算机科学",
                "startTime": "2010-09",
                "endTime": "2014-06"
            }
        ],
        "workExperienceList": [
            {
                "sortNum": 1,
                "company": "腾讯科技",
                "title": "高级工程师",
                "startTime": "2019-03",
                "endTime": "至今",
                "summary": "负责后端系统开发和架构设计"
            }
        ]
    }
]

print("测试parse_candidates_to_text函数...")
try:
    result = parse_candidates_to_text(test_candidates)
    print(f"✅ 函数执行成功，返回结果：")
    print(f"找到 {len(result)} 个候选人")
    
    if result:
        first_candidate = result[0]
        print(f"候选人ID: {first_candidate.get('cv_id')}")
        print(f"候选人文本长度: {len(first_candidate.get('candidate_text', ''))} 字符")
        print(f"候选人文本预览: {first_candidate.get('candidate_text', '')[:100]}...")
    
    print("\n测试通过！")
except Exception as e:
    print(f"❌ 测试失败: {str(e)}")