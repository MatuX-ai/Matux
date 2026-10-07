#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 OpenAPI dump 提取所有 API 路径"""
import json
import re

with open(r"G:\iMato\backend\openapi_dump.json", "r", encoding="utf-8") as f:
    spec = json.load(f)

paths = sorted(spec.get("paths", {}).keys())
# Filter for student/learning/course/dashboard related paths
for p in paths:
    if any(k in p.lower() for k in ["course", "learning", "enrollment", "lesson",
                                       "student", "dashboard", "achievement",
                                       "leaderboard", "recommend", "task",
                                       "user/me", "users/me"]):
        print(p)