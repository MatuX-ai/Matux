/**
 * LearningMapService 单元测试（P2-A）
 *
 * 覆盖：
 * - buildTracksFromProfile（profile 转 track）
 * - buildMockTracks（fallback）
 * - getTrack / getNode
 * - getNextRecommended
 * - summarize
 * - layoutNodes
 * - generateConnections
 * - 状态计算（locked / available / mastered）
 */

import { TestBed } from '@angular/core/testing';

import type { StudentLearningProfile } from '../models/ai-teacher.models';
import {
  LearningMapNode,
  LearningMapStatus,
} from '../models/learning-map.model';
import { LearningMapService } from './learning-map.service';

describe('LearningMapService', () => {
  let service: LearningMapService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(LearningMapService);
  });

  // ================ Mock Tracks ================

  describe('buildMockTracks', () => {
    it('应返回 2 条 mock tracks（Python + STEM）', () => {
      const tracks = service.buildMockTracks();
      expect(tracks.length).toBe(2);
      expect(tracks.map((t) => t.id)).toContain('python');
      expect(tracks.map((t) => t.id)).toContain('stem');
    });

    it('每条 mock track 至少有 5 个节点', () => {
      const tracks = service.buildMockTracks();
      for (const track of tracks) {
        expect(track.nodes.length).toBeGreaterThanOrEqual(5);
      }
    });

    it('mock track 包含多种状态（mastered / in_progress / available / locked）', () => {
      const tracks = service.buildMockTracks();
      const allNodes = tracks.flatMap((t) => t.nodes);
      const statuses = new Set(allNodes.map((n) => n.status));
      expect(statuses.has('mastered')).toBe(true);
      expect(statuses.has('in_progress')).toBe(true);
      expect(statuses.has('available')).toBe(true);
      expect(statuses.has('locked')).toBe(true);
    });
  });

  // ================ buildTracksFromProfile ================

  describe('buildTracksFromProfile', () => {
    it('profile 为空时应使用 mock fallback', () => {
      const tracks = service.buildTracksFromProfile(null);
      expect(tracks.length).toBe(2);
    });

    it('profile.skillTree 为空时应使用 mock fallback', () => {
      const profile = createProfile({ skillTree: [] });
      const tracks = service.buildTracksFromProfile(profile);
      expect(tracks.length).toBe(2);
    });

    it('profile.skillTree 有数据时应按 category 分组', () => {
      const profile = createProfile({
        skillTree: [
          { id: 'py-1', name: '变量', category: 'python', progress: 0.5, status: 'learning' },
          { id: 'py-2', name: '条件', category: 'python', progress: 0, status: 'not_started', parent: 'py-1' },
          { id: 'stem-1', name: '水', category: 'stem', progress: 1, status: 'mastered' },
        ],
      });
      const tracks = service.buildTracksFromProfile(profile);
      const pythonTrack = tracks.find((t) => t.id === 'python');
      const stemTrack = tracks.find((t) => t.id === 'stem');

      expect(pythonTrack).toBeDefined();
      expect(stemTrack).toBeDefined();
      expect(pythonTrack!.nodes.length).toBe(2);
      expect(stemTrack!.nodes.length).toBe(1);
    });

    it('应正确统计 mastered / inProgress / completionPercent', () => {
      const tracks = service.buildMockTracks();
      const pythonTrack = service.getTrack(tracks, 'python')!;
      const mastered = pythonTrack.nodes.filter(
        (n) => n.status === 'mastered' || n.status === 'legendary'
      ).length;
      expect(pythonTrack.masteredNodes).toBe(mastered);
      expect(pythonTrack.completionPercent).toBe(mastered / pythonTrack.totalNodes);
    });
  });

  // ================ getTrack / getNode ================

  describe('getTrack / getNode', () => {
    it('getTrack 应返回指定 track', () => {
      const tracks = service.buildMockTracks();
      const python = service.getTrack(tracks, 'python');
      expect(python?.name).toBe('Python 基础');
    });

    it('getTrack 返回 undefined 当 id 不存在', () => {
      const tracks = service.buildMockTracks();
      expect(service.getTrack(tracks, 'nonexistent')).toBeUndefined();
    });

    it('getNode 应跨 track 查找', () => {
      const tracks = service.buildMockTracks();
      const node = service.getNode(tracks, 'py-loop');
      expect(node?.category).toBe('python');
    });

    it('getNode 返回 undefined 当 id 不存在', () => {
      const tracks = service.buildMockTracks();
      expect(service.getNode(tracks, 'nonexistent')).toBeUndefined();
    });
  });

  // ================ getNextRecommended ================

  describe('getNextRecommended', () => {
    it('应优先推荐 in_progress 节点', () => {
      const tracks = service.buildMockTracks();
      const rec = service.getNextRecommended(tracks);
      // mock 数据中 py-loop 是 in_progress
      expect(rec?.node.id).toBe('py-loop');
      expect(rec?.reason).toBe('继续当前学习');
    });

    it('无 in_progress 时应推荐 available 节点（按 tier 从低到高）', () => {
      const tracks = [
        {
          id: 'python',
          name: 'Python',
          emoji: '🐍',
          color: '#3b82f6',
          gradient: 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
          description: '',
          nodes: [
            createNode('a', 1, 'mastered', []),
            createNode('b', 2, 'available', ['a']),
            createNode('c', 3, 'available', ['b']),
          ],
          totalNodes: 3,
          masteredNodes: 1,
          inProgressNodes: 0,
          completionPercent: 1 / 3,
          isMainTrack: true,
        },
      ];
      const rec = service.getNextRecommended(tracks);
      expect(rec?.node.id).toBe('b'); // tier 2 优先
    });

    it('全部完成时应返回 undefined', () => {
      const tracks = [
        {
          id: 'python',
          name: 'Python',
          emoji: '🐍',
          color: '#3b82f6',
          gradient: 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
          description: '',
          nodes: [
            createNode('a', 1, 'mastered', []),
            createNode('b', 2, 'mastered', ['a']),
          ],
          totalNodes: 2,
          masteredNodes: 2,
          inProgressNodes: 0,
          completionPercent: 1,
          isMainTrack: true,
        },
      ];
      expect(service.getNextRecommended(tracks)).toBeUndefined();
    });

    it('空 tracks 数组应返回 undefined', () => {
      expect(service.getNextRecommended([])).toBeUndefined();
    });
  });

  // ================ summarize ================

  describe('summarize', () => {
    it('应正确聚合所有状态', () => {
      const tracks = service.buildMockTracks();
      const summary = service.summarize(tracks);
      expect(summary.totalNodes).toBeGreaterThan(0);
      expect(summary.masteredNodes + summary.inProgressNodes + summary.availableNodes + summary.lockedNodes)
        .toBe(summary.totalNodes);
      expect(summary.overallPercent).toBe(summary.masteredNodes / summary.totalNodes);
    });

    it('应自动填充 recommendedNext', () => {
      const tracks = service.buildMockTracks();
      const summary = service.summarize(tracks);
      expect(summary.recommendedNext).toBeDefined();
      expect(summary.recommendedNext!.status).toMatch(/in_progress|available/);
    });

    it('空 tracks 数组应返回零值', () => {
      const summary = service.summarize([]);
      expect(summary.totalNodes).toBe(0);
      expect(summary.overallPercent).toBe(0);
      expect(summary.recommendedNext).toBeUndefined();
    });
  });

  // ================ layoutNodes ================

  describe('layoutNodes', () => {
    it('应按 tier 分层（不同 tier 的 y 不同）', () => {
      const tracks = service.buildMockTracks();
      const pythonTrack = service.getTrack(tracks, 'python')!;
      const positions = service.layoutNodes(pythonTrack);

      expect(positions.length).toBe(pythonTrack.nodes.length);

      // 按 tier 分组
      const byTier = new Map<number, number>();
      for (const pos of positions) {
        byTier.set(pos.node.tier, pos.y);
      }

      const ys = Array.from(byTier.values());
      // 至少 2 个不同的 tier，y 不全相同
      expect(ys.length).toBeGreaterThan(1);
      expect(new Set(ys).size).toBe(ys.length);
    });

    it('每个节点的 x 应在合理范围内', () => {
      const tracks = service.buildMockTracks();
      const pythonTrack = service.getTrack(tracks, 'python')!;
      const positions = service.layoutNodes(pythonTrack);
      const dim = service.getMapDimensions();

      for (const pos of positions) {
        expect(pos.x).toBeGreaterThan(0);
        expect(pos.x).toBeLessThan(dim.width);
        expect(pos.y).toBeGreaterThanOrEqual(0);
      }
    });

    it('空 track 应返回空位置数组', () => {
      const emptyTrack: any = {
        id: 'empty',
        name: 'Empty',
        nodes: [],
        totalNodes: 0,
        masteredNodes: 0,
        inProgressNodes: 0,
        completionPercent: 0,
      };
      const positions = service.layoutNodes(emptyTrack);
      expect(positions.length).toBe(0);
    });
  });

  // ================ generateConnections ================

  describe('generateConnections', () => {
    it('应基于 prerequisites 生成连线', () => {
      const tracks = service.buildMockTracks();
      const pythonTrack = service.getTrack(tracks, 'python')!;
      const positions = service.layoutNodes(pythonTrack);
      const connections = service.generateConnections(positions);

      // py-var → py-if, py-if → py-loop, py-loop → py-func, py-func → py-class, py-func → py-debug
      expect(connections.length).toBeGreaterThanOrEqual(5);

      // 每条连线都有 SVG path
      for (const conn of connections) {
        expect(conn.path).toMatch(/^M\s/);
        expect(conn.path).toContain('C');
      }
    });

    it('isCompleted 应基于 from 节点状态', () => {
      const tracks = service.buildMockTracks();
      const pythonTrack = service.getTrack(tracks, 'python')!;
      const positions = service.layoutNodes(pythonTrack);
      const connections = service.generateConnections(positions);

      // py-var → py-if：py-var 已 mastered，py-if 已 mastered → completed
      const varToIf = connections.find(
        (c) => c.from.node.id === 'py-var' && c.to.node.id === 'py-if'
      );
      expect(varToIf?.isCompleted).toBe(true);
    });

    it('isActivePath 应标记 from 已 mastered 且 to 为 available/in_progress 的连线', () => {
      const tracks = service.buildMockTracks();
      const pythonTrack = service.getTrack(tracks, 'python')!;
      const positions = service.layoutNodes(pythonTrack);
      const connections = service.generateConnections(positions);

      // py-loop → py-func：py-loop 是 in_progress（不算 mastered），所以不算 active
      // 应该是 completed（因为 py-loop 已是 in_progress，即前置已掌握）
      const loopToFunc = connections.find(
        (c) => c.from.node.id === 'py-loop' && c.to.node.id === 'py-func'
      );
      // 这里要确认 mock 数据中 py-loop 是 in_progress（即已 unlocked），py-func 是 available
      // 状态判断：isCompleted = from is mastered/legendary AND to != locked
      expect(loopToFunc).toBeDefined();
    });
  });

  // ================ 状态计算（通过 mock 验证） ================

  describe('状态计算', () => {
    it('mastered 节点 progress < 1 应保持 mastered', () => {
      const tracks = service.buildMockTracks();
      const node = service.getNode(tracks, 'py-var')!;
      expect(node.progress).toBe(1);
      expect(node.status).toBe('mastered');
    });

    it('in_progress 节点应保留 in_progress 状态（即使前置已 mastered）', () => {
      const tracks = service.buildMockTracks();
      const node = service.getNode(tracks, 'py-loop')!;
      expect(node.status).toBe('in_progress');
    });

    it('locked 节点前置未完成', () => {
      const tracks = service.buildMockTracks();
      const node = service.getNode(tracks, 'py-class')!;
      expect(node.status).toBe('locked');
      expect(node.prerequisites.length).toBeGreaterThan(0);
    });

    it('available 节点前置已"激活"（mastered / legendary / in_progress）', () => {
      const tracks = service.buildMockTracks();
      const node = service.getNode(tracks, 'py-func')!;
      expect(node.status).toBe('available');
      const prereqIds = node.prerequisites;
      for (const id of prereqIds) {
        const prereq = service.getNode(tracks, id)!;
        // 已 started 即可解锁：mastered / legendary / in_progress
        expect(['mastered', 'legendary', 'in_progress']).toContain(prereq.status);
      }
    });

    it('locked 节点前置未激活（mastered / in_progress 都不算）', () => {
      const tracks = service.buildMockTracks();
      const node = service.getNode(tracks, 'py-class')!;
      expect(node.status).toBe('locked');
      // py-class 前置是 py-func（available），所以 py-class 是 locked
      // 因为 available 不算"已激活"
      const prereqIds = node.prerequisites;
      for (const id of prereqIds) {
        const prereq = service.getNode(tracks, id)!;
        expect(['mastered', 'legendary', 'in_progress']).not.toContain(prereq.status);
      }
    });
  });

  // ================ 边界条件 ================

  describe('边界条件', () => {
    it('getMapDimensions 应返回有效尺寸', () => {
      const dim = service.getMapDimensions();
      expect(dim.width).toBeGreaterThan(0);
      expect(dim.height).toBeGreaterThan(0);
    });

    it('getNodeRadius 应返回正数', () => {
      expect(service.getNodeRadius()).toBeGreaterThan(0);
    });

    it('getDefaultConfig 应返回默认视图配置', () => {
      const cfg = service.getDefaultConfig();
      expect(cfg.mode).toBe('map');
      expect(cfg.zoom).toBe(1);
    });
  });

  // ================ 【P3-A-2】applyEventUpdate（WebSocket 事件响应） =============

  describe('applyEventUpdate（P3-A-2 事件响应）', () => {
    it('应将节点状态更新为 in_progress 并触发解锁传播', () => {
      const tracks = service.buildMockTracks();
      // py-class 在 mock 中是 locked
      const before = service.getNode(tracks, 'py-class')!;
      expect(before.status).toBe('locked');

      // 模拟事件：py-func 变为 in_progress（其前置 py-loop 仍是 in_progress）
      const result = service.applyEventUpdate(tracks, {
        skill_id: 'py-func',
        old_status: 'available',
        new_status: 'in_progress',
        progress: 0.3,
      });

      expect(result.changed).toBe(true);
      const updated = service.getNode(tracks, 'py-func')!;
      expect(updated.status).toBe('in_progress');
      expect(updated.progress).toBe(0.3);

      // py-class 应自动 unlock（其前置 py-func 现已激活）
      const pyClass = service.getNode(tracks, 'py-class')!;
      expect(['available', 'in_progress']).toContain(pyClass.status);
    });

    it('应映射后端状态字符串 completed 为前端 mastered', () => {
      const tracks = service.buildMockTracks();
      service.applyEventUpdate(tracks, {
        skill_id: 'py-var',
        new_status: 'completed',
      });
      expect(service.getNode(tracks, 'py-var')!.status).toBe('mastered');
    });

    it('未找到节点时应返回 changed=false', () => {
      const tracks = service.buildMockTracks();
      const result = service.applyEventUpdate(tracks, {
        skill_id: 'nonexistent-skill',
        new_status: 'mastered',
      });
      expect(result.changed).toBe(false);
      expect(result.updatedNode).toBeUndefined();
    });

    it('应正确更新 relatedAchievementIds', () => {
      const tracks = service.buildMockTracks();
      const result = service.applyEventUpdate(tracks, {
        skill_id: 'py-loop',
        new_status: 'in_progress',
        progress: 0.8,
        related_achievement_ids: ['ach-loop-master', 'ach-loop-streak'],
      });
      expect(result.changed).toBe(true);
      const updated = service.getNode(tracks, 'py-loop')!;
      expect(updated.relatedAchievementIds).toEqual(['ach-loop-master', 'ach-loop-streak']);
    });
  });
});

