'use client';

import { motion } from 'framer-motion';
import { User, BookOpen, Box, Cpu, Award, ArrowRight, CheckCircle } from 'lucide-react';

const steps = [
  {
    title: '智能登录与画像构建',
    desc: '学生通过多模态方式登录，系统根据历史数据自动生成 STEM 能力画像。',
    icon: User,
    side: 'left'
  },
  {
    title: 'AI 推荐学习路径',
    desc: '基于知识图谱，AI 引擎为学生推送个性化的硬件实验项目与理论课程。',
    icon: BookOpen,
    side: 'right'
  },
  {
    title: '元宇宙虚拟实操',
    desc: '进入 Vircadia 虚拟实验室，在 3D 环境中完成电路设计与机械组装。',
    icon: Box,
    side: 'left'
  },
  {
    title: '软硬联动执行',
    desc: '将虚拟代码下发至 ESP32 硬件，通过语音或传感器反馈实时验证实验结果。',
    icon: Cpu,
    side: 'right'
  },
  {
    title: '区块链成就认证',
    desc: '实验成功后，成果自动上链并转化为积分与数字勋章，计入成长档案。',
    icon: Award,
    side: 'left'
  }
];

export default function JourneyPage() {
  return (
    <div className="container mx-auto px-4 py-16">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-20"
      >
        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl text-primary mb-4">典型用户流程</h1>
        <p className="max-w-[700px] mx-auto text-gray-500 text-lg">
          从兴趣激发到技能认证，MatuX 打造闭环式 STEM 学习体验。
        </p>
      </motion.div>

      <div className="relative">
        {/* Vertical Line */}
        <div className="absolute left-4 md:left-1/2 top-0 bottom-0 w-0.5 bg-slate-200 -translate-x-1/2 hidden md:block"></div>

        <div className="space-y-12">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: step.side === 'left' ? -50 : 50 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className={`flex flex-col md:flex-row items-center gap-8 ${
                step.side === 'right' ? 'md:flex-row-reverse' : ''
              }`}
            >
              <div className="flex-1 w-full">
                <div className={`bg-white p-6 rounded-xl border shadow-sm hover:shadow-md transition-all ${
                  step.side === 'right' ? 'md:text-left' : 'md:text-right'
                }`}>
                  <h3 className="text-xl font-bold text-primary mb-2">{step.title}</h3>
                  <p className="text-gray-500 text-sm">{step.desc}</p>
                </div>
              </div>

              <div className="relative z-10 flex items-center justify-center w-12 h-12 rounded-full bg-primary text-white shadow-lg shrink-0">
                <step.icon className="h-6 w-6" />
              </div>

              <div className="flex-1 hidden md:block"></div>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="mt-24 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="bg-gradient-to-br from-primary/5 to-accent/5 rounded-2xl p-12 border"
        >
          <h2 className="text-3xl font-bold text-primary mb-4">准备好开启您的 STEM 之旅了吗？</h2>
          <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
            加入 MatuX，体验 AI 驱动的个性化 STEM 教育，让学习更高效、更有趣。
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button className="inline-flex items-center justify-center rounded-full text-sm font-medium transition-all bg-accent text-white hover:bg-accent/90 hover:shadow-lg h-12 px-8 text-base">
              立即注册体验 <ArrowRight className="ml-2 h-5 w-5" />
            </button>
            <button className="inline-flex items-center justify-center rounded-full text-sm font-medium transition-all border-2 border-primary text-primary hover:bg-primary hover:text-white h-12 px-8 text-base">
              了解更多 <CheckCircle className="ml-2 h-5 w-5" />
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
