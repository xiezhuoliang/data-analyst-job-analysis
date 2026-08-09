import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style('whitegrid')

BASE = '../'  # notebook 在 notebooks/ 下
df = pd.read_csv(BASE + 'data/processed/jobs_clean.csv', encoding='utf-8-sig')

# 薪资口径：剔除 26-37万 极值(>15万) + 剔除实习岗
def salary_df(data=df):
    return data[data['月薪中位(万)'].notna()
           & (data['月薪中位(万)'] < 15)
           & (data['is_intern'] != 1)].copy()

def footnote(ax, n, extra=''):
    """统一口径脚注"""
    ax.set_xlabel(f'n={n}｜薪资为月薪中位(万)，已剔除极值与实习岗{("｜"+extra) if extra else ""}',
                  fontsize=9, color='gray')

s = salary_df()
print(len(s), s['月薪中位(万)'].median().round(2))
