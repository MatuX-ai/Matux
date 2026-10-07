import { useState } from 'react';
import { ChatMessage } from '../types';

export function useChat() {
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: 'ai',
      content: '你好！我是你的 AI 老师 👋\n\n我看到你正在学习：\n• Python 基础语法（75%）\n• Arduino LED 实验（已完成✅）\n• 机器学习基础（30%）\n\n有什么我可以帮助你的吗？',
      memoryRef: '📌 引用记忆：你 3 天前问过 range()，正确率仅 55%'
    },
    {
      role: 'user',
      content: 'Python 变量命名有什么规则？'
    },
    {
      role: 'ai',
      content: '很好的问题！Python 变量命名规则：\n\n✅ 允许的字符：\n• 字母（a-z, A-Z）\n• 数字（0-9，但不能开头）\n• 下划线 _\n\n❌ 不允许：\n• 空格和特殊字符\n• 以数字开头\n• Python 关键字（如 if, for）\n\n💡 最佳实践：\n• 使用小写字母和下划线\n• 要有意义，如 student_name\n• 避免单个字母（除了 i, j, k）\n\n例如：\n✓ user_age = 15\n✓ total_score = 95.5\n✗ 2name = "错误"\n✗ my-name = "错误"',
      memoryRef: '📌 引用记忆：你上周完成 LED 实验，已掌握 pinMode/digitalWrite'
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
      let memoryRef: string | undefined = undefined;

      if (inputMessage.includes('Python') || inputMessage.includes('变量')) {
        aiResponse = '关于 Python 变量，记住这几个要点：\n\n1️⃣ 变量名要有意义\n   例如：student_name 比 sn 更好\n\n2️⃣ 使用小写字母和下划线\n   例如：total_score = 95\n\n3️⃣ 赋值用 = 符号\n   例如：age = 15\n\n📝 练习：\n试着定义一个变量存储你的姓名：\nmy_name = "你的名字"\n\n你想看更多例子吗？';
        memoryRef = '📌 引用记忆：你本周 Python 进度 75%，"变量与数据类型"章节未完成';
      } else if (inputMessage.includes('Arduino') || inputMessage.includes('LED') || inputMessage.includes('引脚')) {
        aiResponse = 'LED 控制实验的关键步骤：\n\n📌 硬件连接：\n• LED 正极 → 数字引脚 13\n• LED 负极 → GND\n• 建议加 220Ω 电阻\n\n📌 代码要点：\n```cpp\nvoid setup() {\n  pinMode(13, OUTPUT);\n}\n\nvoid loop() {\n  digitalWrite(13, HIGH);\n  delay(1000);\n  digitalWrite(13, LOW);\n  delay(1000);\n}\n```\n\n💡 提示：HIGH=亮，LOW=灭\n\n需要我帮你检查代码吗？';
      } else if (inputMessage.includes('进度') || inputMessage.includes('任务') || inputMessage.includes('学习')) {
        aiResponse = '我看到你今天完成了 1/3 的任务，很棒！💪\n\n📊 当前进度：\n✅ Arduino LED 实验 - 100%\n🔄 Python 视频课程 - 75%\n⏳ 机器学习测验 - 30%\n\n💡 建议：\n1. 先完成 Python 课程的剩余 25%\n2. 然后做机器学习的小测验\n3. 最后可以尝试综合项目\n\n🎯 今日目标：完成所有任务\n加油！你可以的！';
      } else if (inputMessage.includes('循环') || inputMessage.includes('for') || inputMessage.includes('while')) {
        aiResponse = 'Python 循环结构详解：\n\n🔁 for 循环（已知次数）：\n```python\nfor i in range(5):\n    print(i)\n# 输出: 0, 1, 2, 3, 4\n```\n\n🔁 while 循环（条件控制）：\n```python\ncount = 0\nwhile count < 5:\n    print(count)\n    count += 1\n```\n\n💡 使用场景：\n• for：遍历列表、固定次数\n• while：不确定次数、条件判断\n\n想看看实际例子吗？';
        memoryRef = '📌 引用记忆：range() 是你的薄弱点（正确率 55%），重点讲讲参数';
      } else if (inputMessage.includes('函数') || inputMessage.includes('def')) {
        aiResponse = 'Python 函数定义：\n\n📦 基本语法：\n```python\ndef greet(name):\n    return f"你好, {name}!"\n\n# 调用函数\nmessage = greet("李明")\nprint(message)  # 你好, 李明!\n```\n\n✨ 优点：\n• 代码复用\n• 模块化\n• 易于维护\n\n💡 练习：\n写一个计算面积的函数：\n```python\ndef calc_area(width, height):\n    return width * height\n```\n\n需要更多示例吗？';
      } else if (inputMessage.includes('传感器') || inputMessage.includes('sensor')) {
        aiResponse = '常用传感器介绍：\n\n🌡️ 温度传感器：\n• 型号：DHT11/DHT22\n• 用途：测量环境温度\n\n💡 光敏电阻：\n• 用途：检测光线强度\n• 应用：自动夜灯\n\n📏 超声波传感器：\n• 型号：HC-SR04\n• 用途：测距\n• 精度：±3mm\n\n🎯 推荐项目：\n制作一个智能温湿度监测站！\n\n想了解哪个传感器的详细用法？';
      } else {
        aiResponse = `我理解你的问题："${inputMessage}"\n\n让我为你解答...\n\n💡 根据你当前的学习进度，我建议：\n\n1️⃣ 查看相关课程资料\n   • Python 基础教程\n   • Arduino 实验指南\n\n2️⃣ 实践操作巩固知识\n   • 动手写代码\n   • 搭建电路\n\n3️⃣ 有问题随时问我\n   • 代码调试\n   • 概念解释\n   • 项目指导\n\n还有其他疑问吗？😊`;
      }

      setChatMessages(prev => [...prev, { role: 'ai', content: aiResponse, memoryRef }]);
    }, 800 + Math.random() * 700);

    setInputMessage('');
  };

  return {
    chatMessages,
    inputMessage,
    setInputMessage,
    handleSendMessage,
    setChatMessages
  };
}
