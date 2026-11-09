/**
 * LevelTitleService 单元测试
 */

import { TestBed } from '@angular/core/testing';

import { LevelTitleService } from './level-title.service';

describe('LevelTitleService (P0-3)', () => {
  let service: LevelTitleService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(LevelTitleService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('getTitleByLevel: 越界保护 (level=0 返回 Lv1)', () => {
    const r = service.getTitleByLevel(0);
    expect(r.level).toBe(1);
    expect(r.tier).toBe('bronze');
  });

  it('getTitleByLevel: 越界保护 (level=99 截断 Lv10)', () => {
    const r = service.getTitleByLevel(99);
    expect(r.level).toBe(10);
    expect(r.tier).toBe('star');
  });

  it('getTitleByLevel: Lv5 映射到 silver + nextBadgeIcon 非空', () => {
    const r = service.getTitleByLevel(5);
    expect(r.tier).toBe('silver');
    expect(r.nextBadgeIcon).toBeTruthy();
    expect(r.cumulativeExp).toBe(1500);
  });

  it('getNextTitle: 满级返 null', () => {
    expect(service.getNextTitle(10)).toBeNull();
  });

  it('getNextTitle: Lv3 返 Lv4 数据', () => {
    const n = service.getNextTitle(3);
    expect(n?.level).toBe(4);
    expect(n?.tier).toBe('silver');
  });

  it('getTierColor: 5 段位色均非空且以 # 开头', () => {
    const tiers: Array<'bronze' | 'silver' | 'gold' | 'diamond' | 'star'> = [
      'bronze',
      'silver',
      'gold',
      'diamond',
      'star',
    ];
    tiers.forEach((t) => {
      const c = service.getTierColor(t);
      expect(c).toMatch(/^#[0-9a-f]{6}$/i);
    });
  });

  it('expToNext: 满级返 0', () => {
    expect(service.expToNext(10, 99999)).toBe(0);
  });

  it('expToNext: Lv1 totalExp=50 距 Lv2 还需 50', () => {
    expect(service.expToNext(1, 50)).toBe(50);
  });

  it('isMaxLevel: Lv>=10 视为满级', () => {
    expect(service.isMaxLevel(10)).toBeTrue();
    expect(service.isMaxLevel(11)).toBeTrue();
    expect(service.isMaxLevel(9)).toBeFalse();
  });

  it('maxLevel 暴露常量 = 10', () => {
    expect(service.maxLevel).toBe(10);
  });
});
