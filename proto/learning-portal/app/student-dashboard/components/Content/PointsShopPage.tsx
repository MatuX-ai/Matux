'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShoppingCart, Star, Trophy, Gift, X, Check, AlertCircle,
  Clock, Package, Sparkles,
} from 'lucide-react';
import { DeviceMode } from '../../types';

interface PointsShopPageProps {
  mode: DeviceMode;
}

// ============ 商品数据 ============
interface ShopItem {
  id: number;
  name: string;
  points: number;
  emoji: string;
  category: 'virtual' | 'physical' | 'coupon' | 'badge' | 'service';
  desc?: string;
  originalPrice: string;
  stockNum: number; // 数值化库存，便于扣减
}

const shopItems: ShopItem[] = [
  { id: 1, name: 'AI助手高级版（7天）', points: 200, emoji: '🤖', category: 'virtual', desc: '解锁无限次AI问答，优先响应', originalPrice: '¥20', stockNum: 999 },
  { id: 2, name: 'Arduino Starter Kit', points: 800, emoji: '🔧', category: 'physical', desc: '官方正品套件，含20+传感器', originalPrice: '¥199', stockNum: 3 },
  { id: 3, name: 'Python进阶课程券', points: 350, emoji: '🐍', category: 'coupon', desc: '抵扣任意Python课程费用', originalPrice: '¥99', stockNum: 999 },
  { id: 4, name: '限量版STEM徽章', points: 500, emoji: '🏅', category: 'badge', desc: '实体金属徽章，收藏价值', originalPrice: '限量发售', stockNum: 12 },
  { id: 5, name: '3D打印服务券', points: 450, emoji: '🖨️', category: 'service', desc: '免费打印任意模型（限50g）', originalPrice: '¥50', stockNum: 999 },
  { id: 6, name: '编程马拉松门票', points: 600, emoji: '🎫', category: 'virtual', desc: '线下黑客松活动入场券', originalPrice: '¥150', stockNum: 28 },
];

const categories = [
  { id: 'all', label: '全部', icon: '🛍️' },
  { id: 'virtual', label: '虚拟道具', icon: '💻' },
  { id: 'physical', label: '实物奖品', icon: '📦' },
  { id: 'coupon', label: '课程优惠', icon: '🎟️' },
  { id: 'badge', label: '勋章', icon: '🏅' },
  { id: 'service', label: '服务', icon: '🛎️' },
] as const;

// 兑换记录
interface ExchangeRecord {
  id: number;
  itemName: string;
  emoji: string;
  points: number;
  date: string;
  status: 'completed' | 'pending';
}

