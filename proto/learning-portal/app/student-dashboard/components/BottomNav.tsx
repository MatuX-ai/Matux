'use client';

import { motion } from 'framer-motion';
import { Box, Code, MessageSquare, User, Camera, Award, ShoppingCart } from 'lucide-react';
import { DeviceMode } from '../types';

interface BottomNavProps {
  mode: DeviceMode;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function BottomNav({ mode, activeTab, onTabChange }: BottomNavProps) {
  const isPhone = mode === 'phone';

  // 手机导航项
  const phoneTabs = [
    { id: 'home', icon: Box, label: 'home' },
    { id: 'learn', icon: Code, label: 'learn' },
    { id: 'community', icon: MessageSquare, label: 'community' },
    { id: 'profile', icon: User, label: 'profile' }
  ];

  // 平板导航项
  const tabletTabs = [
    { id: 'home', icon: Box, label: '首页' },
    { id: 'courses', icon: Code, label: '课程' },
    { id: 'ar-lab', icon: Camera, label: 'AR实验' },
    { id: 'projects', icon: Box, label: '项目' },
    { id: 'shop', icon: ShoppingCart, label: '积分商城' },
    { id: 'achievements', icon: Award, label: '成就' }
  ];

  const tabs = isPhone ? phoneTabs : tabletTabs;

  if (isPhone) {
    return (
      <div className="absolute bottom-0 w-full h-[96px] bg-white/95 backdrop-blur-lg border-t border-slate-200 flex justify-around items-center px-2 pb-2 shadow-2xl z-50">
        {tabs.map((tab) => (
          <motion.button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            whileTap={{ scale: 0.9 }}
            className={`flex flex-col items-center gap-1.5 px-3 py-2 transition-all ${
              activeTab === tab.id ? 'bg-gradient-to-br from-blue-50 to-purple-50' : 'hover:bg-slate-50'
            }`}
          >
            <div className={`relative ${activeTab === tab.id ? 'text-blue-600' : 'text-slate-400'}`}>
              <tab.icon className="h-6 w-6" />
              {activeTab === tab.id && (
                <motion.div
                  layoutId="nav-indicator"
                  className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-blue-600 rounded-full"
                />
              )}
            </div>
            <span className={`text-[10px] font-semibold capitalize ${activeTab === tab.id ? 'text-blue-600' : 'text-slate-400'}`}>
              {tab.label}
            </span>
          </motion.button>
        ))}
      </div>
    );
  }

  // 平板 Dock 样式
  return (
    <div className="absolute bottom-5 left-1/2 -translate-x-1/2 bg-white/80 backdrop-blur-xl rounded-2xl px-4 py-2.5 shadow-xl border border-white/30 flex gap-2">
      {tabs.map((tab) => (
        <motion.button
          key={tab.id}
          whileHover={{ scale: 1.1, y: -6 }}
          whileTap={{ scale: 1.05 }}
          onClick={() => onTabChange(tab.id)}
          className={`w-12 h-12 rounded-lg flex items-center justify-center transition-colors relative group ${
            activeTab === tab.id ? 'bg-blue-100' : 'hover:bg-black/5'
          }`}
          title={tab.label}
        >
          <tab.icon className={`h-6 w-6 ${activeTab === tab.id ? 'text-blue-600' : 'text-slate-700'}`} />
          {/* Tooltip */}
          <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            {tab.label}
          </div>
        </motion.button>
      ))}
    </div>
  );
}
