import pandas as pd
import numpy as np
import re
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, 'data', 'interim', 'step4_salary_clean.csv')
OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'interim', 'step5_exp_edu_mapped.csv')


def tier_for_lower(n):
    """===== 7.31质检修正：新增，按经验下限统一归档位 =====
    0→应届/无需经验; 1-2→1-3年; 3-4→3-5年; 5-9→5-10年; ≥10→10年以上"""
    if n == 0:
        return '应届/无需经验'
    if n <= 2:
        return '1-3年'
    if n <= 4:
        return '3-5年'
    if n <= 9:
        return '5-10年'
    return '10年以上'


def parse_experience(s):
    """解析经验要求 → (下限, 上限, 档位)"""
    if pd.isna(s) or str(s).strip() == '':
        return np.nan, np.nan, '未知'

    s = str(s).strip().replace(' ', '').replace('\u3000', '')

    # 无需经验 / 不限
    if any(k in s for k in ['无需经验', '不限经验', '经验不限', '不限', '应届', '无经验']):
        return 0.0, 0.0, '应届/无需经验'

    # 提取数字
    nums = re.findall(r'(\d+)', s)
    if not nums:
        return np.nan, np.nan, '未知'
    nums = [int(n) for n in nums]

    # ===== 固定范围（优先匹配） =====
    if '1-3年' in s:
        return 1.0, 3.0, '1-3年'
    if '2-3年' in s:
        return 1.0, 3.0, '1-3年'
    if '3-4年' in s:
        return 3.0, 4.0, '3-5年'
    if '3-5年' in s:
        return 3.0, 5.0, '3-5年'
    if '5-10年' in s:
        return 5.0, 10.0, '5-10年'
    if '8-10年' in s:
        return 5.0, 10.0, '5-10年'

    # ===== 7.31质检修正：通用区间 X-Y年 补漏 =====
    # 修复前：1-2年/1-5年/2-5年/2-4年/3-7年 等43条全部落入「未知」
    m = re.search(r'(\d+)-(\d+)年', s)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return float(lo), float(hi), tier_for_lower(lo)

    # ===== 含 "及以上" / "以上" =====
    if '及以上' in s or '以上' in s:
        n = nums[0]
        if n == 1:
            return 1.0, np.nan, '1-3年'
        elif n == 2:
            return 2.0, np.nan, '1-3年'
        elif n == 3:
            return 3.0, np.nan, '3-5年'
        elif n == 4:
            return 4.0, np.nan, '3-5年'
        elif n == 5:
            return 5.0, np.nan, '5-10年'
        elif n in (6, 7):
            return float(n), np.nan, '5-10年'
        # ===== 7.31质检修正：8/9年不再归入10年以上 =====
        elif n in (8, 9):
            return float(n), np.nan, '5-10年'
        elif n >= 10:
            return float(n), np.nan, '10年以上'
        else:
            return float(n), np.nan, '未知'

    # ===== 纯单值 =====
    if len(nums) == 1:
        n = nums[0]
        if n == 0:
            return 0.0, 0.0, '应届/无需经验'
        elif n == 1:
            return 1.0, np.nan, '1-3年'
        elif n == 2:
            return 2.0, np.nan, '1-3年'
        elif n == 3:
            return 3.0, np.nan, '3-5年'
        elif n == 4:
            return 4.0, np.nan, '3-5年'
        elif n == 5:
            return 5.0, np.nan, '5-10年'
        elif n in (6, 7):
            return float(n), np.nan, '5-10年'
        # ===== 7.31质检修正：8/9年不再归入10年以上 =====
        elif n in (8, 9):
            return float(n), np.nan, '5-10年'
        elif n >= 10:
            return float(n), np.nan, '10年以上'

    return np.nan, np.nan, '未知'


def parse_education(s):
    """解析学历 → (层级 1-5)"""
    if pd.isna(s) or str(s).strip() == '':
        return np.nan

    s = str(s).strip()

    if any(k in s for k in ['高中', '中技', '中专']):
        return 1.0
    if '大专' in s or '专科' in s:
        return 2.0
    if '本科' in s or '大学' in s:
        return 3.0
    if '硕士' in s or '研究生' in s:
        return 4.0
    if '博士' in s:
        return 5.0

    return np.nan


def main():
    print("=" * 60)
    print("Step 5: 经验/学历分档映射")
    print("=" * 60)

    if not os.path.exists(INPUT_PATH):
        print(f"错误: 输入文件不存在: {INPUT_PATH}")
        sys.exit(1)

    df = pd.read_csv(INPUT_PATH, encoding='utf-8-sig')
    print(f"读取数据: {len(df)} 行")

    # 经验
    exp_results = df['经验要求'].apply(parse_experience)
    df['经验下限(年)'] = [r[0] for r in exp_results]
    df['经验上限(年)'] = [r[1] for r in exp_results]
    df['经验档位'] = [r[2] for r in exp_results]

    # 学历
    df['学历层级'] = df['学历要求'].apply(parse_education)

    # 统计
    print("\n--- 经验档位分布 ---")
    print(df['经验档位'].value_counts().sort_index())
    print(f"\n经验档位为「未知」: {len(df[df['经验档位'] == '未知'])} 条")
    print("\n--- 学历层级分布 ---")
    print(df['学历层级'].value_counts().sort_index())

    # 保存
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"\n✅ 输出保存: {OUTPUT_PATH}")
    print("Step 5 完成.")


if __name__ == '__main__':
    main()