'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot,
  Home,
  Code,
  Box,
  Palette,
  Search,
  Bell,
  ArrowLeft,
  Sparkles,
  ChevronDown,
  Brain,
  TrendingUp,
  Settings,
  Award,
  Coins,
  Flame,
  Shield,
  Cpu,
  Activity,
  Clock,
  User,
  FileText,
  Puzzle,
  Zap,
} from 'lucide-react';
import { useChat } from '../student-dashboard/hooks/useChat';
import {
  HomePage,
  LearnPage,
  CommunityPage,
  ProfilePage,
  ARLabPage,
  PointsShopPage,
  StreakSystem,
  BlockchainCertPage,
  DeviceConnectPage,
  SensorMonitorPage,
  CreativityPage,
  LearningProfilePage,
  GrowthTrajectoryPage,
  AITeacherSettingsPage,
  QuizPage,
  BlocklyPage,
  CircuitLabPage,
  LearningReportPage,
  ProfileEditPage,
  DailyChallengePage,
} from '../student-dashboard/components';
import { AIChatModal } from '../student-dashboard/components';
import * as SubPages from '../student-dashboard/components/PhoneContent/SubPages';

// PRD 6.5 节顶部水平导航：首页 / 课程 / AR实验室 / 项目 / 创作
const navItems = [
  { id: 'home', label: '首页', icon: Home },
  { id: 'courses', label: '课程', icon: Code },
  { id: 'ar-lab', label: 'AR 实验室', icon: Box },
  { id: 'projects', label: '项目', icon: Palette },
  { id: 'creativity', label: '创作', icon: Sparkles },
];

