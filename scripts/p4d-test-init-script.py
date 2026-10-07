#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v10：验证 addInitScript 是否真的运行"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        ctx.add_init_script("console.log('>>> INIT SCRIPT RAN <<<');")
        page = ctx.new_page()
        logs = []
        page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text}))

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.wait_for_timeout(2000)

        print('=== 5 log lines ===')
        for log in logs[:5]:
            print(log)

        browser.close()

run()