'use client';

import { motion } from 'framer-motion';
import { Wifi, Battery } from 'lucide-react';
import { DeviceMode } from '../types';

interface DeviceFrameProps {
  mode: DeviceMode;
  children: React.ReactNode;
  statusBar?: React.ReactNode;
}

export function DeviceFrame({ mode, children, statusBar }: DeviceFrameProps) {
  const isPhone = mode === 'phone';

  // 设备尺寸配置
  const frameConfig = {
    phone: {
      width: 'w-[360px]',
      height: 'h-[720px]',
      borderRadius: 'rounded-[3rem]',
      borderWidth: 'border-[8px]',
      notch: true
    },
    tablet: {
      width: 'w-[1024px]',
      height: 'h-[768px]',
      borderRadius: 'rounded-[2rem]',
      borderWidth: 'border-[12px]',
      notch: false
    }
  };

  const config = frameConfig[mode];

  return (
    <motion.div
      key={mode}
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.9, opacity: 0 }}
      className={`relative ${config.width} ${config.height} bg-black ${config.borderRadius} shadow-2xl ${config.borderWidth} border-slate-800 overflow-hidden`}
    >
      {/* Phone Notch / Dynamic Island */}
      {config.notch && (
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-7 bg-black rounded-b-2xl z-20 flex items-center justify-center space-x-2">
          <div className="w-16 h-4 bg-slate-900 rounded-full"></div>
        </div>
      )}

      {/* Status Bar */}
      {statusBar || (
        <div className={`h-${isPhone ? '10' : '8'} w-full flex justify-between items-center ${isPhone ? 'px-6 pt-2' : 'px-6'} text-xs font-medium text-${isPhone ? 'slate-900' : 'white'} ${!isPhone && 'bg-slate-900'}`}>
          {isPhone ? (
            <>
              <span>9:41</span>
              <div className="flex items-center space-x-1">
                <Wifi className="h-3 w-3" />
                <Battery className="h-3 w-3" />
              </div>
            </>
          ) : (
            <>
              <span>{new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}</span>
              <div className="flex items-center space-x-2">
                <Wifi className="h-3 w-3" />
                <Battery className="h-3 w-3" />
                <span>85%</span>
              </div>
            </>
          )}
        </div>
      )}

      {/* Screen Content Container - 使用flex布局确保BottomNav固定在底部 */}
      <div className="relative w-full h-full flex flex-col overflow-hidden">
        {/* Scrollable Content Area */}
        <div className={`flex-1 ${isPhone ? 'bg-slate-50 overflow-y-auto no-scrollbar pr-1' : 'bg-gradient-to-br from-slate-50 to-slate-100 overflow-y-auto no-scrollbar p-8'}`}>
          <div className="min-h-full">
            {children}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
