'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, Home, Code, MessageSquare, User, ArrowLeft } from 'lucide-react';
import { PhoneSubPage } from '../student-dashboard/types';
import { useChat } from '../student-dashboard/hooks/useChat';
import {
  HomePage,
  LearnPage,
  CommunityPage,
  ProfilePage,
  AIChatModal,
  LearningProfilePage,
  GrowthTrajectoryPage,
  AITeacherSettingsPage,
  DeviceConnectPage,
  BlockchainCertPage,
  SensorMonitorPage,
  QuizPage,
  BlocklyPage,
  CircuitLabPage,
  LearningReportPage,
  ProfileEditPage,
  PointsShopPage,
  StreakSystem,
  ARLabPage,
  CreativityPage,
  DailyChallengePage,
} from '../student-dashboard/components';
import * as PhoneSubPages from '../student-dashboard/components/PhoneContent/SubPages';

// 移动版底部标签
const phoneTabs = [
  { id: 'home', icon: Home, label: '首页' },
  { id: 'learn', icon: Code, label: '学习' },
  { id: 'community', icon: MessageSquare, label: '社区' },
  { id: 'profile', icon: User, label: '我的' },
];

export default function MobilePage() {
  const [activeTab, setActiveTab] = useState('home');
  const [phoneSubPage, setPhoneSubPage] = useState<PhoneSubPage>(null);
  const [showAIAssistant, setShowAIAssistant] = useState(false);

  // AI Chat
  const { chatMessages, inputMessage, setInputMessage, handleSendMessage } = useChat();

  // 处理导航
  const handleNavigate = (page: string) => {
    setPhoneSubPage(page as PhoneSubPage);
  };

  // 渲染手机子页面
  const renderPhoneSubPage = () => {
    if (!phoneSubPage) return null;

    // PRD 6.6 个人中心页面（自带头部+返回，手机模式直接渲染）
    if (phoneSubPage === '学习画像') {
      return <LearningProfilePage mode="phone" onBack={() => setPhoneSubPage(null)} />;
    }
    if (phoneSubPage === '成长轨迹') {
      return <GrowthTrajectoryPage mode="phone" onBack={() => setPhoneSubPage(null)} />;
    }
    if (phoneSubPage === 'AI教师设置') {
      return <AITeacherSettingsPage mode="phone" onBack={() => setPhoneSubPage(null)} />;
    }
    // 硬件与证书页面（自带头部，手机模式直接渲染）
    if (phoneSubPage === '设备连接') {
      return <DeviceConnectPage mode="phone" onNavigate={(p) => p === 'sensors' ? setPhoneSubPage('传感器监控') : handleNavigate(p)} />;
    }
    if (phoneSubPage === '区块链证书') {
      return <BlockchainCertPage mode="phone" />;
    }
    if (phoneSubPage === '传感器监控') {
      return <SensorMonitorPage mode="phone" />;
    }
    if (phoneSubPage === '防作弊测验') {
      return <QuizPage mode="phone" onBack={() => setPhoneSubPage(null)} />;
    }
    if (phoneSubPage === '学习报告') {
      return <LearningReportPage mode="phone" onBack={() => setPhoneSubPage(null)} />;
    }
    if (phoneSubPage === 'Blockly编程') {
      return <BlocklyPage mode="phone" />;
    }
    if (phoneSubPage === '电路实验') {
      return <CircuitLabPage mode="phone" />;
    }
    if (phoneSubPage === '个人资料') {
      return <ProfileEditPage mode="phone" onBack={() => setPhoneSubPage(null)} />;
    }
    if (phoneSubPage === '积分商城') {
      return <PointsShopPage mode="phone" />;
    }
    if (phoneSubPage === '连胜系统') {
      return <StreakSystem mode="phone" />;
    }
    if (phoneSubPage === 'AR实验室') {
      return <ARLabPage mode="phone" />;
    }
    if (phoneSubPage === '创意引擎') {
      return <CreativityPage mode="phone" />;
    }
    if (phoneSubPage === '每日挑战') {
      return <DailyChallengePage mode="phone" onBack={() => setPhoneSubPage(null)} />;
    }

    const ComponentMap: Record<string, React.ComponentType<{ onNavigate: (page: string) => void }>> = {
      '课程详情': PhoneSubPages.CourseDetail,
      '项目详情': PhoneSubPages.ProjectDetail,
      '成就详情': PhoneSubPages.AchievementDetail,
      '代码编辑器': PhoneSubPages.CodeEditor,
      '系统设置': PhoneSubPages.Settings,
      '知识图谱': PhoneSubPages.KnowledgeGraph,
    };

    const Component = ComponentMap[phoneSubPage];
    if (!Component) return null;

    return <Component onNavigate={handleNavigate} />;
  };

  // 自带头部的子页面（无需重复渲染移动端子页头）
  const selfHeaderPages = ['学习画像', '成长轨迹', 'AI教师设置', '防作弊测验', '学习报告', '个人资料'];
  const subPageHasOwnHeader = phoneSubPage ? selfHeaderPages.includes(phoneSubPage) : false;

  return (
    <div className="flex flex-col h-screen bg-slate-50 overflow-hidden">
      {/* App Header */}
      <header className="px-5 py-4 flex justify-between items-center bg-white border-b border-slate-200 flex-shrink-0">
        <div>
          <h2 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Hi, 李明 👋
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">准备好开始今天的实验了吗？</p>
        </div>
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="w-11 h-11 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg cursor-pointer"
        >
          <span className="text-white text-lg">👤</span>
        </motion.div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto pb-24">
        {/* Sub Page Display */}
        <AnimatePresence>
          {phoneSubPage && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="absolute inset-0 bg-slate-50 z-40 overflow-y-auto pb-24"
            >
              {!subPageHasOwnHeader && (
                <div className="sticky top-0 bg-white border-b px-5 py-3 flex items-center gap-3 z-10">
                  <button
                    onClick={() => setPhoneSubPage(null)}
                    className="p-2 hover:bg-slate-100 rounded-full"
                  >
                    <ArrowLeft className="h-5 w-5 text-slate-600" />
                  </button>
                  <h3 className="font-bold text-lg">{phoneSubPage}</h3>
                </div>
              )}
              <div className={subPageHasOwnHeader ? '' : 'p-5'}>{renderPhoneSubPage()}</div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Tab Content */}
        {!phoneSubPage && (
          <>
            {activeTab === 'home' && <HomePage mode="phone" onNavigate={handleNavigate} />}
            {activeTab === 'learn' && <LearnPage mode="phone" onNavigate={handleNavigate} />}
            {activeTab === 'community' && <CommunityPage mode="phone" onNavigate={handleNavigate} />}
            {activeTab === 'profile' && (
              <ProfilePage mode="phone" onNavigate={(page) => page && handleNavigate(page)} />
            )}
          </>
        )}
      </div>

      {/* Floating AI Button */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setShowAIAssistant(true)}
        className="absolute bottom-28 right-4 w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full shadow-xl flex items-center justify-center text-white z-30"
      >
        <Bot className="h-6 w-6" />
      </motion.button>

      {/* Bottom Navigation */}
      <nav className="absolute bottom-0 w-full h-[72px] bg-white/95 backdrop-blur-lg border-t border-slate-200 flex justify-around items-center px-2 pb-2 shadow-2xl z-50">
        {phoneTabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <motion.button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setPhoneSubPage(null);
              }}
              whileTap={{ scale: 0.9 }}
              className={`flex flex-col items-center gap-1 px-4 py-2 transition-all ${
                isActive ? 'bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl' : ''
              }`}
            >
              <div className={`relative ${isActive ? 'text-blue-600' : 'text-slate-400'}`}>
                <tab.icon className="h-6 w-6" />
                {isActive && (
                  <motion.div
                    layoutId="mobile-nav-indicator"
                    className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-blue-600 rounded-full"
                  />
                )}
              </div>
              <span
                className={`text-[10px] font-semibold ${
                  isActive ? 'text-blue-600' : 'text-slate-400'
                }`}
              >
                {tab.label}
              </span>
            </motion.button>
          );
        })}
      </nav>

      {/* AI Chat Modal */}
      <AIChatModal
        show={showAIAssistant}
        onClose={() => setShowAIAssistant(false)}
        messages={chatMessages}
        inputMessage={inputMessage}
        onInputChange={setInputMessage}
        onSendMessage={handleSendMessage}
        mode="phone"
      />
    </div>
  );
}
