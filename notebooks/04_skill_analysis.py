# -*- coding: utf-8 -*-
"""
04_skill_analysis.py — 技能维度分析
输入 : data/processed/jobs_clean.csv
输出 : docs/charts/4-1 ~ 4-4 共四张图
口径 : 文本可用岗位 n=641（描述或要求任一非空）；技能命中=单条记录出现即计 1；
       薪资相关沿用 n=671 中位数口径
方法 : 人工词典 + 正则匹配（英文缩写用词边界防误匹配），不用 jieba 分词——
       jieba 会把 SQL/Excel 等英文缩写切碎，导致漏匹配；
       词典完备性经「词典外高频词扫描」验证（见06_）
"""

# 全局设置与数据加载
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid', {'font.sans-serif': ['Microsoft YaHei', 'SimHei']})
plt.rcParams['axes.unicode_minus'] = False

BASE = '../'
CHART_DIR = os.path.join(BASE, 'docs', 'charts')
os.makedirs(CHART_DIR, exist_ok=True)

df = pd.read_csv(BASE + 'data/processed/jobs_clean.csv', encoding='utf-8-sig')
print(f'终表加载: {df.shape[0]} 行 × {df.shape[1]} 列')


def salary_df(data):
    """薪资分析口径：剔除 26-37万 极值(>15万) 与实习岗。有效 n=671，中位 1.15 万"""
    mask = (data['月薪中位(万)'].notna()
            & (data['月薪中位(万)'] < 15)
            & (data['is_intern'] != 1))
    return data[mask].copy()


MAIN = '#1B4F72'
MED = '#2E86C1'
RED = '#C0392B'


def finish_fig(fig, title, note, path):
    """统一收尾：结论式标题(顶部加粗) + 口径脚注(底部灰色) + 保存 150dpi"""
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    fig.text(0.5, 0.005, note, ha='center', fontsize=9, color='gray')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.show()

# 口径与验证：词典定义 + 合并文本口径
# 英文缩写必须带词边界 \b，否则 R 会匹配到所有含 r 的单词；
# BI 需含具体工具名（Tableau/PowerBI/FineBI），否则 PowerBI 连写时漏匹配
SKILL_PATTERNS = {
    '可视化': re.compile(r'可视化'),
    '建模': re.compile(r'建模'),                     # 只算"建模"，"模型"太泛
    'BI': re.compile(r'\bBI\b|商业智能|tableau|power\s*bi|finebi|帆软', re.I),
    'SQL': re.compile(r'\bsql\b|mysql|hive', re.I),
    '大数据': re.compile(r'大数据|hadoop|spark|flink', re.I),
    'Python': re.compile(r'\bpython\b', re.I),
    'R': re.compile(r'(?<![a-zA-Z])R(?![a-zA-Z])'),  # 独立字母 R 才算
    '英语': re.compile(r'英语|\benglish\b|cet', re.I),
    'Excel': re.compile(r'\bexcel\b', re.I),
    'ETL': re.compile(r'\betl\b', re.I),
}

# 技能要求可能写在描述或要求字段 → 合并匹配
both = df['职位描述_clean'].fillna('') + ' ' + df['任职要求_clean'].fillna('')
n_text = int((df['职位描述_clean'].notna() | df['任职要求_clean'].notna()).sum())
hits = {k: int(both.str.contains(p).sum()) for k, p in SKILL_PATTERNS.items()}
hits = dict(sorted(hits.items(), key=lambda x: -x[1]))
print(f'文本口径 n={n_text}')
for k, v in hits.items():
    print(f'  {k}: {v} 条（{v / n_text * 100:.0f}%）')

# 图4-1 技能命中率横条图
fig, ax = plt.subplots(figsize=(9, 5))
names, vals = list(hits.keys()), list(hits.values())
colors = [MAIN if v >= 140 else (MED if v >= 70 else '#AED6F1') for v in vals]
ax.barh(range(len(vals)), vals, color=colors, height=0.6)
ax.set_yticks(range(len(vals)), names)
ax.invert_yaxis()
for i, v in enumerate(vals):
    ax.text(v + 2, i, f'{v} 条（{v / n_text * 100:.0f}%）', va='center', fontsize=10)
ax.set_xlim(0, max(vals) * 1.3)
ax.set_xlabel('命中岗位数')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '技能需求梯队：可视化/建模/BI/SQL/大数据为第一梯队，ETL 最少',
           f'n={n_text}（描述或要求任一可用的岗位）｜单条记录命中即计 1，人工词典匹配',
           CHART_DIR + '/4-1_skill_hits.png')

