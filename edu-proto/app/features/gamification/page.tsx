'use client';

import { motion } from 'framer-motion';
import { Zap, Trophy, Star, Target, Flame, ArrowLeft, Award, BarChart3 } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function GamificationPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-red-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-600 to-orange-500 text-white py-16 relative overflow-hidden">
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
            <div className="inline-flex items-center px-3 py-1 rounded-full bg-white/20 border border-white/30 text-white text-sm mb-4">
              <Flame className="h-4 w-4 mr-2" /> 三维激励机制
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">多模态游戏化激励</h1>
            <p className="text-xl text-red-100 max-w-2xl">
              融合语音、AR 手势与成就系统，打造沉浸式学习体验，激发学生无限探索欲
            </p>
          </motion.div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16 space-y-20">
        {/* Motivation Dimensions */}
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: Zap,
              title: '语音互动激励',
              desc: 'AI 语音助手实时反馈，通过语音鼓励与提示增强学习动力。',
              color: 'yellow',
              examples: ['太棒了！电路连接正确！', '再试一次，你可以的！', '恭喜完成挑战！']
            },
            {
              icon: Target,
              title: 'AR 手势激励',
              desc: '通过摄像头识别学生手势动作，给予虚拟奖励与特效反馈。',
              color: 'purple',
              examples: ['✋ 手势识别成功', '👍 点赞动画触发', '🎉 胜利特效播放']
            },
            {
              icon: Trophy,
              title: '成就系统激励',
              desc: '多层次成就徽章与积分排行榜，构建良性竞争学习氛围。',
              color: 'orange',
              examples: ['🏆 电路大师徽章', '⭐ 连续学习 7 天', '🎯 实验满分成就']
            }
          ].map((dim, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15 }}
              className="bg-white rounded-2xl p-6 border shadow-sm"
            >
              <div className={`w-14 h-14 rounded-xl bg-${dim.color}-100 flex items-center justify-center text-${dim.color}-600 mb-4`}>
                <dim.icon className="h-7 w-7" />
              </div>
              <h3 className="text-xl font-bold text-primary mb-3">{dim.title}</h3>
              <p className="text-gray-600 text-sm mb-4">{dim.desc}</p>
              <div className="space-y-2">
                {dim.examples.map((example, j) => (
                  <div key={j} className="text-xs bg-slate-50 px-3 py-2 rounded-lg text-gray-700 border">
                    {example}
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Achievement System Demo */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="bg-white rounded-3xl border p-8 md:p-12"
        >
          <h2 className="text-3xl font-bold text-primary mb-8 text-center">成就徽章系统</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { name: '新手创客', icon: Star, level: '青铜', color: 'gray' },
              { name: '电路达人', icon: Zap, level: '白银', color: 'blue' },
              { name: '机器人专家', icon: Award, level: '黄金', color: 'yellow' },
              { name: 'STEM 大师', icon: Trophy, level: '钻石', color: 'purple' }
            ].map((badge, i) => (
              <motion.div
                key={i}
                whileHover={{ scale: 1.05 }}
                className="flex flex-col items-center p-4 rounded-2xl bg-gradient-to-br from-slate-50 to-white border hover:shadow-lg transition-shadow"
              >
                <div className={`w-16 h-16 rounded-full bg-${badge.color}-100 flex items-center justify-center mb-3`}>
                  <badge.icon className={`h-8 w-8 text-${badge.color}-600`} />
                </div>
                <h4 className="font-bold text-primary text-sm mb-1">{badge.name}</h4>
                <span className={`text-xs px-2 py-0.5 rounded-full bg-${badge.color}-100 text-${badge.color}-700`}>
                  {badge.level}
                </span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Leaderboard Preview */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="bg-white rounded-3xl border p-8 md:p-12"
        >
          <h2 className="text-3xl font-bold text-primary mb-8 text-center flex items-center justify-center">
            <BarChart3 className="h-8 w-8 mr-3 text-red-500" />
            实时积分排行榜
          </h2>
          <div className="max-w-2xl mx-auto space-y-3">
            {[
              { rank: 1, name: '李明', points: 2850, badge: '🥇' },
              { rank: 2, name: '王芳', points: 2720, badge: '🥈' },
              { rank: 3, name: '张伟', points: 2680, badge: '🥉' },
              { rank: 4, name: '刘洋', points: 2540, badge: '4' },
              { rank: 5, name: '陈静', points: 2490, badge: '5' }
            ].map((player, i) => (
              <div 
                key={i} 
                className={`flex items-center justify-between p-4 rounded-xl ${
                  i === 0 ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-300' : 
                  i === 1 ? 'bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-300' :
                  i === 2 ? 'bg-gradient-to-r from-orange-50 to-amber-50 border border-orange-300' :
                  'bg-slate-50 border'
                }`}
              >
                <div className="flex items-center space-x-4">
                  <span className="text-2xl">{player.badge}</span>
                  <div>
                    <div className="font-bold text-primary">{player.name}</div>
                    <div className="text-xs text-gray-500">第 {player.rank} 名</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-red-600">{player.points} 分</div>
                  <div className="text-xs text-gray-500">本周积分</div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* CTA */}
        <div className="text-center">
          <button className="bg-gradient-to-r from-red-600 to-orange-500 hover:from-red-700 hover:to-orange-600 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all shadow-lg">
            体验游戏化激励系统
          </button>
        </div>
      </div>
    </div>
  );
}
