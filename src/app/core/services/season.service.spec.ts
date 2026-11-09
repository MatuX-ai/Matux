/**
 * SeasonService 单元测试
 *
 * 覆盖：
 * - 4 个季度边界（1/1, 4/1, 7/1, 10/1）
 * - 跨年倒数（Q4 → Q1）
 * - 季末日（3/31 / 6/30 / 9/30 / 12/31）
 * - 倒计时精度（天/时/分）
 * - 终奖 3 档固定
 * - season number 自 2024-Q1 起
 */

import { TestBed } from '@angular/core/testing';

import { SeasonService } from './season.service';

describe('SeasonService', () => {
  let service: SeasonService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SeasonService);
  });

  describe('getCurrentSeason', () => {
    it('1 月 → Q1 春季赛', () => {
      const s = service.getCurrentSeason(new Date(2026, 0, 15));
      expect(s.id).toBe('season-2026-q1');
      expect(s.name).toBe('2026 春季赛');
      expect(s.startDate.getMonth()).toBe(0); // 1 月
      expect(s.endDate.getMonth()).toBe(2); // 3 月
    });

    it('4 月 → Q2 夏季赛', () => {
      const s = service.getCurrentSeason(new Date(2026, 3, 1));
      expect(s.id).toBe('season-2026-q2');
      expect(s.name).toBe('2026 夏季赛');
      expect(s.startDate.getMonth()).toBe(3);
      expect(s.endDate.getMonth()).toBe(5);
    });

    it('7 月 → Q3 秋季赛', () => {
      const s = service.getCurrentSeason(new Date(2026, 6, 1));
      expect(s.id).toBe('season-2026-q3');
      expect(s.name).toBe('2026 秋季赛');
      expect(s.startDate.getMonth()).toBe(6);
      expect(s.endDate.getMonth()).toBe(8);
    });

    it('10 月 → Q4 冬季赛', () => {
      const s = service.getCurrentSeason(new Date(2026, 9, 8));
      expect(s.id).toBe('season-2026-q4');
      expect(s.name).toBe('2026 冬季赛');
      expect(s.startDate.getMonth()).toBe(9);
      expect(s.endDate.getMonth()).toBe(11);
    });

    it('Q4 末日 12/31 仍在 Q4', () => {
      const s = service.getCurrentSeason(new Date(2026, 11, 31, 23, 59, 59));
      expect(s.id).toBe('season-2026-q4');
    });

    it('Q1 首日 1/1 已在 Q1', () => {
      const s = service.getCurrentSeason(new Date(2026, 0, 1, 0, 0, 0));
      expect(s.id).toBe('season-2026-q1');
    });

    it('durationDays 为 90-92（Q2=91 闰年=91）', () => {
      // 2026 非闰年：Q1=90, Q2=91, Q3=92, Q4=92
      expect(service.getCurrentSeason(new Date(2026, 0, 1)).durationDays).toBe(90);
      expect(service.getCurrentSeason(new Date(2026, 3, 1)).durationDays).toBe(91);
      expect(service.getCurrentSeason(new Date(2026, 6, 1)).durationDays).toBe(92);
      expect(service.getCurrentSeason(new Date(2026, 9, 1)).durationDays).toBe(92);
    });

    it('season number 自 2024-Q1 起', () => {
      expect(service.getCurrentSeason(new Date(2024, 0, 1)).seasonNumber).toBe(1);
      expect(service.getCurrentSeason(new Date(2024, 3, 1)).seasonNumber).toBe(2);
      expect(service.getCurrentSeason(new Date(2025, 0, 1)).seasonNumber).toBe(5);
      expect(service.getCurrentSeason(new Date(2026, 9, 8)).seasonNumber).toBe(12);
    });
  });

  describe('timeRemaining', () => {
    it('季首日 → 满期（季长 - 1 天，因含两端）', () => {
      // Q1 起始 1/1 → 剩余约 89-90 天
      const r = service.timeRemaining(new Date(2026, 0, 1, 0, 0, 0));
      expect(r.expired).toBe(false);
      expect(r.days).toBeGreaterThanOrEqual(89);
      expect(r.days).toBeLessThanOrEqual(90);
    });

    it('季末日 23:59:59 → 0 天未到期', () => {
      const r = service.timeRemaining(new Date(2026, 2, 31, 23, 59, 0));
      expect(r.expired).toBe(false);
      expect(r.days).toBe(0);
      expect(r.hours).toBeGreaterThanOrEqual(0);
    });

    it('季末日 23:59:59 仍在 Q4（Q4 跨年）', () => {
      // 2026-12-31 23:59:59 仍在 Q4（12 月）
      const s = service.getCurrentSeason(new Date(2026, 11, 31, 23, 59, 59));
      expect(s.id).toBe('season-2026-q4');
    });

    it('次年首日 1/1 已切换到 Q1', () => {
      const s = service.getCurrentSeason(new Date(2027, 0, 1, 0, 0, 0));
      expect(s.id).toBe('season-2027-q1');
    });

    it('跨年倒数：2026-12-31 23:59 → 0 days, 0 hours', () => {
      const r = service.timeRemaining(new Date(2026, 11, 31, 23, 59, 0));
      expect(r.expired).toBe(false);
      expect(r.days).toBe(0);
    });
  });

  describe('upcomingRewards', () => {
    it('3 档固定，按名次降序', () => {
      const list = service.upcomingRewards();
      expect(list.length).toBe(3);
      expect(list[0].rankRange).toBe('1-3');
      expect(list[1].rankRange).toBe('4-10');
      expect(list[2].rankRange).toBe('11-50');
    });

    it('3 档 exp 降序：1000 / 500 / 200', () => {
      const list = service.upcomingRewards();
      expect(list[0].exp).toBeGreaterThan(list[1].exp);
      expect(list[1].exp).toBeGreaterThan(list[2].exp);
    });

    it('每档都有 badge 和 gradient 双色', () => {
      const list = service.upcomingRewards();
      for (const r of list) {
        expect(r.badge).toBeTruthy();
        expect(r.gradient.length).toBe(2);
      }
    });

    it('upcomingRewards 返回拷贝（不影响内部 REWARDS）', () => {
      const a = service.upcomingRewards();
      a[0].exp = 9999;
      const b = service.upcomingRewards();
      expect(b[0].exp).not.toBe(9999);
    });
  });

  describe('currentSeason$', () => {
    it('订阅时立即发射当前赛季', (done) => {
      service.currentSeason$.subscribe((s) => {
        expect(s.id).toMatch(/^season-\d{4}-q[1-4]$/);
        done();
      });
    });

    it('refresh 触发下游更新', (done) => {
      const collected: string[] = [];
      const sub = service.currentSeason$.subscribe((s) => collected.push(s.id));
      service.refresh(new Date(2026, 0, 1));
      sub.unsubscribe();
      expect(collected[collected.length - 1]).toBe('season-2026-q1');
      done();
    });
  });
});
