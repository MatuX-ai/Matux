/**
 * 【P3-A-1】AchievementStatsService 单元测试
 *
 * 覆盖：
 * - loadStats() 拉取并缓存
 * - getStats() 同步返回缓存值
 * - getStats$() 异步首次拉取
 * - refresh() 强制刷新
 * - clear() 清空缓存
 * - 60s TTL 缓存复用
 * - 拉取失败时降级到旧缓存
 */

import { TestBed } from '@angular/core/testing';
import {
  HttpClientTestingModule,
  HttpTestingController,
} from '@angular/common/http/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';

import {
  AchievementStatsService,
  AchievementStats,
} from './achievement-stats.service';

describe('AchievementStatsService', () => {
  let service: AchievementStatsService;
  let httpMock: HttpTestingController;

  const mockBackendList = [
    {
      id: 1,
      name: '循环大师',
      rarity: 'rare',
      total_unlocked: 1234,
      unlock_rate: 0.25,
      global_unlock_rate: 0.18,
      total_holders: 1800,
      stats_updated_at: '2026-10-09T00:00:00Z',
    },
    {
      id: 2,
      name: '初学者',
      rarity: 'common',
      total_unlocked: 5000,
      unlock_rate: 0.75,
      global_unlock_rate: 0.72,
      total_holders: 7200,
      stats_updated_at: '2026-10-09T00:00:00Z',
    },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        AchievementStatsService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(AchievementStatsService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  // ================ loadStats() ================

  describe('loadStats()', () => {
    it('应调用 /stats/batch 端点并规范化返回数据', async () => {
      const promise = service.loadStats();

      const req = httpMock.expectOne((r) => r.url.includes('/achievements/stats/batch'));
      expect(req.request.method).toBe('GET');
      req.flush({ success: true, data: mockBackendList });

      const map = await promise;
      expect(map.size).toBe(2);
      const first = map.get('1') as AchievementStats;
      expect(first.name).toBe('循环大师');
      expect(first.globalUnlockRate).toBe(0.18);
      expect(first.totalHolders).toBe(1800);
    });

    it('应在 60s 内复用缓存（不重复请求）', async () => {
      const promise1 = service.loadStats();
      const req1 = httpMock.expectOne((r) => r.url.includes('/achievements/stats/batch'));
      req1.flush({ success: true, data: mockBackendList });
      await promise1;

      // 第二次调用应直接返回缓存，不发请求
      const map2 = await service.loadStats();
      expect(map2.size).toBe(2);
      httpMock.expectNone((r) => r.url.includes('/achievements/stats/batch'));
    });

    it('拉取失败时应返回旧缓存而不抛错', async () => {
      // 第一次成功
      const p1 = service.loadStats();
      const req1 = httpMock.expectOne((r) => r.url.includes('/achievements/stats/batch'));
      req1.flush({ success: true, data: mockBackendList });
      const map1 = await p1;

      // 强制刷新
      const p2 = service.refresh();
      const req2 = httpMock.expectOne((r) => r.url.includes('/achievements/stats/batch'));
      req2.error(new ProgressEvent('error'), { status: 500, statusText: 'Server Error' });

      const map2 = await p2;
      // 应降级到旧缓存
      expect(map2.size).toBe(map1.size);
    });
  });

  // ================ getStats() ================

  describe('getStats()', () => {
    it('未加载时应返回 undefined', () => {
      expect(service.getStats('1')).toBeUndefined();
    });

    it('加载后应同步返回缓存值', async () => {
      const p = service.loadStats();
      httpMock.expectOne((r) => r.url.includes('/achievements/stats/batch')).flush({
        success: true,
        data: mockBackendList,
      });
      await p;

      const stats = service.getStats('1');
      expect(stats).toBeDefined();
      expect(stats?.globalUnlockRate).toBe(0.18);
    });

    it('应支持 number 和 string 类型的 id', async () => {
      const p = service.loadStats();
      httpMock.expectOne((r) => r.url.includes('/achievements/stats/batch')).flush({
        success: true,
        data: mockBackendList,
      });
      await p;

      expect(service.getStats(1)).toBeDefined();
      expect(service.getStats('1')).toBeDefined();
    });
  });

  // ================ clear() ================

  describe('clear()', () => {
    it('应清空缓存并重置 lastLoadedAt', async () => {
      const p = service.loadStats();
      httpMock.expectOne((r) => r.url.includes('/achievements/stats/batch')).flush({
        success: true,
        data: mockBackendList,
      });
      await p;

      service.clear();
      expect(service.getStats('1')).toBeUndefined();
    });
  });

  // ================ refresh() ================

  describe('refresh()', () => {
    it('应忽略 TTL 立即发请求', async () => {
      const p1 = service.loadStats();
      httpMock.expectOne((r) => r.url.includes('/achievements/stats/batch')).flush({
        success: true,
        data: mockBackendList,
      });
      await p1;

      // refresh 应立即发请求
      const p2 = service.refresh();
      const req2 = httpMock.expectOne((r) => r.url.includes('/achievements/stats/batch'));
      req2.flush({ success: true, data: mockBackendList });
      const map2 = await p2;
      expect(map2.size).toBe(2);
    });
  });

  // ================ 数据规范化 ================

  describe('数据规范化', () => {
    it('应将 snake_case 字段转换为 camelCase', async () => {
      const p = service.loadStats();
      httpMock.expectOne((r) => r.url.includes('/achievements/stats/batch')).flush({
        success: true,
        data: mockBackendList,
      });
      await p;

      const stats = service.getStats('1')!;
      // camelCase fields
      expect(stats.totalUnlocked).toBe(1234);
      expect(stats.unlockRate).toBe(0.25);
      expect(stats.globalUnlockRate).toBe(0.18);
      expect(stats.totalHolders).toBe(1800);
      expect(stats.statsUpdatedAt).toBe('2026-10-09T00:00:00Z');
    });

    it('空 data 数组应返回空 Map', async () => {
      const p = service.loadStats();
      httpMock.expectOne((r) => r.url.includes('/achievements/stats/batch')).flush({
        success: true,
        data: [],
      });
      const map = await p;
      expect(map.size).toBe(0);
    });
  });

  // ================ getStats$() ================

  describe('getStats$()', () => {
    it('命中缓存时应立即返回', (done) => {
      // 预热缓存
      const p = service.loadStats();
      httpMock.expectOne((r) => r.url.includes('/achievements/stats/batch')).flush({
        success: true,
        data: mockBackendList,
      });
      p.then(() => {
        service.getStats$('1').subscribe((stats) => {
          expect(stats?.globalUnlockRate).toBe(0.18);
          done();
        });
      });
    });
  });
});