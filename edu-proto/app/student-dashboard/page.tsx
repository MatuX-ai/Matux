'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, MessageSquare, Box, User, Zap, Battery, Wifi, Play, Code, Camera, Globe, Award, Tablet, Sparkles, X, Send, Bot } from 'lucide-react';
import { useState } from 'react';

export default function StudentMobileDemo() {
  const [activeTab, setActiveTab] = useState('home');
  const [showAIAssistant, setShowAIAssistant] = useState(false);
  const [deviceMode, setDeviceMode] = useState<'phone' | 'tablet'>('phone');
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'ai'; content: string }>>([
    {
      role: 'ai',
      content: '你好！我是你的 AI 老师 👋\n\n我看到你正在学习：\n• Python 基础语法（75%）\n• Arduino LED 实验（已完成✅）\n• 机器学习基础（30%）\n\n有什么我可以帮助你的吗？'
    },
    {
      role: 'user',
      content: 'Python 变量命名有什么规则？'
    },
    {
      role: 'ai',
      content: '很好的问题！Python 变量命名规则：\n\n✅ 允许的字符：\n• 字母（a-z, A-Z）\n• 数字（0-9，但不能开头）\n• 下划线 _\n\n❌ 不允许：\n• 空格和特殊字符\n• 以数字开头\n• Python 关键字（如 if, for）\n\n💡 最佳实践：\n• 使用小写字母和下划线\n• 要有意义，如 student_name\n• 避免单个字母（除了 i, j, k）\n\n例如：\n✓ user_age = 15\n✓ total_score = 95.5\n✗ 2name = "错误"\n✗ my-name = "错误"'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    // Add user message
    setChatMessages(prev => [...prev, { role: 'user', content: inputMessage }]);

    // Simulate AI response based on context
    setTimeout(() => {
      let aiResponse = '';

      if (inputMessage.includes('Python') || inputMessage.includes('变量')) {
        aiResponse = '关于 Python 变量，记住这几个要点：\n\n1️⃣ 变量名要有意义\n   例如：student_name 比 sn 更好\n\n2️⃣ 使用小写字母和下划线\n   例如：total_score = 95\n\n3️⃣ 赋值用 = 符号\n   例如：age = 15\n\n📝 练习：\n试着定义一个变量存储你的姓名：\nmy_name = "你的名字"\n\n你想看更多例子吗？';
      } else if (inputMessage.includes('Arduino') || inputMessage.includes('LED') || inputMessage.includes('引脚')) {
        aiResponse = 'LED 控制实验的关键步骤：\n\n📌 硬件连接：\n• LED 正极 → 数字引脚 13\n• LED 负极 → GND\n• 建议加 220Ω 电阻\n\n📌 代码要点：\n```cpp\nvoid setup() {\n  pinMode(13, OUTPUT);\n}\n\nvoid loop() {\n  digitalWrite(13, HIGH);\n  delay(1000);\n  digitalWrite(13, LOW);\n  delay(1000);\n}\n```\n\n💡 提示：HIGH=亮，LOW=灭\n\n需要我帮你检查代码吗？';
      } else if (inputMessage.includes('进度') || inputMessage.includes('任务') || inputMessage.includes('学习')) {
        aiResponse = '我看到你今天完成了 1/3 的任务，很棒！💪\n\n📊 当前进度：\n✅ Arduino LED 实验 - 100%\n🔄 Python 视频课程 - 75%\n⏳ 机器学习测验 - 30%\n\n💡 建议：\n1. 先完成 Python 课程的剩余 25%\n2. 然后做机器学习的小测验\n3. 最后可以尝试综合项目\n\n🎯 今日目标：完成所有任务\n加油！你可以的！';
      } else if (inputMessage.includes('循环') || inputMessage.includes('for') || inputMessage.includes('while')) {
        aiResponse = 'Python 循环结构详解：\n\n🔁 for 循环（已知次数）：\n```python\nfor i in range(5):\n    print(i)\n# 输出: 0, 1, 2, 3, 4\n```\n\n🔁 while 循环（条件控制）：\n```python\ncount = 0\nwhile count < 5:\n    print(count)\n    count += 1\n```\n\n💡 使用场景：\n• for：遍历列表、固定次数\n• while：不确定次数、条件判断\n\n想看看实际例子吗？';
      } else if (inputMessage.includes('函数') || inputMessage.includes('def')) {
        aiResponse = 'Python 函数定义：\n\n📦 基本语法：\n```python\ndef greet(name):\n    return f"你好, {name}!"\n\n# 调用函数\nmessage = greet("李明")\nprint(message)  # 你好, 李明!\n```\n\n✨ 优点：\n• 代码复用\n• 模块化\n• 易于维护\n\n💡 练习：\n写一个计算面积的函数：\n```python\ndef calc_area(width, height):\n    return width * height\n```\n\n需要更多示例吗？';
      } else if (inputMessage.includes('传感器') || inputMessage.includes('sensor')) {
        aiResponse = '常用传感器介绍：\n\n🌡️ 温度传感器：\n• 型号：DHT11/DHT22\n• 用途：测量环境温度\n\n💡 光敏电阻：\n• 用途：检测光线强度\n• 应用：自动夜灯\n\n📏 超声波传感器：\n• 型号：HC-SR04\n• 用途：测距\n• 精度：±3mm\n\n🎯 推荐项目：\n制作一个智能温湿度监测站！\n\n想了解哪个传感器的详细用法？';
      } else {
        aiResponse = `我理解你的问题："${inputMessage}"\n\n让我为你解答...\n\n💡 根据你当前的学习进度，我建议：\n\n1️⃣ 查看相关课程资料\n   • Python 基础教程\n   • Arduino 实验指南\n\n2️⃣ 实践操作巩固知识\n   • 动手写代码\n   • 搭建电路\n\n3️⃣ 有问题随时问我\n   • 代码调试\n   • 概念解释\n   • 项目指导\n\n还有其他疑问吗？😊`;
      }

      setChatMessages(prev => [...prev, { role: 'ai', content: aiResponse }]);
    }, 800 + Math.random() * 700);

    setInputMessage('');
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col items-center justify-center py-12 px-4">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-primary">MatuX 移动端体验</h1>
        <p className="text-gray-500 mt-2">随时随地探索 STEM 世界</p>

        {/* Device Switcher */}
        <div className="mt-6 inline-flex bg-white rounded-full p-1 shadow-md border">
          <button
            onClick={() => setDeviceMode('phone')}
            className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
              deviceMode === 'phone'
                ? 'bg-primary text-white shadow-sm'
                : 'text-gray-600 hover:text-primary'
            }`}
          >
            📱 手机模式
          </button>
          <button
            onClick={() => setDeviceMode('tablet')}
            className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
              deviceMode === 'tablet'
                ? 'bg-primary text-white shadow-sm'
                : 'text-gray-600 hover:text-primary'
            }`}
          >
            📟 平板模式
          </button>
        </div>
      </div>

      {/* Device Frame - Phone or Tablet */}
      {deviceMode === 'phone' ? (
        <motion.div
          key="phone"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="relative w-[360px] h-[720px] bg-black rounded-[3rem] shadow-2xl border-[8px] border-slate-800 overflow-hidden"
        >
        {/* Notch / Dynamic Island */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-7 bg-black rounded-b-2xl z-20 flex items-center justify-center space-x-2">
          <div className="w-16 h-4 bg-slate-900 rounded-full"></div>
        </div>

        {/* Screen Content */}
        <div className="w-full h-full bg-slate-50 overflow-y-auto no-scrollbar pb-20 relative">
          {/* Status Bar */}
          <div className="h-10 w-full flex justify-between items-center px-6 pt-2 text-xs font-medium text-slate-900">
            <span>9:41</span>
            <div className="flex items-center space-x-1">
              <Wifi className="h-3 w-3" />
              <Battery className="h-3 w-3" />
            </div>
          </div>

          {/* App Header */}
          <div className="px-5 py-4 flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-primary">Hi, 李明 👋</h2>
              <p className="text-xs text-gray-500">准备好开始今天的实验了吗？</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center">
              <User className="h-5 w-5 text-accent" />
            </div>
          </div>

          {/* Main Content Area - Dynamic Switching */}
          <div className="px-5 space-y-6">
            {activeTab === 'home' && (
              <>
                {/* Hardware Status Card */}
                <div className="bg-slate-900 rounded-2xl p-4 text-white shadow-lg">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center space-x-2">
                      <Cpu className="h-5 w-5 text-accent" />
                      <span className="font-bold text-sm">ESP32 开发板</span>
                    </div>
                    <span className="text-[10px] bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">在线</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="bg-white/10 rounded-lg p-2 flex items-center space-x-2">
                      <Battery className="h-3 w-3 text-green-400" /> <span>85%</span>
                    </div>
                    <div className="bg-white/10 rounded-lg p-2 flex items-center space-x-2">
                      <Wifi className="h-3 w-3 text-blue-400" /> <span>-42dBm</span>
                    </div>
                  </div>
                </div>

                {/* AI Recommendation */}
                <div>
                  <h3 className="font-bold text-primary text-sm mb-3">AI 推荐项目</h3>
                  <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-4 text-white shadow-md relative overflow-hidden">
                    <Zap className="absolute -right-2 -bottom-2 h-20 w-20 text-white/10" />
                    <h4 className="font-bold text-base mb-1">智能感应小夜灯</h4>
                    <p className="text-[10px] text-indigo-100 mb-3 line-clamp-2">利用光敏电阻实现环境光自适应控制。</p>
                    <button className="bg-white text-indigo-600 text-xs font-bold px-4 py-2 rounded-full flex items-center">
                      <Play className="h-3 w-3 mr-1 fill-current" /> 开始实验
                    </button>
                  </div>
                </div>

                {/* Quick Actions Grid */}
                <div>
                  <h3 className="font-bold text-primary text-sm mb-3">常用工具</h3>
                  <div className="grid grid-cols-4 gap-3">
                    {[
                      { icon: Code, label: '代码', color: 'bg-blue-100 text-blue-600' },
                      { icon: Box, label: '3D模型', color: 'bg-orange-100 text-orange-600' },
                      { icon: Camera, label: 'AR扫描', color: 'bg-green-100 text-green-600' },
                      { icon: MessageSquare, label: 'AI助手', color: 'bg-purple-100 text-purple-600' }
                    ].map((item, i) => (
                      <div key={i} className="flex flex-col items-center space-y-2">
                        <div className={`w-12 h-12 rounded-xl ${item.color} flex items-center justify-center shadow-sm`}>
                          <item.icon className="h-6 w-6" />
                        </div>
                        <span className="text-[10px] font-medium text-gray-600">{item.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {activeTab === 'learn' && (
              <div className="space-y-5">
                {/* Daily Challenge */}
                <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-2xl p-4 text-white shadow-md">
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="font-bold text-sm flex items-center"><Zap className="h-4 w-4 mr-1"/> 每日挑战</h3>
                    <span className="text-[10px] bg-white/20 px-2 py-0.5 rounded-full">剩余 2h</span>
                  </div>
                  <p className="text-xs text-orange-50 mb-3">使用 PWM 信号控制舵机转动到指定角度。</p>
                  <button className="w-full bg-white text-orange-600 text-xs font-bold py-2 rounded-lg">接受挑战</button>
                </div>

                <h3 className="font-bold text-primary text-sm">我的课程表</h3>
                {[{ name: 'Arduino 基础语法', p: 100 }, { name: '传感器数据采集', p: 75 }, { name: '无线通信协议 (BLE)', p: 65 }, { name: 'Python 硬件编程', p: 30 }].map((course, i) => (
                  <div key={i} className="bg-white p-3 rounded-xl border shadow-sm flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center text-lg">
                      {i % 2 === 0 ? '🤖' : '📡'}
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="font-bold">{course.name}</span>
                        <span className="text-accent">{course.p}%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-1.5">
                        <div className="bg-accent h-1.5 rounded-full" style={{ width: `${course.p}%` }}></div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* Knowledge Graph Entry */}
                <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-indigo-900 text-xs">STEM 知识图谱</h4>
                    <p className="text-[10px] text-indigo-600 mt-1">探索电子、机械与编程的联系</p>
                  </div>
                  <div className="w-8 h-8 bg-indigo-200 rounded-full flex items-center justify-center text-indigo-700">
                    <Globe className="h-4 w-4" />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'community' && (
              <div className="space-y-4">
                {/* Topic Tabs */}
                <div className="flex space-x-2 overflow-x-auto no-scrollbar pb-1">
                  {['全部', '开源硬件', '3D打印', '机器人', 'AI应用'].map((tag, i) => (
                    <span key={i} className={`text-[10px] px-3 py-1.5 rounded-full whitespace-nowrap ${i === 0 ? 'bg-primary text-white' : 'bg-white border text-gray-600'}`}>
                      {tag}
                    </span>
                  ))}
                </div>

                <h3 className="font-bold text-primary text-sm">创客广场</h3>
                {[1, 2, 3].map((_, i) => (
                  <div key={i} className="bg-white rounded-xl border shadow-sm overflow-hidden">
                    <div className="h-28 bg-slate-200 flex items-center justify-center text-gray-400 text-xs relative">
                      [项目作品展示图]
                      <div className="absolute top-2 right-2 bg-black/50 text-white text-[9px] px-2 py-0.5 rounded-full flex items-center">
                        <User className="h-2 w-2 mr-1" /> 王同学
                      </div>
                    </div>
                    <div className="p-3">
                      <h4 className="font-bold text-xs mb-1">基于 ESP32 的自动浇花系统</h4>
                      <p className="text-[10px] text-gray-500 mb-2 line-clamp-2">通过土壤湿度传感器实时监测，当数值低于阈值时自动开启水泵...</p>
                      <div className="flex justify-between items-center">
                        <div className="flex space-x-2">
                          <span className="text-[9px] bg-slate-100 px-2 py-0.5 rounded text-gray-600">#物联网</span>
                          <span className="text-[9px] bg-slate-100 px-2 py-0.5 rounded text-gray-600">#自动化</span>
                        </div>
                        <div className="flex items-center space-x-1 text-gray-400">
                          <Award className="h-3 w-3" /> <span className="text-[9px]">128</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'profile' && (
              <div className="space-y-6 text-center pt-4">
                <div className="flex flex-col items-center">
                  <div className="w-20 h-20 rounded-full bg-accent/10 flex items-center justify-center mb-2">
                    <User className="h-10 w-10 text-accent" />
                  </div>
                  <h3 className="font-bold text-primary">李明</h3>
                  <p className="text-[10px] text-gray-500">STEM 探索者 Lv.5</p>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-white p-2 rounded-lg border">
                    <div className="font-bold text-accent">12</div>
                    <div className="text-[9px] text-gray-500">完成项目</div>
                  </div>
                  <div className="bg-white p-2 rounded-lg border">
                    <div className="font-bold text-accent">850</div>
                    <div className="text-[9px] text-gray-500">获得积分</div>
                  </div>
                  <div className="bg-white p-2 rounded-lg border">
                    <div className="font-bold text-accent">5</div>
                    <div className="text-[9px] text-gray-500">数字勋章</div>
                  </div>
                </div>
                <div className="bg-white rounded-xl border text-left overflow-hidden">
                  {['我的硬件设备', '区块链证书', '学习报告', '系统设置'].map((item, i) => (
                    <div key={i} className="p-3 border-b last:border-0 flex justify-between items-center text-xs hover:bg-slate-50 cursor-pointer">
                      <span>{item}</span>
                      <span className="text-gray-400">&gt;</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Floating AI Bubble Button - Inside Phone Frame */}
        <motion.button
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => setShowAIAssistant(true)}
          className="absolute bottom-20 right-4 w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full shadow-xl flex items-center justify-center text-white z-30"
        >
          <Bot className="h-6 w-6" />
        </motion.button>

          {/* AI Chat Modal - Phone */}
          <AnimatePresence>
            {showAIAssistant && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-4"
                onClick={() => setShowAIAssistant(false)}
              >
                <motion.div
                  initial={{ y: 50, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: 50, opacity: 0 }}
                  className="bg-white rounded-t-3xl sm:rounded-2xl w-full max-w-md max-h-[80vh] flex flex-col shadow-2xl"
                  onClick={(e) => e.stopPropagation()}
                >
                  {/* Chat Header */}
                  <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-4 rounded-t-3xl sm:rounded-t-2xl flex justify-between items-center">
                    <div className="flex items-center gap-2 text-white">
                      <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                        <Bot className="h-5 w-5" />
                      </div>
                      <div>
                        <span className="font-bold block">AI 老师</span>
                        <span className="text-xs text-white/80">在线答疑</span>
                      </div>
                    </div>
                    <button onClick={() => setShowAIAssistant(false)} className="text-white hover:bg-white/20 rounded-full p-1 transition-colors">
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  {/* Chat Messages */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50" style={{ maxHeight: '50vh' }}>
                    {chatMessages.map((msg, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-line shadow-sm ${
                          msg.role === 'user'
                            ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-sm'
                            : 'bg-white text-slate-900 rounded-bl-sm border'
                        }`}>
                          {msg.content}
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  {/* Chat Input */}
                  <div className="p-4 bg-white border-t">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                        placeholder="输入你的问题..."
                        className="flex-1 px-4 py-2 border-2 rounded-full text-sm focus:outline-none focus:border-purple-500 transition-colors"
                      />
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleSendMessage}
                        className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white shadow-md"
                      >
                        <Send className="h-4 w-4" />
                      </motion.button>
                    </div>
                    <p className="text-xs text-slate-500 mt-2 text-center">💡 AI老师会根据你的学习情况提供个性化指导</p>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Bottom Navigation Bar */}
          <div className="absolute bottom-0 w-full h-16 bg-white border-t flex justify-around items-center px-2 pb-2">
            {['home', 'learn', 'community', 'profile'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex flex-col items-center space-y-1 ${activeTab === tab ? 'text-accent' : 'text-gray-400'}`}
              >
                {tab === 'home' && <Box className="h-5 w-5" />}
                {tab === 'learn' && <Code className="h-5 w-5" />}
                {tab === 'community' && <MessageSquare className="h-5 w-5" />}
                {tab === 'profile' && <User className="h-5 w-5" />}
                <span className="text-[9px] font-medium capitalize">{tab}</span>
              </button>
            ))}
          </div>
        </motion.div>
      ) : (
        /* Tablet Mode */
        <motion.div
          key="tablet"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="relative w-[1024px] h-[768px] bg-black rounded-[2rem] shadow-2xl border-[12px] border-slate-800 overflow-hidden"
        >
          {/* Tablet Status Bar */}
          <div className="h-8 bg-slate-900 flex justify-between items-center px-6 text-xs text-white">
            <span>{new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}</span>
            <div className="flex items-center space-x-2">
              <Wifi className="h-3 w-3" />
              <Battery className="h-3 w-3" />
              <span>85%</span>
            </div>
          </div>

          {/* Tablet Content */}
          <div className="w-full h-full bg-gradient-to-br from-slate-50 to-slate-100 overflow-y-auto p-8 pb-24">
            {/* Welcome Section */}
            <div className="mb-8">
              <h2 className="text-4xl font-bold text-slate-900 mb-2">你好，同学 👋</h2>
              <p className="text-lg text-slate-600">{new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })}</p>
            </div>

            {/* Quick Actions Grid */}
            <div className="grid grid-cols-4 gap-5 mb-8">
              {[
                { icon: Code, label: '我的课程', color: 'from-blue-500 to-blue-600', emoji: '📚' },
                { icon: Camera, label: 'AR 实验室', color: 'from-purple-500 to-purple-600', emoji: '🥽' },
                { icon: Box, label: '实战项目', color: 'from-green-500 to-green-600', emoji: '🚀' },
                { icon: Award, label: '学习成就', color: 'from-orange-500 to-orange-600', emoji: '🏆' }
              ].map((item, i) => (
                <motion.button
                  key={i}
                  whileHover={{ scale: 1.05, y: -4 }}
                  whileTap={{ scale: 0.98 }}
                  className="bg-white rounded-2xl p-6 shadow-md hover:shadow-xl transition-all flex flex-col items-center gap-3"
                >
                  <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${item.color} flex items-center justify-center text-3xl`}>
                    {item.emoji}
                  </div>
                  <span className="font-semibold text-slate-900">{item.label}</span>
                </motion.button>
              ))}
            </div>

            {/* Today's Tasks */}
            <div className="mb-8">
              <h3 className="text-xl font-bold text-slate-900 mb-4">今日学习任务</h3>
              <div className="bg-white rounded-2xl p-4 shadow-md space-y-3">
                {[
                  { title: 'Python 基础语法 - 变量与数据类型', duration: '30分钟', type: '视频课程', progress: 75, completed: false },
                  { title: 'Arduino 入门 - LED 控制实验', duration: '45分钟', type: '实践操作', progress: 100, completed: true },
                  { title: '机器学习基础 - 监督学习概念', duration: '25分钟', type: '互动测验', progress: 30, completed: false }
                ].map((task, i) => (
                  <div key={i} className="flex items-center gap-4 p-4 rounded-xl hover:bg-slate-50 transition-colors">
                    <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                      task.completed ? 'bg-green-500 border-green-500 text-white' : 'border-slate-300'
                    }`}>
                      {task.completed && '✓'}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-slate-900 text-sm mb-1">{task.title}</h4>
                      <p className="text-xs text-slate-500">{task.duration} · {task.type}</p>
                    </div>
                    <div className="flex items-center gap-3 min-w-[120px]">
                      <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full" style={{ width: `${task.progress}%` }}></div>
                      </div>
                      <span className="text-xs font-semibold text-blue-600 min-w-[35px] text-right">{task.progress}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Learning Stats */}
            <div className="mb-8">
              <h3 className="text-xl font-bold text-slate-900 mb-4">本周学习统计</h3>
              <div className="grid grid-cols-4 gap-4">
                {[
                  { value: '12.5', label: '学习时长(小时)' },
                  { value: '8', label: '完成任务' },
                  { value: '450', label: '获得积分' },
                  { value: '3', label: '连续天数' }
                ].map((stat, i) => (
                  <motion.div
                    key={i}
                    whileHover={{ y: -2 }}
                    className="bg-white rounded-xl p-6 text-center shadow-md"
                  >
                    <div className="text-3xl font-bold text-blue-600 mb-2">{stat.value}</div>
                    <div className="text-sm text-slate-600">{stat.label}</div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Recommended Courses */}
            <div>
              <h3 className="text-xl font-bold text-slate-900 mb-4">为你推荐</h3>
              <div className="grid grid-cols-3 gap-5">
                {[
                  { title: '机器人编程进阶', desc: '学习传感器应用和自动控制原理', level: '中级', duration: '12课时', emoji: '🤖', gradient: 'from-indigo-500 to-purple-600' },
                  { title: 'AI 视觉识别', desc: '掌握图像处理和模式识别技术', level: '高级', duration: '16课时', emoji: '👁️', gradient: 'from-pink-500 to-red-500' },
                  { title: '3D 建模与设计', desc: '使用 Blender 创建三维模型', level: '初级', duration: '10课时', emoji: '🎨', gradient: 'from-cyan-500 to-blue-500' }
                ].map((course, i) => (
                  <motion.div
                    key={i}
                    whileHover={{ y: -4 }}
                    className="bg-white rounded-2xl overflow-hidden shadow-md hover:shadow-xl transition-all"
                  >
                    <div className={`h-40 bg-gradient-to-br ${course.gradient} flex items-center justify-center text-6xl`}>
                      {course.emoji}
                    </div>
                    <div className="p-5">
                      <h4 className="font-bold text-slate-900 mb-2">{course.title}</h4>
                      <p className="text-sm text-slate-600 mb-3 line-clamp-2">{course.desc}</p>
                      <div className="flex gap-3 text-xs text-slate-500 mb-4">
                        <span>{course.level}</span>
                        <span>·</span>
                        <span>{course.duration}</span>
                      </div>
                      <button className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white py-2.5 rounded-xl font-semibold text-sm hover:shadow-lg transition-all">
                        开始学习
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>

          {/* Floating AI Bubble Button - Inside Tablet Frame */}
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setShowAIAssistant(true)}
            className="absolute bottom-24 right-8 w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full shadow-2xl flex items-center justify-center text-white z-30"
          >
            <Bot className="h-7 w-7" />
          </motion.button>

          {/* AI Chat Modal - Tablet */}
          <AnimatePresence>
            {showAIAssistant && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-8"
                onClick={() => setShowAIAssistant(false)}
              >
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.9, opacity: 0 }}
                  className="bg-white rounded-3xl w-full max-w-2xl h-[600px] flex flex-col shadow-2xl overflow-hidden"
                  onClick={(e) => e.stopPropagation()}
                >
                  {/* Chat Header */}
                  <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-6 flex justify-between items-center">
                    <div className="flex items-center gap-3 text-white">
                      <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                        <Bot className="h-6 w-6" />
                      </div>
                      <div>
                        <h3 className="font-bold text-lg">AI 老师</h3>
                        <p className="text-xs text-white/80">根据你的学习进度提供个性化指导</p>
                      </div>
                    </div>
                    <button onClick={() => setShowAIAssistant(false)} className="text-white hover:bg-white/20 rounded-full p-2 transition-colors">
                      <X className="h-6 w-6" />
                    </button>
                  </div>

                  {/* Chat Messages */}
                  <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50">
                    {chatMessages.map((msg, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-[70%] rounded-2xl px-5 py-3 text-sm whitespace-pre-line shadow-sm ${
                          msg.role === 'user'
                            ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-sm'
                            : 'bg-white text-slate-900 rounded-bl-sm border'
                        }`}>
                          {msg.content}
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  {/* Chat Input */}
                  <div className="p-6 bg-white border-t">
                    <div className="flex gap-3">
                      <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                        placeholder="输入你的问题，AI老师会根据你的学习情况给出建议..."
                        className="flex-1 px-5 py-3 border-2 rounded-full text-sm focus:outline-none focus:border-purple-500 transition-colors"
                      />
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleSendMessage}
                        className="px-6 h-12 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold shadow-lg hover:shadow-xl transition-all"
                      >
                        <Send className="h-5 w-5" />
                      </motion.button>
                    </div>
                    <p className="text-xs text-slate-500 mt-3 text-center">💡 AI老师已了解你的学习进度：Python 75% · Arduino 100% · 机器学习 30%</p>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Tablet Dock */}
          <div className="absolute bottom-5 left-1/2 -translate-x-1/2 bg-white/80 backdrop-blur-xl rounded-2xl px-5 py-3 shadow-xl border border-white/30 flex gap-4">
            {[
              { icon: Box, label: '首页' },
              { icon: Code, label: '课程' },
              { icon: Camera, label: 'AR实验' },
              { icon: Box, label: '项目' },
              { icon: User, label: '我的' }
            ].map((item, i) => (
              <motion.button
                key={i}
                whileHover={{ scale: 1.15, y: -8 }}
                whileTap={{ scale: 1.05 }}
                className="w-14 h-14 rounded-xl flex items-center justify-center hover:bg-black/5 transition-colors"
                title={item.label}
              >
                <item.icon className="h-7 w-7 text-slate-700" />
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
