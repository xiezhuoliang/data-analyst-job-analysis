from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from bs4 import BeautifulSoup
import csv, time, os, random

# ========== 配置 ==========
INPUT_FILE = "51job_数据分析_25城市列表页.csv"
OUTPUT_FILE = "51job_数据分析_完整版.csv"
CHECKPOINT_FILE = "detail_crawled.txt"
BATCH_LIMIT = 0                # 0=刷完为止
DELAY_MIN, DELAY_MAX = 5, 10
BATCH_SIZE = 20
BATCH_REST_MIN, BATCH_REST_MAX = 20, 40
# ==========================

driver_path = None
for p in [os.path.join(os.path.dirname(__file__), "drivers", "msedgedriver.exe"),
          os.path.join(os.path.dirname(__file__), "..", "drivers", "msedgedriver.exe"),
          "msedgedriver.exe"]:
    if os.path.exists(p):
        driver_path = os.path.abspath(p)
        print(f"[✓] 找到 msedgedriver: {driver_path}")
        break
if not driver_path:
    raise FileNotFoundError("找不到 msedgedriver.exe")

# CDP 接管调试模式打开的 Edge
options = EdgeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Edge(service=EdgeService(driver_path), options=options)
print("[✓] 已接管调试 Edge")

def load_crawled():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return set(l.strip() for l in f if l.strip())
    return set()

def save_crawled(link):
    with open(CHECKPOINT_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def human_scroll():
    try:
        for _ in range(random.randint(1, 3)):
            driver.execute_script(f"window.scrollBy(0, {random.randint(200,600)});")
            time.sleep(random.uniform(0.3, 0.8))
    except:
        pass

def extract_detail(html):
    soup = BeautifulSoup(html, "html.parser")
    result = {"职位描述": "", "任职要求": "", "福利标签": ""}

    desc_text = ""

    # 方案1（优先）：直接找 51job 标准正文容器
    box = (soup.select_one("div.bmsg.job_msg.inbox") or
           soup.select_one("div.bmsg.job_msg") or
           soup.select_one(".job_msg"))
    if box and len(box.get_text(strip=True)) > 50:
        desc_text = box.get_text("\n", strip=True)

    # 方案2：找"职位描述"标题（h2.prop），取后面的兄弟区块
    if not desc_text:
        h2 = soup.find("h2", class_="prop")
        if h2:
            sib = h2.find_next_sibling()
            while sib:
                t = sib.get_text(strip=True)
                if len(t) > 100:
                    desc_text = sib.get_text("\n", strip=True)
                    break
                sib = sib.find_next_sibling()

    # 方案3兜底：找含关键词的最小容器
    if not desc_text:
        cands = []
        for d in soup.find_all("div"):
            t = d.get_text()
            if any(k in t for k in ["岗位职责", "工作职责", "职位描述：", "职位描述:"]) and 100 < len(t) < 3000:
                cands.append(d)
        if cands:
            desc_text = min(cands, key=lambda x: len(x.get_text())).get_text("\n", strip=True)

    # 拆分 职位描述 / 任职要求
    if desc_text:
        split_words = ["任职要求：", "任职要求:", "任职资格：", "任职资格:",
                       "岗位要求：", "岗位要求:", "职位要求：", "职位要求:"]
        pos = -1
        for sw in split_words:
            p_ = desc_text.find(sw)
            if p_ != -1:
                pos = p_
                break
        if pos != -1:
            result["职位描述"] = desc_text[:pos].strip()
            result["任职要求"] = desc_text[pos:].strip()
        else:
            result["职位描述"] = desc_text

    # 福利标签：从 div.tags 提取
    tags_box = soup.find("div", class_="tags")
    if tags_box:
        tags = [t.get_text(strip=True) for t in tags_box.find_all(["span", "a", "em", "i"]) if t.get_text(strip=True)]
        result["福利标签"] = " | ".join(tags[:10])

    return result

def flush(all_jobs, fieldnames):
    """全量重写，每条都调用"""
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_jobs)

def main():
    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        all_jobs = list(csv.DictReader(f))
    crawled = load_crawled()
    fieldnames = list(all_jobs[0].keys()) + ["职位描述", "任职要求", "福利标签"]
    print(f"[*] 共 {len(all_jobs)} 条 | 已爬 {len(crawled)} 条 | 待爬 {len(all_jobs)-len(crawled)} 条")

    driver.switch_to.new_window("tab")
    print("[*] 先打开第一条链接测试...")
    first = next(j for j in all_jobs if j.get("详情链接") and j["详情链接"] not in crawled)
    driver.get(first["详情链接"])
    time.sleep(4)
    if "验证" in driver.title:
        print("[!] 触发验证，请手动滑动完成，完成后按回车开始...")
        input()
    else:
        print("[✓] 正常打开，开始批量抓取")

    success = 0
    empty = 0
    start = time.time()

    for i, job in enumerate(all_jobs, 1):
        link = job.get("详情链接", "")
        if not link or link in crawled:
            continue
        if BATCH_LIMIT and success >= BATCH_LIMIT:
            print(f"\n[*] 本批 {BATCH_LIMIT} 条完成，停止")
            break

        delay = random.uniform(DELAY_MIN, DELAY_MAX)
        print(f"\n[*] [{i}] 等待 {delay:.1f} 秒...", end=" ")
        time.sleep(delay)

        try:
            driver.get(link)
        except Exception as e:
            print(f"页面加载异常: {e}，跳过")
            job.update({"职位描述": "", "任职要求": "", "福利标签": ""})
            save_crawled(link)
            flush(all_jobs, fieldnames)
            continue

        if "验证" in driver.title:
            print("触发验证！先保存当前进度...")
            job.update({"职位描述": "", "任职要求": "", "福利标签": ""})
            save_crawled(link)
            flush(all_jobs, fieldnames)
            print("已保存。请：1)关掉这个标签页 2)手动新开一个详情页滑过真验证 3)回这里按回车继续")
            input()
            time.sleep(2)
            continue

        time.sleep(random.uniform(1.5, 3))
        human_scroll()

        try:
            html = driver.page_source
        except Exception as e:
            print(f"获取页面源码异常: {e}，跳过")
            job.update({"职位描述": "", "任职要求": "", "福利标签": ""})
            save_crawled(link)
            flush(all_jobs, fieldnames)
            continue

        detail = extract_detail(html)

        if not detail["职位描述"]:
            empty += 1
            print("解析为空", end=" ")

        job.update(detail)
        success += 1
        save_crawled(link)
        flush(all_jobs, fieldnames)   # 每条都落盘
        print(f"成功 | 描述{len(detail['职位描述'])}字")

        if success % BATCH_SIZE == 0:
            rest = random.uniform(BATCH_REST_MIN, BATCH_REST_MAX)
            print(f"[*] 已爬 {success} 条，休息 {rest:.0f} 秒")
            time.sleep(rest)

    print(f"\n[✓] 完成 {success} 条（其中空 {empty} 条）| 耗时 {(time.time()-start)/60:.1f} 分钟")
    print(f"[✓] 累计进度：{len(load_crawled())}/{len(all_jobs)}")
    print(f"[✓] 已保存: {OUTPUT_FILE}")

try:
    main()
except KeyboardInterrupt:
    print("\n[!] 用户中断，进度已保存")
except Exception as e:
    print(f"\n[!] 程序异常: {e}")
    import traceback
    traceback.print_exc()
finally:
    input("\n[*] 按回车结束（调试 Edge 不会被关）...")