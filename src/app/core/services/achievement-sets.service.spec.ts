/**
 * AchievementSetsService 单元测试（P2-B）
 */

import { TestBed } from '@angular/core/testing';

import {
  AchievementBadge,
  AchievementRarity,
  ExtendedAchievementBadge,
} from '../../features/achievement-integration/models/achievement.model';
import { AchievementSetsService } from './achievement-sets.service';

describe('AchievementSetsService', () => {
  let service: AchievementSetsService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AchievementSetsService);
  });

  // ================ getAllSets ================

  describe('getAllSets', () => {
    it('should return at least 4 default sets', () => {
      const sets = service.getAllSets();
      expect(sets.length).toBeGreaterThanOrEqual(4);
    });

    it('should sort by order (first-steps first)', () => {
      const sets = service.getAllSets();
      const firstSet = sets[0];
      expect(firstSet.id).toBe('set-first-steps');
    });

    it('each set should have required fields', () => {
      const sets = service.getAllSets();
      for (const set of sets) {
        expect(set.id).toBeDefined();
        expect(set.name).toBeDefined();
        expect(set.achievementIds.length).toBeGreaterThan(0);
        expect(set.emoji).toBeDefined();
        expect(set.color).toMatch(/^#[0-9a-f]{6}$/i);
      }
    });
  });

  // ================ getSetById ================

  describe('getSetById', () => {
    it('should return set by ID', () => {
      const set = service.getSetById('set-perfect-attendance');
      expect(set?.name).toBe('全勤奖');
    });

    it('should return undefined for unknown ID', () => {
      expect(service.getSetById('nonexistent')).toBeUndefined();
    });
  });

  // ================ enhanceBadges ================

  describe('enhanceBadges', () => {
    it('should auto-fill unlockRate, totalHolders, pointsValue', () => {
      const badges: AchievementBadge[] = [
        createBadge('ach-1', '成就1', AchievementRarity.COMMON, true),
        createBadge('ach-2', '成就2', AchievementRarity.LEGENDARY, false),
      ];
      const enhanced = service.enhanceBadges(badges);
      expect(enhanced.length).toBe(2);
      expect(enhanced[0].unlockRate).toBeGreaterThan(0);
      expect(enhanced[1].unlockRate).toBeGreaterThanOrEqual(0);
      expect(enhanced[0].totalHolders).toBeDefined();
      expect(enhanced[0].pointsValue).toBe(10);
      expect(enhanced[1].pointsValue).toBe(250);
    });

    it('should infer setId correctly', () => {
      const badges: AchievementBadge[] = [
        createBadge('streak-7', '打卡7天', AchievementRarity.COMMON, false),
        createBadge('streak-30', '打卡30天', AchievementRarity.RARE, true),
      ];
      const enhanced = service.enhanceBadges(badges);
      expect(enhanced[0].setId).toBe('set-perfect-attendance');
      expect(enhanced[1].setId).toBe('set-perfect-attendance');
    });

    it('should infer relatedSkillIds', () => {
      const badges: AchievementBadge[] = [
        createBadge('py-loop-ach', '循环大师', AchievementRarity.RARE, false),
      ];
      const enhanced = service.enhanceBadges(badges);
      expect(enhanced[0].relatedSkillIds).toContain('py-loop-ach');
    });

    it('unlock rate should decrease with rarity', () => {
      const badges: AchievementBadge[] = [
        createBadge('c1', '普通', AchievementRarity.COMMON, false),
        createBadge('u1', '少见', AchievementRarity.UNCOMMON, false),
        createBadge('r1', '稀有', AchievementRarity.RARE, false),
        createBadge('e1', '史诗', AchievementRarity.EPIC, false),
        createBadge('l1', '传说', AchievementRarity.LEGENDARY, false),
      ];
      const enhanced = service.enhanceBadges(badges);
      const rates = [
        enhanced.find((e) => e.id === 'c1')!.unlockRate!,
        enhanced.find((e) => e.id === 'u1')!.unlockRate!,
        enhanced.find((e) => e.id === 'r1')!.unlockRate!,
        enhanced.find((e) => e.id === 'e1')!.unlockRate!,
        enhanced.find((e) => e.id === 'l1')!.unlockRate!,
      ];
      for (let i = 0; i < rates.length - 1; i++) {
        expect(rates[i]).toBeGreaterThanOrEqual(rates[i + 1]);
      }
    });
  });

  // ================ computeProgress ================

  describe('computeProgress', () => {
    it('should correctly compute set progress', () => {
      const set = service.getSetById('set-perfect-attendance')!;
      const badges: ExtendedAchievementBadge[] = [
        createBadge('streak-7', '7天', AchievementRarity.COMMON, true),
        createBadge('streak-14', '14天', AchievementRarity.RARE, true),
        createBadge('streak-30', '30天', AchievementRarity.EPIC, false),
        createBadge('streak-60', '60天', AchievementRarity.EPIC, false),
        createBadge('streak-100', '100天', AchievementRarity.LEGENDARY, false),
      ];
      const enhanced = service.enhanceBadges(badges);
      const progress = service.computeProgress(set, enhanced);

      expect(progress.totalCount).toBe(5);
      expect(progress.unlockedCount).toBe(2);
      expect(progress.completionPercent).toBeCloseTo(0.4, 1);
      expect(progress.isCompleted).toBe(false);
      expect(progress.remaining.length).toBe(3);
    });

    it('all unlocked should mark isCompleted', () => {
      const set = service.getSetById('set-perfect-attendance')!;
      const badges: ExtendedAchievementBadge[] = [
        createBadge('streak-7', '7天', AchievementRarity.COMMON, true),
        createBadge('streak-14', '14天', AchievementRarity.RARE, true),
        createBadge('streak-30', '30天', AchievementRarity.EPIC, true),
        createBadge('streak-60', '60天', AchievementRarity.EPIC, true),
        createBadge('streak-100', '100天', AchievementRarity.LEGENDARY, true),
      ];
      const enhanced = service.enhanceBadges(badges);
      const progress = service.computeProgress(set, enhanced);
      expect(progress.isCompleted).toBe(true);
      expect(progress.completionPercent).toBe(1);
    });

    it('empty badges should return 0% progress', () => {
      const set = service.getSetById('set-perfect-attendance')!;
      const progress = service.computeProgress(set, []);
      expect(progress.unlockedCount).toBe(0);
      expect(progress.completionPercent).toBe(0);
      expect(progress.isCompleted).toBe(false);
    });

    it('remaining should include unlocked and missing achievements', () => {
      const set = service.getSetById('set-perfect-attendance')!;
      const badges: ExtendedAchievementBadge[] = [
        createBadge('streak-7', '7天', AchievementRarity.COMMON, true),
      ];
      const enhanced = service.enhanceBadges(badges);
      const progress = service.computeProgress(set, enhanced);
      expect(progress.remaining.length).toBe(4);
      for (const r of progress.remaining) {
        expect(r.unlocked).toBe(false);
      }
    });
  });

  // ================ computeAllProgress ================

  describe('computeAllProgress', () => {
    it('should return progress for all sets', () => {
      const badges = service.enhanceBadges([]);
      const progressList = service.computeAllProgress(badges);
      expect(progressList.length).toBe(service.getAllSets().length);
    });

    it('order should match getAllSets', () => {
      const badges = service.enhanceBadges([]);
      const sets = service.getAllSets();
      const progressList = service.computeAllProgress(badges);
      for (let i = 0; i < sets.length; i++) {
        expect(progressList[i].set.id).toBe(sets[i].id);
      }
    });
  });

  // ================ summarize ================

  describe('summarize', () => {
    it('should compute totals, unlocked, locked, unlock rate', () => {
      const badges = service.enhanceBadges([
        createBadge('a1', 'a1', AchievementRarity.COMMON, true),
        createBadge('a2', 'a2', AchievementRarity.COMMON, true),
        createBadge('a3', 'a3', AchievementRarity.COMMON, false),
        createBadge('a4', 'a4', AchievementRarity.RARE, false),
      ]);
      const summary = service.summarize(badges);
      expect(summary.total).toBe(4);
      expect(summary.unlocked).toBe(2);
      expect(summary.locked).toBe(2);
      expect(summary.unlockRate).toBe(0.5);
    });

    it('should group by rarity', () => {
      const badges = service.enhanceBadges([
        createBadge('a1', 'a1', AchievementRarity.COMMON, true),
        createBadge('a2', 'a2', AchievementRarity.COMMON, true),
        createBadge('a3', 'a3', AchievementRarity.RARE, false),
      ]);
      const summary = service.summarize(badges);
      expect(summary.byRarity[AchievementRarity.COMMON].total).toBe(2);
      expect(summary.byRarity[AchievementRarity.COMMON].unlocked).toBe(2);
      expect(summary.byRarity[AchievementRarity.RARE].total).toBe(1);
      expect(summary.byRarity[AchievementRarity.RARE].unlocked).toBe(0);
    });

    it('should correctly compute points statistics', () => {
      const badges = service.enhanceBadges([
        createBadge('a1', 'a1', AchievementRarity.COMMON, true),
        createBadge('a2', 'a2', AchievementRarity.LEGENDARY, true),
        createBadge('a3', 'a3', AchievementRarity.RARE, false),
      ]);
      const summary = service.summarize(badges);
      expect(summary.totalPoints).toBe(310);
      expect(summary.earnedPoints).toBe(260);
    });

    it('recentUnlocks should sort by date desc and limit to 5', () => {
      const badges = service.enhanceBadges([
        createBadge('a1', 'a1', AchievementRarity.COMMON, true, '2024-01-01'),
        createBadge('a2', 'a2', AchievementRarity.COMMON, true, '2024-06-15'),
        createBadge('a3', 'a3', AchievementRarity.COMMON, true, '2024-03-10'),
        createBadge('a4', 'a4', AchievementRarity.COMMON, false),
      ]);
      const summary = service.summarize(badges);
      expect(summary.recentUnlocks.length).toBe(3);
      expect(summary.recentUnlocks[0].id).toBe('a2');
    });
  });

  // ================ recommendNext ================

  describe('recommendNext', () => {
    it('should return incomplete sets with progress > 0', () => {
      const badges = service.enhanceBadges([
        createBadge('streak-7', '7天', AchievementRarity.COMMON, true),
        createBadge('streak-14', '14天', AchievementRarity.RARE, false),
        createBadge('py-variable', '变量', AchievementRarity.COMMON, true),
      ]);
      const recs = service.recommendNext(badges);
      expect(recs.length).toBeGreaterThan(0);
      for (const rec of recs) {
        expect(rec.unlockedCount).toBeGreaterThan(0);
        expect(rec.isCompleted).toBe(false);
      }
    });

    it('should return non-empty when some sets have progress', () => {
      const badges = service.enhanceBadges([
        createBadge('streak-7', '7天', AchievementRarity.COMMON, true),
      ]);
      const recs = service.recommendNext(badges);
      expect(recs.length).toBeGreaterThanOrEqual(1);
    });

    it('empty badges should return empty', () => {
      const recs = service.recommendNext([]);
      expect(recs.length).toBe(0);
    });
  });
});

// ================ Helpers ================

function createBadge(
  id: string,
  name: string,
  rarity: AchievementRarity,
  unlocked: boolean,
  unlockedDate?: string
): AchievementBadge {
  return {
    id,
    name,
    description: '成就描述',
    icon: '🏆',
    rarity,
    unlocked,
    unlockedDate,
  };
}