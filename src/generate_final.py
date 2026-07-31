import pandas as pd
import numpy as np
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, 'data', 'interim', 'step6_text_clean.csv')
OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'jobs_clean.csv')

# 最终 Schema（严格对齐 cleaning_plan.md）
FINAL_COLUMNS = [
    # 标识与分类
    'job_id', '城市组', 'job_category', 'dup_count',
    # 原始字段（保留原样）
    '职位名称', '公司名称', '薪资', '经验要求', '学历要求',
    '公司性质', '公司规模', '发布时间', '详情链接',
    # 城市（Step 3）
    '城市', '城市等级', 'city_source',
    # 薪资（Step 4）
    '薪资下限(万)', '薪资上限(万)', '月薪中位(万)', '薪月数',
    '年薪中位(万)', 'is_intern',
    # 经验/学历（Step 5）
    '经验下限(年)', '经验上限(年)', '经验档位', '学历层级',
    # 文本（Step 6）
    '职位描述_clean', '任职要求_clean', '福利列表'
]


def main():
    print("=" * 60)
    print("生成最终数据: jobs_clean.csv")
    print("=" * 60)

    if not os.path.exists(INPUT_PATH):
        print(f"错误: 输入文件不存在: {INPUT_PATH}")
        sys.exit(1)

    df = pd.read_csv(INPUT_PATH, encoding='utf-8-sig')
    print(f"读取 step6: {len(df)} 行 × {len(df.columns)} 列")

    # ================= 7.31质检修正：终表三道收口 =================
    # 1) dup_count 语义统一：无重复记 1（原为 NaN/1 混用）
    df['dup_count'] = df['dup_count'].fillna(1)

    # 2) 跨搜索组残留重复：公司+职位+薪资+城市 相同只保留信息最全的一行
    df['_nonnull'] = df.notna().sum(axis=1)
    before = len(df)
    df = (df.sort_values('_nonnull', ascending=False)
            .drop_duplicates(subset=['职位名称', '公司名称', '薪资', '城市'],
                             keep='first')
            .drop(columns='_nonnull'))
    print(f"残留重复清理: 删除 {before - len(df)} 条")

    # 3) 剔除 noise，最终表只含 core + related
    #    （noise 保留在 step1/step2 中间文件，可溯源）
    before = len(df)
    df = df[df['job_category'] != 'noise'].reset_index(drop=True)
    print(f"noise 过滤: 移除 {before - len(df)} 条，保留 {len(df)} 条")
    # ================= 修正结束 =================

    # 生成 job_id（收口后再编号，保证连续）
    df['job_id'] = range(1, len(df) + 1)

    # 只保留最终 Schema 列，丢弃调试/中间列
    existing_cols = [c for c in FINAL_COLUMNS if c in df.columns]
    missing_cols = [c for c in FINAL_COLUMNS if c not in df.columns]

    if missing_cols:
        print(f"\n⚠️  Schema 中以下列在 step6 输出中不存在，已跳过: {missing_cols}")

    df_final = df[existing_cols].copy()

    # 保存
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df_final.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')

    # 7.31质检修正：终检输出
    print(f"\n✅ 最终数据保存: {OUTPUT_PATH}")
    print(f"   行数: {len(df_final)}")
    print(f"   列数: {len(df_final.columns)}")
    print(f"\n--- 终检 ---")
    print(f"job_category: {df_final['job_category'].value_counts().to_dict()}")
    print(f"经验档位「未知」: {(df_final['经验档位'] == '未知').sum()} 条")
    print(f"残留重复(公司+职位+薪资+城市): "
          f"{df_final.duplicated(subset=['职位名称', '公司名称', '薪资', '城市']).sum()} 条")
    print("生成完成.")


if __name__ == '__main__':
    main()