'use client';

import { motion } from 'framer-motion';
import { GitFork, Link, Mail, Award, Globe, Cpu } from 'lucide-react';

const team = [
  {
    name: "陈伟博士",
    role: "创始人 & CEO",
    desc: "前知名高校 AI 实验室首席科学家，专注于边缘计算与 STEM 教育科技的深度融合。",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=200&h=200"
  },
  {
    name: "林晓梅",
    role: "CTO",
    desc: "资深全栈架构师，拥有 10+ 年微服务与区块链系统开发经验，主导过多个大型教育平台搭建。",
    avatar: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&q=80&w=200&h=200"
  },
  {
    name: "张伟",
    role: "硬件研发总监",
    desc: "嵌入式系统专家，曾主导百万级 IoT 设备的量产项目，致力于让硬件编程更简单。",
    avatar: "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&q=80&w=200&h=200"
  }
];

export default function AboutPage() {
  return (
    <div className="container mx-auto px-4 py-16">
      {/* Mission Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-20 max-w-3xl mx-auto"
      >
        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl text-primary mb-6">我们的愿景</h1>
        <p className="text-lg text-gray-500 leading-relaxed mb-8">
          MatuX 致力于通过前沿技术消除教育资源的不平等。我们相信，每一个孩子都应该有机会接触到最先进的 STEM 实验设备，无论他们身处何地。
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          {[
            { icon: Globe, title: "全球视野", desc: "整合国际优质 STEM 课程资源" },
            { icon: Cpu, title: "技术驱动", desc: "AI 与物联网赋能个性化学习" },
            { icon: Award, title: "公平认证", desc: "区块链保障每一份学习成果" }
          ].map((item, i) => (
            <div key={i} className="p-6 rounded-xl bg-slate-50 border">
              <item.icon className="h-8 w-8 text-accent mx-auto mb-3" />
              <h3 className="font-bold text-primary">{item.title}</h3>
              <p className="text-sm text-gray-500 mt-2">{item.desc}</p>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Team Section */}
      <div className="mb-20">
        <h2 className="text-3xl font-bold text-center text-primary mb-12">核心团队</h2>
        <div className="grid gap-8 md:grid-cols-3">
          {team.map((member, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="flex flex-col items-center text-center p-6 rounded-2xl border bg-white shadow-sm hover:shadow-md transition-all"
            >
              <div className="w-24 h-24 rounded-full overflow-hidden mb-4 border-4 border-slate-100">
                <img src={member.avatar} alt={member.name} className="w-full h-full object-cover" />
              </div>
              <h3 className="text-xl font-bold text-primary">{member.name}</h3>
              <p className="text-accent font-medium text-sm mb-3">{member.role}</p>
              <p className="text-gray-500 text-sm mb-4">{member.desc}</p>
              <div className="flex space-x-3">
                <button className="p-2 rounded-full bg-slate-100 hover:bg-slate-200 transition-colors"><GitFork className="h-4 w-4" /></button>
                <button className="p-2 rounded-full bg-slate-100 hover:bg-slate-200 transition-colors"><Link className="h-4 w-4" /></button>
                <button className="p-2 rounded-full bg-slate-100 hover:bg-slate-200 transition-colors"><Mail className="h-4 w-4" /></button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Contact CTA */}
      <div className="rounded-2xl bg-primary p-12 text-center text-primary-foreground relative overflow-hidden">
        <div className="relative z-10">
          <h2 className="text-2xl font-bold mb-4">寻求合作或投资？</h2>
          <p className="mb-8 opacity-90 max-w-2xl mx-auto">我们期待与志同道合的伙伴共同推动 STEM 教育的未来。欢迎联系我们获取详细的商业计划书。</p>
          <button className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-white text-primary hover:bg-slate-100 h-11 px-8">
            联系商务团队
          </button>
        </div>
      </div>
    </div>
  );
}
