# -*- coding: utf-8 -*-
"""
06_core_vs_related.py — 核心岗 vs 泛数据岗对比 + 综合结论
输入 : data/processed/jobs_clean.csv
输出 : docs/charts/6-1 ~ 6-3 共三张图 + docs/aggregates/ 聚合 CSV
口径 : 薪资 n=671 中位数口径；分布对比 n=681
"""

# 全局设置与数据加载
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

sns.set_style('whitegrid', {'font.sans-serif': ['Microsoft YaHei', 'SimHei']})
plt.rcParams['axes.unicode_minus'] = False

BASE = '../'
CHART_DIR = os.path.join(BASE, 'docs', 'charts')
AGG_DIR = os.path.join(BASE, 'docs', 'aggregates')
os.makedirs(CHART_DIR, exist_ok=True)
os.makedirs(AGG_DIR, exist_ok=True)

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

# 统计验证：Mann-Whitney U 检验
a = s.loc[s['job_category'] == 'core', '月薪中位(万)']
b = s.loc[s['job_category'] == 'related', '月薪中位(万)']
g = s.groupby('job_category')['月薪中位(万)']
cr = pd.DataFrame({'n': g.size(), 'P25': g.quantile(.25),
                   '中位': g.median(), 'P75': g.quantile(.75)})
print(cr.round(3))
u = stats.mannwhitneyu(a, b, alternative='two-sided')
print(f'Mann-Whitney U: statistic={u.statistic:.0f}, p={u.pvalue:.3f}')
print('解读: p>0.05 → 两组分布无显著差异；但 P25 差 13%，核心岗下限更高')

# 图6-1 薪资分布对比（重叠直方图）
fig, ax = plt.subplots(figsize=(9.5, 4.5))
bins = np.arange(0, 4.5, 0.15)
ax.hist(a, bins=bins, alpha=0.55, color=MAIN, density=True, label=f'core 核心岗（n={len(a)}）')
ax.hist(b, bins=bins, alpha=0.55, color='#E67E22', density=True, label=f'related 泛数据岗（n={len(b)}）')
ax.axvline(1.15, color=RED, ls='--', lw=1.5)
ax.text(1.17, ax.get_ylim()[1] * 0.85, '两组中位数均为 1.15 万', color=RED, fontsize=10)
ax.set_xlabel('月薪中位（万）')
ax.set_ylabel('密度')
ax.legend(fontsize=10)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '核心岗与泛数据岗定价无显著差异（Mann-Whitney p=0.14）',
           'n=671 薪资口径｜密度直方图；core 309 条，related 362 条',
           CHART_DIR + '/6-1_core_vs_related_dist.png')

# 图6-2 分位数分组对比
fig, ax = plt.subplots(figsize=(8.5, 4.5))
x = np.arange(2)
w = 0.25
for j, col in enumerate(['P25', '中位', 'P75']):
    bars = ax.bar(x + (j - 1) * w, cr[col], width=w,
                  label={'P25': 'P25', '中位': '中位数', 'P75': 'P75'}[col],
                  color=['#AED6F1', MED, MAIN][j])
    for bb in bars:
        ax.text(bb.get_x() + bb.get_width() / 2, bb.get_height() + 0.02,
                f'{bb.get_height():.2f}', ha='center', fontsize=10)
ax.set_xticks(x, ['core 核心岗', 'related 泛数据岗'])
ax.set_ylabel('月薪（万）')
ax.set_ylim(0, 1.9)
ax.legend(fontsize=10)
ax.annotate('P25 差 13%：核心岗薪资下限更高', xy=(0.35, 0.9),
            fontsize=10, color=RED, fontweight='bold')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '中位数相同，但核心岗 P25 高 13%：薪资底线更有保障',
           'n=671 薪资口径｜P25/P75 为四分位；Mann-Whitney p=0.14 整体分布无显著差异',
           CHART_DIR + '/6-2_quantile_compare.png')

# 图6-3 经验结构对比（100% 堆叠条）
EXP_ORDER = ['应届/无需经验', '1-3年', '3-5年', '5-10年', '10年以上']
EXP_COLORS = ['#AED6F1', '#5DADE2', MED, MAIN, '#0B2E4F']
ct6 = pd.crosstab(df['job_category'], df['经验档位']).reindex(columns=EXP_ORDER).fillna(0)
pct6 = ct6.div(ct6.sum(axis=1), axis=0) * 100

fig, ax = plt.subplots(figsize=(9.5, 3.8))
left = np.zeros(len(pct6))
for col, c in zip(EXP_ORDER, EXP_COLORS):
    ax.barh(pct6.index, pct6[col], left=left, color=c, height=0.45, label=col)
    for i, v in enumerate(pct6[col]):
        if v >= 7:
            ax.text(left[i] + v / 2, i, f'{v:.0f}%', ha='center', va='center',
                    fontsize=9, color='white', fontweight='bold')
    left += pct6[col].values
ax.set_xlim(0, 100)
ax.set_xlabel('占比（%）')
ax.legend(ncol=5, loc='upper center', bbox_to_anchor=(0.5, 1.25), fontsize=9, frameon=False)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.1, 1, 0.85])
finish_fig(fig, '核心岗与泛数据岗经验结构几乎一致：1-5 年经验均占约 70%',
           f'n=681｜core {int(ct6.loc["core"].sum())} 条，related {int(ct6.loc["related"].sum())} 条；岗位名称 ≠ 实际要求',
           CHART_DIR + '/6-3_exp_structure_compare.png')

# 聚合数据表导出（README 引用素材）
EDU_MAP = {1: '高中及以下', 2: '大专', 3: '本科', 4: '硕士', 5: '博士'}
g_exp = s.groupby('经验档位')['月薪中位(万)']
g_edu = s.assign(学历=s['学历层级'].map(EDU_MAP)).groupby('学历')['月薪中位(万)']
g_city = s[s['城市等级'].isin(['一线', '新一线', '二线'])].groupby('城市等级')['月薪中位(万)']

def qtbl(gg):
    return pd.DataFrame({'n': gg.size(), 'P25': gg.quantile(.25),
                         '中位': gg.median(), 'P75': gg.quantile(.75)}).round(3)

qtbl(g_exp).reindex(EXP_ORDER).to_csv(AGG_DIR + '/salary_by_experience.csv', encoding='utf-8-sig')
qtbl(g_edu).reindex(['高中及以下', '大专', '本科', '硕士']) \
           .to_csv(AGG_DIR + '/salary_by_education.csv', encoding='utf-8-sig')
qtbl(g_city).reindex(['一线', '新一线', '二线']).to_csv(AGG_DIR + '/salary_by_city_tier.csv', encoding='utf-8-sig')
cr.round(3).to_csv(AGG_DIR + '/core_vs_related_salary.csv', encoding='utf-8-sig')
print('聚合 CSV 导出完成 →', AGG_DIR)
