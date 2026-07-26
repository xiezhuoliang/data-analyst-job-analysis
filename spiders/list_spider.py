from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.action_chains import ActionChains
import csv
import time
import os
import random

# ========== 配置 ==========
KEYWORD = "数据分析"
OUTPUT_FILE = "51job_数据分析_25城市列表页.csv"

# 5组城市（从日志提取，51job一次最多5城）
CITY_GROUPS = [
    "010000,020000,030200,040000,180200",  # 北京上海广州深圳武汉
    "200200,080200,070200,090200,060000",  # 西安杭州南京成都重庆
    "030800,230300,230200,070300,250200",  # 东莞大连沈阳苏州昆明
    "190200,150200,080300,170200,050000",  # 长沙合肥宁波郑州天津
    "120300,120200,220200,240200,110200",  # 福州青岛济南哈尔滨长春
]

# 防封配置
MAX_PAGES_PER_GROUP = 15  # 每组最多爬15页
DELAY_MIN = 3  # 翻页最短间隔3秒
DELAY_MAX = 8  # 翻页最长间隔8秒
GROUP_REST_MIN = 15  # 组间休息15秒
GROUP_REST_MAX = 30  # 组间休息30秒
SCROLL_ENABLED = True  # 启用页面滚动模拟
# =========================

# 找 msedgedriver
driver_path = None
possible_paths = [
    os.path.join(os.path.dirname(__file__), "drivers", "msedgedriver.exe"),
    os.path.join(os.path.dirname(__file__), "..", "drivers", "msedgedriver.exe"),
    "msedgedriver.exe",
]
for p in possible_paths:
    if os.path.exists(p):
        driver_path = os.path.abspath(p)
        print(f"[✓] 找到 msedgedriver: {driver_path}")
        break

if not driver_path:
    raise FileNotFoundError("找不到 msedgedriver.exe")

# 启动 Edge（多层反检测）
options = EdgeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
# 窗口大小正常化，避免被识别为无头
options.add_argument("--window-size=1366,768")

service = EdgeService(driver_path)
driver = webdriver.Edge(service=service, options=options)

