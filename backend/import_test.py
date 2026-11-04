"""测量后端冷启动各阶段耗时"""
import time

t0 = time.time()


def ms(label):
    print(f"{label}: {(time.time() - t0) * 1000:.0f}ms", flush=True)


ms("start")
import sys  # noqa: E402

ms(f"sys imported (argv={sys.argv})")

# 模拟 main.py:imports
ms("importing fastapi...")
from fastapi import FastAPI  # noqa: E402

ms("importing config...")
from config.settings import Settings  # noqa: E402

ms("importing models (heavy)...")
# 跳过实际 import 全部 models，改为只测大块时间

import models  # noqa: E402

ms(f"models package imported (count={len([n for n in dir(models) if not n.startswith('_')])})")

ms("importing database...")

ms("importing legacy_routes...")

ms("importing utils init_test_data...")

ms("imports done")

# 模拟 main.py 实际启动
app = FastAPI()
ms("FastAPI() created")
settings = Settings()
ms("Settings() created")
