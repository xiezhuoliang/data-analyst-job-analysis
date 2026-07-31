import pandas as pd
import numpy as np
import re
import os
import sys

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, 'data', 'interim', 'step3_city_recovered.csv')
OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'interim', 'step4_salary_clean.csv')


# ==================== 函数定义 ====================

def extract_salary_months(s):
    """提取 ·N薪，返回 (清洗后的字符串, 薪月数)"""
    if pd.isna(s):
        return s, None
    s = str(s).strip()
    match = re.search(r'·(\d+)薪', s)
    if match:
        months = int(match.group(1))
        s_clean = re.sub(r'·\d+薪', '', s).strip()
        return s_clean, months
    return s, None


def parse_salary(s):
    """
    解析薪资字符串，统一换算为 万元/月
    返回: [薪资下限(万), 薪资上限(万), 月薪中位(万), is_intern, salary_flag, salary_note]
    """
    if pd.isna(s) or s == '':
        return [np.nan, np.nan, np.nan, 0, 'empty', '薪资为空']

    # 去空格，统一处理
    s = str(s).strip().replace(' ', '').replace('\u3000', '')

    # 1. 年薪 (/年)
    if '/年' in s:
        match = re.match(r'([\d.]+)-([\d.]+)万/年', s)
        if match:
            min_val = float(match.group(1)) / 12
            max_val = float(match.group(2)) / 12
            mid = (min_val + max_val) / 2
            return [round(min_val, 4), round(max_val, 4), round(mid, 4),
                    0, 'yearly', '年薪÷12转月薪']
        match = re.match(r'([\d.]+)万/年', s)
        if match:
            val = float(match.group(1)) / 12
            return [round(val, 4), round(val, 4), round(val, 4),
                    0, 'yearly', '年薪÷12转月薪']
        return [np.nan, np.nan, np.nan, 0, 'error', f'无法解析年薪: {s}']

    # 2. 日薪 (元/天)
    if '元/天' in s:
        match = re.match(r'([\d.]+)元/天', s)
        if match:
            val = float(match.group(1)) * 21.75 / 10000
            return [round(val, 4), round(val, 4), round(val, 4),
                    1, 'daily', '日薪×21.75转月薪']
        return [np.nan, np.nan, np.nan, 1, 'error', f'无法解析日薪: {s}']

    # 3. 开放式（及以下 / 以上）
    if '及以下' in s:
        match = re.search(r'([\d.]+)(千|万)及以下', s)
        if match:
            val = float(match.group(1))
            unit = match.group(2)
            if unit == '千':
                val = val / 10
            max_val = val
            min_val = val * 0.8   # 按方案：下限 = 上限 × 0.8
            mid = (min_val + max_val) / 2
            return [round(min_val, 4), round(max_val, 4), round(mid, 4),
                    0, 'open_end', '开放式(及以下),下限=上限×0.8']
        return [np.nan, np.nan, np.nan, 0, 'open_end', f'开放式薪资无法解析: {s}']

    if '以上' in s:
        match = re.search(r'([\d.]+)(千|万)以上', s)
        if match:
            val = float(match.group(1))
            unit = match.group(2)
            if unit == '千':
                val = val / 10
            return [round(val, 4), np.nan, round(val, 4),
                    0, 'open_end', '开放式(以上)']
        return [np.nan, np.nan, np.nan, 0, 'open_end', f'开放式薪资无法解析: {s}']

    # 4. 跨单位：X千-Y万
    cross = re.match(r'([\d.]+)千-([\d.]+)万', s)
    if cross:
        min_val = float(cross.group(1)) / 10
        max_val = float(cross.group(2))
        mid = (min_val + max_val) / 2
        return [round(min_val, 4), round(max_val, 4), round(mid, 4),
                0, 'cross_unit', '跨单位千-万']

    # 5. 纯千范围：X-Y千
    k_range = re.match(r'([\d.]+)-([\d.]+)千', s)
    if k_range:
        min_val = float(k_range.group(1)) / 10
        max_val = float(k_range.group(2)) / 10
        mid = (min_val + max_val) / 2
        return [round(min_val, 4), round(max_val, 4), round(mid, 4),
                0, 'pure_k', '纯千']

    # 6. 纯万范围：X-Y万
    w_range = re.match(r'([\d.]+)-([\d.]+)万', s)
    if w_range:
        min_val = float(w_range.group(1))
        max_val = float(w_range.group(2))
        mid = (min_val + max_val) / 2
        return [round(min_val, 4), round(max_val, 4), round(mid, 4),
                0, 'pure_w', '纯万']

    # 7. 单值纯万
    w_single = re.match(r'^([\d.]+)万$', s)
    if w_single:
        val = float(w_single.group(1))
        return [round(val, 4), round(val, 4), round(val, 4),
                0, 'pure_w', '纯万单值']

    # 8. 单值纯千
    k_single = re.match(r'^([\d.]+)千$', s)
    if k_single:
        val = float(k_single.group(1)) / 10
        return [round(val, 4), round(val, 4), round(val, 4),
                0, 'pure_k', '纯千单值']

    # 未匹配
    return [np.nan, np.nan, np.nan, 0, 'error', f'未匹配格式: {s}']