# 深度隐藏 webdriver 标志
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        window.chrome = { runtime: {} };
    """
})

wait = WebDriverWait(driver, 25)
all_jobs = []
seen_links = set()


def human_like_scroll():
    """模拟人类滚动行为"""
    if not SCROLL_ENABLED:
        return
    try:
        # 随机滚动几次
        for _ in range(random.randint(2, 5)):
            scroll_y = random.randint(300, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_y});")
            time.sleep(random.uniform(0.5, 1.5))
        # 偶尔回滚一点
        if random.random() > 0.7:
            driver.execute_script(f"window.scrollBy(0, -{random.randint(100, 300)});")
            time.sleep(random.uniform(0.3, 0.8))
    except:
        pass


def human_like_mouse_move():
    """模拟鼠标在页面上随机移动"""
    try:
        actions = ActionChains(driver)
        # 随机移动到几个位置
        for _ in range(random.randint(2, 4)):
            x = random.randint(200, 1000)
            y = random.randint(200, 600)
            actions.move_by_offset(x, y).pause(random.uniform(0.2, 0.5))
        actions.perform()
    except:
        pass


def fetch_group_page(city_group, page_num):
    """在浏览器环境里调接口"""
    script = f"""
        return fetch('https://we.51job.com/api/job/search-pc?api_key=51job&timestamp=' + Math.floor(Date.now()/1000) + '&keyword={KEYWORD}&searchType=2&jobArea={city_group}&sortType=0&pageNum={page_num}&pageSize=20&source=1&scene=7', {{
            headers: {{'Accept': 'application/json, text/plain, */*'}},
            credentials: 'include'
        }}).then(r => r.json()).catch(e => {{return {{error: e.message}};}});
    """
    return driver.execute_script(script)


def parse_items(items, group_index):
    """解析并去重"""
    new_jobs = []
    for item in items:
        link = item.get("jobHref", "")
        if not link or link in seen_links:
            continue
        seen_links.add(link)
        new_jobs.append({
            "城市组": f"组{group_index + 1}",
            "职位名称": item.get("jobName", ""),
            "公司名称": item.get("companyName", ""),
            "工作地点": item.get("cityString", ""),
            "薪资": item.get("provideSalaryString", ""),
            "经验要求": item.get("workYearString", ""),
            "学历要求": item.get("degreeString", ""),
            "公司性质": item.get("companyTypeString", ""),
            "公司规模": item.get("companySizeString", ""),
            "发布时间": item.get("issueDateString", ""),
            "详情链接": link,
        })
    return new_jobs


try:
    total_start = time.time()

    for i, city_group in enumerate(CITY_GROUPS):
        print(f"\n{'=' * 60}")
        print(f"[*] 开始爬取【第 {i + 1}/5 组城市】...")
        print(f"    城市代码: {city_group}")

        # 打开该组搜索页
        search_url = f"https://we.51job.com/pc/search?jobArea={city_group}&keyword={KEYWORD}&searchType=2"
        driver.get(search_url)

        # 等待加载
        loaded = False
        for selector in [".joblist-item", ".job_item", "[class*='joblist']", ".joblist"]:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                loaded = True
                break
            except:
                continue

        if not loaded:
            print(f"[!] 第 {i + 1} 组页面加载超时，跳过")
            continue

        # 模拟人类行为：滚动 + 鼠标移动
        time.sleep(random.uniform(2, 4))
        human_like_scroll()
        human_like_mouse_move()

        # 翻页循环
        group_jobs = []
        empty_count = 0
        consecutive_error = 0

        for page in range(1, MAX_PAGES_PER_GROUP + 1):
            # 随机延迟（核心防封）
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            print(f"  [*] 第 {i + 1} 组 第 {page} 页... (等待 {delay:.1f} 秒)", end=" ")
            time.sleep(delay)

            # 偶尔再滚动一下，模拟"看完一页再翻页"
            if random.random() > 0.5:
                human_like_scroll()

            result = fetch_group_page(city_group, page)

            # 错误处理
            if isinstance(result, dict) and "error" in result:
                print(f"接口报错: {result['error']}")
                consecutive_error += 1
                # 连续3次错误，可能被封了，暂停休息
                if consecutive_error >= 3:
                    print(f"  [!] 连续3次错误，暂停60秒...")
                    time.sleep(60)
                    consecutive_error = 0
                continue

            consecutive_error = 0
            items = result.get("resultbody", {}).get("job", {}).get("items", [])
            new_jobs = parse_items(items, i)
            group_jobs.extend(new_jobs)

            print(f"新数据 {len(new_jobs)} 条，累计 {len(group_jobs)} 条")

            # 连续2页没新数据就停
            if len(new_jobs) == 0:
                empty_count += 1
                if empty_count >= 2:
                    print(f"  [✓] 第 {i + 1} 组连续2页无新数据，结束")
                    break
            else:
                empty_count = 0

        all_jobs.extend(group_jobs)
        print(f"  [✓] 第 {i + 1} 组共 {len(group_jobs)} 条（去重后）")

        # 组间长休息（关键防封）
        if i < len(CITY_GROUPS) - 1:
            rest = random.uniform(GROUP_REST_MIN, GROUP_REST_MAX)
            print(f"  [*] 组间休息 {rest:.1f} 秒，模拟人类切换城市...")
            time.sleep(rest)

    # 汇总保存
    print(f"\n{'=' * 60}")
    print(f"[✓] 全部城市爬取完成！")
    print(f"    总耗时: {(time.time() - total_start) / 60:.1f} 分钟")
    print(f"    总条数（去重后）: {len(all_jobs)} 条")

    if all_jobs:
        fieldnames = ["城市组", "职位名称", "公司名称", "工作地点", "薪资",
                      "经验要求", "学历要求", "公司性质", "公司规模", "发布时间", "详情链接"]
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_jobs)
        print(f"    已保存到: {OUTPUT_FILE}")

        from collections import Counter

        group_counts = Counter(j["城市组"] for j in all_jobs)
        print(f"\n[*] 各组分布:")
        for g, cnt in group_counts.most_common():
            print(f"    {g}: {cnt} 条")
    else:
        print("[!] 没有抓到数据，可能被封了，建议几小时后再试")

finally:
    input("\n[*] 按回车键关闭浏览器...")
    driver.quit()