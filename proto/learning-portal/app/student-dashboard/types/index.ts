// 聊天消息类型
export interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
  memoryRef?: string; // 记忆引用：AI 引用的历史对话/画像数据（PRD 1392）
}

// 设备模式类型
export type DeviceMode = 'phone' | 'tablet';

// 手机 Tab 类型
export type PhoneTab = 'home' | 'learn' | 'community' | 'profile';

// 手机子页面类型
export type PhoneSubPage =
  | '课程详情'
  | '项目详情'
  | '成就详情'
  | '代码编辑器'
  | '系统设置'
  | '知识图谱'
  | '每日挑战'
  | '帖子详情'
  | '硬件设备'
  | '证书管理'
  | '学习报告'
  | '学习画像'
  | '成长轨迹'
  | 'AI教师设置'
  | '设备连接'
  | '区块链证书'
  | '传感器监控'
  | '防作弊测验'
  | 'Blockly编程'
  | '电路实验'
  | '个人资料'
  | '积分商城'
  | '连胜系统'
  | 'AR实验室'
  | '创意引擎'
  | null;

// 平板页面类型
export type TabletPage = 'home' | 'courses' | 'ar-lab' | 'projects' | 'achievements';

// 平板子页面类型
export type TabletSubPage = 
  | 'task-detail'
  | 'course-recommendation'
  | `course-learn-${number}`
  | `ar-experiment-${number}`
  | `project-workspace-${number}`
  | `badge-detail-${number}`
  | null;

// 课程类型
export interface Course {
  name: string;
  progress: number;
  emoji: string;
  total?: number;
  completed?: number;
  color?: string;
}

// 任务类型
export interface Task {
  title: string;
  duration: string;
  type: string;
  progress: number;
  completed: boolean;
}

// 项目类型
export interface Project {
  title: string;
  status: string;
  progress: number;
  emoji: string;
  difficulty: string;
}

// 徽章类型
export interface Badge {
  name: string;
  icon: string;
  earned: boolean;
  desc?: string;
}
