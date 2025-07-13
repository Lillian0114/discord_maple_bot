import os
import json
import aiohttp
import shutil

def parse_time_range(time_str):
    """解析時間字串，返回最小秒數"""
    if "~" in time_str:
        min_time, _ = time_str.split("~")
    else:
        min_time = time_str

    def to_seconds(t):
        t = t.strip()
        if "小時" in t:
            parts = t.split("小時")
            hours = int(parts[0]) if parts[0] else 0
            minutes = int(parts[1].replace("分", "")) if len(parts) > 1 and "分" in parts[1] else 0
            return hours * 3600 + minutes * 60
        elif "分" in t:
            return int(t.replace("分", "")) * 60
        return 0

    return to_seconds(min_time)

def load_boss_times(filepath=None):
    if filepath is None:
        # 找出 src/boss_time.json 的絕對路徑
        base_dir = os.path.dirname(__file__)  # /app/src/utils
        filepath = os.path.abspath(os.path.join(base_dir, '..', 'boss_time.json'))

    with open(filepath, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    return raw, {k: parse_time_range(v) for k, v in raw.items()}

async def save_boss_times_from_web():
    url = "https://a2983456456.github.io/artale-drop/boss_time.json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()

        base_dir = os.path.dirname(__file__)
        filepath = os.path.abspath(os.path.join(base_dir, '..', 'boss_time.json'))
        tmp_path = filepath + '.tmp'

        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        shutil.move(tmp_path, filepath)

        print("boss_time.json 已安全更新！")
        return True
    except Exception as e:
        print(f"更新 boss_time.json 失敗：{e}")
        return False