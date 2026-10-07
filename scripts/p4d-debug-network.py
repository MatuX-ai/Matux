#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D debug v2：拦截 user-profile 的网络请求，看真实情况"""
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
        all_requests = []
        all_responses = []
        page.on('request', lambda req: all_requests.append({'method': req.method, 'url': req.url}))
        page.on('response', lambda resp: all_responses.append({'status': resp.status, 'method': resp.request.method, 'url': resp.url}))

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)

        all_requests.clear()
        all_responses.clear()

        page.goto('http://127.0.0.1:8080/user/profile', wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(15000)

        print("=== profile 页面请求 ===")
        for r in all_requests:
            print(f"  REQUEST {r['method']} {r['url']}")
        for r in all_responses:
            print(f"  RESPONSE {r['status']} {r['method']} {r['url']}")

        browser.close()

run()