# ==================== 主流程 ====================

def main():
    print("=" * 60)
    print("Step 4: 薪资标准化")
    print("=" * 60)

    if not os.path.exists(INPUT_PATH):
        print(f"错误: 输入文件不存在: {INPUT_PATH}")
        sys.exit(1)

    df = pd.read_csv(INPUT_PATH, encoding='utf-8-sig')
    print(f"读取数据: {len(df)} 行")

    # --- 提取 ·N薪 ---
    months_list = []
    clean_str_list = []
    for val in df['薪资']:
        c_str, months = extract_salary_months(val)
        clean_str_list.append(c_str)
        months_list.append(months)

    df['薪月数'] = months_list
    # 保留调试列（最终 jobs_clean 可丢弃）
    df['salary_clean_str'] = clean_str_list

    # --- 解析薪资主体 ---
    results = []
    for s in clean_str_list:
        results.append(parse_salary(s))

    res_df = pd.DataFrame(results, columns=[
        '薪资下限(万)', '薪资上限(万)', '月薪中位(万)',
        'is_intern', 'salary_flag', 'salary_note'
    ])

    df = pd.concat([df.reset_index(drop=True), res_df.reset_index(drop=True)], axis=1)

    # --- 计算年薪中位 = 月薪中位 × 薪月数 ---
    df['年薪中位(万)'] = df.apply(
        lambda x: round(x['月薪中位(万)'] * x['薪月数'], 4)
        if pd.notna(x['月薪中位(万)']) and pd.notna(x['薪月数']) else np.nan,
        axis=1
    )

    # --- 边界检查：月薪中位 < 0.3万 或 > 15万 需人工复核 ---
    def boundary_check(row):
        if pd.isna(row['月薪中位(万)']):
            return 'unknown'
        if row['月薪中位(万)'] < 0.3:
            return 'review_low'
        if row['月薪中位(万)'] > 15:
            return 'review_high'
        return 'ok'

    df['boundary_check'] = df.apply(boundary_check, axis=1)

    # --- 统计报告 ---
    print("\n--- 薪资解析统计 ---")
    print(df['salary_flag'].value_counts().sort_index())
    print(f"\n含 ·N薪 记录: {df['薪月数'].notna().sum()} 条")
    print(f"日薪/实习标记(is_intern=1): {df['is_intern'].sum()} 条")
    print("\n边界检查分布:")
    print(df['boundary_check'].value_counts().sort_index())

    # 异常样本展示
    errors = df[df['salary_flag'] == 'error']
    if not errors.empty:
        print(f"\n⚠️  解析失败共 {len(errors)} 条，样本如下:")
        print(errors[['薪资', 'salary_clean_str', 'salary_note']].head(10))

    open_ends = df[df['salary_flag'] == 'open_end']
    if not open_ends.empty:
        print(f"\n⚠️  开放式薪资共 {len(open_ends)} 条，建议分析时剔除或复核:")
        print(open_ends[['薪资', '薪资下限(万)', '薪资上限(万)', 'salary_note']].head(10))

    review = df[df['boundary_check'].isin(['review_low', 'review_high'])]
    if not review.empty:
        print(f"\n⚠️  边界异常需复核共 {len(review)} 条:")
        print(review[['薪资', '月薪中位(万)', 'boundary_check']].head(10))

    # --- 保存 ---
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"\n✅ 输出保存: {OUTPUT_PATH}")
    print("Step 4 完成.")


if __name__ == '__main__':
    main()
