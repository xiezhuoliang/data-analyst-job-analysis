# 数据分析岗位招聘市场画像分析

> 基于 51job 平台 25 个城市「数据分析」相关岗位招聘数据，构建市场画像，为求职与职业规划提供数据支撑。
> 
> 本项目为个人面试作品，完整覆盖数据采集 → 数据清洗 → 分析可视化全流程。

---

## 项目背景

数据分析师岗位市场需求大、薪资跨度广、技能要求杂。通过系统性采集和清洗招聘平台数据，可以回答：

- 哪些城市对数据分析师需求最旺？
- 不同经验/学历对应的薪资带宽是多少？
- 企业最看重哪些技能（SQL、Python、BI 工具）？
- 核心数据分析岗 vs 泛数据岗的定价差异？

## 数据说明

| 项目 | 内容 |
|------|------|
| 数据来源 | 前程无忧（51job） |
| 搜索关键词 | 数据分析 |
| 覆盖城市 | 25 个（一线 4 + 新一线 14 + 二线 7） |
| 时间跨度 | 2025-09 ~ 2026-07 |
| 原始数据量 | 1495 条（列表页） |
| 清洗后数据量 | ~900 条（核心岗 + 数据相关岗，去重后） |
| 字段 | 职位名称、公司、城市、薪资、经验、学历、公司性质/规模、发布时间、职位描述、任职要求、福利标签 |

## 技术栈

- **语言**：Python 3.12
- **数据采集**：Selenium + Edge（绕过 WAF 反爬）
- **数据处理**：pandas、numpy
- **可视化**：pyecharts、matplotlib、seaborn
- **版本控制**：Git + GitHub

## 项目结构

```
data-analyst-job-analysis/
├── data/
│   ├── raw/              # 原始 CSV（永不改动）
│   ├── interim/          # 清洗中间文件（step1~6）
│   └── processed/        # 最终干净数据
├── src/
│   ├── city_map.py       # 城市拼音映射表
│   ├── step1_filter.py   # 岗位相关性过滤
│   ├── step2_dedup.py    # 去重
│   ├── step3_city.py     # 城市恢复与归一化
│   ├── step4_salary.py   # 薪资标准化
│   ├── step5_exp_edu.py  # 经验/学历分档
│   ├── step6_text.py     # 文本清洗与任职要求回收
│   └── run_all.py        # 一键执行流水线
├── docs/
│   ├── logs/             # 每日工作日志
│   ├── cleaning_plan.md  # 清洗方案
│   └── quality_report.md # 质检报告
├── notebooks/            # 分析可视化
├── spiders/              # 爬虫脚本
│   ├── list_spider.py    # 列表页采集
│   └── detail_spider.py  # 详情页采集
├── README.md
├── requirements.txt
└── .gitignore
```

## 清洗流水线（6 步）

| 步骤 | 任务 | 关键产出 |
|------|------|---------|
| Step 1 | 岗位相关性过滤 | `job_category ∈ {core, related, noise}` |
| Step 2 | 去重 | `dup_count`（招聘急迫度代理变量） |
| Step 3 | 城市恢复 | 从 URL 拼音提取 → 23 城市全覆盖 |
| Step 4 | 薪资标准化 | 6 种薪资模式统一换算为月薪（万元） |
| Step 5 | 经验/学历分档 | 15 种写法映射为标准档位 |
| Step 6 | 文本回收 | 任职要求从职位描述切分回收 |

**设计原则**：原始列永不覆盖，每步输出独立中间文件，保证可复现。

## 运行方式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行清洗流水线（逐步）
cd src
python step1_filter.py
python step2_dedup.py
python step3_city.py
python step4_salary.py
python step5_exp_edu.py
python step6_text.py

# 或一键执行（全部完成后）
python run_all.py
```

## 分析维度（预告）

- [ ] 城市薪资对比（一线 vs 新一线 vs 二线）
- [ ] 经验-薪资带宽分析
- [ ] 学历门槛与薪资溢价
- [ ] 技能词频与薪资相关性
- [ ] 公司规模/性质对薪资的影响
- [ ] 核心岗 vs 泛数据岗定价差异

## 进度

| 阶段 | 时间 | 状态 |
|------|------|------|
| 爬虫采集 | 7.24 ~ 7.29 | ✅ 完成 |
| 数据清洗 | 7.30 ~ 8.3 | 🔄 Step 1~3 完成，Step 4~6 进行中 |
| 分析可视化 | 8.4 ~ 8.9 | ⏳ 待开始 |
| README 收尾 | 8.10 ~ 8.15 | ⏳ 待开始 |

## 许可证

本项目为个人学习作品，数据仅用于分析研究，如有侵权请联系删除。
