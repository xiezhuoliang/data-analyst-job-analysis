import os
import pandas as pd
import re
from city_map import CITY_PINYIN_MAP, CITY_TIER

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_PATH = os.path.join(BASE_DIR, 'data', 'interim', 'step2_deduped.csv')
OUT_PATH = os.path.join(BASE_DIR, 'data', 'interim', 'step3_city_recovered.csv')


def extract_city_pinyin(url: str):
    if pd.isna(url):
        return None

    url = str(url).strip()

    if re.match(r'^[a-z0-9]+[.]51job[.]com', url, re.I):
        return '__subdomain__'

    m = re.search(r'jobs[.]51job[.]com/([a-zA-Z0-9-]+)/', url)
    if m:
        return m.group(1).lower()

    return None


def recover_city(row):
    url = row.get('详情链接', '')
    pinyin = extract_city_pinyin(url)

    if pinyin == '__subdomain__':
        return '未知', '未知', 'unknown'

    if pinyin and pinyin in CITY_PINYIN_MAP:
        city_cn = CITY_PINYIN_MAP[pinyin]
        tier = CITY_TIER.get(city_cn, '其他')
        return city_cn, tier, 'url'

    return '未知', '未知', 'unknown'


def main():
    df = pd.read_csv(IN_PATH)
    print(f'[Step 3] 读取: {len(df)} 行')

    city_data = df.apply(recover_city, axis=1, result_type='expand')
    city_data.columns = ['城市', '城市等级', 'city_source']
    df = pd.concat([df, city_data], axis=1)

    known = (df['城市'] != '未知').sum()
    print(f'  城市恢复成功: {known} / {len(df)} ({known/len(df)*100:.1f}%)')

    unmapped = df[df['city_source'] == 'unknown']['详情链接'].apply(extract_city_pinyin).unique()
    unmapped = [u for u in unmapped if u and u != '__subdomain__']
    if unmapped:
        print(f'  ⚠️ 未映射拼音（请补充 city_map.py）: {unmapped}')

    print('  城市分布:')
    for city, cnt in df['城市'].value_counts().items():
        print(f'    {city}: {cnt}')

    df.to_csv(OUT_PATH, index=False, encoding='utf-8-sig')
    print(f'[Step 3] 已保存: {OUT_PATH}')


if __name__ == '__main__':
    main()
