/**
 * 学习地图服务（P2-A）
 *
 * 职责：
 * 1. 从 StudentLearningProfile.skillTree 构建 LearningMapTrack[]
 * 2. 计算节点状态（locked/available/in_progress/mastered/legendary）
 * 3. 提供 SVG 节点位置 + 连线算法
 * 4. 推荐下一步节点
 * 5. 内置 mock tracks（fallback）
 *
 * @see 桌面端游戏化P2升级.md §2
 */

import { Injectable } from '@angular/core';

import type { StudentLearningProfile } from '../models/ai-teacher.models';
import {
  DEFAULT_LEARNING_MAP_CONFIG,
  LearningMapCategory,
  LearningMapConnection,
  LearningMapNode,
  LearningMapNodePosition,
  LearningMapRecommendation,
  LearningMapStatus,
  LearningMapSummary,
  LearningMapTrack,
  LearningMapViewConfig,
  TRACK_THEMES,
} from '../models/learning-map.model';

// ================ 常量 ================

/**
 * Map 渲染尺寸
 */
const MAP_WIDTH = 880;
const MAP_HEIGHT = 520;
const NODE_RADIUS = 32;
const TRACK_HORIZONTAL_PADDING = 60;
const TRACK_VERTICAL_PADDING = 60;
const TIER_VERTICAL_GAP = 110;
const NODE_HORIZONTAL_GAP = 140;

// ================ Service ================

@Injectable({ providedIn: 'root' })
export class LearningMapService {
  // ================ 公共方法 ================

  /**
   * 从 StudentLearningProfile 构建学习地图 tracks
   * 若 profile 为空或 skillTree 为空，使用 mock fallback
   */
  buildTracksFromProfile(profile: StudentLearningProfile | null | undefined): LearningMapTrack[] {
    if (!profile?.skillTree?.length) {
      return this.buildMockTracks();
    }

    // 按 category 分组
    const tracks: LearningMapTrack[] = [];
    const grouped = this.groupByCategory(profile.skillTree);

    for (const [category, nodes] of grouped.entries()) {
      const theme = TRACK_THEMES[category as LearningMapCategory] ?? TRACK_THEMES['python'];
      const learningMapNodes = nodes.map((n) => this.toLearningMapNode(n));

      // 计算后置节点
      this.computeUnlocks(learningMapNodes);

      // 计算状态
      this.computeStatuses(learningMapNodes);

      const mastered = learningMapNodes.filter((n) => n.status === 'mastered' || n.status === 'legendary').length;
      const inProgress = learningMapNodes.filter((n) => n.status === 'in_progress').length;

      tracks.push({
        id: category,
        name: theme.label,
        emoji: theme.emoji,
        color: theme.color,
        gradient: theme.gradient,
        description: this.getTrackDescription(category),
        nodes: learningMapNodes,
        totalNodes: learningMapNodes.length,
        masteredNodes: mastered,
        inProgressNodes: inProgress,
        completionPercent: learningMapNodes.length === 0 ? 0 : mastered / learningMapNodes.length,
        isMainTrack: category === 'python' || category === 'stem',
      });
    }

    // 若没有任何 track，返回 mock
    return tracks.length > 0 ? tracks : this.buildMockTracks();
  }

  /**
   * 获取单个 track
   */
  getTrack(tracks: LearningMapTrack[], trackId: string): LearningMapTrack | undefined {
    return tracks.find((t) => t.id === trackId);
  }

  /**
   * 获取单个节点
   */
  getNode(tracks: LearningMapTrack[], nodeId: string): LearningMapNode | undefined {
    for (const track of tracks) {
      const node = track.nodes.find((n) => n.id === nodeId);
      if (node) return node;
    }
    return undefined;
  }

  /**
   * 推荐下一步节点
   * 优先级：in_progress > available（按 tier 从低到高）
   */
  getNextRecommended(tracks: LearningMapTrack[]): LearningMapRecommendation | undefined {
    const allNodes = tracks.flatMap((t) => t.nodes);

    // 优先 in_progress
    const inProgressNodes = allNodes.filter((n) => n.status === 'in_progress');
    if (inProgressNodes.length > 0) {
      const node = inProgressNodes.sort((a, b) => a.tier - b.tier)[0];
      return this.toRecommendation(node, '继续当前学习');
    }

    // 其次 available
    const availableNodes = allNodes.filter((n) => n.status === 'available');
    if (availableNodes.length > 0) {
      const node = availableNodes.sort((a, b) => a.tier - b.tier)[0];
      return this.toRecommendation(node, '可解锁的新技能');
    }

    // 最后 mastered（已全部完成）
    const mastered = allNodes.filter((n) => n.status === 'mastered' || n.status === 'legendary');
    if (mastered.length === allNodes.length && allNodes.length > 0) {
      return undefined; // 全部完成
    }

    return undefined;
  }

