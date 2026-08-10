# -*- coding: utf-8 -*-
"""
01_data_overview.py — 数据概览
输入 : data/processed/jobs_clean.csv（终表 681×29）
输出 : docs/charts/0-1 ~ 0-4 共四张图（数据漏斗、经验/学历分布、发布月份、字段缺失率）
口径 : 全样本 n=681；薪资相关口径（n=671）在 salary_df() 中统一定义
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 中文显示与负号修正（字体在 set_style 时一并注入，防覆盖）
sns.set_style('whitegrid', {'font.sans-serif': ['Microsoft YaHei', 'SimHei']})
plt.rcParams['axes.unicode_minus'] = False

# 路径：notebook 位于 notebooks/ 下，数据与图表目录按项目结构定位
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

# ===== 全局图表样式（后续 notebook 复用）=====
MAIN = '#1B4F72'   # 深蓝：强调
MED = '#2E86C1'    # 品牌蓝：主色
RED = '#C0392B'    # 警示红：缺失/异常


def finish_fig(fig, title, note, path):
    """统一收尾：结论式标题(顶部加粗) + 口径脚注(底部灰色) + 保存 150dpi"""
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    fig.text(0.5, 0.005, note, ha='center', fontsize=9, color='gray')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.show()


# ===== 图0-1 数据漏斗 =====
fig, ax = plt.subplots(figsize=(8.5, 4))
stages = ['终表（core 313 + related 368）', '去重后', '原始采集']
vals = [681, 1270, 1495]
bars = ax.barh(stages, vals, color=[MAIN, '#5DADE2', '#AED6F1'], height=0.55)
for b, v in zip(bars, vals):
    ax.text(v + 18, b.get_y() + b.get_height() / 2,
            f'{v} 条（{v / vals[2] * 100:.0f}%）', va='center', fontsize=11)
ax.set_xlim(0, 1750)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, f'三级收敛：{vals[0] / vals[2] * 100:.0f}% 的采集数据进入最终分析集',
           '原始 1495 → 去重 1270（-225）→ 终表 681（noise 586 条剔除）',
           CHART_DIR + '/1-1_funnel.png')

# ===== 图0-2 经验/学历分布 =====
exp_order = ['应届/无需经验', '1-3年', '3-5年', '5-10年', '10年以上']
edu_map = {1: '高中及以下', 2: '大专', 3: '本科', 4: '硕士', 5: '博士'}
edu_order = ['高中及以下', '大专', '本科', '硕士', '博士']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.2))
ec = df['经验档位'].value_counts().reindex(exp_order).fillna(0).astype(int)
uc = df['学历层级'].map(edu_map).value_counts().reindex(edu_order).fillna(0).astype(int)
for ax, cnt, ttl in [(ax1, ec, '经验档位分布'), (ax2, uc, '学历层级分布')]:
    ax.barh(range(len(cnt)), cnt.values, color=MED, height=0.55)
    ax.set_yticks(range(len(cnt)), cnt.index)
    ax.invert_yaxis()
    for i, v in enumerate(cnt.values):
        ax.text(v + 5, i, str(v), va='center', fontsize=10)
    ax.set_xlim(0, cnt.max() * 1.18)
    ax.set_title(ttl, fontsize=12, pad=10)
    ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.06, 1, 0.9])
finish_fig(fig, '市场以 1-3 年经验、本科学历岗位为绝对主力',
           f'n=681｜学历缺失 {df["学历层级"].isna().sum()} 条',
           CHART_DIR + '/1-2_exp_edu.png')

# ===== 图0-3 发布月份分布 =====
t = pd.to_datetime(df['发布时间'], errors='coerce')
mc = t.dt.to_period('M').value_counts().sort_index()

fig, ax = plt.subplots(figsize=(10, 4.2))
ax.bar(mc.index.astype(str), mc.values, color=MED, width=0.55)
for x, v in zip(mc.index.astype(str), mc.values):
    ax.text(x, v + 4, str(v), ha='center', fontsize=10)
ax.set_ylim(0, mc.max() * 1.2)
ax.tick_params(axis='x', rotation=45)
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '在架岗位以 2026 年 6-7 月发布为主，岗位新鲜度高',
           f'n={int(mc.sum())}｜爬取时点（2026-07）仍在架岗位画像，不代表市场招聘量趋势',
           CHART_DIR + '/1-3_timeline.png')

# ===== 图0-4 关键字段缺失率 =====
key_cols = ['月薪中位(万)', '经验下限(年)', '学历层级',
            '职位描述_clean', '任职要求_clean', '福利列表']
mr = (df[key_cols].isna().mean() * 100).sort_values()
labels = [f'{c}（{df[c].isna().sum()} 条）' for c in mr.index]

fig, ax = plt.subplots(figsize=(8.5, 4))
bars = ax.barh(labels, mr.values,
               color=[RED if v > 10 else MED for v in mr.values], height=0.5)
for b, v in zip(bars, mr.values):
    ax.text(v + 0.5, b.get_y() + b.get_height() / 2, f'{v:.1f}%', va='center', fontsize=10)
ax.set_xlim(0, mr.max() * 1.25)
ax.set_xlabel('缺失率（%）')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout(rect=[0, 0.08, 1, 0.9])
finish_fig(fig, '核心字段基本完整，缺失集中在任职要求与福利文本',
           'n=681｜缺失集中于组4/组5 采集失败链接；文本类分析以有值样本为口径',
           CHART_DIR + '/1-4_missing.png')
