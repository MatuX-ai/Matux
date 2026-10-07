#!/usr/bin/env python3
"""P4-B 诊断：为什么 /user/learning-profile router-outlet 为空"""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"I:\iMato\screenshots\p4b-debug")
OUT.mkdir(parents=True, exist_ok=True)

PAGES = [
    "/user/dashboard",
    "/user/profile",
    "/user/courses",
    "/user/learning-profile",
]

INIT_JS = """
() => {
  localStorage.setItem('access_token', 'fake-token-routing-test');
  localStorage.setItem('user_data', JSON.stringify({
    id: '1', username: 'test', email: 'test@example.com', userType: 'student',
  }));
  localStorage.setItem('remember_me', 'true');
}
"""

DIAGNOSE_JS = """
() => {
  const outlet = document.querySelector('app-user-page-layout router-outlet');
  const lp = document.querySelector('app-learning-profile');
  const navbar = document.querySelector('app-user-navbar');
  return {
    outletChildren: outlet?.children?.length || 0,
    outletInnerHTMLPreview: (outlet?.innerHTML || '').substring(0, 300),
    outletNextSibling: outlet?.nextElementSibling?.tagName || null,
    learningProfileFound: !!lp,
    learningProfileHTML: lp?.outerHTML?.substring(0, 200) || null,
    navbarFound: !!navbar,
    bodyHTMLPreview: document.body?.innerHTML?.substring(0, 500),
  };
}
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        ctx.add_init_script(INIT_JS)
        page = ctx.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(
            {"type": msg.type, "text": msg.text[:400]}))
        page.on("pageerror", lambda err: console_logs.append(
            {"type": "pageerror", "text": str(err)[:600]}))

        report = {"pages": {}}

        for path in PAGES:
            ts = int(time.time() * 1000)
            url = f"http://127.0.0.1:8080{path}?_t={ts}"
            print(f"\n=== {path} ===")
            page_logs = []
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception as e:
                page_logs.append(f"navigation error: {e}")
            page.wait_for_timeout(2500)
            diag = page.evaluate(DIAGNOSE_JS)
            page_logs.append(f"diagnose: {diag}")
            try:
                shot = OUT / f"{path.strip('/').replace('/', '_')}.png"
                page.screenshot(path=str(shot), full_page=True)
                page_logs.append(f"screenshot: {shot}")
            except Exception as e:
                page_logs.append(f"screenshot error: {e}")

            p4b_logs = [log for log in console_logs
                        if '[P4-B]' in log.get('text', '')
                        or log.get('type') in ('error', 'pageerror', 'warning')]
            report["pages"][path] = {
                "diagnose": diag,
                "p4b_logs": p4b_logs[-10:],
                "log_count": len(console_logs),
            }
            for line in page_logs:
                print(" ", line)
            for log in p4b_logs[-5:]:
                print(f"  [{log['type']}] {log['text'][:200]}")

        report_path = OUT / "report.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                encoding='utf-8')
        print(f"\nReport saved: {report_path}")

        # 额外：尝试在 dashboard 页通过 routerLink 跳转 learning-profile
        print("\n=== extra: router-link jump test ===")
        try:
            page.goto("http://127.0.0.1:8080/user/dashboard?_t=" + str(int(time.time() * 1000)),
                       wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(1500)
            # 通过修改 history.pushState + dispatchEvent 模拟路由
            page.evaluate("""() => {
              const injector = window.ng?.getInjector?.(document.querySelector('app-root'));
              console.log('injector found:', !!injector);
              // 直接 navigateByUrl via history
              history.pushState({}, '', '/user/learning-profile?_t=' + Date.now());
              window.dispatchEvent(new PopStateEvent('popstate'));
            }""")
            page.wait_for_timeout(2500)
            diag2 = page.evaluate(DIAGNOSE_JS)
            print("after popstate:", diag2)
            page.screenshot(path=str(OUT / "popstate-jump.png"), full_page=True)
        except Exception as e:
            print(f"popstate jump error: {e}")

        browser.close()


if __name__ == "__main__":
    main()
