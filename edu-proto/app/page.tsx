'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Cpu, Box, Code, ShieldCheck, Zap, Globe } from 'lucide-react';

export default function Home() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="w-full py-20 md:py-32 lg:py-48 bg-primary text-primary-foreground relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&q=80')] bg-cover bg-center opacity-20"></div>
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-primary/90"></div>
        <div className="container px-4 md:px-6 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="flex flex-col items-center space-y-6 text-center"
          >
            <div className="space-y-4 max-w-4xl">
              <div className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-3 py-1 text-sm backdrop-blur-md">
                <span className="flex h-2 w-2 rounded-full bg-accent mr-2 animate-pulse"></span>
                MatuX STEM 平台 v1.0 原型发布
              </div>
              <h1 className="text-4xl font-extrabold tracking-tighter sm:text-6xl lg:text-7xl/none bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                AI 驱动的 STEM 教育新纪元
              </h1>
              <p className="mx-auto max-w-[800px] text-slate-300 md:text-xl lg:text-2xl leading-relaxed">
                融合边缘计算、元宇宙与区块链技术，打造沉浸式、个性化的智能硬件学习生态。
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <a href="/demo" className="inline-flex items-center justify-center rounded-lg text-base font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-accent text-white hover:bg-accent/90 h-12 px-8 shadow-lg shadow-accent/20 hover:shadow-accent/40 hover:-translate-y-1">
                进入演示环境 <ArrowRight className="ml-2 h-5 w-5" />
              </a>
              <a href="/tech" className="inline-flex items-center justify-center rounded-lg text-base font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-white/20 bg-white/5 hover:bg-white/10 h-12 px-8 backdrop-blur-sm hover:-translate-y-1">
                探索技术架构
              </a>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="w-full py-12 md:py-24 lg:py-32 bg-slate-50">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl text-primary">核心功能</h2>
              <p className="max-w-[900px] text-gray-500 md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                从代码生成到虚拟实验室，全方位赋能 STEM 教学与实践。
              </p>
            </div>
          </div>
          <div className="mx-auto grid max-w-5xl items-center gap-6 py-12 lg:grid-cols-3">
            {[
              { icon: Code, title: "AI 代码生成", desc: "自然语言驱动，实时生成 Arduino/Python 硬件控制代码。" },
              { icon: Box, title: "元宇宙实验室", desc: "基于 Vircadia 的百人同服虚拟场景，实现远程协作共创。" },
              { icon: Cpu, title: "边缘智能认证", desc: "ESP32 TinyML 语音识别与模型热更新，软硬联动闭环。" }
            ].map((item, i) => (
              <motion.div
                key={i}
                whileHover={{ scale: 1.05 }}
                className="flex flex-col items-center space-y-4 rounded-lg border bg-white p-6 shadow-sm"
              >
                <div className="p-2 bg-primary/10 rounded-full">
                  <item.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-xl font-bold">{item.title}</h3>
                <p className="text-gray-500 text-center">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Showcase */}
      <section id="tech" className="w-full py-12 md:py-24 lg:py-32">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl text-primary">前沿技术栈</h2>
            </div>
          </div>
          <div className="grid gap-6 mt-8 lg:grid-cols-2 lg:gap-12">
            <div className="flex flex-col justify-center space-y-4">
              <ul className="grid gap-6">
                {[
                  { title: "Hyperledger Fabric", desc: "企业级区块链网络，保障学分与证书不可篡改。" },
                  { title: "TensorFlow Lite Micro", desc: "端侧推理能力，实现离线语音指令识别。" },
                  { title: "FastAPI + Angular", desc: "高性能微服务架构，支持大规模并发访问。" }
                ].map((t, i) => (
                  <li key={i} className="flex items-start gap-4">
                    <div className="mt-1 bg-accent/20 p-1 rounded">
                      <Zap className="h-4 w-4 text-accent" />
                    </div>
                    <div>
                      <h4 className="font-bold">{t.title}</h4>
                      <p className="text-sm text-gray-500">{t.desc}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl overflow-hidden border shadow-lg">
              <img src="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80" alt="Tech Stack" className="w-full h-full object-cover" />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