  /**
   * 获取地图聚合统计
   */
  summarize(tracks: LearningMapTrack[]): LearningMapSummary {
    const allNodes = tracks.flatMap((t) => t.nodes);
    const mastered = allNodes.filter((n) => n.status === 'mastered' || n.status === 'legendary');
    const legendary = allNodes.filter((n) => n.status === 'legendary');
    const inProgress = allNodes.filter((n) => n.status === 'in_progress');
    const available = allNodes.filter((n) => n.status === 'available');
    const locked = allNodes.filter((n) => n.status === 'locked');
    const recommended = this.getNextRecommended(tracks);

    return {
      totalNodes: allNodes.length,
      masteredNodes: mastered.length,
      inProgressNodes: inProgress.length,
      availableNodes: available.length,
      lockedNodes: locked.length,
      legendaryNodes: legendary.length,
      overallPercent: allNodes.length === 0 ? 0 : mastered.length / allNodes.length,
      recommendedNext: recommended?.node,
    };
  }

  /**
   * 计算 SVG 节点位置（按 tier 分层，水平均匀分布）
   */
  layoutNodes(track: LearningMapTrack): LearningMapNodePosition[] {
    const positions: LearningMapNodePosition[] = [];
    const nodes = track.nodes;

    if (nodes.length === 0) return positions;

    // 按 tier 分组
    const byTier = new Map<number, LearningMapNode[]>();
    for (const node of nodes) {
      const arr = byTier.get(node.tier) ?? [];
      arr.push(node);
      byTier.set(node.tier, arr);
    }

    // 每个 tier 的节点水平均匀分布
    const tierKeys = Array.from(byTier.keys()).sort((a, b) => a - b);

    for (const tier of tierKeys) {
      const tierNodes = byTier.get(tier)!;
      const tierCount = tierNodes.length;
      const usableWidth = MAP_WIDTH - 2 * TRACK_HORIZONTAL_PADDING;
      const stepX = tierCount > 1 ? usableWidth / (tierCount - 1) : 0;
      const startX = tierCount > 1 ? TRACK_HORIZONTAL_PADDING : MAP_WIDTH / 2;

      const y = TRACK_VERTICAL_PADDING + (tier - 1) * TIER_VERTICAL_GAP;

      tierNodes.forEach((node, idx) => {
        const x = startX + idx * stepX;
        positions.push({ node, x, y });
      });
    }

    return positions;
  }

  /**
   * 生成 SVG 连线（基于前置关系）
   */
  generateConnections(positions: LearningMapNodePosition[]): LearningMapConnection[] {
    const connections: LearningMapConnection[] = [];
    const posMap = new Map<string, LearningMapNodePosition>();

    for (const pos of positions) {
      posMap.set(pos.node.id, pos);
    }

    for (const pos of positions) {
      for (const prereqId of pos.node.prerequisites) {
        const fromPos = posMap.get(prereqId);
        if (!fromPos) continue;

        const path = this.buildCurvePath(fromPos, pos);
        const isCompleted =
          (fromPos.node.status === 'mastered' || fromPos.node.status === 'legendary') &&
          (pos.node.status !== 'locked');
        const isActivePath =
          (fromPos.node.status === 'mastered' || fromPos.node.status === 'legendary') &&
          pos.node.status === 'available';

        connections.push({ from: fromPos, to: pos, path, isCompleted, isActivePath });
      }
    }

    return connections;
  }

  /**
   * 地图视图尺寸（用于 SVG viewBox）
   */
  getMapDimensions(): { width: number; height: number } {
    return { width: MAP_WIDTH, height: MAP_HEIGHT };
  }

  /**
   * 节点半径
   */
  getNodeRadius(): number {
    return NODE_RADIUS;
  }

  /**
   * 默认配置
   */
  getDefaultConfig(): LearningMapViewConfig {
    return { ...DEFAULT_LEARNING_MAP_CONFIG };
  }

