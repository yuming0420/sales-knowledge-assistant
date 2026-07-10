#!/usr/bin/env python3
"""何总销售训练打卡器 - 低自控力专用"""
import sys
from datetime import datetime, date, timedelta

# 最小可行日
MIN_TASKS = [
    ("1_金句", "背诵今日金句（30秒）"),
    ("2_电话", "打1个电话（无论结果）"),
    ("3_复盘", "AI助手问1个问题"),
]

FULL_TASKS = {
    "金句背诵": "晨会金句抄一遍 + 背出来",
    "客户数据": "筛选5条新客户数据",
    "开发电话": "上午10:00-11:30 打20个电话",
    "追踪客户": "给已加微信的客户发追踪消息",
    "客户分类": "更新ABCD分类表",
    "样品跟进": "确认已寄样品客户测试进度",
    "AI训练": "用AI助手深度练习1个场景",
    "夕会复盘": "写3句话：今天最好/最差/明天改进",
}

def load():
    from core.history import training
    return training

def checkin():
    t = load()
    data = t.checkin()
    today = date.today().isoformat()
    record = data.get("history", {}).get(today, {})
    
    if record and record.get("checkin"):
        print("=" * 40)
        print("  何总销售训练 - 晨间打卡")
        print("=" * 40)
        print()
        print("今日最小可行日（铁律）：")
        for _, desc in MIN_TASKS:
            print(f"  [ ] {desc}")
        print()
        print("现在去打第一个电话，别想，直接打。")
        print(f"当前连胜: {data.get('streak', 0)} 天 | 最佳: {data.get('best_streak', 0)} 天")
        input("\n按回车确认打卡 -> ")
        print("打卡成功！去执行吧。")

def checkout():
    t = load()
    data = t._load()
    today = date.today().isoformat()
    record = data.get("history", {}).get(today, {})
    
    if not record:
        print("还没打卡！先执行: python daily_tracker.py checkin")
        return
    
    print("=" * 40)
    print("  何总销售训练 - 晚间复盘")
    print("=" * 40)
    print()
    
    tasks_done = {}
    all_done = True
    for key, desc in MIN_TASKS:
        done = record.get("tasks", {}).get(key, False)
        mark = "[OK]" if done else "[X]"
        if not done: all_done = False
        print(f"  {mark} {desc}")
        tasks_done[key] = done
    
    if not all_done:
        print("\n最小可行日未完成！现在补：")
        for key, desc in MIN_TASKS:
            if not tasks_done[key]:
                ans = input(f"  {desc} 完成了吗？(y/n): ")
                if ans.lower() == 'y':
                    tasks_done[key] = True
                    all_done = all(tasks_done.values())
    
    print("\n今日加分项：")
    score = 0
    for key, desc in FULL_TASKS.items():
        done = record.get("tasks", {}).get(key, False)
        if done:
            print(f"  [OK] {desc}")
            score += 1
        else:
            ans = input(f"  [ ] {desc} 做了吗？(y/n/s): ")
            if ans.lower() == 'y':
                tasks_done[key] = True
                score += 1
    
    # Save
    t.checkout(tasks_done)
    data = t._load()
    
    print(f"\n今日得分: {score}/{len(FULL_TASKS)}")
    if all_done:
        print(f"连胜: {data.get('streak', 0)} 天 | 最佳: {data.get('best_streak', 0)} 天")
        if data.get('streak', 0) % 7 == 0:
            print(f"连续 {data['streak']} 天了！该奖励自己！")
    else:
        print("明天继续！请不要假装很努力，因为结果不会陪你演戏。")
    
    note = input("\n今日一句话总结 (可选): ")
    if note:
        record["note"] = note
        t._save(data)

def status():
    t = load()
    info = t.get()
    print("=" * 40)
    print("  何总销售训练 - 进度面板")
    print("=" * 40)
    print(f"  当前连胜: {info['streak']} 天")
    print(f"  历史最佳: {info['best_streak']} 天")
    print(f"  累计完成: {info['total_days']} 天")
    print()
    print("  最近7天:")
    for d in info["recent"]:
        icon = {"completed": "[OK]", "checked_in": "[..]", "empty": "[  ]"}
        print(f"    {d['date']} {icon.get(d['status'], '?')}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "checkin": checkin()
    elif cmd == "checkout": checkout()
    elif cmd == "status": status()
    else:
        print("用法: python daily_tracker.py checkin|checkout|status")