export function PointsShopPage({ mode }: PointsShopPageProps) {
  const isPhone = mode === 'phone';

  // ============ 状态 ============
  const [points, setPoints] = useState(850);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [exchangeHistory, setExchangeHistory] = useState<ExchangeRecord[]>([
    { id: 1, itemName: 'AI助手高级版（7天）', emoji: '🤖', points: 200, date: '2026-06-25 14:30', status: 'completed' },
    { id: 2, itemName: 'Python入门课程券', emoji: '🐍', points: 150, date: '2026-06-20 09:15', status: 'completed' },
  ]);
  const [confirmItem, setConfirmItem] = useState<ShopItem | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);
  const [exchanging, setExchanging] = useState(false);

  // 库存跟踪（可扣减）
  const [stockMap, setStockMap] = useState<Record<number, number>>(
    Object.fromEntries(shopItems.map(i => [i.id, i.stockNum]))
  );

  // ============ 筛选 ============
  const filteredItems = useMemo(() => {
    if (selectedCategory === 'all') return shopItems;
    return shopItems.filter(i => i.category === selectedCategory);
  }, [selectedCategory]);

  // ============ Toast ============
  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 2500);
  };

  // ============ 兑换逻辑 ============
  const handleExchange = (item: ShopItem) => {
    // 校验
    if (points < item.points) {
      showToast('error', `积分不足！还需 ${item.points - points} 积分`);
      return;
    }
    if (stockMap[item.id] <= 0) {
      showToast('error', '该商品已兑换完毕');
      return;
    }
    setConfirmItem(item);
  };

  const confirmExchange = () => {
    if (!confirmItem) return;
    setExchanging(true);

    // 模拟兑换请求
    setTimeout(() => {
      setPoints(prev => prev - confirmItem.points);
      setStockMap(prev => ({ ...prev, [confirmItem.id]: prev[confirmItem.id] - 1 }));
      setExchangeHistory(prev => [
        {
          id: Date.now(),
          itemName: confirmItem.name,
          emoji: confirmItem.emoji,
          points: confirmItem.points,
          date: new Date().toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }),
          status: 'completed',
        },
        ...prev,
      ]);
      setExchanging(false);
      setConfirmItem(null);
      showToast('success', `兑换成功！-${confirmItem.points} 积分`);
    }, 1200);
  };

  // ============ 库存显示文案 ============
  const stockLabel = (id: number) => {
    const s = stockMap[id];
    if (s <= 0) return '已兑完';
    if (s <= 5) return `仅剩 ${s} 件`;
    if (s <= 30) return `剩余 ${s} 件`;
    return '充足';
  };

  const stockColor = (id: number) => {
    const s = stockMap[id];
    if (s <= 0) return 'bg-slate-100 text-slate-400';
    if (s <= 5) return 'bg-red-100 text-red-600';
    if (s <= 30) return 'bg-yellow-100 text-yellow-600';
    return 'bg-green-100 text-green-600';
  };

  // ============ Toast 组件 ============
  const Toast = () => (
    <AnimatePresence>
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: -20, x: '-50%' }}
          animate={{ opacity: 1, y: 0, x: '-50%' }}
          exit={{ opacity: 0, y: -20, x: '-50%' }}
          className={`fixed top-6 left-1/2 z-[60] flex items-center gap-2 px-5 py-3 rounded-xl shadow-2xl text-sm font-medium ${
            toast.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
          }`}
        >
          {toast.type === 'success' ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
          {toast.msg}
        </motion.div>
      )}
    </AnimatePresence>
  );

  // ============ 兑换确认弹窗 ============
  const ConfirmModal = () => (
    <AnimatePresence>
      {confirmItem && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => !exchanging && setConfirmItem(null)}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-3xl w-full max-w-sm p-6 shadow-2xl"
          >
            <div className="text-center mb-5">
              <div className="w-20 h-20 bg-gradient-to-br from-slate-100 to-slate-200 rounded-2xl flex items-center justify-center text-4xl mx-auto mb-3">
                {confirmItem.emoji}
              </div>
              <h3 className="font-bold text-lg text-slate-900 mb-1">{confirmItem.name}</h3>
              <p className="text-sm text-slate-500">{confirmItem.desc}</p>
            </div>

            <div className="bg-slate-50 rounded-xl p-4 space-y-2 mb-5">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">兑换积分</span>
                <span className="font-bold text-orange-600">-{confirmItem.points}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">当前余额</span>
                <span className="font-medium text-slate-900">{points}</span>
              </div>
              <div className="border-t border-slate-200 pt-2 flex justify-between text-sm">
                <span className="text-slate-600">兑换后余额</span>
                <span className="font-bold text-slate-900">{points - confirmItem.points}</span>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setConfirmItem(null)}
                disabled={exchanging}
                className="flex-1 py-3 bg-slate-100 text-slate-600 rounded-xl font-semibold text-sm hover:bg-slate-200 transition-colors disabled:opacity-50"
              >
                取消
              </button>
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={confirmExchange}
                disabled={exchanging}
                className="flex-1 py-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-70"
              >
                {exchanging ? (
                  <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> 兑换中...</>
                ) : (
                  <><Check className="h-4 w-4" /> 确认兑换</>
                )}
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  // ============ 兑换记录弹窗 ============
  const HistoryModal = () => (
    <AnimatePresence>
      {showHistory && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setShowHistory(false)}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-3xl w-full max-w-md max-h-[70vh] overflow-hidden flex flex-col shadow-2xl"
          >
            <div className="flex items-center justify-between p-5 border-b">
              <h3 className="font-bold text-lg flex items-center gap-2">
                <ShoppingCart className="h-5 w-5 text-indigo-600" />
                兑换记录
              </h3>
              <button onClick={() => setShowHistory(false)} className="text-slate-400 hover:text-slate-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="overflow-y-auto p-5 space-y-3">
              {exchangeHistory.length === 0 ? (
                <div className="text-center text-slate-400 py-10">
                  <Package className="h-12 w-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">暂无兑换记录</p>
                </div>
              ) : (
                exchangeHistory.map((rec) => (
                  <div key={rec.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl">
                    <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center text-xl flex-shrink-0">
                      {rec.emoji}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-slate-900 truncate">{rec.itemName}</div>
                      <div className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                        <Clock className="h-3 w-3" /> {rec.date}
                      </div>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="text-sm font-bold text-orange-600">-{rec.points}</div>
                      <div className="text-[10px] text-green-600 flex items-center gap-0.5 justify-end">
                        <Check className="h-2.5 w-2.5" /> 已完成
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  // ============ 商品卡片（共用） ============
  const ItemCard = ({ item }: { item: ShopItem }) => {
    const canAfford = points >= item.points;
    const inStock = stockMap[item.id] > 0;
    const disabled = !canAfford || !inStock;

    // 手机模式：横向卡片（emoji + 信息 + 按钮）
    if (isPhone) {
      return (
        <motion.div
          whileTap={{ scale: 0.98 }}
          className={`bg-white rounded-xl border overflow-hidden transition-all ${disabled ? 'opacity-60' : ''}`}
        >
          <div className="flex items-center p-3">
            <div className="w-16 h-16 bg-gradient-to-br from-slate-100 to-slate-200 rounded-lg flex items-center justify-center text-3xl mr-3 flex-shrink-0">
              {item.emoji}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-bold text-xs mb-1 truncate">{item.name}</h4>
              <p className="text-[10px] text-slate-500 mb-2">原价 {item.originalPrice}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1">
                  <Star className="h-3 w-3 text-orange-500 fill-orange-500" />
                  <span className="text-sm font-bold text-orange-600">{item.points}</span>
                </div>
                <span className={`text-[9px] px-2 py-0.5 rounded-full ${stockColor(item.id)}`}>
                  {stockLabel(item.id)}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={() => handleExchange(item)}
            disabled={disabled}
            className={`w-full py-2 text-xs font-bold transition-all ${
              disabled
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-orange-500 to-orange-600 text-white'
            }`}
          >
            {!canAfford ? '积分不足' : !inStock ? '已兑完' : '立即兑换'}
          </button>
        </motion.div>
      );
    }

    // 平板模式：纵向卡片
    return (
      <motion.div
        whileHover={{ y: -4 }}
        className={`bg-white rounded-2xl overflow-hidden border border-slate-100 transition-all relative ${
          disabled ? 'opacity-60' : 'shadow-md hover:shadow-xl cursor-pointer'
        }`}
      >
        {item.points <= 200 && (
          <div className="absolute top-3 right-3 bg-red-500 text-white text-[10px] px-2 py-1 rounded-full font-bold z-10">
            HOT
          </div>
        )}
        <div className="h-40 bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center text-6xl">
          {item.emoji}
        </div>
        <div className="p-5">
          <h4 className="font-bold text-slate-900 mb-2">{item.name}</h4>
          <p className="text-sm text-slate-600 mb-3 line-clamp-2">{item.desc}</p>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Star className="h-5 w-5 text-orange-500 fill-orange-500" />
              <span className="text-xl font-bold text-orange-600">{item.points}</span>
            </div>
            <span className="text-xs text-slate-400 line-through">{item.originalPrice}</span>
          </div>
          <div className="flex items-center justify-between mb-3">
            <span className={`text-xs px-2 py-1 rounded-full ${stockColor(item.id)}`}>
              {stockLabel(item.id)}
            </span>
          </div>
          <button
            onClick={() => handleExchange(item)}
            disabled={disabled}
            className={`w-full py-2.5 rounded-xl font-bold text-sm transition-all ${
              disabled
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-orange-500 to-orange-600 text-white hover:shadow-lg'
            }`}
          >
            {!canAfford ? '积分不足' : !inStock ? '已兑完' : '立即兑换'}
          </button>
        </div>
      </motion.div>
    );
  };

  // ============ 手机模式 ============
  if (isPhone) {
    return (
      <div className="px-5 space-y-5">
        <Toast />
        <ConfirmModal />
        <HistoryModal />

        {/* 积分头部 */}
        <motion.div
          key={points}
          initial={{ scale: 0.95 }}
          animate={{ scale: 1 }}
          className="bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl p-5 text-white text-center"
        >
          <div className="text-4xl font-bold mb-1 flex items-center justify-center gap-2">
            {points}
            <Sparkles className="h-5 w-5 opacity-70" />
          </div>
          <div className="text-sm opacity-90 mb-3">当前积分</div>
          <div className="flex justify-center gap-4 text-xs">
            <span className="bg-white/20 px-3 py-1 rounded-full">本周 +120</span>
            <span className="bg-white/20 px-3 py-1 rounded-full">历史 2,450</span>
          </div>
        </motion.div>

        {/* 分类筛选 */}
        <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`text-[10px] px-3 py-1.5 rounded-full whitespace-nowrap flex items-center gap-1 transition-all ${
                selectedCategory === cat.id
                  ? 'bg-orange-500 text-white'
                  : 'bg-white border text-gray-600'
              }`}
            >
              <span>{cat.icon}</span> {cat.label}
            </button>
          ))}
        </div>

        {/* 商品列表 */}
        <h3 className="font-bold text-slate-900 text-base">
          {selectedCategory === 'all' ? '热门兑换' : categories.find(c => c.id === selectedCategory)?.label}
          <span className="text-xs text-slate-400 ml-2">({filteredItems.length})</span>
        </h3>
        <div className="space-y-3">
          {filteredItems.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>

        {/* 兑换记录入口 */}
        <motion.button
          whileTap={{ scale: 0.98 }}
          onClick={() => setShowHistory(true)}
          className="w-full bg-indigo-50 border border-indigo-100 rounded-xl p-4 flex items-center justify-between"
        >
          <div className="text-left">
            <h4 className="font-bold text-indigo-900 text-xs">兑换记录</h4>
            <p className="text-[10px] text-indigo-600 mt-1">{exchangeHistory.length} 笔历史订单</p>
          </div>
          <div className="flex items-center gap-2">
            <ShoppingCart className="h-5 w-5 text-indigo-600" />
            <span className="text-indigo-400">&gt;</span>
          </div>
        </motion.button>
      </div>
    );
  }

  // ============ 平板模式 ============
  return (
    <div className="space-y-6">
      <Toast />
      <ConfirmModal />
      <HistoryModal />

      {/* 积分概览 */}
      <motion.div
        key={points}
        initial={{ scale: 0.98 }}
        animate={{ scale: 1 }}
        className="bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl p-8 text-white"
      >
        <div className="flex items-start justify-between">
          <div>
            <p className="text-orange-100 text-sm mb-2">我的积分余额</p>
            <h2 className="text-5xl font-bold mb-4 flex items-center gap-3">
              {points}
              <Sparkles className="h-7 w-7 opacity-70" />
            </h2>
            <div className="flex gap-4 text-sm">
              <div className="bg-white/20 backdrop-blur px-4 py-2 rounded-lg">
                <div className="text-orange-100 text-xs mb-1">本周获得</div>
                <div className="font-bold">+120</div>
              </div>
              <div className="bg-white/20 backdrop-blur px-4 py-2 rounded-lg">
                <div className="text-orange-100 text-xs mb-1">累计获得</div>
                <div className="font-bold">2,450</div>
              </div>
              <div className="bg-white/20 backdrop-blur px-4 py-2 rounded-lg">
                <div className="text-orange-100 text-xs mb-1">已使用</div>
                <div className="font-bold">{2450 - points}</div>
              </div>
            </div>
          </div>
          <Trophy className="h-24 w-24 opacity-20" />
        </div>
      </motion.div>

      {/* 分类筛选 */}
      <div className="flex gap-3">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={`px-6 py-2.5 rounded-xl font-medium text-sm transition-all flex items-center gap-1.5 ${
              selectedCategory === cat.id
                ? 'bg-gradient-to-r from-orange-500 to-orange-600 text-white shadow-lg'
                : 'bg-white border text-slate-700 hover:border-orange-300'
            }`}
          >
            <span>{cat.icon}</span> {cat.label}
          </button>
        ))}
        <button
          onClick={() => setShowHistory(true)}
          className="ml-auto px-5 py-2.5 rounded-xl font-medium text-sm bg-indigo-50 text-indigo-600 border border-indigo-100 hover:bg-indigo-100 transition-all flex items-center gap-1.5"
        >
          <ShoppingCart className="h-4 w-4" /> 兑换记录 ({exchangeHistory.length})
        </button>
      </div>

      {/* 商品网格 */}
      <div>
        <h3 className="text-xl font-bold text-slate-900 mb-4">
          {selectedCategory === 'all' ? '精选好物' : categories.find(c => c.id === selectedCategory)?.label}
          <span className="text-sm text-slate-400 ml-2">({filteredItems.length} 件商品)</span>
        </h3>
        <div className="grid grid-cols-3 gap-5">
          {filteredItems.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      </div>

      {/* 积分规则 */}
      <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6">
        <h4 className="font-bold text-blue-900 mb-3 flex items-center gap-2">
          <Gift className="h-5 w-5" /> 积分获取规则
        </h4>
        <div className="grid grid-cols-4 gap-4 text-sm text-blue-800">
          <div className="flex items-start gap-2">
            <span className="text-lg">✓</span>
            <div>
              <div className="font-semibold">完成课程</div>
              <div className="text-xs opacity-80">+50~100分/课</div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-lg">✓</span>
            <div>
              <div className="font-semibold">连胜奖励</div>
              <div className="text-xs opacity-80">+20~100分</div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-lg">✓</span>
            <div>
              <div className="font-semibold">作品分享</div>
              <div className="text-xs opacity-80">+30分/次</div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-lg">✓</span>
            <div>
              <div className="font-semibold">每日挑战</div>
              <div className="text-xs opacity-80">+50分/次</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
