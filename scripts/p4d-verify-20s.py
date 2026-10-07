#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D v4：等 20s 看是否进入错误状态"""
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

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)
        page.goto('http://127.0.0.1:8080/user/profile', wait_until='domcontentloaded', timeout=20000)

        # 等 20s
        page.wait_for_timeout(20000)

        result = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  if (!root) return { hasComponent: false };
  return {
    loadingContainerVisible: !!root.querySelector('.loading-container'),
    errorContainerVisible: !!root.querySelector('.error-container'),
    profileContentVisible: !!root.querySelector('.profile-content'),
    errorText: root.querySelector('.error-container .error-message')?.innerText ?? null,
    innerText: root.innerText.substring(0, 500)
  };
}
""")
        print("=== 20s 后 ===")
        print("loading-container:", result.get('loadingContainerVisible'))
        print("error-container:", result.get('errorContainerVisible'))
        print("profile-content:", result.get('profileContentVisible'))
        print("error-text:", result.get('errorText'))
        print("inner-text:", result.get('innerText'))

        print("\n=== console logs ===")
        for log in logs:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                continue
            print(f"  [{log['type']}] {text[:300]}")

        browser.close()

run()
