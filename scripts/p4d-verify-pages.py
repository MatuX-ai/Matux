#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D 验证：访问 user/ 下所有 profile/courses 页面，检查是否有无限 loading"""
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

# 要测试的路由
PAGES = [
    ('/user/my-courses',          '.courses-page, .my-courses-page, .course-grid, mat-card'),
    ('/user/course-detail/1',     '.course-detail, .course-header, mat-card'),
    ('/user/profile',             '.profile-page, .user-profile, mat-card'),
    ('/user/token-dashboard',     '.token-dashboard, mat-card'),
    ('/user/achievements',        '.achievements-page, mat-card'),
    ('/user/growth-trajectory',   '.growth-trajectory-page, mat-card'),
    ('/user/learning-reports',    '.learning-reports-page, mat-card'),
    ('/user/teaching-suggestions','.teaching-suggestions-page, mat-card'),
    ('/user/emotional-companion', '.emotional-companion-page, mat-card'),
]

def check_page(page, url, selectors):
    print(f"\n=== {url} ===")
    try:
        resp = page.goto(f'http://127.0.0.1:8080{url}', wait_until='domcontentloaded', timeout=20000)
        print(f"  HTTP {resp.status}")
        page.wait_for_timeout(8000)

        # 检查 spinner
        spinner_count = page.locator('mat-spinner').count()
        progress_count = page.locator('mat-progress-spinner, mat-progress-bar').count()
        # 找是否有任何"加载中"文字
        loading_text_count = page.locator(':text("加载中"), :text("loading"), :text("Loading"), :text("正在加载")').count()

        # 查找内容容器
        body_text = page.evaluate("() => document.body.innerText || ''").strip()
        is_blank = len(body_text) < 50

        print(f"  mat-spinner: {spinner_count}")
        print(f"  progress: {progress_count}")
        print(f"  '加载中' text: {loading_text_count}")
        print(f"  body 长度: {len(body_text)}")
        print(f"  空白页: {'是 ⚠' if is_blank else '否 ✓'}")
        if body_text and len(body_text) < 200:
            print(f"  内容预览: {body_text[:200]}")

        return is_blank or spinner_count > 0 and loading_text_count > 0
    except Exception as e:
        print(f"  ⚠ 错误: {str(e)[:200]}")
        return True

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=20000)
        page.evaluate(INIT)

        stuck = []
        for url, _ in PAGES:
            if check_page(page, url, None):
                stuck.append(url)

        print("\n=== 总结 ===")
        if stuck:
            print(f"以下页面有 loading 卡顿嫌疑:")
            for u in stuck:
                print(f"  ⚠ {u}")
        else:
            print("所有页面都在 8s 内完成了初始渲染")

        browser.close()
        sys.exit(0 if not stuck else 1)

run()