  /**
   * 【P3-A-2】增量更新节点状态（响应 WebSocket node_status_updated 事件）
   *
   * 行为：
   * 1. 找到对应节点，更新 status / progress
   * 2. 重新计算所有节点状态（解锁传播）
   * 3. 返回是否发生变更（供调用方决定是否刷新）
   */
  applyEventUpdate(
    tracks: LearningMapTrack[],
    event: {
      skill_id: string;
      old_status?: string;
      new_status: string;
      progress?: number;
      related_achievement_ids?: (string | number)[];
    },
  ): { changed: boolean; updatedNode?: LearningMapNode } {
    let updatedNode: LearningMapNode | undefined;
    for (const track of tracks) {
      const node = track.nodes.find((n) => n.id === event.skill_id);
      if (node) {
        // 类型映射：后端 status 可能是 'not_started'/'in_progress'/'completed'
        const mapped = this.mapStatusFromEvent(event.new_status);
        node.status = mapped;
        if (typeof event.progress === 'number') {
          node.progress = Math.max(0, Math.min(1, event.progress));
        }
        if (event.related_achievement_ids && event.related_achievement_ids.length > 0) {
          node.relatedAchievementIds = event.related_achievement_ids.map(String);
        }
        updatedNode = node;
        break;
      }
    }

    if (!updatedNode) {
      return { changed: false };
    }

    // 重新计算所有 track 的节点状态（解锁传播）
    for (const track of tracks) {
      this.computeStatuses(track.nodes);
    }

    return { changed: true, updatedNode };
  }

  /**
   * 后端事件 status → 前端 map status
   */
  private mapStatusFromEvent(eventStatus: string): LearningMapStatus {
    const s = eventStatus.toLowerCase();
    if (s === 'completed' || s === 'mastered') return 'mastered';
    if (s === 'legendary') return 'legendary';
    if (s === 'in_progress' || s === 'learning') return 'in_progress';
    if (s === 'available' || s === 'unlocked') return 'available';
    return 'locked';
  }

  // ================ 私有方法 ================

  /**
   * 按 category 分组 SkillTreeNode
   */
  private groupByCategory(nodes: any[]): Map<string, any[]> {
    const grouped = new Map<string, any[]>();
    for (const node of nodes) {
      const arr = grouped.get(node.category) ?? [];
      arr.push(node);
      grouped.set(node.category, arr);
    }
    return grouped;
  }

  /**
   * SkillTreeNode → LearningMapNode
   */
  private toLearningMapNode(raw: any): LearningMapNode {
    let status: LearningMapStatus;
    if (raw.status === 'mastered') {
      status = raw.progress >= 1 ? 'legendary' : 'mastered';
    } else if (raw.status === 'learning') {
      status = 'in_progress';
    } else {
      status = 'locked';
    }

    return {
      id: raw.id,
      name: raw.name,
      description: raw.unlockRequirement ?? '开始学习这个技能节点',
      icon: this.inferIcon(raw.id, raw.category),
      category: (raw.category as LearningMapCategory) ?? 'python',
      tier: raw.tier ?? this.inferTier(raw.id),
      status,
      progress: raw.progress,
      prerequisites: raw.parent ? [raw.parent] : [],
      estimatedMinutes: raw.estimatedMinutes ?? 30,
      rarity: raw.rarity ?? 'common',
    };
  }

  /**
   * 计算 unlocks（每个节点的后置节点列表）
   */
  private computeUnlocks(nodes: LearningMapNode[]): void {
    for (const node of nodes) {
      const unlocks: string[] = [];
      for (const other of nodes) {
        if (other.prerequisites.includes(node.id)) {
          unlocks.push(other.id);
        }
      }
      node.unlocks = unlocks;
    }
  }

  /**
   * 计算节点状态
   * 规则：
   * - 已 mastered / legendary / in_progress：保留（已开始即视为已"激活"
   *   其后置节点，前置解锁不仅要求 mastered，也允许 in_progress）
   * - 所有 prerequisites 都已"激活"（mastered / legendary / in_progress）：available
   * - 否则：locked
   */
  private computeStatuses(nodes: LearningMapNode[]): void {
    for (const node of nodes) {
      if (
        node.status === 'mastered' ||
        node.status === 'legendary' ||
        node.status === 'in_progress'
      ) {
        continue; // 保留已激活状态
      }

      const allPrereqMet = node.prerequisites.every((id) => {
        const prereq = nodes.find((n) => n.id === id);
        return (
          prereq &&
          (prereq.status === 'mastered' ||
            prereq.status === 'legendary' ||
            prereq.status === 'in_progress')
        );
      });

      // 若无前置或全部满足 → available
      if (allPrereqMet) {
        node.status = 'available';
      } else {
        node.status = 'locked';
      }
    }
  }

