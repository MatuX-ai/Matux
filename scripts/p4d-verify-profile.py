#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D 验证 v2：访问 /user/profile，等待足够长的时间确认不会无限 loading"""
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

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)

        print("=== /user/profile 长等待 ===")
        resp = page.goto('http://127.0.0.1:8080/user/profile', wait_until='domcontentloaded', timeout=20000)
        print(f"HTTP {resp.status}")

        # 采样不同时间点的状态
        for t in [3, 6, 10, 13, 16]:
            page.wait_for_timeout(t * 1000 - (sum([3, 6, 10, 13, 16][:[3, 6, 10, 13, 16].index(t)]) if t > 3 else 0) * 1000)
            spinner = page.locator('.profile-container mat-spinner').count()
            error = page.locator('.profile-container .error-container').count()
            content = page.locator('.profile-container .profile-content').count()
            body = page.evaluate("() => document.body.innerText || ''")
            print(f"t={t}s: spinner={spinner} error={error} content={content} body={len(body)}")
            if error > 0:
                err_text = page.locator('.profile-container .error-message').first.inner_text()
                print(f"  error text: {err_text}")

        page.screenshot(path='screenshots/p4d-user-profile.png', full_page=True)
        browser.close()

run()
