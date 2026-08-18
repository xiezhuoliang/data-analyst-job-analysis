<div align="center">

<img src="docs/assets/banner.png" alt="数据分析师岗位招聘市场画像分析" width="100%">

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![pandas](https://img.shields.io/badge/pandas-2.0%2B-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.0%2B-43B02A?logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![matplotlib](https://img.shields.io/badge/matplotlib-3.7%2B-1B4F72)](https://matplotlib.org/)
[![last commit](https://img.shields.io/github/last-commit/xiezhuoliang/data-analyst-job-analysis)](https://github.com/xiezhuoliang/data-analyst-job-analysis/commits/main)

**从前程无忧 26 城 681 条在架岗位出发，回答一个问题：2026 年的数据分析岗，在招什么人、开什么价**

</div>

## 核心结论一览

| # | 结论 | 关键数字 |
|---|---|---|
| 1 | 月薪中位 1.15 万，分布右偏，全项目以中位数为准 | n=671，偏度 2.64 |
| 2 | 经验是最强薪资杠杆 | 应届 0.75 万 → 10 年以上 2.92 万，近 3 倍 |
| 3 | 学历溢价清晰，本科是绝对主力 | 本科较大专 +60%，硕士再 +21%；本科占 76% |
| 4 | 城市「量价错位」，新一线贡献过半需求 | 上海量最大（18%），北京价最高（1.35 万），新一线占 55.8% |
| 5 | 硬技能有溢价，软技能是隐形门槛 | Python/SQL/大数据 溢价 0.15-0.25 万；沟通协作提及率 68% |
| 6 | 核心岗与泛数据岗定价无显著差异 | Mann-Whitney p=0.14；核心岗 P25 高 13% |

## 精选图表

<table>
  <tr>
    <td><img src="docs/charts/3-2_exp_salary_band.png" alt="经验×薪资带宽图" width="100%"></td>
    <td><img src="docs/charts/3-1_salary_dist.png" alt="薪资分布直方图" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><sub><b>经验 × 薪资带宽</b>｜越资深分化越大，谈薪空间越宽</sub></td>
    <td align="center"><sub><b>薪资分布</b>｜明显右偏，中位数比均值更可靠</sub></td>
  </tr>
  <tr>
    <td><img src="docs/charts/2-3_city_dual_axis.png" alt="城市双轴图" width="100%"></td>
    <td><img src="docs/charts/3-3_edu_salary.png" alt="学历×薪资" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><sub><b>城市量价错位</b>｜上海量最大，北京价最高，苏州量大价不低</sub></td>
    <td align="center"><sub><b>学历溢价</b>｜本科是分水岭，较大专 +60%</sub></td>
  </tr>
  <tr>
    <td><img src="docs/charts/4-1_skill_hits.png" alt="技能命中率" width="100%"></td>
    <td><img src="docs/charts/4-2_skill_salary_dumbbell.png" alt="技能×薪资哑铃图" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><sub><b>技能梯队</b>｜可视化/建模/BI/SQL/大数据为第一梯队</sub></td>
    <td align="center"><sub><b>技能溢价</b>｜Python/SQL/大数据 +0.15-0.25 万，可视化已无溢价</sub></td>
  </tr>
  <tr>
    <td><img src="docs/charts/4-4_soft_skills.png" alt="软技能" width="100%"></td>
    <td><img src="docs/charts/6-2_quantile_compare.png" alt="核心岗分位数对比" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><sub><b>软技能是隐形门槛</b>｜沟通协作提及率 68%，超过所有硬技能</sub></td>
    <td align="center"><sub><b>核心岗 vs 泛数据岗</b>｜定价无显著差异，别看 title 看 JD</sub></td>
  </tr>
</table>

## 方法论亮点

- **口径验证先行**：每个维度先做口径验证再下结论（如中位数三连证：偏度检验 → 极值敏感度实验 → 定口径）
- **词典完备性验证**：人工词典 + 正则词边界提取技能，再用「词典外高频词扫描」兜底——Tableau/PowerBI 由此补入，BI 命中从 85 修正到 151
- **结论式标题 + 数据回核**：每张图标题是一句结论，n 和口径统一放脚注，标题中每个数字都能在图上指出
- **阴性结果如实呈现**：核心岗对比无显著差异（p=0.14），如实报告并给出解释，不硬凑差异
- **全流程可复现**：`run_all.py` 一键从原始数据重建终表；两轮质检 + 六项终检全部留档

## 文档导航

- [分析报告](docs/analysis_report.md)：完整分析结论与建议
- [质检报告](docs/quality_report.md)：两轮质检 + 六项终检
- [清洗方案](docs/cleaning_plan.md)：6 步清洗管线的设计与口径定义
- [可视化方案](docs/visualization_plan.md)：6 大主题 22 图的设计与口径规则
- [开发日志](docs/logs/)：2026-07-24 ~ 2026-08-14 逐日记录

<details>
<summary><b>数据说明与口径</b></summary>

| 项 | 说明 |
|---|---|
| 来源 | 前程无忧（51job）公开招聘页面，仅供学习研究 |
| 采集窗口 | 2026-07，爬取时点仍在架的岗位（非市场招聘量趋势） |
| 范围 | 26 个城市（一线 4 + 新一线 14 + 二线 8），关键词「数据分析」 |
| 数据量 | 原始 1495 条 → 去重 1270 条 → 终表 681 条 × 29 列（core 313 + related 368） |
| 新鲜度 | 在架岗位以 2026 年 6-7 月发布为主 |
| 薪资口径 | 月薪中位（万），剔除 1 条 26-37万 极值与实习岗，n=671 |

</details>

<details>
<summary><b>目录结构与一键复现</b></summary>

```
data-analyst-job-analysis/
├── spiders/            # 爬虫：列表页 + 详情页（断点续传/熔断/原子写入）
├── src/                # 6 步清洗管线 + run_all.py 一键复现
├── notebooks/          # 6 个分析文件（01 总览 ~ 06 核心岗对比）
├── docs/
│   ├── charts/         # 22 张分析图表（PNG）
│   ├── aggregates/     # 聚合数据表（CSV）
│   ├── logs/           # 开发日志
│   ├── cleaning_plan.md       # 清洗方案
│   ├── quality_report.md      # 质检报告
│   └── visualization_plan.md  # 可视化方案
└── data/               # 数据文件（不上传 git）
```

```bash
pip install -r requirements.txt
python src/run_all.py        # 数据管线一键复现
# 然后按编号顺序运行 notebooks/ 下的分析文件
```

</details>

---

<sub>项目声明：本项目为个人学习作品（求职面试用作品集），非商业用途；数据来自公开招聘页面，仅用于技术研究与分析练习，不代表任何机构立场，如有侵权或不当之处请联系删除。</sub>