  /**
   * 绘制曲线（S 形 SVG path）
   */
  private buildCurvePath(from: LearningMapNodePosition, to: LearningMapNodePosition): string {
    const { x: x1, y: y1 } = from;
    const { x: x2, y: y2 } = to;
    const midY = (y1 + y2) / 2;
    return `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
  }

  /**
   * 推断 tier（基于 ID 数字后缀）
   */
  private inferTier(id: string): 1 | 2 | 3 | 4 | 5 {
    const match = id.match(/(\d+)$/);
    if (match) {
      const n = parseInt(match[1], 10);
      if (n <= 1) return 1;
      if (n <= 2) return 2;
      if (n <= 3) return 3;
      if (n <= 4) return 4;
      return 5;
    }
    return 1;
  }

  /**
   * 推断图标 emoji
   */
  private inferIcon(id: string, category: string): string {
    const lower = id.toLowerCase();
    if (lower.includes('variable')) return '📦';
    if (lower.includes('loop') || lower.includes('for')) return '🔁';
    if (lower.includes('function') || lower.includes('func')) return '⚙️';
    if (lower.includes('class') || lower.includes('object')) return '🏛️';
    if (lower.includes('module') || lower.includes('package')) return '📚';
    if (lower.includes('error') || lower.includes('exception')) return '🐛';
    if (lower.includes('data') || lower.includes('list')) return '📊';
    if (lower.includes('algorithm') || lower.includes('sort')) return '🧮';
    if (lower.includes('project')) return '🛠️';
    if (lower.includes('robot') || lower.includes('arduino')) return '🤖';
    if (lower.includes('water')) return '💧';
    if (lower.includes('electric') || lower.includes('circuit')) return '⚡';
    if (lower.includes('light') || lower.includes('optical')) return '💡';
    if (lower.includes('chemistry') || lower.includes('chem')) return '⚗️';
    if (lower.includes('physics')) return '🔭';
    if (lower.includes('bio')) return '🧬';

    // fallback by category
    const catMap: Record<string, string> = {
      python: '🐍',
      stem: '🔬',
      algorithm: '🧮',
      project: '🛠️',
      creation: '🎨',
      javascript: '📜',
      arduino: '⚡',
      ai: '🤖',
    };
    return catMap[category] ?? '⭐';
  }

  /**
   * Track 描述
   */
  private getTrackDescription(category: string): string {
    const map: Record<string, string> = {
      python: '从变量到函数到面向对象，构建完整的 Python 编程能力',
      stem: '科学、技术、工程、数学实验，开启探索世界的大门',
      algorithm: '排序、搜索、递归，训练计算思维',
      project: '动手做项目，将知识转化为作品',
      creation: '用代码创作艺术、游戏和互动体验',
    };
    return map[category] ?? '开启你的学习之旅';
  }

  /**
   * 推荐对象构造
   */
  private toRecommendation(node: LearningMapNode, reason: string): LearningMapRecommendation {
    return {
      node,
      reason,
      estimatedMinutes: node.estimatedMinutes,
      prerequisiteCount: node.prerequisites.length,
    };
  }

  // ================ Mock 数据 ================

  /**
   * 内置 mock tracks（fallback）
   * 两条主线：Python 基础（6 节点）+ STEM 实验（5 节点）
   */
  buildMockTracks(): LearningMapTrack[] {
    const pythonTheme = TRACK_THEMES['python'];
    const stemTheme = TRACK_THEMES['stem'];

    const pythonNodes: LearningMapNode[] = [
      {
        id: 'py-var',
        name: '变量与类型',
        description: '学习 Python 变量、整数、字符串、布尔值等基本数据类型',
        icon: '📦',
        category: 'python',
        tier: 1,
        status: 'mastered',
        progress: 1,
        prerequisites: [],
        unlocks: ['py-if'],
        estimatedMinutes: 30,
        rarity: 'common',
      },
      {
        id: 'py-if',
        name: '条件判断',
        description: '掌握 if/elif/else 分支结构',
        icon: '🔀',
        category: 'python',
        tier: 2,
        status: 'mastered',
        progress: 1,
        prerequisites: ['py-var'],
        unlocks: ['py-loop'],
        estimatedMinutes: 45,
        rarity: 'common',
      },
      {
        id: 'py-loop',
        name: '循环结构',
        description: 'for / while 循环，掌握迭代思想',
        icon: '🔁',
        category: 'python',
        tier: 3,
        status: 'in_progress',
        progress: 0.6,
        prerequisites: ['py-if'],
        unlocks: ['py-func'],
        estimatedMinutes: 60,
        rarity: 'rare',
        relatedAchievementIds: ['ach-loop-master'],
      },
      {
        id: 'py-func',
        name: '函数与封装',
        description: '定义函数、参数、返回值，模块化编程',
        icon: '⚙️',
        category: 'python',
        tier: 4,
        status: 'available',
        progress: 0,
        prerequisites: ['py-loop'],
        unlocks: ['py-class'],
        estimatedMinutes: 75,
        rarity: 'rare',
        relatedAchievementIds: ['ach-function-wizard'],
      },
      {
        id: 'py-class',
        name: '面向对象',
        description: '类、对象、继承、多态',
        icon: '🏛️',
        category: 'python',
        tier: 5,
        status: 'locked',
        progress: 0,
        prerequisites: ['py-func'],
        unlocks: [],
        estimatedMinutes: 90,
        rarity: 'epic',
        relatedAchievementIds: ['ach-oop-architect'],
      },
      {
        id: 'py-debug',
        name: '调试与异常',
        description: 'try/except、断点调试、错误排查',
        icon: '🐛',
        category: 'python',
        tier: 4,
        status: 'locked',
        progress: 0,
        prerequisites: ['py-func'],
        unlocks: [],
        estimatedMinutes: 60,
        rarity: 'rare',
      },
    ];

    const stemNodes: LearningMapNode[] = [
      {
        id: 'stem-water',
        name: '水的循环',
        description: '蒸发、凝结、降水，理解水的三态变化',
        icon: '💧',
        category: 'stem',
        tier: 1,
        status: 'mastered',
        progress: 1,
        prerequisites: [],
        unlocks: ['stem-electric'],
        estimatedMinutes: 30,
        rarity: 'common',
      },
      {
        id: 'stem-electric',
        name: '电路基础',
        description: '电压、电流、电阻，欧姆定律',
        icon: '⚡',
        category: 'stem',
        tier: 2,
        status: 'mastered',
        progress: 1,
        prerequisites: ['stem-water'],
        unlocks: ['stem-light'],
        estimatedMinutes: 45,
        rarity: 'common',
      },
      {
        id: 'stem-light',
        name: '光学实验',
        description: '光的折射、反射、透镜成像',
        icon: '💡',
        category: 'stem',
        tier: 3,
        status: 'in_progress',
        progress: 0.4,
        prerequisites: ['stem-electric'],
        unlocks: ['stem-chem'],
        estimatedMinutes: 60,
        rarity: 'rare',
      },
      {
        id: 'stem-chem',
        name: '化学反应',
        description: '酸碱中和、金属氧化',
        icon: '⚗️',
        category: 'stem',
        tier: 4,
        status: 'available',
        progress: 0,
        prerequisites: ['stem-light'],
        unlocks: [],
        estimatedMinutes: 75,
        rarity: 'epic',
        relatedAchievementIds: ['ach-chem-master'],
      },
      {
        id: 'stem-bio',
        name: '生物细胞',
        description: '细胞结构、光合作用',
        icon: '🧬',
        category: 'stem',
        tier: 3,
        status: 'locked',
        progress: 0,
        prerequisites: ['stem-electric'],
        unlocks: [],
        estimatedMinutes: 60,
        rarity: 'rare',
      },
    ];

    return [
      {
        id: 'python',
        name: pythonTheme.label,
        emoji: pythonTheme.emoji,
        color: pythonTheme.color,
        gradient: pythonTheme.gradient,
        description: '从变量到函数到面向对象，构建完整的 Python 编程能力',
        nodes: pythonNodes,
        totalNodes: pythonNodes.length,
        masteredNodes: pythonNodes.filter((n) => n.status === 'mastered' || n.status === 'legendary').length,
        inProgressNodes: pythonNodes.filter((n) => n.status === 'in_progress').length,
        completionPercent:
          pythonNodes.filter((n) => n.status === 'mastered' || n.status === 'legendary').length /
          pythonNodes.length,
        isMainTrack: true,
      },
      {
        id: 'stem',
        name: stemTheme.label,
        emoji: stemTheme.emoji,
        color: stemTheme.color,
        gradient: stemTheme.gradient,
        description: '科学、技术、工程、数学实验，开启探索世界的大门',
        nodes: stemNodes,
        totalNodes: stemNodes.length,
        masteredNodes: stemNodes.filter((n) => n.status === 'mastered' || n.status === 'legendary').length,
        inProgressNodes: stemNodes.filter((n) => n.status === 'in_progress').length,
        completionPercent:
          stemNodes.filter((n) => n.status === 'mastered' || n.status === 'legendary').length /
          stemNodes.length,
        isMainTrack: true,
      },
    ];
  }
}