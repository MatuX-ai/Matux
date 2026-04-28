'use client';

import { motion } from 'framer-motion';
import { Cpu, Wifi, ArrowRightLeft, ShieldCheck } from 'lucide-react';

export default function TechPage() {
  const technologies = [
    {
      title: "边缘计算与 TinyML",
      icon: Cpu,
      desc: "基于 ESP32 的端侧语音识别系统，支持 BLE 模型热更新。实现离线环境下的精准指令控制，保障数据隐私与响应速度。",
      tags: ["TensorFlow Lite Micro", "BLE 5.0", "SHA256 校验"]
    },
    {
      title: "元宇宙虚拟实验室",
      icon: Wifi,
      desc: "深度集成 Vircadia 平台，构建去中心化联邦服务器。支持百人同服实时交互，提供沉浸式 STEM 协作共创场景。",
      tags: ["Vircadia API", "WebRTC", "3D 物理引擎"]
    },
    {
      title: "区块链学分认证",
      icon: ArrowRightLeft,
      desc: "利用 Hyperledger Fabric 企业级网络，将学习成果与硬件操作记录上链。确保教育数据的不可篡改性与跨机构互认。",
      tags: ["Hyperledger Fabric", "智能合约", "数字身份"]
    },
    {
      title: "AI 驱动的代码生成",
      icon: ShieldCheck,
      desc: "融合多模态大模型，实现从自然语言到 Arduino/Python 硬件代码的秒级转换。内置安全沙箱，自动检测逻辑漏洞。",
      tags: ["LangChain", "Code Llama", "AST 解析"]
    }
  ];

  return (
    <div className="container mx-auto px-4 py-16">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-16"
      >
        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl text-primary mb-4">核心技术架构</h1>
        <p className="max-w-[700px] mx-auto text-gray-500 text-lg">
          MatuX 平台采用软硬结合、云边协同的先进架构，重新定义 STEM 教育的边界。
        </p>
      </motion.div>

      <div className="grid gap-8 md:grid-cols-2">
        {technologies.map((tech, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.02 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className="group relative overflow-hidden rounded-2xl border bg-white p-8 shadow-sm hover:shadow-md transition-all"
          >
            <div className="absolute top-0 right-0 -mt-4 -mr-4 h-24 w-24 rounded-full bg-primary/5 transition-all group-hover:scale-150" />
            <div className="relative z-10">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <tech.icon className="h-6 w-6" />
              </div>
              <h3 className="mb-2 text-xl font-bold text-primary">{tech.title}</h3>
              <p className="mb-6 text-gray-500 leading-relaxed">{tech.desc}</p>
              <div className="flex flex-wrap gap-2">
                {tech.tags.map((tag, i) => (
                  <span key={i} className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="mt-20 rounded-2xl bg-primary p-8 md:p-12 text-primary-foreground text-center">
        <h2 className="text-2xl font-bold mb-4">准备好探索未来教育了吗？</h2>
        <p className="mb-8 opacity-90">立即体验 MatuX 原型站，感受 AI 与 STEM 的完美融合。</p>
        <a href="/demo" className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-accent text-white hover:bg-accent/90 h-10 px-6 py-2">
          进入演示环境
        </a>
      </div>
    </div>
  );
}
