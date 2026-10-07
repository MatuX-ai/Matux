'use client';

import { motion } from 'framer-motion';
import { User, Award, Coins, Zap, Plus } from 'lucide-react';
import { useState } from 'react';
import { DeviceMode, PhoneSubPage } from '../../types';

interface ProfilePageProps {
  mode: DeviceMode;
  onNavigate?: (page: PhoneSubPage) => void;
}

export function ProfilePage({ mode, onNavigate }: ProfilePageProps) {
  const isPhone = mode === 'phone';
  
  // Token管理状态
  const [showRechargeModal, setShowRechargeModal] = useState(false);
  const [customAmount, setCustomAmount] = useState('');
  
  // 模拟Token数据（实际应从后端获取）
  const tokenData = {
    total: 1000000, // 每月赠送100万
    used: 235000,   // 已使用
    remaining: 765000, // 剩余
    resetDate: '2026-03-01' // 下次重置日期
  };

  // 处理充值
  const handleRecharge = (amount: number) => {
    if (amount <= 0) {
      alert('请输入有效的充值金额');
      return;
    }
    // TODO: 调用后端支付API
    console.log(`充值 ¥${amount}，获得 ${amount}万 Token`);
    alert(`充值成功！\n金额：¥${amount}\n获得：${amount}万 Token`);
    setShowRechargeModal(false);
    setCustomAmount('');
  };

  if (isPhone) {
    return (
      <div className="space-y-6 text-center pt-4 px-5 pb-24">
        {/* 用户信息 */}
        <div className="flex flex-col items-center">
          <div className="w-20 h-20 rounded-full bg-blue-100 flex items-center justify-center mb-2">
            <User className="h-10 w-10 text-blue-600" />
          </div>
          <h3 className="font-bold text-blue-600">李明</h3>
          <p className="text-[10px] text-gray-500">STEM 探索者 Lv.5</p>
        </div>

        {/* Token使用情况 */}
        <motion.div
          whileTap={{ scale: 0.98 }}
          onClick={() => setShowRechargeModal(true)}
          className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-4 border-2 border-indigo-200 cursor-pointer hover:border-indigo-400 transition-colors"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Coins className="h-5 w-5 text-indigo-600" />
              <span className="font-bold text-sm text-slate-900">AI教师 Token</span>
            </div>
            <Plus className="h-4 w-4 text-indigo-600" />
          </div>
          <div className="text-left space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-600">剩余</span>
              <span className="font-bold text-indigo-600">{(tokenData.remaining / 10000).toFixed(1)}万</span>
            </div>
            <div className="w-full h-2 bg-white rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all"
                style={{ width: `${(tokenData.remaining / tokenData.total) * 100}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>已用 {(tokenData.used / 10000).toFixed(1)}万</span>
              <span>总额 {(tokenData.total / 10000).toFixed(0)}万/月</span>
            </div>
          </div>
        </motion.div>

        {/* 统计数据 */}
        <motion.div
          whileTap={{ scale: 0.98 }}
          onClick={() => onNavigate?.('成就详情')}
          className="grid grid-cols-3 gap-2 text-center cursor-pointer"
        >
          <div className="bg-white p-2 rounded-lg border">
            <div className="font-bold text-blue-600">12</div>
            <div className="text-[9px] text-gray-500">完成项目</div>
          </div>
          <div className="bg-white p-2 rounded-lg border">
            <div className="font-bold text-blue-600">850</div>
            <div className="text-[9px] text-gray-500">获得积分</div>
          </div>
          <div className="bg-white p-2 rounded-lg border">
            <div className="font-bold text-blue-600">5</div>
            <div className="text-[9px] text-gray-500">数字勋章</div>
          </div>
        </motion.div>

        {/* 菜单列表 */}
        <div className="bg-white rounded-xl border text-left overflow-hidden">
          {[
            { label: '编辑资料', icon: '✏️', action: () => onNavigate?.('个人资料') },
            { label: '学习画像', icon: '🧠', action: () => onNavigate?.('学习画像') },
            { label: '成长轨迹', icon: '📈', action: () => onNavigate?.('成长轨迹') },
            { label: 'AI 教师设置', icon: '🤖', action: () => onNavigate?.('AI教师设置') },
            { label: '防作弊测验', icon: '📝', action: () => onNavigate?.('防作弊测验') },
            { label: 'Blockly 编程', icon: '🧩', action: () => onNavigate?.('Blockly编程') },
            { label: '电路实验', icon: '⚡', action: () => onNavigate?.('电路实验') },
            { label: 'AR 实验室', icon: '🔬', action: () => onNavigate?.('AR实验室') },
            { label: '创意引擎', icon: '🎨', action: () => onNavigate?.('创意引擎') },
            { label: '积分商城', icon: '🛒', action: () => onNavigate?.('积分商城') },
            { label: '连胜系统', icon: '🔥', action: () => onNavigate?.('连胜系统') },
            { label: '我的硬件设备', icon: '🔌', action: () => onNavigate?.('设备连接') },
            { label: '区块链证书', icon: '📜', action: () => onNavigate?.('区块链证书') },
            { label: '学习报告', icon: '📊', action: () => onNavigate?.('学习报告') },
            { label: '系统设置', icon: '⚙️', action: () => onNavigate?.('系统设置') }
          ].map((item, i) => (
            <motion.div
              key={i}
              whileTap={{ scale: 0.98 }}
              onClick={item.action}
              className="p-3 border-b last:border-0 flex justify-between items-center text-xs hover:bg-slate-50 cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </div>
              <span className="text-gray-400">&gt;</span>
            </motion.div>
          ))}
        </div>

        {/* 充值模态框 */}
        {showRechargeModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-4"
            onClick={() => setShowRechargeModal(false)}
          >
            <motion.div
              initial={{ y: 50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 50, opacity: 0 }}
              className="bg-white rounded-t-3xl sm:rounded-2xl w-full max-w-md p-6 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-lg flex items-center gap-2">
                  <Zap className="h-5 w-5 text-indigo-600" />
                  Token 充值
                </h3>
                <button 
                  onClick={() => setShowRechargeModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                {/* 当前余额 */}
                <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-4">
                  <p className="text-xs text-slate-600 mb-1">当前剩余</p>
                  <p className="text-2xl font-bold text-indigo-600">{(tokenData.remaining / 10000).toFixed(1)}万 Token</p>
                  <p className="text-[10px] text-slate-500 mt-1">下次重置: {tokenData.resetDate}</p>
                </div>

                {/* 充值选项 */}
                <div>
                  <p className="text-sm font-semibold text-slate-900 mb-3">选择充值金额</p>
                  <div className="grid grid-cols-3 gap-2">
                    {[10, 20, 50].map((amount) => (
                      <motion.button
                        key={amount}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => handleRecharge(amount)}
                        className="py-3 px-4 bg-white border-2 border-slate-200 rounded-xl hover:border-indigo-500 hover:bg-indigo-50 transition-all"
                      >
                        <div className="text-lg font-bold text-slate-900">¥{amount}</div>
                        <div className="text-[10px] text-slate-500">+{amount}万 Token</div>
                      </motion.button>
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {[100].map((amount) => (
                      <motion.button
                        key={amount}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => handleRecharge(amount)}
                        className="py-3 px-4 bg-white border-2 border-slate-200 rounded-xl hover:border-indigo-500 hover:bg-indigo-50 transition-all"
                      >
                        <div className="text-lg font-bold text-slate-900">¥{amount}</div>
                        <div className="text-[10px] text-slate-500">+{amount}万 Token</div>
                      </motion.button>
                    ))}
                    <motion.button
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setCustomAmount(customAmount ? '' : 'input')}
                      className="py-3 px-4 bg-white border-2 border-dashed border-slate-300 rounded-xl hover:border-indigo-500 hover:bg-indigo-50 transition-all"
                    >
                      <div className="text-lg font-bold text-slate-900">自定义</div>
                      <div className="text-[10px] text-slate-500">输入金额</div>
                    </motion.button>
                  </div>
                </div>

                {/* 自定义金额输入 */}
                {customAmount === 'input' && (
                  <div className="space-y-2">
                    <input
                      type="number"
                      placeholder="输入充值金额（元）"
                      className="w-full px-4 py-3 border-2 rounded-xl focus:outline-none focus:border-indigo-500"
                      onChange={(e) => setCustomAmount(e.target.value)}
                    />
                    <motion.button
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleRecharge(parseInt(customAmount) || 0)}
                      className="w-full py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl font-semibold"
                    >
                      确认充值
                    </motion.button>
                  </div>
                )}

                {/* 说明 */}
                <div className="bg-slate-50 rounded-lg p-3 text-xs text-slate-600 space-y-1">
                  <p>💡 充值说明：</p>
                  <p>• 每月赠送100万Token</p>
                  <p>• 超出部分按 ¥10/100万Token 计费</p>
                  <p>• Token永久有效，不会过期</p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </div>
    );
  }

  // 平板模式 - 学习成就页面
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-slate-900">学习成就 🏆</h2>
      </div>

      {/* Token使用情况卡片 */}
      <motion.div
        whileHover={{ scale: 1.01 }}
        onClick={() => setShowRechargeModal(true)}
        className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-6 text-white cursor-pointer hover:shadow-xl transition-all"
      >
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Coins className="h-6 w-6" />
              <p className="text-lg font-bold">AI教师 Token</p>
            </div>
            <p className="text-4xl font-bold mb-2">{(tokenData.remaining / 10000).toFixed(1)}万</p>
            <p className="text-sm text-white/80">剩余可用 · 下次重置: {tokenData.resetDate}</p>
          </div>
          <div className="text-right">
            <div className="text-sm mb-1">已使用</div>
            <div className="text-2xl font-bold">{(tokenData.used / 10000).toFixed(1)}万</div>
            <div className="text-xs mt-2 opacity-80">总额 {(tokenData.total / 10000).toFixed(0)}万/月</div>
          </div>
        </div>
        <div className="mt-4">
          <div className="w-full h-3 bg-white/30 rounded-full overflow-hidden">
            <div 
              className="h-full bg-white rounded-full transition-all"
              style={{ width: `${(tokenData.remaining / tokenData.total) * 100}%` }}
            ></div>
          </div>
        </div>
        <div className="mt-4 flex items-center gap-2 text-sm">
          <Plus className="h-4 w-4" />
          <span>点击充值更多 Token</span>
        </div>
      </motion.div>

      {/* 等级和经验值 */}
      <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-orange-100 text-sm mb-1">当前等级</p>
            <h3 className="text-3xl font-bold">STEM 探索者 Lv.5</h3>
          </div>
          <Award className="h-16 w-16 opacity-80" />
        </div>
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-2">
            <span>经验值</span>
            <span>850 / 1000</span>
          </div>
          <div className="w-full h-3 bg-white/30 rounded-full overflow-hidden">
            <div className="h-full bg-white rounded-full" style={{ width: '85%' }}></div>
          </div>
        </div>
      </div>

      {/* 徽章网格 */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { name: '首次实验', icon: '🎯', earned: true },
          { name: '代码大师', icon: '💻', earned: true },
          { name: '硬件专家', icon: '🔧', earned: true },
          { name: '团队合作', icon: '👥', earned: true },
          { name: '创新思维', icon: '💡', earned: false },
          { name: '坚持不懈', icon: '🔥', earned: false },
          { name: '知识分享', icon: '📚', earned: false },
          { name: '完美主义者', icon: '⭐', earned: false }
        ].map((badge, i) => (
          <motion.div
            key={i}
            whileHover={{ scale: 1.05 }}
            className={`bg-white rounded-2xl p-4 text-center shadow-md ${
              badge.earned ? 'cursor-pointer hover:shadow-lg' : 'opacity-50 grayscale'
            }`}
          >
            <div className="text-3xl mb-2">{badge.icon}</div>
            <p className="text-xs font-medium text-slate-900">{badge.name}</p>
            {badge.earned && <p className="text-[10px] text-green-600 mt-1">已获得</p>}
          </motion.div>
        ))}
      </div>

      {/* 充值模态框（平板） */}
      {showRechargeModal && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-8"
          onClick={() => setShowRechargeModal(false)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-white rounded-3xl w-full max-w-2xl p-8 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-bold text-2xl flex items-center gap-3">
                <Zap className="h-7 w-7 text-indigo-600" />
                Token 充值中心
              </h3>
              <button 
                onClick={() => setShowRechargeModal(false)}
                className="text-slate-400 hover:text-slate-600 text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-6">
              {/* 左侧：余额信息 */}
              <div className="space-y-4">
                <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-6">
                  <p className="text-sm text-slate-600 mb-2">当前剩余</p>
                  <p className="text-4xl font-bold text-indigo-600">{(tokenData.remaining / 10000).toFixed(1)}万</p>
                  <p className="text-sm text-slate-500 mt-2">Token</p>
                  <div className="mt-4 pt-4 border-t border-indigo-200">
                    <p className="text-xs text-slate-600">下次重置日期</p>
                    <p className="text-lg font-semibold text-slate-900">{tokenData.resetDate}</p>
                  </div>
                </div>

                <div className="bg-slate-50 rounded-xl p-4 text-sm text-slate-700 space-y-2">
                  <p className="font-semibold">💡 计费说明：</p>
                  <ul className="space-y-1 text-xs">
                    <li>• 每月赠送 100万 Token</li>
                    <li>• 超出部分按 ¥10/100万Token 计费</li>
                    <li>• Token永久有效，不会过期</li>
                    <li>• 支持微信、支付宝支付</li>
                  </ul>
                </div>
              </div>

              {/* 右侧：充值选项 */}
              <div className="space-y-4">
                <p className="text-lg font-semibold text-slate-900">选择充值金额</p>
                <div className="grid grid-cols-2 gap-3">
                  {[10, 20, 50, 100].map((amount) => (
                    <motion.button
                      key={amount}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleRecharge(amount)}
                      className="py-4 px-6 bg-white border-2 border-slate-200 rounded-xl hover:border-indigo-500 hover:bg-indigo-50 transition-all text-center"
                    >
                      <div className="text-2xl font-bold text-slate-900">¥{amount}</div>
                      <div className="text-sm text-slate-500 mt-1">+{amount}万 Token</div>
                    </motion.button>
                  ))}
                </div>

                {/* 自定义金额 */}
                <div className="pt-2">
                  <input
                    type="number"
                    placeholder="输入自定义金额（元）"
                    className="w-full px-4 py-3 border-2 rounded-xl focus:outline-none focus:border-indigo-500 text-center"
                    onChange={(e) => setCustomAmount(e.target.value)}
                  />
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleRecharge(parseInt(customAmount) || 0)}
                    className="w-full mt-3 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl font-semibold text-lg hover:shadow-lg transition-all"
                  >
                    确认充值
                  </motion.button>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
