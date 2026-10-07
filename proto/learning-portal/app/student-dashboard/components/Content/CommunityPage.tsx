'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';
import { User, Award } from 'lucide-react';
import { DeviceMode } from '../../types';

interface CommunityPageProps {
  mode: DeviceMode;
  onNavigate?: (page: string) => void;
}

export function CommunityPage({ mode, onNavigate }: CommunityPageProps) {
  const isPhone = mode === 'phone';

  if (isPhone) {
    return (
      <div className="px-5 space-y-4">
        {/* Topic Tabs */}
        <div className="flex space-x-2 overflow-x-auto no-scrollbar pb-1">
          {['全部', '开源硬件', '3D打印', '机器人', 'AI应用'].map((tag, i) => (
            <span key={i} className={`text-[10px] px-3 py-1.5 rounded-full whitespace-nowrap ${i === 0 ? 'bg-blue-600 text-white' : 'bg-white border text-gray-600'}`}>
              {tag}
            </span>
          ))}
        </div>

        <h3 className="font-bold text-blue-600 text-sm">创客广场</h3>
        {[
          { image: '/images/projects/auto-watering-system.svg', author: '王同学', title: '基于 ESP32 的自动浇花系统', desc: '通过土壤湿度传感器实时监测，当数值低于阈值时自动开启水泵...', tags: ['#物联网', '#自动化'], likes: 128 },
          { image: '/images/projects/smart-fan.svg', author: '李同学', title: '智能温控风扇系统', desc: '基于温度传感器自动调节风扇转速，实现智能节能控制...', tags: ['#智能家居', '#节能'], likes: 96 },
          { image: '/images/projects/voice-car.svg', author: '张同学', title: '语音控制智能小车', desc: '通过语音识别模块实现小车的前进、后退、转弯等控制...', tags: ['#机器人', '#语音识别'], likes: 145 }
        ].map((project, i) => (
          <motion.div
            key={i}
            whileTap={{ scale: 0.98 }}
            onClick={() => onNavigate?.('项目详情')}
            className="bg-white rounded-xl border shadow-sm overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
          >
            <div className="h-28 bg-slate-100 relative overflow-hidden">
              <Image 
                src={project.image} 
                alt={project.title} 
                fill
                className="object-cover"
              />
              <div className="absolute top-2 right-2 bg-black/50 text-white text-[9px] px-2 py-0.5 rounded-full flex items-center z-10">
                <User className="h-2 w-2 mr-1" /> {project.author}
              </div>
            </div>
            <div className="p-3">
              <h4 className="font-bold text-xs mb-1">{project.title}</h4>
              <p className="text-[10px] text-gray-500 mb-2 line-clamp-2">{project.desc}</p>
              <div className="flex justify-between items-center">
                <div className="flex space-x-2">
                  {project.tags.map((tag, j) => (
                    <span key={j} className="text-[9px] bg-slate-100 px-2 py-0.5 rounded text-gray-600">{tag}</span>
                  ))}
                </div>
                <div className="flex items-center space-x-1 text-gray-400">
                  <Award className="h-3 w-3" /> <span className="text-[9px]">{project.likes}</span>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    );
  }

  // 平板模式 - 实战项目页面
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-slate-900">实战项目 🚀</h2>
      </div>
      <div className="grid grid-cols-2 gap-5">
        {[
          { title: '智能温控风扇', status: '进行中', progress: 65, emoji: '🌬️', difficulty: '中级' },
          { title: '自动浇花系统', status: '已完成', progress: 100, emoji: '💧', difficulty: '初级' },
          { title: '语音控制小车', status: '进行中', progress: 40, emoji: '🚗', difficulty: '高级' },
          { title: '环境监测站', status: '未开始', progress: 0, emoji: '🌡️', difficulty: '中级' }
        ].map((project, i) => (
          <motion.div
            key={i}
            whileHover={{ y: -4 }}
            onClick={() => onNavigate?.('项目详情')}
            className="bg-white rounded-2xl p-6 shadow-md hover:shadow-xl transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="text-4xl">{project.emoji}</div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                project.status === '已完成' ? 'bg-green-100 text-green-700' :
                project.status === '进行中' ? 'bg-blue-100 text-blue-700' :
                'bg-slate-100 text-slate-600'
              }`}>
                {project.status}
              </span>
            </div>
            <h4 className="font-bold text-slate-900 mb-2">{project.title}</h4>
            <p className="text-xs text-slate-500 mb-3">难度：{project.difficulty}</p>
            {project.progress > 0 && (
              <div className="mb-3">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-600">完成度</span>
                  <span className="font-semibold text-blue-600">{project.progress}%</span>
                </div>
                <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full" style={{ width: `${project.progress}%` }}></div>
                </div>
              </div>
            )}
            <button className="w-full bg-gradient-to-r from-green-500 to-green-600 text-white py-2 rounded-xl font-semibold text-sm hover:shadow-lg transition-all">
              {project.status === '未开始' ? '开始项目' : '继续开发'}
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
