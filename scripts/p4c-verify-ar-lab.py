#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-C 验证：访问 /ar-lab，看到 Unity 构建占位 UI（CSS 3D 立方体 + 步骤文档）"""
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
        logs = []
        errors = []
        page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text[:1500]}))
        page.on('pageerror', lambda e: errors.append(str(e)[:2000]))

        # 1. 访问登录页并注入 token
        page.goto('http://127.0.0.1:8080/auth/login', wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(2000)
        page.evaluate(INIT)

        # 2. 访问 /ar-lab
        print("=== 访问 /ar-lab ===")
        resp = page.goto('http://127.0.0.1:8080/ar-lab', wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(4000)
        print(f"HTTP status: {resp.status}")

        # 3. 检查占位 UI 元素
        print("\n=== 占位 UI 元素检查 ===")
        cube_present = page.locator('.cube-scene .cube').count()
        h2_present = page.locator('.placeholder-overlay h2').count()
        h2_text = page.locator('.placeholder-overlay h2').first.inner_text() if h2_present else 'N/A'
        build_steps = page.locator('.build-steps ol li').count()
        rebuild_btn = page.locator('button:has-text("重新检测")').count()
        force_btn = page.locator('button:has-text("强制尝试加载")').count()
        path_text = page.locator('.placeholder-detail code').first.inner_text() if page.locator('.placeholder-detail code').count() else 'N/A'

        print(f"CSS 3D 立方体: {'✓' if cube_present else '✗'} (count={cube_present})")
        print(f"占位 h2: {'✓' if h2_present else '✗'} text='{h2_text}'")
        print(f"构建步骤 li 数: {build_steps} (期望 5)")
        print(f"'重新检测'按钮: {'✓' if rebuild_btn else '✗'}")
        print(f"'强制尝试加载'按钮: {'✓' if force_btn else '✗'}")
        print(f"期望路径显示: {path_text}")

        # 4. 检查 console errors
        print("\n=== Console / Pageerror ===")
        critical_errors = []
        for log in logs:
            if log['type'] in ('error', 'pageerror') or log['type'] == 'warning':
                text = log.get('text', '')
                # 过滤掉已知的 CORS / WebSocket / 第三方
                if 'CORS' in text or 'WebSocket' in text or 'cdn.' in text or 'fonts.' in text:
                    continue
                critical_errors.append(log)
                print(f"[{log['type']}] {text[:400]}")

        for err in errors:
            print(f"[pageerror] {err[:400]}")

        print(f"\n共 {len(critical_errors)} 条 critical errors / warnings")

        # 5. 截图
        page.screenshot(path='screenshots/p4c-ar-lab-placeholder.png', full_page=True)
        print("截图保存到 screenshots/p4c-ar-lab-placeholder.png")

        # 6. 点击 '重新检测' 按钮不会崩
        print("\n=== 验证 '重新检测' 按钮 ===")
        if rebuild_btn:
            page.locator('button:has-text("重新检测")').click()
            page.wait_for_timeout(2000)
            cube_after = page.locator('.cube-scene .cube').count()
            print(f"重新检测后立方体仍在: {'✓' if cube_after else '✗'}")

        browser.close()
        return cube_present > 0 and h2_present > 0 and build_steps == 5

if __name__ == '__main__':
    ok = run()
    sys.exit(0 if ok else 1)
