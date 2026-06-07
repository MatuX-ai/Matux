"""测量后端冷启动各阶段耗时"""
import time

t0 = time.time()


def ms(label):
    print(f"{label}: {(time.time() - t0) * 1000:.0f}ms", flush=True)


ms("start")
import sys

ms(f"sys imported (argv={sys.argv})")

# 模拟 main.py:imports
ms("importing fastapi...")
from fastapi import FastAPI

ms("importing config...")
from config.settings import Settings

ms("importing models (heavy)...")
# 跳过实际 import 全部 models，改为只测大块时间
import importlib
import models

ms(f"models package imported (count={len([n for n in dir(models) if not n.startswith('_')])})")

ms("importing database...")
from utils.database import create_db_and_tables, AsyncSessionLocal

ms("importing legacy_routes...")
from legacy_routes import register_all_routes

ms("importing utils init_test_data...")
from utils.init_test_data import initialize_test_data

ms("imports done")

# 模拟 main.py 实际启动
app = FastAPI()
ms("FastAPI() created")
settings = Settings()
ms("Settings() created")
