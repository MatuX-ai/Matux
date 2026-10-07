#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-C 验证：访问 /ar-lab，等待更长时间看占位 UI"""
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

        # 拦截网络请求
        all_requests = []
        all_responses = []
        page.on('request', lambda req: all_requests.append({'url': req.url, 'method': req.method}))
        page.on('response', lambda resp: all_responses.append({'url': resp.url, 'status': resp.status, 'method': resp.request.method}))

        logs = []
        errors = []
        page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text[:1500]}))
        page.on('pageerror', lambda e: errors.append(str(e)[:2000]))

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(2000)
        page.evaluate(INIT)

        page.goto('http://127.0.0.1:8080/ar-lab', wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(8000)  # 等更长

        # 列出所有 ar-lab 相关请求
        print("=== /ar-lab 相关请求 ===")
        for req in all_requests:
            if 'ar-lab' in req['url']:
                print(f"  REQUEST {req['method']} {req['url']}")
        for resp in all_responses:
            if 'ar-lab' in resp['url']:
                print(f"  RESPONSE {resp['status']} {resp['method']} {resp['url']}")

        # 占位 UI 检查
        print("\n=== 占位 UI ===")
        cube_present = page.locator('.cube-scene .cube').count()
        h2_present = page.locator('.placeholder-overlay h2').count()
        build_steps = page.locator('.build-steps ol li').count()
        print(f"cube: {cube_present}")
        print(f"h2: {h2_present}")
        print(f"build steps: {build_steps}")

        # 当前状态
        loading_count = page.locator('.loading-overlay').count()
        placeholder_count = page.locator('.placeholder-overlay').count()
        error_count = page.locator('.error-overlay').count()
        unity_count = page.locator('.unity-content').count()
        print(f"loading-overlay: {loading_count}")
        print(f"placeholder-overlay: {placeholder_count}")
        print(f"error-overlay: {error_count}")
        print(f"unity-content: {unity_count}")

        # 检查所有 console logs
        print("\n=== 所有 console logs (filtered) ===")
        for log in logs:
            text = log.get('text', '')
            if 'CORS' in text or 'WebSocket' in text or 'fonts.' in text or 'cdn.' in text:
                continue
            print(f"  [{log['type']}] {text[:300]}")

        page.screenshot(path='screenshots/p4c-ar-lab-long-wait.png', full_page=True)

        browser.close()

run()
