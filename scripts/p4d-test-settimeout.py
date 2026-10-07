#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v5：直接测试 setTimeout 在 page context 内是否工作"""
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
        logs = []
        page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text}))
        page.on('pageerror', lambda e: logs.append({'type': 'pageerror', 'text': str(e)}))

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)
        page.goto('http://127.0.0.1:8080/user/profile', wait_until='domcontentloaded', timeout=20000)

        # 在 page context 设置一个 setTimeout 看是否工作
        page.evaluate("""
() => {
  window.__testFired = false;
  window.setTimeout(() => { window.__testFired = true; }, 1000);
  console.log('test setTimeout registered');
}
""")
        page.wait_for_timeout(3000)
        fired = page.evaluate("() => window.__testFired")
        print(f"setTimeout fired: {fired}")

        # 测一下 zone.js 是否激活
        zone_active = page.evaluate("""
() => {
  return typeof window.Zone !== 'undefined' || (typeof Zone !== 'undefined');
}
""")
        print(f"Zone defined: {zone_active}")

        # 等 5s 后再看 user-profile 状态
        page.wait_for_timeout(5000)
        result = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  if (!root) return { hasComponent: false };
  return {
    loadingContainerVisible: !!root.querySelector('.loading-container'),
    errorContainerVisible: !!root.querySelector('.error-container'),
    profileContentVisible: !!root.querySelector('.profile-content'),
    innerText: root.innerText.substring(0, 200)
  };
}
""")
        print(f"\n=== user-profile state ===")
        print(result)

        print("\n=== console logs ===")
        for log in logs:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:400]}")

        browser.close()

run()
