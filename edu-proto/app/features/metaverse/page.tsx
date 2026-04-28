'use client';

import { motion } from 'framer-motion';
import { Globe, Users, Zap, Box, ArrowLeft, MousePointer, Radio, Shield } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function MetaverseLabPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-purple-50">
      {/* Header */}
      <div className="bg-primary text-white py-16 relative overflow-hidden">
        <div className="absolute inset-0 bg-grid-white/10"></div>
        <div className="container mx-auto px-4 relative z-10">
          <button 
            onClick={() => router.back()}
            className="flex items-center text-white/80 hover:text-white mb-8 transition-colors"
          >
            <ArrowLeft className="h-5 w-5 mr-2" /> 返回功能列表
          </button>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="inline-flex items-center px-3 py-1 rounded-full bg-purple-500/20 border border-purple-400/30 text-purple-200 text-sm mb-4">
              <Globe className="h-4 w-4 mr-2" /> 沉浸式 3D 教学环境
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">元宇宙虚拟实验室</h1>
            <p className="text-xl text-purple-100 max-w-2xl">
              基于 Vircadia 引擎构建的下一代 STEM 实验教学平台，让虚拟与现实无缝融合
            </p>
          </motion.div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16 space-y-20">
        {/* Core Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {[
            {
              icon: Users,
              title: '百人同服协作',
              desc: '支持多达 100 名学生同时在线，在虚拟实验室中进行团队协作与项目讨论。',
              color: 'blue'
            },
            {
              icon: Box,
              title: '3D 电路搭建',
              desc: '拖拽式元器件库，支持电阻、电容、单片机等组件的虚拟组装与仿真测试。',
              color: 'purple'
            },
            {
              icon: Shield,
              title: '安全实验环境',
              desc: '在虚拟空间中进行高压电路、化学反应等高风险实验，零安全隐患。',
              color: 'green'
            },
            {
              icon: Zap,
              title: '实时物理引擎',
              desc: '基于 Unity 物理系统，精确模拟重力、碰撞、电流等真实世界物理现象。',
              color: 'orange'
            },
            {
              icon: MousePointer,
              title: '手势交互控制',
              desc: '支持 VR 手柄与 Leap Motion 手势识别，实现自然的虚拟物体操作体验。',
              color: 'pink'
            },
            {
              icon: Radio,
              title: '跨平台接入',
              desc: '支持 PC、VR 头显、平板等多种终端，随时随地进入虚拟实验室。',
              color: 'cyan'
            }
          ].map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="bg-white rounded-2xl p-6 border shadow-sm hover:shadow-lg transition-shadow"
            >
              <div className={`w-12 h-12 rounded-xl bg-${feature.color}-100 flex items-center justify-center text-${feature.color}-600 mb-4`}>
                <feature.icon className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-primary mb-2">{feature.title}</h3>
              <p className="text-gray-600 text-sm">{feature.desc}</p>
            </motion.div>
          ))}
        </div>

        {/* Demo Scenario */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="bg-white rounded-3xl border p-8 md:p-12"
        >
          <h2 className="text-3xl font-bold text-primary mb-8 text-center">典型教学场景</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                step: '01',
                title: '进入虚拟教室',
                desc: '学生通过客户端登录，进入教师创建的虚拟实验室空间。'
              },
              {
                step: '02',
                title: '领取实验任务',
                desc: '从任务面板获取实验指导书与所需元器件清单。'
              },
              {
                step: '03',
                title: '协作完成实验',
                desc: '多人协同搭建电路，实时查看仿真结果并提交实验报告。'
              }
            ].map((item, i) => (
              <div key={i} className="relative p-6 rounded-2xl bg-gradient-to-br from-purple-50 to-blue-50 border">
                <div className="text-5xl font-bold text-purple-200 mb-4">{item.step}</div>
                <h3 className="text-xl font-bold text-primary mb-2">{item.title}</h3>
                <p className="text-gray-600 text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* CTA */}
        <div className="text-center">
          <button className="bg-primary hover:bg-primary/90 text-white px-8 py-4 rounded-xl font-bold text-lg transition-colors shadow-lg">
            预约虚拟实验室演示
          </button>
        </div>
      </div>
    </div>
  );
}
