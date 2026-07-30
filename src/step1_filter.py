import os
import pandas as pd
import re

# 自动定位项目根目录（脚本在 src/ 下）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE_DIR, 'data', 'raw', '51job_数据分析_完整版.csv')
OUT_PATH = os.path.join(BASE_DIR, 'data', 'interim', 'step1_filtered.csv')


def classify_job(title: str) -> str:
    """三层分桶，不删只打标"""
    t = str(title).lower()

    if re.search(r'数据分析|data analyst', t, re.I):
        return 'core'

    if re.search(r'数据|BI|经营分析|商业分析|数据运营|数据挖掘', t, re.I):
        return 'related'

    return 'noise'


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    df = pd.read_csv(RAW_PATH)
    print(f'[Step 1] 读取原始数据: {len(df)} 行')

    df['job_category'] = df['职位名称'].apply(classify_job)

    counts = df['job_category'].value_counts()
    print(f'  A 核心岗(core):       {counts.get("core", 0)} 条')
    print(f'  B 数据相关岗(related): {counts.get("related", 0)} 条')
    print(f'  C 噪音岗(noise):      {counts.get("noise", 0)} 条')

    df.to_csv(OUT_PATH, index=False, encoding='utf-8-sig')
    print(f'[Step 1] 已保存: {OUT_PATH}')


if __name__ == '__main__':
    main()