export default function WebPage() {
  const [activeTab, setActiveTab] = useState('home');
  const [showAIAssistant, setShowAIAssistant] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  // AI Chat
  const { chatMessages, inputMessage, setInputMessage, handleSendMessage } = useChat();

  // 主导航 + 主页快捷入口/画像页跳转统一处理
  const handleNavigate = (page: string) => {
    setActiveTab(page);
    setShowUserMenu(false);
  };

  // SubPages 内部用中文名互跳，这里映射为 web 端 case id
  const subPageNav = (page: string) => {
    const map: Record<string, string> = {
      '课程详情': 'course-detail',
      '项目详情': 'project-detail',
      '代码编辑器': 'code-editor',
      '知识图谱': 'knowledge-graph',
      '每日挑战': 'daily-challenge',
    };
    if (map[page]) setActiveTab(map[page]);
  };

  // SubPage 包裹器：手机设计的子页面在平板上居中显示 + 返回按钮
  const renderSubPage = (title: string, onBack: () => void, children: React.ReactNode) => (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={onBack} className="p-2 bg-slate-100 rounded-xl text-slate-500 hover:bg-slate-200 transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h2 className="text-2xl font-bold text-slate-900">{title}</h2>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 p-6">
        {children}
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return <HomePage mode="tablet" onNavigate={handleNavigate} />;
      case 'courses':
        return <LearnPage mode="tablet" onNavigate={handleNavigate} />;
      case 'ar-lab':
        return <ARLabPage mode="tablet" />;
      case 'projects':
        return <CommunityPage mode="tablet" onNavigate={handleNavigate} />;
      case 'creativity':
        return <CreativityPage mode="tablet" />;
      // 个人中心：学习画像 / 成长轨迹 / AI教师设置（PRD 6.6）
      case 'profile':
        return <LearningProfilePage mode="tablet" onBack={() => setActiveTab('home')} />;
      case 'profile-edit':
        return <ProfileEditPage mode="tablet" onBack={() => setActiveTab('profile')} />;
      case 'growth':
        return <GrowthTrajectoryPage mode="tablet" onBack={() => setActiveTab('home')} />;
      case 'ai-settings':
        return <AITeacherSettingsPage mode="tablet" onBack={() => setActiveTab('home')} />;
      // 主页快捷入口 / 画像页可触达的次级页面
      case 'shop':
        return <PointsShopPage mode="tablet" />;
      case 'achievements':
        return <ProfilePage mode="tablet" onNavigate={(page) => page && handleNavigate(page)} />;
      case 'streak':
        return <StreakSystem mode="tablet" />;
      case 'certificates':
        return <BlockchainCertPage mode="tablet" />;
      case 'devices':
        return <DeviceConnectPage mode="tablet" onNavigate={handleNavigate} />;
      case 'sensors':
        return <SensorMonitorPage mode="tablet" />;
      case 'quiz':
        return <QuizPage mode="tablet" onBack={() => setActiveTab('home')} />;
      case 'blockly':
        return <BlocklyPage mode="tablet" onBack={() => setActiveTab('home')} />;
      case 'circuit':
        return <CircuitLabPage mode="tablet" onBack={() => setActiveTab('home')} />;
      case 'report':
        return <LearningReportPage mode="tablet" onBack={() => setActiveTab('home')} />;
      // 课程/项目/挑战等次级页面（SubPages，居中渲染）
      case 'course-detail':
        return renderSubPage('课程详情', () => setActiveTab('courses'), <SubPages.CourseDetail onNavigate={subPageNav} />);
      case 'project-detail':
        return renderSubPage('项目详情', () => setActiveTab('projects'), <SubPages.ProjectDetail onNavigate={subPageNav} />);
      case 'code-editor':
        return (
          <div>
            <div className="flex items-center gap-4 mb-6">
              <button onClick={() => setActiveTab('projects')} className="p-2 bg-slate-100 rounded-xl text-slate-500 hover:bg-slate-200 transition-colors">
                <ArrowLeft className="h-5 w-5" />
              </button>
              <h2 className="text-2xl font-bold text-slate-900">代码编辑器</h2>
            </div>
            <div className="h-[calc(100vh-200px)]">
              <SubPages.CodeEditor onNavigate={subPageNav} />
            </div>
          </div>
        );
      case 'knowledge-graph':
        return renderSubPage('知识图谱', () => setActiveTab('courses'), <SubPages.KnowledgeGraph onNavigate={subPageNav} />);
      case 'daily-challenge':
        return <DailyChallengePage mode="tablet" onBack={() => setActiveTab('courses')} />;
      default:
        return <HomePage mode="tablet" onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50 overflow-hidden">
      {/* 顶部导航栏 64px - PRD 6.5: bg-primary (#0f172a) text-white */}
      <header className="h-16 bg-[#0f172a] text-white flex items-center justify-between px-6 flex-shrink-0 border-b border-white/5">
        {/* Logo + 水平菜单 */}
        <div className="flex items-center gap-8">
          <a href="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform">
              <span className="text-white font-bold text-sm">M</span>
            </div>
            <span className="font-bold text-lg tracking-tight">MatuX</span>
          </a>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-white/10 text-white'
                      : 'text-slate-300 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* 搜索 + 通知 + 用户 */}
        <div className="flex items-center gap-3">
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="搜索课程、项目、实验..."
              className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-slate-400 focus:outline-none focus:bg-white/10 focus:border-blue-500 transition-all"
            />
          </div>
          {/* 通知下拉面板 - PRD F-14 学习提醒/成就通知/AI 教师消息 */}
          <div className="relative">
            <button
              onClick={() => { setShowNotifications(!showNotifications); setShowUserMenu(false); }}
              className="relative p-2 hover:bg-white/10 rounded-xl transition-colors"
            >
              <Bell className="h-5 w-5 text-slate-300" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
            <AnimatePresence>
              {showNotifications && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: -8, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, scale: 0.96 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 top-12 w-80 bg-white rounded-2xl shadow-2xl border border-slate-100 z-50 overflow-hidden"
                  >
                    <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                      <h3 className="font-semibold text-slate-900 text-sm">通知</h3>
                      <button className="text-xs text-blue-600 hover:text-blue-700">全部已读</button>
                    </div>
                    <div className="max-h-80 overflow-y-auto">
                      {[
                        { icon: '📚', title: '今日学习提醒', desc: '该完成「Python 循环」任务了，预计 20 分钟', time: '5 分钟前', unread: true, color: 'bg-blue-50' },
                        { icon: '🏆', title: '获得新徽章', desc: '恭喜！你解锁了「学习达人」徽章', time: '1 小时前', unread: true, color: 'bg-orange-50' },
                        { icon: '🤖', title: 'AI 教师消息', desc: '我注意到你的 range() 正确率较低，要不要一起攻克？', time: '2 小时前', unread: true, color: 'bg-purple-50' },
                        { icon: '🔥', title: '连胜已达 15 天', desc: '继续保持！再坚持 5 天即可解锁「20 天连胜」', time: '今天 08:00', unread: false, color: 'bg-red-50' },
                        { icon: '📋', title: '课程进度更新', desc: 'Arduino LED 实验已全部完成，下一章：传感器读取', time: '昨天', unread: false, color: 'bg-green-50' },
                      ].map((n, i) => (
                        <motion.div
                          key={i}
                          whileHover={{ backgroundColor: '#f8fafc' }}
                          className={`px-4 py-3 border-b border-slate-50 last:border-0 flex gap-3 ${n.unread ? '' : 'opacity-60'}`}
                        >
                          <div className={`w-9 h-9 rounded-xl ${n.color} flex items-center justify-center text-base flex-shrink-0`}>
                            {n.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className="font-semibold text-slate-900 text-xs">{n.title}</p>
                              {n.unread && <span className="w-1.5 h-1.5 bg-blue-500 rounded-full flex-shrink-0"></span>}
                            </div>
                            <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{n.desc}</p>
                            <p className="text-[10px] text-slate-400 mt-1">{n.time}</p>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                    <button className="w-full py-2.5 text-xs text-slate-500 hover:bg-slate-50 border-t border-slate-100 transition-colors">
                      查看全部通知
                    </button>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
          {/* 用户头像下拉菜单 - 个人中心入口（学习画像/成长轨迹/AI教师设置/学习成就） */}
          <div className="relative">
            <button
              onClick={() => { setShowUserMenu(!showUserMenu); setShowNotifications(false); }}
              className="flex items-center gap-2 pl-3 pr-1 py-1 hover:bg-white/10 rounded-xl transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                李
              </div>
              <span className="text-sm font-medium">李明</span>
              <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
            </button>
            <AnimatePresence>
              {showUserMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: -8, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, scale: 0.96 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 top-12 w-56 bg-white rounded-2xl shadow-2xl border border-slate-100 py-2 z-50 overflow-hidden"
                  >
                    <div className="px-4 py-3 border-b border-slate-100">
                      <p className="font-semibold text-slate-900 text-sm">李明</p>
                      <p className="text-xs text-slate-500">STEM 探索者 Lv.5</p>
                    </div>
                    {/* 个人中心 */}
                    <div className="px-4 pt-2 pb-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">个人中心</div>
                    {[
                      { id: 'profile-edit', label: '编辑资料', icon: User, color: 'text-slate-600' },
                      { id: 'profile', label: '学习画像', icon: Brain, color: 'text-indigo-600' },
                      { id: 'growth', label: '成长轨迹', icon: TrendingUp, color: 'text-purple-600' },
                      { id: 'ai-settings', label: 'AI 教师设置', icon: Settings, color: 'text-blue-600' },
                      { id: 'achievements', label: '学习成就', icon: Award, color: 'text-orange-600' },
                      { id: 'report', label: '学习报告', icon: FileText, color: 'text-cyan-600' },
                    ].map((item) => (
                      <button
                        key={item.id}
                        onClick={() => handleNavigate(item.id)}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                      >
                        <item.icon className={`h-4 w-4 ${item.color}`} />
                        {item.label}
                      </button>
                    ))}
                    {/* 学习工具 */}
                    <div className="px-4 pt-2 pb-1 mt-1 border-t border-slate-100 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">学习工具</div>
                    {[
                      { id: 'blockly', label: 'Blockly 编程', icon: Puzzle, color: 'text-blue-600' },
                      { id: 'circuit', label: '电路实验', icon: Zap, color: 'text-amber-600' },
                      { id: 'quiz', label: '防作弊测验', icon: Clock, color: 'text-rose-600' },
                    ].map((item) => (
                      <button
                        key={item.id}
                        onClick={() => handleNavigate(item.id)}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                      >
                        <item.icon className={`h-4 w-4 ${item.color}`} />
                        {item.label}
                      </button>
                    ))}
                    {/* 更多功能 */}
                    <div className="px-4 pt-2 pb-1 mt-1 border-t border-slate-100 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">更多功能</div>
                    {[
                      { id: 'shop', label: '积分商城', icon: Coins, color: 'text-amber-600' },
                      { id: 'streak', label: '连胜系统', icon: Flame, color: 'text-red-500' },
                      { id: 'certificates', label: '区块链证书', icon: Shield, color: 'text-emerald-600' },
                      { id: 'devices', label: '设备连接', icon: Cpu, color: 'text-blue-600' },
                      { id: 'sensors', label: '传感器监控', icon: Activity, color: 'text-purple-600' },
                    ].map((item) => (
                      <button
                        key={item.id}
                        onClick={() => handleNavigate(item.id)}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                      >
                        <item.icon className={`h-4 w-4 ${item.color}`} />
                        {item.label}
                      </button>
                    ))}
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </div>
      </header>

      {/* 主内容区 - PRD 6.5: 无侧边栏，单列布局，max-w 1400px 居中，padding 24px */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-[1400px] mx-auto px-6 py-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {renderContent()}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      {/* 浮动 AI 助手按钮 - PRD 6.5: 56×56px 右下角固定，渐变 indigo→purple */}
      <motion.button
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.3, type: 'spring', stiffness: 260, damping: 20 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setShowAIAssistant(true)}
        className="fixed bottom-12 right-8 w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 shadow-2xl shadow-purple-500/40 flex items-center justify-center text-white z-40"
        title="AI 老师"
      >
        <Bot className="h-6 w-6" />
        <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white"></span>
      </motion.button>

      {/* 底部状态栏 28px - PRD 6.5: 在线状态 + 设备 + 版本 */}
      <footer className="h-7 bg-[#0f172a] text-slate-400 flex items-center justify-between px-6 text-xs flex-shrink-0 border-t border-white/5">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 bg-green-400 rounded-full"></span>
            在线
          </span>
          <span className="text-slate-600">|</span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 bg-green-400 rounded-full"></span>
            ESP32 已连接
          </span>
          <span className="text-slate-600">|</span>
          <span>Python 3.11 运行中</span>
        </div>
        <div className="flex items-center gap-4">
          <a href="/" className="flex items-center gap-1 hover:text-white transition-colors">
            <ArrowLeft className="h-3 w-3" /> 返回选择页
          </a>
          <span className="text-slate-600">|</span>
          <span>v1.0.0</span>
        </div>
      </footer>

      {/* AI Chat Modal */}
      <AIChatModal
        show={showAIAssistant}
        onClose={() => setShowAIAssistant(false)}
        messages={chatMessages}
        inputMessage={inputMessage}
        onInputChange={setInputMessage}
        onSendMessage={handleSendMessage}
        mode="tablet"
      />
    </div>
  );
}
