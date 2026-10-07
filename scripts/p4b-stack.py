#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-B: 获取完整 NG0201 错误堆栈"""
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

INIT_JS = """
() => {
  localStorage.setItem('access_token', 'fake-token-test');
  localStorage.setItem('user_data', JSON.stringify({
    id: '1', username: 'test', email: 'test@example.com', userType: 'student',
  }));
  localStorage.setItem('remember_me', 'true');
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()

    logs = []
    page.on("console", lambda msg: logs.append(
        {"type": msg.type, "text": msg.text}))
    page.on("pageerror", lambda err: logs.append(
        {"type": "pageerror", "text": str(err)}))

    page.goto("http://127.0.0.1:8080/auth/login?_t=" + str(int(time.time()*1000)),
                wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    page.evaluate(INIT_JS)

    page.goto("http://127.0.0.1:8080/user/learning-profile?_t=" + str(int(time.time()*1000)),
                wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(5000)

    # 输出所有 error / pageerror 完整内容
    print("=== 完整错误日志 ===")
    for log in logs:
        if log['type'] in ('error', 'pageerror', 'warning'):
            print(f"[{log['type']}]")
            print(log['text'])
            print('---')

    browser.close()
