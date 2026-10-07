# -*- coding: utf-8 -*-
"""
R-01 强制 mock backend down 验证: 拦截 /api/v1/ai-teacher/growth/:userId 返回 502
"""
import asyncio, os, json
from playwright.async_api import async_playwright

OUT = r'I:\iMato\screenshots\ux-session-20261006-5'
os.makedirs(OUT, exist_ok=True)

USER_DATA = {'id': 1, 'username': 'diag_r1', 'nickname': 'DiagR1', 'email': 'diag@test.com', 'orgId': 1, 'role': 'student'}
INIT = f"""
window.localStorage.setItem('user_data', JSON.stringify({json.dumps(USER_DATA)}));
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=r'C:\Users\Administrator\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe')
        ctx = await browser.new_context(viewport={'width': 1366, 'height': 900}, locale='zh-CN')
        await ctx.add_init_script(INIT)
        page = await ctx.new_page()
        page.on('console', lambda m: print(f'  [console-{m.type}] {m.text[:200]}') if m.type in ['error', 'warning'] else None)

        # 拦截 ai-teacher/growth 强制 502，让 service 走 catchError fallback
        async def mock_growth(route, req):
            if 'ai-teacher/growth' in req.url:
                await route.fulfill(status=502, content_type='application/json', body=json.dumps({'error': 'backend down'}))
            elif 'health-detail' in req.url:
                # 让 health-detail 也失败 3 次让 healthy$ 变 false
                await route.fulfill(status=502, content_type='application/json', body=json.dumps({'error': 'backend down'}))
            else:
                await route.continue_()
        await page.route('**/api/v1/**', mock_growth)

        await page.goto('http://localhost:8080/user/growth-trajectory', wait_until='domcontentloaded')
        await page.screenshot(path=os.path.join(OUT, '01-r1-initial.png'))

        # 等待 30 秒: 让 health-detail 失败 3 次 (间隔 30s 但 polling 启动立即调用)
        # 实际：第一次调用立即失败 → 累计 1 次 → 30s 后 → 累计 2 次 → 30s 后 → 累计 3 次 → healthy=false
        # 但初次 fetchHealth() 是同步调用一次，然后 interval 30s 才开始下一次
        # 所以从订阅 healthy$ 开始需要：1次失败 + 2次interval(30s) + 失败 = 60+秒
        # 但我们的 R-01 修代码订阅 healthy$，初始 false（因为 BehaviorSubject 初始 false）
        # 而 subscription 立即 emit 当前值 → backendAvailable 初始 false → banner 短暂显示
        # 但 fetchHealth() 5s 内成功 → healthy$.next(true) → backendAvailable 变 true → banner 消失

        # 我们的 mock 让 health-detail 一直 502，所以 healthy$ 应该是从 false 开始
        # 然后 3 次失败后变成 false(初始已经 false) → 保持 false
        for t in [2, 5, 10, 15]:
            await asyncio.sleep(t - (2 if t==2 else (t - 3 if t==5 else (t - 7 if t==10 else 5))))
            banner_count = await page.locator('.fallback-banner').count()
            cloud_off = await page.locator('.fallback-banner mat-icon:has-text("cloud_off")').count()
            demo_text = await page.locator('.fallback-banner:has-text("演示数据")').count()
            retry_btn = await page.locator('.fallback-banner button:has-text("重试")').count()
            trajectory_visible = await page.locator('app-growth-trajectory').count()
            print(f'[T+{t}s] banner={banner_count} cloud_off={cloud_off} demo_text={demo_text} retry_btn={retry_btn} trajectory={trajectory_visible}')

        page_html = await page.content()
        for kw in ['fallback-banner', '演示数据', 'cloud_off']:
            cnt = page_html.count(kw)
            print(f'\nDOM 中 "{kw}" 出现 {cnt} 次')

        await page.screenshot(path=os.path.join(OUT, '01-r1-forced-502.png'), full_page=True)
        await browser.close()

asyncio.run(main())
