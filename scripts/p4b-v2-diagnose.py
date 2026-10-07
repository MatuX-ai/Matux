#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-B 修正版诊断：正确检查组件作为 sibling"""
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

PAGES = [
    ("/user/dashboard", "StudentDashboardComponent"),
    ("/user/profile", "UserProfileComponent"),
    ("/user/courses", "MyCoursesComponent"),
    ("/user/learning-profile", "LearningProfileComponent"),
]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        ctx.add_init_script(INIT_JS)
        page = ctx.new_page()

        all_logs = []
        page.on("console", lambda msg: all_logs.append(
            {"type": msg.type, "text": msg.text[:600]}))
        page.on("pageerror", lambda err: all_logs.append(
            {"type": "pageerror", "text": str(err)[:600]}))

        report = {"pages": {}}

        for path, expected_tag in PAGES:
            ts = int(time.time() * 1000)
            url = f"http://127.0.0.1:8080{path}?_t={ts}"
            print(f"\n=== {path} (expect {expected_tag}) ===")
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception as e:
                print(f"  navigation: {e}")
            page.wait_for_timeout(3500)

            diag = page.evaluate(f"""() => {{
              const userLayout = document.querySelector('app-user-page-layout');
              const allInLayout = userLayout ? userLayout.querySelectorAll('*') : [];
              const expected = document.querySelector('app-learning-profile, app-student-dashboard, app-user-profile, app-my-courses');
              return {{
                url: location.href,
                title: document.title,
                userLayoutFound: !!userLayout,
                userLayoutChildrenCount: userLayout?.children?.length || 0,
                expectedComponentFound: !!expected,
                expectedComponentTag: expected?.tagName?.toLowerCase() || null,
                expectedComponentHTMLPreview: expected?.outerHTML?.substring(0, 300) || null,
                layoutInnerPreview: userLayout?.innerHTML?.substring(0, 400) || null,
                bodyEndPreview: document.body.innerHTML.substring(document.body.innerHTML.length - 500),
              }};
            }}""")
            print(json.dumps(diag, indent=2, ensure_ascii=False)[:2000])

            shot = OUT / f"{path.strip('/').replace('/', '_')}.png"
            page.screenshot(path=str(shot), full_page=True)

            p4b_logs = [log for log in all_logs
                        if '[P4-B]' in log.get('text', '')
                        or 'LearningProfile' in log.get('text', '')]
            if p4b_logs:
                print(f"  --- [P4-B] / LearningProfile 相关日志 ({len(p4b_logs)}) ---")
                for log in p4b_logs[-5:]:
                    print(f"  [{log['type']}] {log['text'][:300]}")

            report["pages"][path] = {
                "diag": diag,
                "p4b_logs": p4b_logs[-5:],
            }

        # 错误日志
        errors = [log for log in all_logs
                  if log.get('type') in ('error', 'pageerror')
                  and 'CORS' not in log.get('text', '')
                  and 'WebSocket' not in log.get('text', '')]
        print(f"\n=== {len(errors)} 个非 CORS 错误 ===")
        for log in errors[:10]:
            print(f"[{log['type']}] {log['text'][:400]}")

        (OUT / "report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"\nReport: {OUT / 'report.json'}")

        browser.close()


if __name__ == "__main__":
    main()
