import json
import hashlib

def parse_candidates_to_text(candidates):
    """
    将复杂的json结构体解析为易读的文本格式成为text，并提取其中关键字段进行哈希化作为cv_id,最终形成
            [
                {
                    "cv_id": "哈希化后的cv_id",
                    "candidate_text": "候选人的易读文本表示"
                }
            ]
    """
    # 初始化结果列表
    result = []
    
    # 遍历每个候选人
    for candidate in candidates:
        personal_info = [
            f"性别: {candidate.get('gender', '')}",
            f"年龄: {candidate.get('age', '')}",
            f"工作年限: {candidate.get('workYear', '')}年",
            f"当前所在地: {candidate.get('nowLocation', '')}",
            f"求职状态: {candidate.get('jobState', '')}",
            f"期望薪资: {candidate.get('expectedSalary', '')}",
            f"期望行业: {candidate.get('expectedIndustry', '')}",
            f"期望地点: {candidate.get('expectedLocation', '')}",
            f"期望职位类别: {candidate.get('expectedJobCategory', '')}",
            f"活跃状态: {candidate.get('activeStatus', '')}"
        ]
        candidate_text += "个人信息:\n" + "\n".join([info for info in personal_info if info.split(": ")[1]]) + "\n\n"
                # 教育背景
        if 'educationList' in candidate and candidate['educationList']:
            candidate_text += "教育背景:\n"
            for edu in sorted(candidate['educationList'], key=lambda x: x.get('sortNum', 0)):
                edu_info = f"{edu.get('education', '')} - {edu.get('school', '')} - {edu.get('speciality', '')}"
                period = f"{edu.get('startTime', '')[:4]}-{edu.get('endTime', '至今')[:4]}" if edu.get('startTime') else ''
                if period:
                    edu_info += f" ({period})"
                candidate_text += f"  {edu_info}\n"
            candidate_text += "\n"
        
        # 工作经历
        if 'workExperienceList' in candidate and candidate['workExperienceList']:
            candidate_text += "工作经历:\n"
            for exp in sorted(candidate['workExperienceList'], key=lambda x: x.get('sortNum', 0)):
                exp_info = f"{exp.get('company', '')} - {exp.get('title', '')}"
                period = f"{exp.get('startTime', '')[:4]}-{exp.get('endTime', '至今')[:4]}" if exp.get('startTime') else ''
                if period:
                    exp_info += f" ({period})"
                candidate_text += f"  {exp_info}\n"
                # 工作描述（限制长度）
                summary = exp.get('summary', '')
                if summary:
                    if len(summary) > 150:
                        summary = summary[:150] + "..."
                    candidate_text += f"    工作描述: {summary}\n"


        # 生成 CV ID
        cv_id = generate_candidate_id(candidate)
        result.append({
            "cv_id": cv_id,
            "candidate_text": candidate_text
        })
    
    return result


def generate_candidate_id(candidate):
    """为候选人生成唯一ID
    
    Args:
        candidate: 候选人数据字典
        
    Returns:
        str: 基于候选人关键信息生成的唯一ID字符串
    """
    # 如果候选人已有ID，则直接返回
    if 'id' in candidate and candidate['id']:
        return str(candidate['id'])
    
    # 创建一个用于生成哈希的字符串，包含候选人的关键信息
    # 提取关键个人信息
    personal_info = []
    if 'gender' in candidate:
        personal_info.append(f"gender:{candidate['gender']}")
    if 'age' in candidate:
        personal_info.append(f"age:{candidate['age']}")
    if 'workYear' in candidate:
        personal_info.append(f"workYear:{candidate['workYear']}")
    if 'nowLocation' in candidate:
        personal_info.append(f"location:{candidate['nowLocation']}")
    
    # 提取教育背景信息（取最高学历）
    if 'educationList' in candidate and candidate['educationList']:
        # 按sortNum排序，通常排序越小表示学历越高
        sorted_education = sorted(candidate['educationList'], key=lambda x: x.get('sortNum', 999))
        highest_education = sorted_education[0]
        if 'education' in highest_education:
            personal_info.append(f"edu:{highest_education['education']}")
        if 'school' in highest_education:
            personal_info.append(f"school:{highest_education['school']}")
        if 'speciality' in highest_education:
            personal_info.append(f"major:{highest_education['speciality']}")
    
    # 提取最近的工作经验
    if 'workExperienceList' in candidate and candidate['workExperienceList']:
        # 按sortNum排序，通常排序越小表示最近的工作
        sorted_work = sorted(candidate['workExperienceList'], key=lambda x: x.get('sortNum', 999))
        recent_work = sorted_work[0]
        if 'company' in recent_work:
            personal_info.append(f"company:{recent_work['company']}")
        if 'title' in recent_work:
            personal_info.append(f"title:{recent_work['title']}")
    
    # 如果信息不足以生成ID，使用完整的JSON字符串
    if not personal_info:
        # 为确保一致性，排序键值
        sorted_candidate = json.dumps(candidate, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(sorted_candidate.encode('utf-8')).hexdigest()
    
    # 生成哈希ID
    id_string = '_'.join(personal_info)
    return hashlib.md5(id_string.encode('utf-8')).hexdigest()