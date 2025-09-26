#agent轨迹记录日志
import os, json
from datetime import datetime

def save_history_json(history, log_dir="logs", prefix="searchAgent"):
    os.makedirs(log_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")  # 时间戳唯一标识
    filename = os.path.join(log_dir, f"{prefix}_{ts}.txt")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(history)
    print(f"✅ 轨迹已保存：{filename}")


def save_context_json(context, log_dir="logs", prefix="context"):
    os.makedirs(log_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")  # 时间戳唯一标识
    filename = os.path.join(log_dir, f"{prefix}_{ts}.txt")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(context)
    print(f"✅ 上下文已保存：{filename}")
