#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-B 终极诊断：模仿 deep-diagnose 成功模式验证 learning-profile"""
import json
import time
import sys
import io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

OUT = Path(r"I:\iMato\screenshots\p4b-debug")
OUT.mkdir(parents=True, exist_ok=True)

INIT_JS = """
() => {
  localStorage.setItem('access_token', 'fake-token-test');
  localStorage.setItem('user_data', JSON.stringify({
    id: '1', username: 'test', email: 'test@example.com', userType: 'student',
  }));
  localStorage.setItem('remember_me', 'true');
}
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        all_logs = []
        page.on("console", lambda msg: all_logs.append(
            {"type": msg.type, "text": msg.text[:600]}))
        page.on("pageerror", lambda err: all_logs.append(
            {"type": "pageerror", "text": str(err)[:600]}))

        # 1) 先访问 /auth/login
        print("=== step1: visit /auth/login ===")
        page.goto("http://127.0.0.1:8080/auth/login?_t=" + str(int(time.time()*1000)),
                   wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2500)
        print(f"  url: {page.url}")

        # 2) 注入 token
        print("\n=== step2: inject token ===")
        page.evaluate(INIT_JS)
        # 验证 token 已设置
        token = page.evaluate("() => localStorage.getItem('access_token')")
        print(f"  token in localStorage: {token}")

        # 3) 访问 learning-profile
        print("\n=== step3: visit /user/learning-profile ===")
        page.goto("http://127.0.0.1:8080/user/learning-profile?_t=" + str(int(time.time()*1000)),
                   wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(4000)

        diag = page.evaluate("""() => {
          const lp = document.querySelector('app-learning-profile');
          const layout = document.querySelector('app-user-page-layout');
          return {
            url: location.href,
            title: document.title,
            learningProfileFound: !!lp,
            learningProfileHTMLPreview: lp?.outerHTML?.substring(0, 600) || null,
            learningProfileHasPageTitle: !!lp?.querySelector('h1.page-title'),
            learningProfileHasCards: lp?.querySelectorAll('mat-card')?.length || 0,
            userPageLayoutFound: !!layout,
            bodyInnerPreview: document.body.innerHTML.substring(document.body.innerHTML.length - 600),
          };
        }""")
        print(json.dumps(diag, indent=2, ensure_ascii=False))

        page.screenshot(path=str(OUT / "learning-profile-final.png"), full_page=True)

        # 4) 收集所有 [P4-B] 日志
        p4b = [log for log in all_logs
               if '[P4-B]' in log.get('text', '')
               or 'LearningProfile' in log.get('text', '')
               or 'Learning' in log.get('text', '')]
        print(f"\n=== [P4-B] / LearningProfile 相关日志: {len(p4b)} 条 ===")
        for log in p4b[-10:]:
            print(f"  [{log['type']}] {log['text'][:300]}")

        # 5) 错误日志
        errs = [log for log in all_logs
                if log.get('type') in ('error', 'pageerror', 'warning')
                and 'CORS' not in log.get('text', '')
                and 'WebSocket' not in log.get('text', '')
                and 'health-detail' not in log.get('text', '')
                and 'achievements' not in log.get('text', '')]
        print(f"\n=== 其它错误/警告: {len(errs)} 条 ===")
        for log in errs[:10]:
            print(f"  [{log['type']}] {log['text'][:300]}")

        browser.close()


if __name__ == "__main__":
    main()
