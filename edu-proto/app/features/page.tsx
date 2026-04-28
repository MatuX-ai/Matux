'use client';

import { motion } from 'framer-motion';
import { Code, Box, Cpu, Zap, Layers, Globe, ArrowRight } from 'lucide-react';
import { useRouter } from 'next/navigation';

const features = [
  {
    id: 'ai-code',
    title: 'AI 智能代码生成',
    icon: Code,
    desc: '支持自然语言指令，一键生成 Arduino、Python 等硬件控制代码。内置语法校验与安全沙箱，确保学生编写的代码安全可控。',
    color: 'blue'
  },
  {
    id: 'metaverse-lab',
    title: '元宇宙虚拟实验室',
    icon: Globe,
    desc: '基于 Vircadia 引擎构建的 3D 沉浸式空间。支持百人同服协作，学生可在虚拟环境中进行电路搭建、机械组装等高风险或高成本实验。',
    color: 'purple'
  },
  {
    id: 'edge-computing',
    title: '边缘计算与硬件联动',
    icon: Cpu,
    desc: 'ESP32 TinyML 语音识别系统，实现离线环境下的精准指令控制。支持 BLE 模型热更新，让硬件设备具备持续进化的能力。',
    color: 'green'
  },
  {
    id: 'blockchain-cert',
    title: '区块链学分认证',
    icon: Layers,
    desc: '利用 Hyperledger Fabric 将学习成果上链。每一份实验报告、每一个完成的 STEM 项目都将获得不可篡改的数字证书。',
    color: 'orange'
  },
  {
    id: 'gamification',
    title: '多模态游戏化激励',
    icon: Zap,
    desc: '融合语音、AR 手势与成就系统的三维激励机制。通过实时反馈与积分排行榜，激发学生在 STEM 领域的探索欲。',
    color: 'red'
  },
  {
    id: 'course-lib',
    title: '统一课程资源库',
    icon: Box,
    desc: '汇聚全球优质 STEM 教育资源，支持从基础电子学到高级机器人编程的阶梯式学习路径。提供 3D 模型预览与在线仿真功能。',
    color: 'cyan'
  }
];

const colorMap: Record<string, { bg: string; text: string; light: string }> = {
  blue: { bg: 'bg-blue-500', text: 'text-blue-600', light: 'bg-blue-50' },
  purple: { bg: 'bg-purple-500', text: 'text-purple-600', light: 'bg-purple-50' },
  green: { bg: 'bg-green-500', text: 'text-green-600', light: 'bg-green-50' },
  orange: { bg: 'bg-orange-500', text: 'text-orange-600', light: 'bg-orange-50' },
  red: { bg: 'bg-red-500', text: 'text-red-600', light: 'bg-red-50' },
  cyan: { bg: 'bg-cyan-500', text: 'text-cyan-600', light: 'bg-cyan-50' }
};

export default function FeaturesPage() {
  const router = useRouter();
  return (
    <div className="container mx-auto px-4 py-16">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-16"
      >
        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl text-primary mb-4">平台核心功能</h1>
        <p className="max-w-[700px] mx-auto text-gray-500 text-lg">
          MatuX 深度融合 AI、物联网与区块链技术，为 STEM 教育提供全链路解决方案。
        </p>
      </motion.div>

      <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
        {features.map((feature, index) => {
          const colors = colorMap[feature.color];
          return (
            <motion.div
              key={feature.id}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              whileHover={{ y: -8 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1, type: "spring", stiffness: 300 }}
              className="group relative overflow-hidden rounded-2xl border bg-white p-8 shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer"
              onClick={() => {
                if (feature.id === 'metaverse-lab') router.push('/features/metaverse');
                if (feature.id === 'gamification') router.push('/features/gamification');
              }}
            >
              <div className={`absolute top-0 right-0 -mt-4 -mr-4 h-24 w-24 rounded-full ${colors.bg} opacity-10 transition-all group-hover:scale-150`} />
              <div className="relative z-10">
                <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl ${colors.light}`}>
                  <feature.icon className={`h-6 w-6 ${colors.text}`} />
                </div>
                <h3 className="mb-3 text-xl font-bold text-primary">{feature.title}</h3>
                <p className="text-gray-500 leading-relaxed text-sm mb-4">
                  {feature.desc}
                </p>
                {(feature.id === 'metaverse-lab' || feature.id === 'gamification') && (
                  <span className={`text-sm font-medium flex items-center group-hover:translate-x-1 transition-transform ${colors.text}`}>
                    探索详情 <ArrowRight className="h-4 w-4 ml-1" />
                  </span>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="mt-20 grid gap-8 lg:grid-cols-2 items-center">
        <div className="rounded-2xl overflow-hidden border shadow-lg">
          <img src="https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&q=80" alt="STEM Collaboration" className="w-full h-full object-cover" />
        </div>
        <div className="space-y-6">
          <h2 className="text-3xl font-bold text-primary">为什么选择 MatuX？</h2>
          <ul className="space-y-4">
            {[
              '软硬结合：打通代码编写到硬件执行的完整闭环',
              '沉浸体验：元宇宙技术打破时空限制的实验教学',
              '数据可信：区块链技术保障教育评价的公平公正',
              '个性成长：AI 算法根据学生能力动态调整学习路径'
            ].map((item, i) => (
              <li key={i} className="flex items-center space-x-3">
                <div className="h-2 w-2 rounded-full bg-accent"></div>
                <span className="text-gray-600">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
