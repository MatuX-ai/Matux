# -*- coding: utf-8 -*-
"""
第五轮验证: 直接用 Playwright 验证 R-01 / R-02 修复点
"""
import asyncio, os, json, time
from playwright.async_api import async_playwright

OUTPUT_DIR = r'I:\iMato\screenshots\ux-session-20261006-5'
REPORT_DIR = r'I:\iMato\reports\ux-session-20261006-5'
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# 测试账号 user_data (与第三/四轮一致)
USER_DATA = {
    'id': 1,
    'username': 'test_ux5',
    'nickname': 'UX5 Test',
    'email': 'ux5@test.com',
    'orgId': 1,
    'role': 'student'
}

INIT_SCRIPT = f"""
window.localStorage.setItem('user_data', JSON.stringify({json.dumps(USER_DATA)}));
"""

results = {
    'R-01_growth_trajectory_banner': {'passed': False, 'evidence': []},
    'R-02_ai_edu_banner_top': {'passed': False, 'evidence': []},
}

async def check_r1(page):
    """验证 /user/growth-trajectory backend down 时顶部 fallback banner"""
    print('\n[R-01] 访问 /user/growth-trajectory...')
    await page.goto('http://localhost:8080/user/growth-trajectory', wait_until='domcontentloaded')
    await page.screenshot(path=os.path.join(OUTPUT_DIR, '01-growth-trajectory-initial.png'))
    print('[R-01] 已截图: initial')

    # 等待 ModuleStatusService 完成 3 次失败检测 (~15s)
    print('[R-01] 等待 15s 让 backend 健康检测失败阈值到达...')
    await asyncio.sleep(15)
    await page.screenshot(path=os.path.join(OUTPUT_DIR, '01-growth-trajectory-after-15s.png'), full_page=True)
    print('[R-01] 已截图: after-15s')

    # 检测 fallback-banner DOM
    banner_count = await page.locator('.fallback-banner').count()
    cloud_off_count = await page.locator('.fallback-banner mat-icon:has-text("cloud_off")').count()
    has_demo_text = await page.locator('.fallback-banner:has-text("演示数据")').count()
    has_retry_btn = await page.locator('.fallback-banner button:has-text("重试")').count()

    results['R-01_growth_trajectory_banner']['evidence'] = {
        'fallback_banner_count': banner_count,
        'cloud_off_icon': cloud_off_count,
        'demo_text_present': has_demo_text > 0,
        'retry_button_present': has_retry_btn > 0,
    }
    passed = banner_count > 0 and cloud_off_count > 0 and has_demo_text > 0 and has_retry_btn > 0
    results['R-01_growth_trajectory_banner']['passed'] = passed
    print(f'[R-01] 结果: {results["R-01_growth_trajectory_banner"]}')


async def check_r2(page):
    """验证 /ai-edu fallback banner 移到顶部 + cloud_off + 重新加载按钮"""
    print('\n[R-02] 访问 /ai-edu...')
    await page.goto('http://localhost:8080/ai-edu', wait_until='domcontentloaded')
    await page.screenshot(path=os.path.join(OUTPUT_DIR, '02-ai-edu-initial.png'))
    print('[R-02] 已截图: initial')

    # 等待 fallback 触发 (~8s: 5s HTTP 超时 + 3s catchError 处理)
    print('[R-02] 等待 10s 让 fallback 触发...')
    await asyncio.sleep(10)
    await page.screenshot(path=os.path.join(OUTPUT_DIR, '02-ai-edu-after-10s.png'), full_page=True)
    print('[R-02] 已截图: after-10s')

    # 检测 fallback-banner-top
    banner_top_count = await page.locator('.fallback-banner-top').count()
    cloud_off_in_top = await page.locator('.fallback-banner-top mat-icon:has-text("cloud_off")').count()
    has_backend_msg = await page.locator('.fallback-banner-top:has-text("后端不可达")').count()
    has_reload_btn = await page.locator('.fallback-banner-top button:has-text("重新加载")').count()

    # 验证 banner 位置在 modules-grid 之前 (检查 DOM 顺序)
    grid_count = await page.locator('.modules-grid').count()
    grid_box = None
    banner_box = None
    if grid_count > 0 and banner_top_count > 0:
        grid_box = await page.locator('.modules-grid').first.bounding_box()
        banner_box = await page.locator('.fallback-banner-top').first.bounding_box()

    results['R-02_ai_edu_banner_top']['evidence'] = {
        'banner_top_count': banner_top_count,
        'cloud_off_in_top': cloud_off_in_top,
        'backend_msg_present': has_backend_msg > 0,
        'reload_button_present': has_reload_btn > 0,
        'grid_y': grid_box['y'] if grid_box else None,
        'banner_y': banner_box['y'] if banner_box else None,
        'banner_above_grid': (banner_box['y'] < grid_box['y']) if (banner_box and grid_box) else None,
    }
    passed = (banner_top_count > 0 and cloud_off_in_top > 0
              and has_backend_msg > 0 and has_reload_btn > 0
              and results['R-02_ai_edu_banner_top']['evidence']['banner_above_grid'] == True)
    results['R-02_ai_edu_banner_top']['passed'] = passed
    print(f'[R-02] 结果: {results["R-02_ai_edu_banner_top"]}')


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=r'C:\Users\Administrator\AppData\Local\ms-playwright\chromium-1243\chrome-win64\chrome.exe')
        context = await browser.new_context(viewport={'width': 1366, 'height': 900}, locale='zh-CN')
        await context.add_init_script(INIT_SCRIPT)
        page = await context.new_page()
        page.on('console', lambda msg: print(f'  [browser-{msg.type}] {msg.text}') if msg.type in ['error', 'warning'] else None)

        await check_r1(page)
        await check_r2(page)

        await browser.close()

    # 写入报告
    with open(os.path.join(REPORT_DIR, 'round5-results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print('\n========== 第五轮验证总结 ==========')
    for name, r in results.items():
        status = 'PASS' if r['passed'] else 'FAIL'
        print(f'{name}: {status}')
        print(f'  evidence: {r["evidence"]}')

asyncio.run(main())
