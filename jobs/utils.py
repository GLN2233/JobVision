import re

def normalize_salary_range(salary_range):
    """
    将不同格式的薪资范围统一转换为以元为单位的平均值
    支持的格式：
    - 15k-25k
    - 1.2-1.8万
    - 4-6千
    - 8千-1.3万
    返回元为单位的平均值，如果格式不支持则返回None
    """
    if not salary_range:
        return None
    
    # 统一格式：去除空格，转换为小写
    salary_range = salary_range.strip().lower()
    
    # 检查是否包含必要的单位
    if not any(unit in salary_range for unit in ['k', '万', '千']):
        return None
    
    # 检查是否包含分隔符
    if '-' not in salary_range:
        return None
    
    # 提取数字和单位
    numbers = re.findall(r'\d+(?:\.\d+)?', salary_range)
    if len(numbers) < 2:
        return None
    
    try:
        # 转换为浮点数
        start_value = float(numbers[0])
        end_value = float(numbers[1])
        
        # 判断单位并转换为元
        if 'k' in salary_range:
            start_value *= 1000
            end_value *= 1000
        elif '万' in salary_range:
            start_value *= 10000
            end_value *= 10000
        elif '千' in salary_range:
            start_value *= 1000
            end_value *= 1000
        
        # 处理混合单位情况（如：8千-1.3万）
        parts = salary_range.split('-')
        if '千' in parts[0] and '万' in parts[1]:
            start_value *= 1  # 已经是千单位
            end_value *= 10   # 从千转万
        elif 'k' in parts[0] and '万' in parts[1]:
            start_value *= 1  # 已经是k单位
            end_value *= 10   # 从k转万
        
        # 验证薪资范围的合理性
        if start_value <= 0 or end_value <= 0 or start_value > end_value:
            return None
            
        # 返回平均值
        return int((start_value + end_value) / 2)
    except (ValueError, TypeError):
        return None

def get_salary_distribution(jobs):
    """
    获取薪资分布统计数据
    返回薪资区间及对应的职位数量
    """
    # 定义薪资区间（以元为单位）
    ranges = [
        (0, 5000),
        (5000, 10000),
        (10000, 15000),
        (15000, 20000),
        (20000, 30000),
        (30000, float('inf'))
    ]
    
    # 初始化统计字典
    distribution = {f'{r[0]/1000:.0f}k-{r[1]/1000:.0f}k' if r[1] != float('inf') else f'{r[0]/1000:.0f}k以上': 0 for r in ranges}
    
    # 统计每个区间的职位数量
    for job in jobs:
        avg_salary = normalize_salary_range(job.salary_range)
        if not avg_salary:
            continue
        
        # 确定所属区间
        for r in ranges:
            if r[0] <= avg_salary < r[1]:
                key = f'{r[0]/1000:.0f}k-{r[1]/1000:.0f}k' if r[1] != float('inf') else f'{r[0]/1000:.0f}k以上'
                distribution[key] += 1
                break
    
    return {
        'labels': list(distribution.keys()),
        'data': list(distribution.values())
    }

def get_experience_requirement_distribution(jobs):
    """
    获取经验要求分布统计数据
    返回经验要求及对应的职位数量
    """
    # 初始化分布字典，包含1-10年的具体年限和无经验要求
    distribution = {'无经验要求': 0}
    for i in range(1, 11):
        distribution[f'{i}年'] = 0
    
    for job in jobs:
        description = job.description
        if not description:
            distribution['无经验要求'] += 1
            continue
            
        # 查找经验要求关键词
        idx = description.find('经验要求：')
        if idx == -1:
            distribution['无经验要求'] += 1
            continue
            
        # 提取经验要求信息
        exp_info = description[idx + 5:idx + 15]  # 取更长的片段以确保完整匹配
        
        # 处理无经验和应届的情况
        if '应届' in exp_info or '无经验' in exp_info:
            distribution['无经验要求'] += 1
            continue
        
        # 尝试提取数字
        years = re.findall(r'\d+', exp_info)
        if years:
            year = int(years[0])
            if 1 <= year <= 10:
                distribution[f'{year}年'] += 1
            else:
                distribution['无经验要求'] += 1
        else:
            distribution['无经验要求'] += 1
    
    return {
        'labels': list(distribution.keys()),
        'data': list(distribution.values())
    }

def get_education_distribution(jobs):
    """
    获取学历分布统计数据
    返回学历要求及对应的职位数量
    """
    distribution = {
        '本科': 0,
        '硕士': 0,
        '博士': 0,
        '无学历要求': 0
    }
    
    for job in jobs:
        description = job.description
        if not description:
            distribution['无学历要求'] += 1
            continue
            
        # 查找学历要求关键词
        idx = description.find('学历要求：')
        if idx == -1:
            distribution['无学历要求'] += 1
            continue
            
        # 提取学历要求后的两个字符
        edu_level = description[idx + 5:idx + 7]
        
        # 根据学历要求分类统计
        if '本科' in edu_level:
            distribution['本科'] += 1
        elif '硕士' in edu_level:
            distribution['硕士'] += 1
        elif '博士' in edu_level:
            distribution['博士'] += 1
        else:
            distribution['无学历要求'] += 1
    
    return {
        'labels': list(distribution.keys()),
        'data': list(distribution.values())
    }