# -*- coding: utf-8 -*-
"""
02_city_analysis.py — 城市维度分析
输入 : data/processed/jobs_clean.csv
输出 : docs/charts/2-1 ~ 2-4 共四张图
口径 : 岗位量 n=681；薪资相关沿用 03 口径（n=671，中位数）
"""

# 全局设置与数据加载
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch

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
print(f'口径自检: n={len(s)}, 月薪中位={s["月薪中位(万)"].median():.2f} 万')

MAIN = '#1B4F72'
MED = '#2E86C1'
RED = '#C0392B'


def finish_fig(fig, title, note, path):
    """统一收尾：结论式标题(顶部加粗) + 口径脚注(底部灰色) + 保存 150dpi"""
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    fig.text(0.5, 0.005, note, ha='center', fontsize=9, color='gray')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.show()

# 图2-1 Top12 城市岗位量（一线城市标深蓝）
YIXIAN = {'上海', '北京', '深圳', '广州'}
top12 = df['城市'].value_counts().head(12)

fig, ax = plt.subplots(figsize=(9, 5))
colors = [MAIN if c in YIXIAN else MED for c in top12.index]
ax.barh(range(len(top12)), top12.values, color=colors, height=0.6)
ax.set_yticks(range(len(top12)), top12.index)
ax.invert_yaxis()
for i, v in enumerate(top12.values):
    ax.text(v + 1.5, i, str(v), va='center', fontsize=10)
ax.set_xlim(0, top12.max() * 1.15)
ax.set_xlabel('岗位数')
ax.legend(handles=[Patch(color=MAIN, label='一线城市'),
                   Patch(color=MED, label='新一线/二线城市')],
          loc='lower right', fontsize=10)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '岗位高度集中：上海一城占 18%，Top4 城市合计近一半',
           'n=681｜口径：爬取时点仍在架岗位；Top4 = 上海+苏州+深圳+成都',
           CHART_DIR + '/2-1_top_cities.png')

# 图2-2 城市等级环形图
tier = df.loc[df['城市等级'].isin(['一线', '新一线', '二线']), '城市等级'].value_counts()

fig, ax = plt.subplots(figsize=(6.5, 5))
wedges, _, autotexts = ax.pie(
    tier.values, labels=[f'{k}\n{v} 条' for k, v in tier.items()],
    colors=[MAIN, MED, '#AED6F1'], autopct='%.1f%%', pctdistance=0.78,
    startangle=90, counterclock=False,
    wedgeprops=dict(width=0.42, edgecolor='white', linewidth=2),
    textprops={'fontsize': 11})
for t in autotexts:
    t.set_color('white')
    t.set_fontweight('bold')
ax.text(0, 0, '城市等级\n岗位分布', ha='center', va='center',
        fontsize=13, fontweight='bold', color=MAIN)
plt.tight_layout(rect=[0, 0.06, 1, 0.9])
finish_fig(fig, '新一线城市是需求主力：占 55%，超过一线与二线之和',
           'n=674（城市等级未知/其他 7 条除外）｜一线=北上广深，新一线 14 城，二线 8 城',
           CHART_DIR + '/2-2_tier_donut.png')

# 图2-3 Top10 城市双轴图：柱=岗位量，线=中位薪资
top10 = df['城市'].value_counts().head(10)
cs = s[s['城市'].isin(top10.index)].groupby('城市')['月薪中位(万)'].median().reindex(top10.index)

fig, ax1 = plt.subplots(figsize=(11, 4.8))
ax1.bar(top10.index, top10.values, color='#AED6F1', width=0.55, label='岗位数（左轴）')
ax1.set_ylabel('岗位数')
ax1.set_ylim(0, 150)
ax2 = ax1.twinx()
ax2.plot(top10.index, cs.values, color=RED, lw=2, marker='D', ms=7, label='月薪中位（右轴）')
for x, v in zip(top10.index, cs.values):
    ax2.annotate(f'{v:.2f}', (x, v), textcoords='offset points', xytext=(0, 9),
                 ha='center', fontsize=10, fontweight='bold', color=RED)
ax2.set_ylabel('月薪中位（万）')
ax2.set_ylim(0, 1.6)
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper right', fontsize=10)
ax1.spines[['top']].set_visible(False)
ax2.spines[['top']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '机会与薪资错位：上海量最大，北京价最高，苏州量大价不低',
           '岗位量 n=681｜薪资 n=671 口径；右轴为各城市月薪中位数（万）',
           CHART_DIR + '/2-3_city_dual_axis.png')

# 图2-4 Top6 城市经验结构（100% 堆叠条）
EXP_ORDER = ['应届/无需经验', '1-3年', '3-5年', '5-10年', '10年以上']
EXP_COLORS = ['#AED6F1', '#5DADE2', MED, MAIN, '#0B2E4F']
top6 = df['城市'].value_counts().head(6).index
ct = pd.crosstab(df.loc[df['城市'].isin(top6), '城市'], df['经验档位']) \
       .reindex(index=top6, columns=EXP_ORDER).fillna(0)
pct = ct.div(ct.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(10, 4.8))
left = np.zeros(len(pct))
for col, c in zip(EXP_ORDER, EXP_COLORS):
    ax.barh(pct.index, pct[col], left=left, color=c, height=0.55, label=col)
    for i, v in enumerate(pct[col]):
        if v >= 8:  # 占比过小不标数字，防拥挤
            ax.text(left[i] + v / 2, i, f'{v:.0f}%', ha='center', va='center',
                    fontsize=9, color='white', fontweight='bold')
    left += pct[col].values
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xlabel('占比（%）')
ax.legend(ncol=5, loc='upper center', bbox_to_anchor=(0.5, 1.12), fontsize=9, frameon=False)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.88])
finish_fig(fig, '城市定位分化：东莞 1-3年 岗占 53%，成都 5-10年 资深岗占 28% 最高',
           f'n={int(ct.sum().sum())}（Top6 城市岗位）｜各城市经验档位构成 = 100%',
           CHART_DIR + '/2-4_city_exp_stack.png')
