#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D debug v3：检查 user-profile 页面的完整 DOM 状态"""
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

        page.goto('http://127.0.0.1:8080/user/profile', wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(15000)

        # 直接看 DOM 内容
        result = page.evaluate("""
() => {
  const root = document.querySelector('app-user-profile');
  if (!root) return { hasComponent: false };
  return {
    outerHTML: root.outerHTML.substring(0, 3000),
    innerText: root.innerText,
    loadingContainerVisible: !!root.querySelector('.loading-container'),
    errorContainerVisible: !!root.querySelector('.error-container'),
    profileContentVisible: !!root.querySelector('.profile-content'),
    matSpinnerCount: root.querySelectorAll('mat-spinner').length
  };
}
""")
        print("=== DOM State ===")
        print("loading-container visible:", result.get('loadingContainerVisible'))
        print("error-container visible:", result.get('errorContainerVisible'))
        print("profile-content visible:", result.get('profileContentVisible'))
        print("mat-spinner count:", result.get('matSpinnerCount'))
        print("\n=== innerText ===")
        print(result.get('innerText'))
        print("\n=== outerHTML (first 3000 chars) ===")
        print(result.get('outerHTML'))

        browser.close()

run()