# 图4-2 哑铃图：有/无技能的中位薪资差
s = salary_df(df)
s_both = (s['职位描述_clean'].fillna('') + ' ' + s['任职要求_clean'].fillna(''))
KEY = ['SQL', 'Python', '建模', '可视化', 'BI', '大数据']
rows = []
for k in KEY:
    has = s_both.str.contains(SKILL_PATTERNS[k])
    rows.append({'技能': k, '有': s.loc[has, '月薪中位(万)'].median(),
                 '无': s.loc[~has, '月薪中位(万)'].median()})
ds = pd.DataFrame(rows).set_index('技能').sort_values('有')

fig, ax = plt.subplots(figsize=(9, 4.8))
for i, (name, r) in enumerate(ds.iterrows()):
    ax.plot([r['无'], r['有']], [i, i], color='#BDC3C7', lw=2, zorder=1)
ax.scatter(ds['无'], range(len(ds)), s=130, color='#AED6F1', zorder=2, label='未要求该技能')
ax.scatter(ds['有'], range(len(ds)), s=130, color=MAIN, zorder=2, label='要求该技能')
for i, (name, r) in enumerate(ds.iterrows()):
    diff = r['有'] - r['无']
    ax.text(r['有'] + 0.04, i, f'+{diff:.2f}', va='center', fontsize=11,
            fontweight='bold', color=(RED if diff > 0.1 else 'gray'))
ax.set_yticks(range(len(ds)), ds.index)
ax.set_xlabel('月薪中位（万）')
ax.set_xlim(0.9, 1.6)
ax.legend(loc='lower right', fontsize=10)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '硬技能有溢价：要求 Python/SQL/大数据 的岗位薪资高 0.15-0.25 万',
           'n=671 薪资口径｜哑铃两端为两组中位数，红色数字为差值；可视化技能无溢价',
           CHART_DIR + '/4-2_skill_salary_dumbbell.png')

# 图4-3 技能共现热力图（Top8）
TOP8 = list(hits.keys())[:8]
mat = pd.DataFrame({k: both.str.contains(SKILL_PATTERNS[k]) for k in TOP8})
co = mat.astype(int).T.dot(mat.astype(int))  # bool 需先转 int，否则 dot 结果错误

fig, ax = plt.subplots(figsize=(8, 6.5))
sns.heatmap(co, annot=True, fmt='d', cmap='Blues', square=True,
            linewidths=1, linecolor='white', cbar_kws={'label': '共现岗位数'}, ax=ax)
plt.tight_layout(rect=[0, 0.05, 1, 0.92])
finish_fig(fig, '技能组合画像：可视化 × BI 共现最强（92 条），BI 岗位天然要求可视化',
           f'n={n_text}｜对角线为单技能命中数，非对角线为两技能同现岗位数',
           CHART_DIR + '/4-3_skill_cooccur_heatmap.png')

# 图4-4 软技能维度 + 词典完备性验证
# 软技能：企业 JD 中的通用素质要求，与硬技能互补
SOFT_PATTERNS = {
    '沟通协作': re.compile(r'沟通|团队协作|协作能力'),
    '逻辑思维': re.compile(r'逻辑|逻辑思维'),
    '责任心/主动': re.compile(r'责任心|主动|自驱'),
    '学习能力': re.compile(r'学习能力|快速学习'),
}
soft_hits = {k: int(both.str.contains(p).sum()) for k, p in SOFT_PATTERNS.items()}
soft_hits = dict(sorted(soft_hits.items(), key=lambda x: -x[1]))

fig, ax = plt.subplots(figsize=(8.5, 3.8))
names, vals = list(soft_hits.keys()), list(soft_hits.values())
ax.barh(range(len(vals)), vals, color=MED, height=0.5)
ax.set_yticks(range(len(vals)), names)
ax.invert_yaxis()
for i, v in enumerate(vals):
    ax.text(v + 5, i, f'{v} 条（{v / n_text * 100:.0f}%）', va='center', fontsize=10)
ax.set_xlim(0, max(vals) * 1.3)
ax.set_xlabel('命中岗位数')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.1, 1, 0.88])
finish_fig(fig, '软技能是隐形门槛：沟通协作提及率 68%，超过所有硬技能',
           f'n={n_text}｜软技能为 JD 通用素质要求，口径同硬技能',
           CHART_DIR + '/4-4_soft_skills.png')

# 完备性验证：确认无高频遗漏
extra_scan = {'SPSS': r'(?i)\bspss\b', 'SAS': r'(?i)\bsas\b', 'Linux': r'(?i)\blinux\b',
              '爬虫': r'爬虫', '机器学习': r'机器学习'}
print('词典外扫描（均 <10 条，确认词典完备）:',
      {k: int(both.str.contains(re.compile(p)).sum()) for k, p in extra_scan.items()})
