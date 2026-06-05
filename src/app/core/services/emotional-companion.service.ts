/**
 * 情感陪伴服务
 *
 * PRD F-08-AI.6：情感陪伴模块
 * 提供：
 * - 情感状态检测与分析
 * - 学习情绪追踪
 * - 个性化鼓励与回应策略
 * - 情绪趋势报告
 *
 * 与 AITeacherService 协作，在聊天中注入情感感知能力
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

/** 情感状态 */
export type EmotionState =
  | 'very_happy'    // 😄 很开心
  | 'happy'         // 🙂 开心
  | 'neutral'       // 😐 一般
  | 'sad'           // 😢 难过
  | 'frustrated'    // 😫 沮丧
  | 'anxious'       // 😰 焦虑
  | 'confused'      // 🤔 困惑
  | 'bored'         // 😴 无聊
  | 'angry';        // 😠 生气

/** 情感日志条目 */
export interface EmotionLogEntry {
  timestamp: string;
  emotion: EmotionState;
  /** 触发场景（可选） */
  trigger?: string;
  /** 用户自评强度 1-5 */
  intensity: number;
  /** 陪伴回应 */
  companionReply: string;
}

/** 情感趋势摘要 */
export interface EmotionSummary {
  /** 最近7天主导情绪 */
  dominantEmotion: EmotionState;
  /** 情绪波动指数 0-1 */
  volatility: number;
  /** 积极/消极比例 */
  positivityRatio: number;
  /** 鼓励消息 */
  encouragement: string;
  /** 各情绪分布 */
  distribution: Record<EmotionState, number>;
}

/** 鼓励消息模板 */
const ENCOURAGEMENTS: Record<string, string[]> = {
  frustrated: [
    '别着急，遇到困难是成长的信号！休息一下再试试 💪',
    '每个高手都经历过这个阶段，你已经做得很好了！🌈',
    '困难只是暂时的，你之前突破过更难的知识点 🎯',
  ],
  sad: [
    '学习路上难免有起伏，你已经比昨天进步了 🌱',
    '不完美的学习过程才是真实的，重要的是不要放弃 🌟',
    '你的努力老师都看在眼里，继续加油 💗',
  ],
  anxious: [
    '深呼吸～ 把大目标分解成小任务，一步一步来 🧘',
    '考试/测验只是检验学习效果的方式，不必过度紧张 📚',
    '你已经做了充分准备，相信自己！✨',
  ],
  confused: [
    '这个问题确实有点难，要不要从基础概念重新梳理一下？🤔',
    '困惑是学习新知识的必经阶段，意味着你正在突破舒适区 🌱',
    '试着用 Blockly 搭一下积木看看，也许就清楚了 💡',
  ],
  bored: [
    '要不要换个学习方式？试试项目实践或者 AR 实验 🚀',
    '学习可以更有趣！来看看今天的编程挑战如何？🎮',
    '换个角度思考，把学习当成闯关游戏怎么样？🏆',
  ],
  angry: [
    '先冷静一下，喝杯水休息 5 分钟 ☕',
    '生气解决不了问题，但我们可以一起找到解决方案 🤝',
    '把困难当作游戏 BOSS，打败它你会获得双倍成就感 💥',
  ],
  neutral: [
    '今天状态不错，继续保持！有需要随时找我 😊',
    '放轻松，按自己的节奏学就好 🌟',
    '学习是一场马拉松，保持稳定的节奏最重要 🏃',
  ],
  happy: [
    '做得太棒了！看到你的进步真让人开心 🎉',
    '今天的你状态很好，继续保持这个学习节奏！⭐',
    '学习也能这么快乐，这就是最好的状态 💯',
  ],
  very_happy: [
    '太厉害了！这个突破值得庆祝 🎊🎊🎊',
    '你这段时间的努力有了惊人的回报！保持下去！🏆',
    '你就是学习的榜样！和你一起学习真愉快 💫',
  ],
};

@Injectable({
  providedIn: 'root',
})
export class EmotionalCompanionService {
  /** 当前情感状态 */
  private currentEmotionSubject = new BehaviorSubject<EmotionState>('neutral');
  public currentEmotion$ = this.currentEmotionSubject.asObservable();

  /** 情感日志 */
  private emotionLogSubject = new BehaviorSubject<EmotionLogEntry[]>([]);
  public emotionLog$ = this.emotionLogSubject.asObservable();

  /** 陪伴模式是否开启 */
  private companionModeSubject = new BehaviorSubject<boolean>(false);
  public companionMode$ = this.companionModeSubject.asObservable();

  constructor() {
    this.loadHistory();
  }

  /** 切换陪伴模式 */
  toggleCompanionMode(): void {
    this.companionModeSubject.next(!this.companionModeSubject.value);
  }

  /** 设置陪伴模式 */
  setCompanionMode(enabled: boolean): void {
    this.companionModeSubject.next(enabled);
  }

