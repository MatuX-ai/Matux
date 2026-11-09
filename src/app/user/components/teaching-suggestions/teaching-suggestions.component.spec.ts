/**
 * TeachingSuggestionsComponent 单元测试
 *
 * 【P2-6】补最小 spec，覆盖纯函数分位逻辑（getScoreColor / getScoreLevel）。
 * 不依赖 service / HTTP，直接 new 组件实例传空依赖。
 */

import { TeachingSuggestionsComponent } from './teaching-suggestions.component';

describe('TeachingSuggestionsComponent', () => {
  let component: TeachingSuggestionsComponent;

  beforeEach(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    component = new TeachingSuggestionsComponent(null as any, null as any, null as any, null as any);
  });

  describe('getScoreColor', () => {
    it('should return high-contrast green for score >= 70', () => {
      expect(component.getScoreColor(70)).toBe('#15803d');
      expect(component.getScoreColor(95)).toBe('#15803d');
    });

    it('should return amber for score in [45, 70)', () => {
      expect(component.getScoreColor(45)).toBe('#b45309');
      expect(component.getScoreColor(69)).toBe('#b45309');
    });

    it('should return red for score < 45', () => {
      expect(component.getScoreColor(44)).toBe('#dc2626');
      expect(component.getScoreColor(0)).toBe('#dc2626');
    });
  });

  describe('getScoreLevel', () => {
    it('should bucket scores correctly', () => {
      expect(component.getScoreLevel(80)).toBe('high');
      expect(component.getScoreLevel(50)).toBe('medium');
      expect(component.getScoreLevel(10)).toBe('low');
    });

    it('should use inclusive lower bounds for buckets', () => {
      expect(component.getScoreLevel(70)).toBe('high');
      expect(component.getScoreLevel(45)).toBe('medium');
    });
  });

  describe('healthRating fallback', () => {
    it('should return fair when report is null', () => {
      expect(component.healthRating).toBe('fair');
    });
  });
});