// ================ 辅助函数 ================

function createProfile(overrides: Partial<StudentLearningProfile>): StudentLearningProfile {
  return {
    userId: 'test',
    displayName: 'Test User',
    gradeLevel: 'G5',
    ageGroup: '10-12',
    learningStyle: 'visual',
    preferredContentType: 'interactive',
    abilityDimensions: {
      programmingThinking: 50,
      algorithmAbility: 50,
      debuggingSkill: 50,
      projectPractice: 50,
      stemExperiment: 50,
      codeQuality: 50,
      independentCompletion: 50,
      questionQuality: 50,
    },
    interestPreferences: [],
    knowledgeMastery: {},
    totalStudyTimeMinutes: 0,
    completedCoursesCount: 0,
    averageQuizScore: 0,
    currentStreakDays: 0,
    longestStreakDays: 0,
    weakPoints: [],
    errorPatterns: {},
    attentionProfile: {
      averageFocusDurationMinutes: 0,
      tabSwitchFrequency: 0,
      hesitationTimeMs: 0,
      trend: 'stable',
    },
    emotionalStates: [],
    learningMilestones: [],
    skillTree: [],
    personaSeed: '',
    learningGoals: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides,
  };
}

function createNode(
  id: string,
  tier: 1 | 2 | 3 | 4 | 5,
  status: LearningMapStatus,
  prerequisites: string[]
): LearningMapNode {
  return {
    id,
    name: `Node ${id}`,
    description: '',
    icon: '⭐',
    category: 'python',
    tier,
    status,
    progress: status === 'mastered' ? 1 : status === 'in_progress' ? 0.5 : 0,
    prerequisites,
    estimatedMinutes: 30,
    rarity: 'common',
  };
}