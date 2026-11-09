/**
 * 【P3-A-3】LearningMapHighlightService 单元测试
 *
 * 覆盖：
 * - highlight() 立即设置活跃节点
 * - 同节点重复调用应被忽略
 * - 队列播放（FIFO）
 * - 默认 5s 后清除
 * - 可配置 durationMs
 * - clear() 立即清除
 * - isActive() / getQueueLength() 状态查询
 * - highlightMany() 批量入队
 */

import { LearningMapHighlightService } from './learning-map-highlight.service';

describe('LearningMapHighlightService', () => {
  let service: LearningMapHighlightService;

  beforeEach(() => {
    jasmine.clock().install();
    service = new LearningMapHighlightService();
  });

  afterEach(() => {
    jasmine.clock().uninstall();
    service.clear();
  });

  // ================ highlight() ================

  describe('highlight()', () => {
    it('应立即将 highlightedNode$ 设置为指定节点 ID', (done) => {
      service.highlightedNode$.subscribe((nodeId) => {
        if (nodeId !== null) {
          expect(nodeId).toBe('py-loop');
          done();
        }
      });
      service.highlight('py-loop', 1000);
    });

    it('空字符串 nodeId 应被忽略', () => {
      service.highlight('', 1000);
      expect(service.isActive()).toBe(false);
    });

    it('同一节点连续调用应被忽略', () => {
      service.highlight('py-loop', 1000);
      const firstItem = service['queue'].length; // 1
      service.highlight('py-loop', 1000);
      expect(service['queue'].length).toBe(firstItem);
    });

    it('不同节点应入队', () => {
      service.highlight('py-loop', 1000);
      service.highlight('py-class', 1000);
      expect(service.getQueueLength()).toBe(1); // 第二个等待
    });
  });

  // ================ 时长控制 ================

  describe('时长控制', () => {
    it('默认 durationMs 应为 5000', () => {
      service.highlight('py-loop');
      jasmine.clock().tick(4999);
      expect(service.isActive()).toBe(true);
      jasmine.clock().tick(2);
      expect(service.isActive()).toBe(false);
    });

    it('自定义 durationMs 应生效', () => {
      service.highlight('py-loop', 2000);
      jasmine.clock().tick(1999);
      expect(service.isActive()).toBe(true);
      jasmine.clock().tick(2);
      expect(service.isActive()).toBe(false);
    });

    it('清除后 highlightedNode$ 应为 null', () => {
      let lastValue: string | null = 'initial';
      service.highlightedNode$.subscribe((nodeId) => {
        lastValue = nodeId;
      });
      service.highlight('py-loop', 1000);
      service.clear();
      expect(lastValue).toBeNull();
    });
  });

  // ================ highlightMany() ================

  describe('highlightMany()', () => {
    it('应批量入队所有节点', () => {
      service.highlightMany(['py-var', 'py-loop', 'py-class'], 1000);
      expect(service.getQueueLength()).toBeGreaterThanOrEqual(2);
    });

    it('空数组应不报错', () => {
      expect(() => service.highlightMany([], 1000)).not.toThrow();
    });
  });

  // ================ clear() ================

  describe('clear()', () => {
    it('应立即清除活跃节点和队列', () => {
      service.highlight('py-loop', 10000);
      service.highlight('py-class', 10000);
      service.clear();
      expect(service.isActive()).toBe(false);
      expect(service.getQueueLength()).toBe(0);
    });

    it('允许后续 highlight 重新激活', () => {
      service.highlight('py-loop', 1000);
      service.clear();
      expect(service.isActive()).toBe(false);
      service.highlight('py-class', 1000);
      expect(service.isActive()).toBe(true);
    });
  });

  // ================ 队列播放 ================

  describe('队列播放', () => {
    it('应按 FIFO 顺序播放', () => {
      const seen: string[] = [];
      service.highlightedNode$.subscribe((id) => {
        if (id && !seen.includes(id)) seen.push(id);
      });

      service.highlight('a', 1000);
      service.highlight('b', 1000);
      service.highlight('c', 1000);

      // a 当前活跃，b/c 在队列
      expect(service.isActive()).toBe(true);
      expect(seen).toEqual(['a']);

      // 推进时间让 a 结束 + 250ms 间隔
      jasmine.clock().tick(1250);
      // 此时 b 已被推送给订阅者
      expect(seen).toContain('b');
    });

    it('队列项之间应间隔 250ms', () => {
      service.highlight('a', 1000);
      service.highlight('b', 1000);

      // 第一次 1s 结束后，等待 250ms 才播放下一项
      jasmine.clock().tick(1000);
      // 此时 b 还没开始（仍在等待 250ms）
      expect(service.isActive()).toBe(false);
      jasmine.clock().tick(251);
      expect(service.isActive()).toBe(true);
    });
  });

  // ================ isActive / getQueueLength ================

  describe('状态查询', () => {
    it('isActive 在无活跃时应为 false', () => {
      expect(service.isActive()).toBe(false);
    });

    it('getQueueLength 在无队列时应为 0', () => {
      expect(service.getQueueLength()).toBe(0);
    });
  });
});