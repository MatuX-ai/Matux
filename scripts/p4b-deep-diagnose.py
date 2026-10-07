#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-B 深入诊断：user 模块为何不实例化"""
import json
import time
import sys
import io
import re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

OUT = Path(r"I:\iMato\screenshots\p4b-debug")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        logs = []
        page.on("console", lambda msg: logs.append(
            {"type": msg.type, "text": msg.text[:600]}))
        page.on("pageerror", lambda err: logs.append(
            {"type": "pageerror", "text": str(err)[:800]}))

        # Step 1: 访问 /auth/login 看 Angular 整体是否工作
        print("=== step1: /auth/login ===")
        page.goto("http://127.0.0.1:8080/auth/login?_t=" + str(int(time.time()*1000)),
                   wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        diag_login = page.evaluate("""() => ({
          loginCard: !!document.querySelector('app-login mat-card'),
          appLogin: !!document.querySelector('app-login'),
          routerOutlet: document.querySelector('app-root router-outlet')?.children?.length || 0,
          title: document.title,
          url: location.href,
          bodyStart: document.body.innerHTML.substring(0, 800),
        })""")
        print("  ", diag_login)

        # Step 2: 在登录页注入 fake token + 跳转 /user/dashboard
        print("\n=== step2: 注入 token 后跳 user/dashboard ===")
        page.evaluate("""() => {
          localStorage.setItem('access_token', 'fake-token-test');
          localStorage.setItem('user_data', JSON.stringify({
            id: '1', username: 'test', email: 'test@example.com',
            userType: 'student',
          }));
          localStorage.setItem('remember_me', 'true');
        }""")
        page.goto("http://127.0.0.1:8080/user/dashboard?_t=" + str(int(time.time()*1000)),
                   wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(4000)
        diag_user = page.evaluate("""() => {
          const root = document.querySelector('app-root');
          const routerOutlet = root?.querySelector(':scope > div > div > router-outlet');
          const allOutlets = root?.querySelectorAll('router-outlet');
          return {
            url: location.href,
            title: document.title,
            rootHasChildren: root?.children?.length || 0,
            rootHTMLPreview: root?.outerHTML?.substring(0, 1500),
            outletCount: allOutlets?.length || 0,
            firstOutletChildren: allOutlets?.[0]?.children?.length || 0,
            secondOutletChildren: allOutlets?.[1]?.children?.length || 0,
            userPageLayout: !!document.querySelector('app-user-page-layout'),
            studentDashboard: !!document.querySelector('app-student-dashboard'),
            userNavbar: !!document.querySelector('app-user-navbar'),
          };
        }""")
        print("  ", json.dumps(diag_user, indent=2, ensure_ascii=False))

        # Step 3: 收集所有错误日志
        err_logs = [log for log in logs if log.get('type') in ('error', 'pageerror', 'warning')
                     or '[P4-B]' in log.get('text', '')]
        print(f"\n=== step3: {len(err_logs)} 个错误/警告日志 ===")
        for log in err_logs[:20]:
            print(f"[{log['type']}] {log['text'][:300]}")

        # Step 4: 截图
        page.screenshot(path=str(OUT / "user_dashboard_with_token.png"), full_page=True)

        # Step 5: 检查 SPA server 是否实际响应了 chunks
        print("\n=== step5: 检查 541 chunk 可达性 ===")
        # 找 SPA 实际暴露的 541 chunk 路径
        html = page.content()
        chunks = re.findall(r'(541\.[a-f0-9]+\.js)', html)
        print(f"HTML 中引用的 541 chunk: {chunks}")
        if chunks:
            chunk_url = f"http://127.0.0.1:8080/{chunks[0]}"
            r = ctx.request.get(chunk_url)
            print(f"  status: {r.status}, size: {len(r.body())}")

        browser.close()


if __name__ == "__main__":
    main()