  /** 当前陪伴模式是否开启 */
  get companionModeEnabled(): boolean {
    return this.companionModeSubject.value;
  }

  /** 当前情感状态 */
  get currentEmotion(): EmotionState {
    return this.currentEmotionSubject.value;
  }

  /** 记录情感状态 */
  logEmotion(emotion: EmotionState, trigger?: string, intensity: number = 3): EmotionLogEntry {
    const entry: EmotionLogEntry = {
      timestamp: new Date().toISOString(),
      emotion,
      trigger,
      intensity,
      companionReply: this.getEncouragement(emotion),
    };

    const history = [...this.emotionLogSubject.value, entry];
    if (history.length > 100) {
      this.emotionLogSubject.next(history.slice(history.length - 100));
      this.saveToLocalStorage(history.slice(history.length - 100));
      this.currentEmotionSubject.next(emotion);
      return entry;
    }
    this.emotionLogSubject.next(history);
    this.currentEmotionSubject.next(emotion);
    this.saveToLocalStorage(history);

    return entry;
  }

  /** 获取个性化鼓励消息 */
  getEncouragement(emotion: EmotionState): string {
    const messages = ENCOURAGEMENTS[emotion] ?? ENCOURAGEMENTS['neutral'];
    return messages[Math.floor(Math.random() * messages.length)];
  }

  /** 获取情感趋势摘要 */
  getEmotionSummary(days: number = 7): EmotionSummary {
    const log = this.emotionLogSubject.value;
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    const recent = log.filter((e) => new Date(e.timestamp) >= cutoff);

    if (recent.length === 0) {
      return {
        dominantEmotion: 'neutral',
        volatility: 0,
        positivityRatio: 0.5,
        encouragement: '开始记录你的学习心情吧！🎯',
        distribution: { neutral: 1 } as Record<EmotionState, number>,
      };
    }

    // 情绪分值映射
    const emotionScore: Record<EmotionState, number> = {
      very_happy: 2, happy: 1, neutral: 0,
      sad: -1, frustrated: -2, anxious: -1,
      confused: -0.5, bored: -0.5, angry: -2,
    };

    // 计算分布
    const distribution = {} as Record<EmotionState, number>;
    let totalScore = 0;
    let emotionChanges = 0;

    recent.forEach((e, i) => {
      distribution[e.emotion] = (distribution[e.emotion] ?? 0) + 1;
      totalScore += emotionScore[e.emotion] ?? 0;
      if (i > 0 && recent[i - 1].emotion !== e.emotion) {
        emotionChanges++;
      }
    });

    // 主导情绪
    const dominant = Object.entries(distribution).sort((a, b) => b[1] - a[1])[0][0] as EmotionState;

    // 波动指数
    const volatility = Math.min(1, emotionChanges / recent.length);

    // 积极比例
    const positiveCount = recent.filter((e) => (emotionScore[e.emotion] ?? 0) > 0).length;
    const negativityCount = recent.filter((e) => (emotionScore[e.emotion] ?? 0) < 0).length;
    const positivityRatio = recent.length > 0 ? positiveCount / recent.length : 0.5;

    // 鼓励消息
    let encouragement: string;
    if (positivityRatio > 0.7) {
      encouragement = '最近你的学习状态很棒，积极心态是最好的学习工具！🌟';
    } else if (positivityRatio > 0.4) {
      encouragement = '学习状态稳定，偶尔的波动是正常的，继续保持！💪';
    } else {
      encouragement = '最近感觉有些吃力？记住每个困难都是成长的机会，我们一起面对！🤝';
    }

    return { dominantEmotion: dominant, volatility, positivityRatio, encouragement, distribution };
  }

  /** 获取指定情绪对应的 emoji */
  getEmotionEmoji(emotion: EmotionState): string {
    const map: Record<EmotionState, string> = {
      very_happy: '😄', happy: '🙂', neutral: '😐',
      sad: '😢', frustrated: '😫', anxious: '😰',
      confused: '🤔', bored: '😴', angry: '😠',
    };
    return map[emotion] ?? '😐';
  }

  /** 获取情绪中文名 */
  getEmotionLabel(emotion: EmotionState): string {
    const map: Record<EmotionState, string> = {
      very_happy: '很开心', happy: '开心', neutral: '一般',
      sad: '难过', frustrated: '沮丧', anxious: '焦虑',
      confused: '困惑', bored: '无聊', angry: '生气',
    };
    return map[emotion] ?? '一般';
  }

  // ==================== 持久化 ====================

  private readonly STORAGE_KEY = 'imato_emotion_log';

  private saveToLocalStorage(log: EmotionLogEntry[]): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(log));
    } catch { /* 忽略 */ }
  }

  private loadHistory(): void {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      if (data) {
        const log = JSON.parse(data) as EmotionLogEntry[];
        this.emotionLogSubject.next(log);
        if (log.length > 0) {
          this.currentEmotionSubject.next(log[log.length - 1].emotion);
        }
      }
    } catch { /* 忽略 */ }
  }
}
