# -*- coding: utf-8 -*-
"""
Round5 v2 验证: 注入完整 auth + mock 拦截 backend down
"""
import asyncio, os, json
from playwright.async_api import async_playwright

OUT = r'I:\iMato\screenshots\ux-session-20261006-5'
RPT = r'I:\iMato\reports\ux-session-20261006-5'
os.makedirs(OUT, exist_ok=True)
os.makedirs(RPT, exist_ok=True)

# 完整 auth 注入: user_data + access_token + remember_me
USER_DATA = {'id': 1, 'username': 'r5v2', 'nickname': 'R5V2', 'email': 'r5v2@test.com', 'orgId': 1, 'role': 'student'}
MOCK_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaWF0IjoxNzE0MDAwMDAwLCJleHAiOjk5OTk5OTk5OTl9.test'
INIT = f"""
window.localStorage.setItem('user_data', JSON.stringify({json.dumps(USER_DATA)}));
window.localStorage.setItem('access_token', '{MOCK_TOKEN}');
window.localStorage.setItem('remember_me', 'true');
"""

results = {
    'R-01_growth_trajectory_banner': {'passed': False, 'evidence': {}},
    'R-02_ai_edu_banner_top': {'passed': False, 'evidence': {}},
}


async def mock_backend_down(route, req):
    """Mock backend down: 返回 502"""
    if 'api/v1' in req.url:
        await route.fulfill(status=502, content_type='application/json', body='{}')
    else:
        await route.continue_()


async def check_r1(page):
    print('\n[R-01] 访问 /user/growth-trajectory (mock backend down)...')
    await page.goto('http://localhost:8080/user/growth-trajectory', wait_until='domcontentloaded')
    await asyncio.sleep(8)

    banner_count = await page.locator('.fallback-banner').count()
    cloud_off = await page.locator('.fallback-banner mat-icon:has-text("cloud_off")').count()
    demo_text = await page.locator('.fallback-banner:has-text("\u6f14\u793a\u6570\u636e")').count()
    retry_btn = await page.locator('.fallback-banner button:has-text("\u91cd\u8bd5")').count()
    trajectory = await page.locator('app-growth-trajectory').count()

    results['R-01_growth_trajectory_banner']['evidence'] = {
        'fallback_banner_count': banner_count,
        'cloud_off_icon': cloud_off,
        'demo_text_present': demo_text > 0,
        'retry_button_present': retry_btn > 0,
        'trajectory_visible': trajectory > 0,
        'url': page.url,
    }
    passed = banner_count > 0 and cloud_off > 0 and demo_text > 0 and retry_btn > 0
    results['R-01_growth_trajectory_banner']['passed'] = passed
    await page.screenshot(path=os.path.join(OUT, 'r5v2-01-growth-trajectory.png'), full_page=True)
    print(f'[R-01] {results["R-01_growth_trajectory_banner"]}')


async def check_r2(page):
    print('\n[R-02] 访问 /ai-edu (mock backend down)...')
    await page.goto('http://localhost:8080/ai-edu', wait_until='domcontentloaded')
    await asyncio.sleep(10)

    banner_top = await page.locator('.fallback-banner-top').count()
    cloud_off = await page.locator('.fallback-banner-top mat-icon:has-text("cloud_off")').count()
    backend_msg = await page.locator('.fallback-banner-top:has-text("\u540e\u7aef\u4e0d\u53ef\u8fbe")').count()
    reload_btn = await page.locator('.fallback-banner-top button:has-text("\u91cd\u65b0\u52a0\u8f7d")').count()
    modules = await page.locator('.modules-grid .module-card').count()

    grid_y = None
    banner_y = None
    if banner_top > 0:
        try:
            banner_box = await page.locator('.fallback-banner-top').first.bounding_box()
            banner_y = banner_box['y'] if banner_box else None
        except:
            pass
    if modules > 0:
        try:
            grid_box = await page.locator('.modules-grid').first.bounding_box()
            grid_y = grid_box['y'] if grid_box else None
        except:
            pass

    results['R-02_ai_edu_banner_top']['evidence'] = {
        'banner_top_count': banner_top,
        'cloud_off_in_top': cloud_off,
        'backend_msg_present': backend_msg > 0,
        'reload_button_present': reload_btn > 0,
        'modules_count': modules,
        'banner_y': banner_y,
        'grid_y': grid_y,
        'banner_above_grid': (banner_y is not None and grid_y is not None and banner_y < grid_y),
        'url': page.url,
    }
    passed = (banner_top > 0 and cloud_off > 0 and backend_msg > 0 and reload_btn > 0
              and results['R-02_ai_edu_banner_top']['evidence']['banner_above_grid'])
    results['R-02_ai_edu_banner_top']['passed'] = passed
    await page.screenshot(path=os.path.join(OUT, 'r5v2-02-ai-edu.png'), full_page=True)
    print(f'[R-02] {results["R-02_ai_edu_banner_top"]}')


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=r'C:\Users\Administrator\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe')
        ctx = await browser.new_context(viewport={'width': 1366, 'height': 900}, locale='zh-CN')
        await ctx.add_init_script(INIT)
        await ctx.route('**/api/v1/**', mock_backend_down)
        page = await ctx.new_page()
        page.on('console', lambda m: print(f'  [c-{m.type}] {m.text[:120]}') if m.type in ['error', 'warning'] else None)

        await check_r1(page)
        await check_r2(page)

        await browser.close()

    with open(os.path.join(RPT, 'round5-v2-results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print('\n========== Round5 v2 总结 ==========')
    for n, r in results.items():
        st = 'PASS' if r['passed'] else 'FAIL'
        print(f'{n}: {st}')
        print(f'  {r["evidence"]}')


asyncio.run(main())
