# -*- coding: utf-8 -*-
"""
05_company_welfare.py — 公司性质与福利分析（可视化方案 nb05）
输入 : data/processed/jobs_clean.csv
输出 : docs/charts/5-1 ~ 5-3 共三张图
口径 : 分布 n=681；薪资 n=671 中位数口径；福利 n=522（字段可用岗位）
"""

# 全局设置与数据加载
import os
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


s = salary_df(df)
MAIN = '#1B4F72'
MED = '#2E86C1'
RED = '#C0392B'


def finish_fig(fig, title, note, path):
    """统一收尾：结论式标题(顶部加粗) + 口径脚注(底部灰色) + 保存 150dpi"""
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    fig.text(0.5, 0.005, note, ha='center', fontsize=9, color='gray')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.show()

# 图5-1 公司性质分布（小类合并为"其他"）
nt = df['公司性质'].value_counts()
nt2 = pd.concat([nt[nt >= 20], pd.Series({'其他（事业/非营利/创业）': nt[nt < 20].sum()})])

fig, ax = plt.subplots(figsize=(9, 4.5))
colors = [MED] * len(nt2)
colors[0] = MAIN
ax.bar(nt2.index, nt2.values, color=colors, width=0.55)
for i, v in enumerate(nt2.values):
    ax.text(i, v + 5, f'{v}\n({v / 681 * 100:.0f}%)', ha='center', fontsize=10)
ax.set_ylim(0, nt2.max() * 1.2)
ax.set_ylabel('岗位数')
ax.tick_params(axis='x', rotation=15)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '民营企业是绝对主力：占 54%，上市+国企+外资合计约 40%',
           'n=681｜其他 = 事业单位 4 + 非营利组织 3 + 创业公司 2',
           CHART_DIR + '/5-1_company_type.png')

# 图5-2 公司性质 × 薪资（仅 n≥20 下结论）
st = s.groupby('公司性质')['月薪中位(万)'].agg(['size', 'median'])
st = st[st['size'] >= 20].sort_values('median')

fig, ax = plt.subplots(figsize=(9, 4.5))
colors = [MAIN if v == st['median'].max() else MED for v in st['median']]
ax.barh(st.index, st['median'], color=colors, height=0.55)
for i, (idx, r) in enumerate(st.iterrows()):
    ax.text(r['median'] + 0.02, i, f"{r['median']:.2f}（n={int(r['size'])}）",
            va='center', fontsize=10)
ax.axvline(1.15, color=RED, ls='--', lw=1.2)
ax.text(1.155, len(st) - 0.7, '总体中位 1.15', color=RED, fontsize=9)
ax.set_xlim(0, 1.75)
ax.set_xlabel('月薪中位（万）')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '国企薪资最高（1.38 万），民企低于总体水平',
           'n=671 薪资口径｜仅展示 n≥20 的类型；红虚线为总体中位数',
           CHART_DIR + '/5-2_company_salary.png')

# 图5-3 福利 Top10
wel = df['福利列表'].dropna().str.split('|').explode().str.strip()
wt = wel.value_counts().head(10)
n_wel = int(df['福利列表'].notna().sum())

fig, ax = plt.subplots(figsize=(9, 5))
colors = [MAIN if i == 0 else MED for i in range(len(wt))]
ax.barh(range(len(wt)), wt.values, color=colors, height=0.6)
ax.set_yticks(range(len(wt)), wt.index)
ax.invert_yaxis()
for i, v in enumerate(wt.values):
    ax.text(v + 4, i, f'{v}（{v / n_wel * 100:.0f}%）', va='center', fontsize=10)
ax.set_xlim(0, wt.max() * 1.22)
ax.set_xlabel('提及岗位数')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '五险一金覆盖率 83%，奖金与年假是第二梯队',
           f'n={n_wel}（福利字段可用的岗位）｜单条记录提及即计 1',
           CHART_DIR + '/5-3_welfare_top10.png')
