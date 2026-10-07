#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过 ng serve 4200 拿 dev mode 详细错误"""
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

INIT = """
() => {
  localStorage.setItem('access_token', 'fake');
  localStorage.setItem('user_data', JSON.stringify({id:'1', username:'test', email:'t@t.com', userType:'student'}));
  localStorage.setItem('remember_me', 'true');
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()
    logs = []
    page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text[:1000]}))
    page.on('pageerror', lambda e: logs.append({'type': 'pageerror', 'text': str(e)[:1500]}))
    page.goto('http://127.0.0.1:4200/auth/login', wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(3000)
    page.evaluate(INIT)
    page.goto('http://127.0.0.1:4200/user/learning-profile', wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(5000)
    print("=== 全部 console / pageerror ===")
    for log in logs:
        if log['type'] in ('error', 'pageerror', 'warning'):
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'health-detail' in text:
                continue
            print(f"[{log['type']}]")
            print(text)
            print('---')
    browser.close()
