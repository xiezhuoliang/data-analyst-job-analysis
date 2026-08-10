# -*- coding: utf-8 -*-
"""
03_salary_analysis.py — 薪资维度分析
输入 : data/processed/jobs_clean.csv
输出 : docs/charts/3-1 ~ 3-4 共四张图
口径 : 剔除 26-37万 极值与实习岗，n=671，结论一律用中位数
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


# 口径自检（应输出 n=671, 中位 1.15，对不上先停手查数据）
_s = salary_df(df)
print(f'口径自检: n={len(_s)}, 月薪中位={_s["月薪中位(万)"].median():.2f} 万')

MAIN = '#1B4F72'   # 深蓝：强调
MED = '#2E86C1'    # 品牌蓝：主色
RED = '#C0392B'    # 警示红：缺失/异常


def finish_fig(fig, title, note, path):
    """统一收尾：结论式标题(顶部加粗) + 口径脚注(底部灰色) + 保存 150dpi"""
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    fig.text(0.5, 0.005, note, ha='center', fontsize=9, color='gray')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.show()

# 验证：用中位数而非均值
s = salary_df(df)
sal = s['月薪中位(万)']
full = df.loc[df['月薪中位(万)'].notna() & (df['is_intern'] != 1), '月薪中位(万)']
out = full[full >= 15]

print(f'分析口径: n={len(s)}, 中位={sal.median():.2f} 万, 均值={sal.mean():.2f} 万, 偏度={sal.skew():.2f}')
print(f'P25={sal.quantile(.25):.2f}, P75={sal.quantile(.75):.2f}, P90={sal.quantile(.9):.2f} 万')
print(f'极值行: {out.tolist()} 万')
print(f'剔除极值: 均值 {full.mean():.3f} → {full.drop(out.index).mean():.3f}'
      f'（{(full.drop(out.index).mean() / full.mean() - 1) * 100:.1f}%）,'
      f' 中位 {full.median():.3f} → {full.drop(out.index).median():.3f}（不变）')

# 图3-1 薪资分布直方图：中位 vs 均值
fig, ax = plt.subplots(figsize=(9.5, 4.5))
ax.hist(sal, bins=np.arange(0, 4.5, 0.15), color=MED, edgecolor='white', linewidth=0.5)
ax.axvline(sal.median(), color=MAIN, lw=2, label=f'中位数 {sal.median():.2f} 万')
ax.axvline(sal.mean(), color=RED, lw=1.5, ls='--', label=f'均值 {sal.mean():.2f} 万（右偏拉高）')
ax.legend(fontsize=10)
ax.set_xlabel('月薪中位（万）')
ax.set_ylabel('岗位数')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '薪资分布明显右偏：中位数 1.15 万比均值更代表典型水平',
           'n=671｜口径：剔除 1 条 26-37万 极值与实习岗；偏度 2.64，P90=2.15 万',
           CHART_DIR + '/3-1_salary_dist.png')

# 图3-2 经验 × 薪资带宽图（旗舰图）
EXP_ORDER = ['应届/无需经验', '1-3年', '3-5年', '5-10年', '10年以上']
g = s.groupby('经验档位')['月薪中位(万)']
exp_stat = pd.DataFrame({'n': g.size(), 'P25': g.quantile(.25),
                         '中位': g.median(), 'P75': g.quantile(.75)}).reindex(EXP_ORDER)

fig, ax = plt.subplots(figsize=(9.5, 5))
x = np.arange(len(exp_stat))
ax.fill_between(x, exp_stat['P25'], exp_stat['P75'], color=MED, alpha=0.25, label='P25-P75 薪资带')
ax.plot(x, exp_stat['中位'], color=MAIN, lw=2.5, marker='o', ms=8, label='中位数')
for i, (idx, r) in enumerate(exp_stat.iterrows()):
    ax.annotate(f"{r['中位']:.2f}", (i, r['中位']), textcoords='offset points',
                xytext=(0, 10), ha='center', fontsize=11, fontweight='bold', color=MAIN)
    ax.text(i, exp_stat['P25'].min() * 0.55, f"n={int(r['n'])}", ha='center', fontsize=9, color='gray')
ax.set_xticks(x, exp_stat.index)
ax.set_ylabel('月薪中位（万）')
ax.set_ylim(0, 4)
ax.legend(loc='upper left', fontsize=10)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '经验是最强薪资杠杆：中位数从 0.75 万增至 2.92 万，涨幅近 3 倍',
           'n=671｜薪资口径：剔除极值与实习岗；色带为 P25-P75，点为各档中位数',
           CHART_DIR + '/3-2_exp_salary_band.png')

# 图3-3 学历 × 薪资
EDU_MAP = {1: '高中及以下', 2: '大专', 3: '本科', 4: '硕士', 5: '博士'}
s2 = s.assign(学历标签=s['学历层级'].map(EDU_MAP))
edu_stat = s2.groupby('学历标签')['月薪中位(万)'].agg(['size', 'median']) \
             .reindex(['高中及以下', '大专', '本科', '硕士'])

fig, ax = plt.subplots(figsize=(8.5, 4.5))
bars = ax.bar(edu_stat.index, edu_stat['median'],
              color=['#AED6F1', '#5DADE2', MED, MAIN], width=0.55)
for b, (idx, r) in zip(bars, edu_stat.iterrows()):
    ax.text(b.get_x() + b.get_width() / 2, r['median'] + 0.03, f"{r['median']:.2f}",
            ha='center', fontsize=12, fontweight='bold', color=MAIN)
    ax.text(b.get_x() + b.get_width() / 2, 0.06, f"n={int(r['size'])}",
            ha='center', fontsize=9, color='white')
for i in [1, 2]:  # 大专→本科→硕士 递增幅度
    inc = (edu_stat['median'].iloc[i + 1] / edu_stat['median'].iloc[i] - 1) * 100
    ax.annotate(f'+{inc:.0f}%', xy=(i + 0.5, edu_stat['median'].iloc[i + 1] + 0.18),
                ha='center', fontsize=10, color=RED)
ax.set_ylim(0, 1.8)
ax.set_ylabel('月薪中位（万）')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '学历溢价清晰：本科较大专 +60%，硕士再 +21%',
           'n=663（学历缺失 8 条除外）｜高中及以下仅 4 条，仅供参考；博士岗位 0 条',
           CHART_DIR + '/3-3_edu_salary.png')

# 图3-4 城市等级 × 薪资（箱线 + 散点）
CITY_ORDER = ['一线', '新一线', '二线']
s3 = s[s['城市等级'].isin(CITY_ORDER)]

fig, ax = plt.subplots(figsize=(9, 4.8))
sns.boxplot(data=s3, x='城市等级', y='月薪中位(万)', order=CITY_ORDER,
            color='#AED6F1', width=0.45, fliersize=0, ax=ax)
sns.stripplot(data=s3, x='城市等级', y='月薪中位(万)', order=CITY_ORDER,
              color=MAIN, size=2.5, alpha=0.25, jitter=0.25, ax=ax)
meds = s3.groupby('城市等级')['月薪中位(万)'].median().reindex(CITY_ORDER)
for i, v in enumerate(meds):
    ax.text(i, 3.9, f'中位 {v:.2f}', ha='center', fontsize=10, fontweight='bold', color=MAIN)
ax.set_ylim(0, 4.3)
ax.set_ylabel('月薪中位（万）')
ax.set_xlabel('')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '一线城市薪资领先：中位 1.25 万，较新一线高 19%',
           'n=666（城市等级未知 5 条除外）｜箱线为四分位，散点为各岗位真实分布',
           CHART_DIR + '/3-4_city_tier_salary.png')
