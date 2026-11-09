/**
 * FeedbackFlyService 单元测试
 */

import { TestBed } from '@angular/core/testing';
import { NgZone } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { FeedbackFlyService } from './feedback-fly.service';

function createRect(left: number, top: number, width: number, height: number): DOMRect {
  return {
    left,
    top,
    right: left + width,
    bottom: top + height,
    width,
    height,
    x: left,
    y: top,
    toJSON: () => ({}),
  } as DOMRect;
}

describe('FeedbackFlyService (P0-1)', () => {
  let service: FeedbackFlyService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FeedbackFlyService);
    // 确保 zone 内运行
    TestBed.inject(NgZone).run(() => {});
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('flyNumber: 缺失源/目标直接完成 + 推送 hit', async () => {
    const hitPromise = firstValueFrom(service.hit$);
    const done = firstValueFrom(service.flyNumber(null as any, null as any, '+10', '#fbbf24'));
    const hit = await hitPromise;
    expect(hit.text).toBe('+10');
    await done;
  });

  it('flyNumber: 完成后 emit 完成事件', async () => {
    const src = document.createElement('div');
    const dst = document.createElement('div');
    document.body.appendChild(src);
    document.body.appendChild(dst);
    spyOn(src, 'getBoundingClientRect').and.returnValue(createRect(10, 10, 50, 20));
    spyOn(dst, 'getBoundingClientRect').and.returnValue(createRect(500, 100, 60, 24));
    const done = firstValueFrom(service.flyNumber(src, dst, '+30', '#fbbf24'));
    await expectAsync(done).toBeResolved();
    // 清理 DOM
    document.body.removeChild(src);
    document.body.removeChild(dst);
    // 清理可能残留 ghost
    document.querySelectorAll('span').forEach((s) => {
      if (s.textContent === '+30') s.remove();
    });
  });

  it('flyCard: 源缺失时立即完成', async () => {
    const done = firstValueFrom(service.flyCard(null as any));
    await expectAsync(done).toBeResolved();
  });

  it('hit$ 是 Observable', () => {
    expect(service.hit$.subscribe).toBeDefined();
  });
});
