import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STEPS = [
    ('Step 1: 岗位过滤', 'src/step1_filter.py'),
    ('Step 2: 去重', 'src/step2_dedup.py'),
    ('Step 3: 城市恢复', 'src/step3_city.py'),
    ('Step 4: 薪资标准化', 'src/step4_salary.py'),
    ('Step 5: 经验/学历映射', 'src/step5_exp_edu.py'),
    ('Step 6: 文本清洗', 'src/step6_text.py'),
    ('最终: 生成 jobs_clean.csv', 'src/generate_final.py'),
]


def run_script(name, path):
    print(f"\n{'=' * 60}")
    print(f">>> {name}")
    print(f"{'=' * 60}")
    full_path = os.path.join(BASE_DIR, path)
    if not os.path.exists(full_path):
        print(f"❌ 文件不存在: {full_path}")
        return False

    result = subprocess.run(
        [sys.executable, full_path],
        cwd=BASE_DIR,
        capture_output=False,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ {name} 执行失败，退出码: {result.returncode}")
        return False
    return True


def main():
    print("=" * 60)
    print("数据清洗流水线: 一键执行全部步骤")
    print("=" * 60)

    success = True
    for name, path in STEPS:
        if not run_script(name, path):
            success = False
            break

    print(f"\n{'=' * 60}")
    if success:
        print("✅ 全部步骤执行成功")
        print(f"最终数据: data/processed/jobs_clean.csv")
    else:
        print("❌ 流水线中断，请检查错误后重新运行")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
