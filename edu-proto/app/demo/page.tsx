'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Users, School, Building2, GraduationCap, Code, BookOpen, Activity, Zap } from 'lucide-react';

const roles = [
  { id: 'teacher', name: '教师端', icon: Users },
  { id: 'institution', name: '机构管理员', icon: Building2 },
  { id: 'school', name: '学校管理员', icon: School },
  { id: 'bureau', name: '教育局', icon: GraduationCap },
];

export default function DemoPage() {
  const [activeRole, setActiveRole] = useState('teacher');

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold tracking-tighter sm:text-5xl text-primary mb-4">多角色智能管理中枢</h1>
        <p className="max-w-[700px] mx-auto text-gray-500">
          为不同教育场景提供定制化的数据看板与决策支持。
        </p>
        <div className="mt-6 flex justify-center gap-4">
          <a href="/student-dashboard" className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-accent text-white hover:bg-accent/90 h-10 px-6">
            查看学生端演示
          </a>
        </div>
      </div>

      {/* Role Switcher */}
      <div className="flex flex-wrap justify-center gap-4 mb-8">
        {roles.map((role) => (
          <button
            key={role.id}
            onClick={() => setActiveRole(role.id)}
            className={`flex items-center space-x-2 px-6 py-3 rounded-full transition-all ${
              activeRole === role.id
                ? 'bg-primary text-white shadow-lg scale-105'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <role.icon className="h-5 w-5" />
            <span>{role.name}</span>
          </button>
        ))}
      </div>

      {/* Dashboard Preview */}
      <motion.div
        key={activeRole}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden"
      >
        <div className="p-6 bg-slate-50 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">{roles.find(r => r.id === activeRole)?.name} - 实时概览</h2>
          <span className="text-xs font-mono text-green-600 bg-green-100 px-2 py-1 rounded">Live Data</span>
        </div>
        <div className="p-6 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Mock Stats */}
          <div className="p-4 rounded-lg border bg-white">
            <div className="text-sm font-medium text-muted-foreground">STEM 课程完成率</div>
            <div className="text-2xl font-bold mt-1">87.5%</div>
            <div className="text-xs text-green-500 mt-1">+12% 较上月</div>
          </div>
          <div className="p-4 rounded-lg border bg-white">
            <div className="text-sm font-medium text-muted-foreground">AI 辅助实验次数</div>
            <div className="text-2xl font-bold mt-1">1,240</div>
            <div className="text-xs text-blue-500 mt-1">活跃度高</div>
          </div>
          <div className="p-4 rounded-lg border bg-white">
            <div className="text-sm font-medium text-muted-foreground">硬件设备在线数</div>
            <div className="text-2xl font-bold mt-1">356 / 400</div>
            <div className="text-xs text-orange-500 mt-1">维护中: 12</div>
          </div>

          {/* AI Code Gen Demo Area */}
          <div className="col-span-full p-6 rounded-lg border bg-slate-900 text-slate-50 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Code className="h-5 w-5 text-accent" />
                <h3 className="font-semibold">AI 智能编程助手</h3>
              </div>
              <div className="flex space-x-1">
                <div className="w-2 h-2 rounded-full bg-red-500"></div>
                <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex space-x-2">
                <input
                  type="text"
                  placeholder="输入指令：例如 '让 ESP32 读取温湿度传感器数据'"
                  className="flex-1 rounded-md border border-slate-700 bg-slate-800 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-accent transition-all"
                />
                <button className="bg-accent hover:bg-accent/90 text-white px-6 py-3 rounded-md text-sm font-medium transition-transform active:scale-95 flex items-center">
                  <Zap className="h-4 w-4 mr-2" /> 生成
                </button>
              </div>
              <div className="rounded-md bg-black p-4 font-mono text-xs text-green-400 h-40 overflow-auto border border-slate-800 shadow-inner">
                <span className="text-slate-500"># 等待指令输入...</span>
                <br/>
                <span className="animate-pulse">_</span>
              </div>
              <div className="grid grid-cols-3 gap-4 mt-4">
                {['ESP32 在线', 'BLE 信号强', '电池 85%'].map((status, i) => (
                  <div key={i} className="bg-slate-800/50 rounded p-2 text-center text-xs border border-slate-700">
                    <span className="text-green-400">●</span> {status}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
