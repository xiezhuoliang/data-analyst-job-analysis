import pandas as pd
import numpy as np
import re
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, 'data', 'interim', 'step5_exp_edu_mapped.csv')
OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'interim', 'step6_text_clean.csv')


def clean_text(text):
    """清洗文本：去制表符、回车、乱码编号、连续空白、首尾冗余标题"""
    if pd.isna(text):
        return np.nan

    text = str(text)

    # 去制表符、回车、换行
    text = text.replace('\t', ' ').replace('\r', ' ').replace('\n', ' ')

    # 去乱码编号（如 "61	负责..." 行首数字编号）
    text = re.sub(r'^\d+\s+', '', text)
    # 去文中残留的数字+空格前缀（如 "61 负责"）
    text = re.sub(r'(?<=\s)\d+\s+(?=[\u4e00-\u9fa5])', ' ', text)

    # 去连续空白
    text = re.sub(r' +', ' ', text)

    # 去首尾冗余标题词
    head_patterns = [
        r'^(岗位职责|职位要求|任职要求|任职资格|岗位要求|应聘要求|我们需要|工作职责|工作内容|职能类别|关键字)[:：]?\s*',
    ]
    for p in head_patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE)

    # 去尾部冗余（如 "职能类别：数据分析师 关键字：..."）
    text = re.sub(r'\s*(职能类别|关键字)[:：]?.*$', '', text, flags=re.IGNORECASE)

    text = text.strip()

    return np.nan if text == '' else text


def is_false_positive(text):
    """
    误切校验：如果切分结果包含反向关键词，说明切错了位置
    """
    if pd.isna(text) or len(str(text)) < 20:
        return True

    text = str(text)
    # 反向关键词：如果切分结果里还有这些，说明切到了职责部分
    false_keywords = [
        '岗位职责', '工作内容', '工作职责', '职能类别',
        '公司介绍', '关于我们', '企业简介', '公司福利',
        '职位描述', '岗位描述'
    ]
    for kw in false_keywords:
        if kw in text:
            return True

    # 如果切分结果里又出现「任职要求」本身，说明重复切或位置不对
    req_keywords = ['任职要求', '任职资格', '岗位要求', '职位要求']
    hits = sum(1 for kw in req_keywords if kw in text)
    if hits > 1:
        return True

    return False


def extract_requirements(desc):
    """
    从职位描述中切分任职要求段落
    两轮匹配 + 误切校验
    """
    if pd.isna(desc):
        return np.nan

    desc = str(desc)

    # ===== 第一轮：精确匹配（特异性高，几乎不会误切） =====
    exact_keywords = [
        '任职要求', '任职资格', '岗位要求', '职位要求',
        '应聘要求', '我们需要', '必备条件', '职位需求',
        '岗位需求'
    ]
    # 英文 JD
    en_keywords = ['Must to have', 'Must-to-have', 'Requirements', 'Job Requirements']

    # 构建正则：关键词 + 可选冒号/空格
    all_exact = exact_keywords + en_keywords
    pattern1 = r'(?:' + '|'.join(all_exact) + r')[:：]?\s*'
    match = re.search(pattern1, desc, re.IGNORECASE)

    if match:
        result = desc[match.end():].strip()
        if not is_false_positive(result):
            return result

    # ===== 第二轮：位置约束的宽松匹配（仅对未命中的） =====
    # 匹配「要求」「条件」「你需要」，但要求前面是开头/换行/数字编号
    loose_pattern = r'(?:^|\n|\d+\.\s)(?:要求|条件|你需要|你需要具备)[:：]?\s*'
    match2 = re.search(loose_pattern, desc, re.IGNORECASE)

    if match2:
        result = desc[match2.end():].strip()
        if not is_false_positive(result):
            return result

    return np.nan


def clean_welfare(s):
    """清洗福利标签，统一为 | 分隔"""
    if pd.isna(s) or str(s).strip() == '':
        return np.nan

    s = str(s).strip()
    # 统一分隔符为 |
    s = s.replace('、', '|').replace(',', '|').replace('，', '|').replace(';', '|').replace('；', '|')
    parts = [p.strip() for p in s.split('|') if p.strip()]
    return '|'.join(parts) if parts else np.nan


def main():
    print("=" * 60)
    print("Step 6: 文本清洗 + 任职要求回收")
    print("=" * 60)

    if not os.path.exists(INPUT_PATH):
        print(f"错误: 输入文件不存在: {INPUT_PATH}")
        sys.exit(1)

    df = pd.read_csv(INPUT_PATH, encoding='utf-8-sig')
    print(f"读取数据: {len(df)} 行")

    # 1. 保留原始职位描述
    df['职位描述_raw'] = df['职位描述']

    # 2. 清洗职位描述
    df['职位描述_clean'] = df['职位描述'].apply(clean_text)

    # 3. 任职要求：先清洗原有，再回收缺失
    df['任职要求_clean'] = df['任职要求'].apply(clean_text)

    missing_before = df['任职要求_clean'].isna().sum()
    print(f"\n任职要求清洗后缺失: {missing_before} 条")

    # 从职位描述回收（两轮匹配 + 误切校验）
    mask = df['任职要求_clean'].isna()
    recovered = df.loc[mask, '职位描述_clean'].apply(extract_requirements)
    recovered_count = recovered.notna().sum()

    df.loc[mask & recovered.notna(), '任职要求_clean'] = recovered[recovered.notna()]
    missing_after = df['任职要求_clean'].isna().sum()
    print(f"任职要求回收后缺失: {missing_after} 条 (成功回收 {recovered_count} 条)")

    # 4. 福利标签清洗
    df['福利列表'] = df['福利标签'].apply(clean_welfare)

    # 5. 超长描述标记
    df['long_desc'] = df['职位描述_clean'].apply(
        lambda x: 1 if pd.notna(x) and len(str(x)) > 3000 else 0
    )
    print(f"超长描述(>3000字): {df['long_desc'].sum()} 条")

    # 保存
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"\n✅ 输出保存: {OUTPUT_PATH}")
    print("Step 6 完成.")


if __name__ == '__main__':
    main()