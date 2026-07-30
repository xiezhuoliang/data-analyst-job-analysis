from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import csv, time, os, random, shutil

# ========== 配置 ==========
INPUT_FILE = "51job_数据分析_25城市列表页.csv"
OUTPUT_FILE = "51job_数据分析_完整版.csv"
CHECKPOINT_FILE = "detail_crawled.txt"
DEAD_FILE = "dead_links.txt"       # 已下架岗位，永久跳过
LOG_FILE = "run.log"
BATCH_LIMIT = 0                # 0=刷完为止
DELAY_MIN, DELAY_MAX = 8, 15   # 每条间隔
COOLDOWN_EVERY = 40            # 每40条主动冷却
COOLDOWN_SEC = 180
EMPTY_ABORT = 10               # 连续空10条自动刹车
ERROR_ABORT = 5                # 连续异常5次判定浏览器挂了
DEAD_KEYWORDS = ["已停止招聘", "职位不存在", "已下架", "职位已关闭", "该职位已失效"]
# ==========================

# ---------- 日志：同时打印(立即刷新) + 写文件 ----------
def log(msg):
    print(msg, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(time.strftime("%m-%d %H:%M:%S ") + msg + "\n")
    except Exception:
        pass

# ---------- 驱动 ----------
driver_path = None
for p in [os.path.join(os.path.dirname(__file__), "drivers", "msedgedriver.exe"),
          os.path.join(os.path.dirname(__file__), "..", "drivers", "msedgedriver.exe"),
          "msedgedriver.exe"]:
    if os.path.exists(p):
        driver_path = os.path.abspath(p)
        log(f"[✓] 找到 msedgedriver: {driver_path}")
        break
if not driver_path:
    raise FileNotFoundError("找不到 msedgedriver.exe")

def connect():
    """连接（或重连）调试 Edge"""
    options = EdgeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    return webdriver.Edge(service=EdgeService(driver_path), options=options)

driver = connect()
log("[✓] 已接管调试 Edge")

# ---------- 断点 ----------
def load_set(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return set(l.strip() for l in f if l.strip())
    return set()

def append_line(path, line):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        log(f"[!] 写入 {path} 失败: {e}")

def human_scroll():
    try:
        for _ in range(random.randint(1, 3)):
            driver.execute_script(f"window.scrollBy(0, {random.randint(200,600)});")
            time.sleep(random.uniform(0.3, 0.8))
    except Exception:
        pass

def extract_detail(html):
    soup = BeautifulSoup(html, "html.parser")
    result = {"职位描述": "", "任职要求": "", "福利标签": ""}
    desc_text = ""
    box = (soup.select_one("div.bmsg.job_msg.inbox") or
           soup.select_one("div.bmsg.job_msg") or
           soup.select_one(".job_msg"))
    if box and len(box.get_text(strip=True)) > 50:
        desc_text = box.get_text("\n", strip=True)
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
    if not desc_text:
        cands = []
        for d in soup.find_all("div"):
            t = d.get_text()
            if any(k in t for k in ["岗位职责", "工作职责", "职位描述：", "职位描述:"]) and 100 < len(t) < 3000:
                cands.append(d)
        if cands:
            desc_text = min(cands, key=lambda x: len(x.get_text())).get_text("\n", strip=True)
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
    tags_box = soup.find("div", class_="tags")
    if tags_box:
        tags = [t.get_text(strip=True) for t in tags_box.find_all(["span", "a", "em", "i"]) if t.get_text(strip=True)]
        result["福利标签"] = " | ".join(tags[:10])
    return result

# ---------- 落盘：原子写入 ----------
def flush(all_jobs, fieldnames):
    tmp = OUTPUT_FILE + ".tmp"
    try:
        with open(tmp, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(all_jobs)
        os.replace(tmp, OUTPUT_FILE)
    except PermissionError:
        log("[!] CSV 被占用（是不是 Excel 打开着？）本条暂存内存，下条会再写，数据不丢")
    except Exception as e:
        log(f"[!] 写盘异常: {e}（数据在内存，下条会再写）")

# ---------- 重启保护：合并历史数据 ----------
def merge_history(all_jobs):
    if not os.path.exists(OUTPUT_FILE):
        return 0
    with open(OUTPUT_FILE, "r", encoding="utf-8-sig") as f:
        old = {r.get("详情链接"): r for r in csv.DictReader(f) if r.get("详情链接")}
    n = 0
    for job in all_jobs:
        o = old.get(job.get("详情链接", ""))
        if o and o.get("职位描述"):
            for col in ["职位描述", "任职要求", "福利标签"]:
                job[col] = o.get(col, "")
            n += 1
    return n

# ---------- 假账清理：断点里无数据且非下架的链接，移出断点重跑 ----------
def clean_checkpoint(all_jobs, crawled, dead):
    with_data = {j["详情链接"] for j in all_jobs if j.get("职位描述") and j.get("详情链接")}
    bad = crawled - with_data - dead   # 下架的不算假账
    if bad:
        crawled -= bad
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(crawled)) + "\n")
    return len(bad)

# ---------- 风控页识别 ----------
def is_blocked(html, title):
    if "验证" in title:
        return True
    if len(html) < 20000:
        return True
    if "aliyun" in html[:5000].lower():
        return True
    return False

def main():
    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        all_jobs = list(csv.DictReader(f))
    fieldnames = list(all_jobs[0].keys()) + ["职位描述", "任职要求", "福利标签"]

    if os.path.exists(OUTPUT_FILE):
        shutil.copy2(OUTPUT_FILE, OUTPUT_FILE.replace(".csv", "_备份.csv"))

    merged = merge_history(all_jobs)
    crawled = load_set(CHECKPOINT_FILE)
    dead = load_set(DEAD_FILE)
    bad = clean_checkpoint(all_jobs, crawled, dead)
    log(f"[*] 共 {len(all_jobs)} 条 | 断点 {len(crawled)} 条 | 已下架 {len(dead)} 条 | 合并历史 {merged} 条"
        + (f" | 清理假账 {bad} 条（将重跑）" if bad else ""))
    log(f"[*] 配置：间隔{DELAY_MIN}-{DELAY_MAX}秒 | 每{COOLDOWN_EVERY}条冷却{COOLDOWN_SEC//60}分钟 | 批次上限{BATCH_LIMIT or '不限'}")

    remaining = [j for j in all_jobs
                 if j.get("详情链接") and j["详情链接"] not in crawled and j["详情链接"] not in dead]
    if not remaining:
        log("[✓] 所有链接均已完成（含下架），无需运行")
        return

    global driver
    driver.switch_to.new_window("tab")
    log("[*] 先打开第一条链接测试...")
    driver.get(remaining[0]["详情链接"])
    time.sleep(4)
    if is_blocked(driver.page_source, driver.title):
        log("[!] 开局就被拦，请手动滑过验证后按回车开始...")
        input()

    success = empty = dead_new = consec_empty = consec_error = 0
    start = time.time()

    for i, job in enumerate(all_jobs, 1):
        link = job.get("详情链接", "")
        if not link or link in crawled or link in dead:
            continue
        if BATCH_LIMIT and success >= BATCH_LIMIT:
            log(f"\n[*] 本批 {BATCH_LIMIT} 条完成，停止")
            break

        if success > 0 and success % COOLDOWN_EVERY == 0:
            log(f"\n[*] 已爬 {success} 条，主动冷却 {COOLDOWN_SEC//60} 分钟防验证...")
            time.sleep(COOLDOWN_SEC)

        delay = random.uniform(DELAY_MIN, DELAY_MAX)
        log(f"[*] [{i}] 等待 {delay:.1f} 秒...")
        time.sleep(delay)

        try:
            driver.get(link)
            html = driver.page_source
        except WebDriverException as e:
            consec_error += 1
            log(f"[!] 浏览器异常（连续{consec_error}次）: {str(e)[:80]}")
            if consec_error >= ERROR_ABORT:
                log("[!] 浏览器会话疑似断开（调试Edge被关了？）。请重新调试启动Edge+人肉开门，然后按回车重连...")
                input()
                try:
                    driver = connect()
                    driver.switch_to.new_window("tab")
                    consec_error = 0
                    log("[✓] 已重连，继续")
                except Exception as e2:
                    log(f"[!] 重连失败: {e2}，程序退出，进度已保存，可重启续跑")
                    break
            continue
        consec_error = 0

        if is_blocked(html, driver.title):
            log("[!] 触发风控！请：1)关掉这个标签页 2)手动新开详情页滑过真验证 3)回这里按回车（本条不记断点，之后重跑）")
            input()
            time.sleep(2)
            continue

        time.sleep(random.uniform(1.5, 3))
        human_scroll()
        detail = extract_detail(html)

        if not detail["职位描述"]:
            # 下架页：记入 dead_links，永久跳过，不算连续空
            if any(k in html for k in DEAD_KEYWORDS):
                dead.add(link)
                append_line(DEAD_FILE, link)
                dead_new += 1
                log(f"    职位已下架，记入 {DEAD_FILE}，永久跳过")
                continue
            empty += 1
            consec_empty += 1
            log(f"    解析为空（连空{consec_empty}）")
            if consec_empty >= EMPTY_ABORT:
                log(f"[!] 连续 {EMPTY_ABORT} 条为空，大概率被风控，已刹车。请手动确认页面状态，恢复后按回车继续")
                input()
                consec_empty = 0
                continue
        else:
            consec_empty = 0

        job.update(detail)
        success += 1
        append_line(CHECKPOINT_FILE, link)
        flush(all_jobs, fieldnames)
        log(f"    成功 | 描述{len(detail['职位描述'])}字 | 本次累计{success}条")

    log(f"\n[✓] 本次完成 {success} 条（空 {empty} 条，下架 {dead_new} 条）| 耗时 {(time.time()-start)/60:.1f} 分钟")
    log(f"[✓] 总进度：{len(load_set(CHECKPOINT_FILE))}/{len(all_jobs)}（另有 {len(dead)} 条已下架）")
    log(f"[✓] 已保存: {OUTPUT_FILE}")

try:
    main()
except KeyboardInterrupt:
    log("\n[!] 用户中断，进度已保存，重启自动续跑")
except Exception as e:
    log(f"\n[!] 程序异常: {e}")
    import traceback
    traceback.print_exc()
finally:
    input("\n[*] 按回车结束（调试 Edge 不会被关）...")