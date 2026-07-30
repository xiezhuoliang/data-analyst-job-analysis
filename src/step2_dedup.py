import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_PATH = os.path.join(BASE_DIR, 'data', 'interim', 'step1_filtered.csv')
OUT_PATH = os.path.join(BASE_DIR, 'data', 'interim', 'step2_deduped.csv')


def normalize_company(name: str) -> str:
    s = str(name).strip()
    s = s.replace('（', '(').replace('）', ')')
    s = s.replace(' ', '')
    return s


def normalize_job(title: str) -> str:
    return str(title).strip().replace(' ', '')


def dedup_bucket(df_bucket: pd.DataFrame, keep_dup_count: bool = True) -> pd.DataFrame:
    df = df_bucket.copy()
    df['__company_norm'] = df['公司名称'].apply(normalize_company)
    df['__job_norm'] = df['职位名称'].apply(normalize_job)
    df['__desc_short'] = df['职位描述'].astype(str).str[:100]

    group_cols = ['__company_norm', '__job_norm', '薪资', '__desc_short']
    df['dup_count'] = df.groupby(group_cols)['职位名称'].transform('count')

    df = df.drop_duplicates(subset=group_cols, keep='first')

    if not keep_dup_count:
        df = df.drop(columns=['dup_count'])

    df = df.drop(columns=[c for c in df.columns if c.startswith('__')])
    return df


def main():
    df = pd.read_csv(IN_PATH)
    print(f'[Step 2] 读取: {len(df)} 行')

    df_a = df[df['job_category'] == 'core'].copy()
    df_b = df[df['job_category'] == 'related'].copy()
    df_c = df[df['job_category'] == 'noise'].copy()

    print(f'  A桶(core)     去重前: {len(df_a)}')
    print(f'  B桶(related)  去重前: {len(df_b)}')
    print(f'  C桶(noise)    去重前: {len(df_c)}')

    df_a_dedup = dedup_bucket(df_a, keep_dup_count=True)
    df_b_dedup = dedup_bucket(df_b, keep_dup_count=True)
    df_c_dedup = dedup_bucket(df_c, keep_dup_count=False)

    print(f'  A桶(core)     去重后: {len(df_a_dedup)}')
    print(f'  B桶(related)  去重后: {len(df_b_dedup)}')
    print(f'  C桶(noise)    去重后: {len(df_c_dedup)}')

    df_out = pd.concat([df_a_dedup, df_b_dedup, df_c_dedup], ignore_index=True)
    print(f'[Step 2] 合并输出: {len(df_out)} 行')

    df_out.to_csv(OUT_PATH, index=False, encoding='utf-8-sig')
    print(f'[Step 2] 已保存: {OUT_PATH}')


if __name__ == '__main__':
    main()
