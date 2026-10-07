#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-C 调试：捕获所有 console 错误，看到底为什么占位 UI 没渲染"""
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

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        all_logs = []
        page.on('console', lambda m: all_logs.append({'type': m.type, 'text': m.text}))
        page.on('pageerror', lambda e: all_logs.append({'type': 'pageerror', 'text': str(e)}))

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=30000)
        page.evaluate(INIT)
        page.goto('http://127.0.0.1:8080/ar-lab', wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(10000)

        print("=== 所有 console logs (不过滤) ===")
        for log in all_logs:
            print(f"  [{log['type']}] {log['text'][:500]}")

        # 检查当前组件状态
        state = page.evaluate("""
() => {
  const comp = document.querySelector('app-ar-lab');
  if (!comp) return { hasComponent: false };
  const placeholder = comp.querySelector('.placeholder-overlay');
  const loading = comp.querySelector('.loading-overlay');
  const cube = comp.querySelector('.cube-scene .cube');
  const h2 = comp.querySelector('.placeholder-overlay h2');
  return {
    hasComponent: true,
    placeholderExists: !!placeholder,
    loadingExists: !!loading,
    cubeExists: !!cube,
    h2Text: h2?.innerText ?? null,
    bodyText: comp.innerText.substring(0, 500)
  };
}
""")
        print("\n=== Component State ===")
        print(state)

        page.screenshot(path='screenshots/p4c-final.png', full_page=True)
        browser.close()

run()
