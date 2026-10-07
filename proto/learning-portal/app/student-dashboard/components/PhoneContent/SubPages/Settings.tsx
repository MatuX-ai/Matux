'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell, Shield, Moon, Globe, LogOut, ChevronRight, ChevronDown,
  Volume2, RefreshCw, Smartphone, Wifi, User, AlertTriangle, Check,
  FileText, HelpCircle, Star,
} from 'lucide-react';

interface SettingsProps {
  onNavigate?: (page: string) => void;
}

// ============ 可复用开关组件 ============
interface ToggleProps {
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}

function Toggle({ checked, onChange, disabled }: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => !disabled && onChange(!checked)}
      className={`relative w-11 h-6 rounded-full transition-colors duration-200 flex-shrink-0 ${
        disabled
          ? 'bg-slate-100 cursor-not-allowed'
          : checked
            ? 'bg-blue-500'
            : 'bg-slate-200'
      }`}
    >
      <motion.div
        layout
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow-md ${
          checked ? 'left-[22px]' : 'left-0.5'
        }`}
      />
    </button>
  );
}

// ============ 设置项行组件 ============
interface SettingRowProps {
  icon: React.ElementType;
  iconColor: string;
  label: string;
  desc?: string;
  right?: React.ReactNode;
  onClick?: () => void;
  toggle?: { checked: boolean; onChange: (v: boolean) => void };
  danger?: boolean;
}

function SettingRow({ icon: Icon, iconColor, label, desc, right, onClick, toggle, danger }: SettingRowProps) {
  const clickable = !!onClick;
  return (
    <motion.div
      whileTap={clickable ? { scale: 0.98 } : undefined}
      onClick={onClick}
      className={`p-4 border-b last:border-0 flex items-center justify-between ${
        clickable ? 'cursor-pointer hover:bg-slate-50' : ''
      }`}
    >
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${danger ? 'bg-red-50' : 'bg-slate-50'}`}>
          <Icon className={`h-4 w-4 ${danger ? 'text-red-500' : iconColor}`} />
        </div>
        <div className="min-w-0 flex-1">
          <div className={`text-sm font-medium ${danger ? 'text-red-600' : 'text-slate-800'}`}>{label}</div>
          {desc && <div className="text-[11px] text-slate-400 mt-0.5 truncate">{desc}</div>}
        </div>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {right}
        {toggle && <Toggle checked={toggle.checked} onChange={toggle.onChange} />}
        {clickable && !toggle && <ChevronRight className="h-4 w-4 text-slate-300" />}
      </div>
    </motion.div>
  );
}

// ============ 卡片容器 ============
function SettingCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border overflow-hidden">
      <div className="px-4 py-2.5 border-b bg-slate-50">
        <h3 className="font-bold text-xs text-slate-500 uppercase tracking-wide">{title}</h3>
      </div>
      {children}
    </div>
  );
}

export default function Settings(_: SettingsProps) {
  // 开关状态
  const [darkMode, setDarkMode] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [autoSync, setAutoSync] = useState(true);
  const [soundEffects, setSoundEffects] = useState(true);
  const [dataSaver, setDataSaver] = useState(false);

  // 语言选择
  const [language, setLanguage] = useState<'zh' | 'en'>('zh');
  const [showLangMenu, setShowLangMenu] = useState(false);

  // 弹窗状态
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [showClearCacheConfirm, setShowClearCacheConfirm] = useState(false);
  const [clearing, setClearing] = useState(false);

  // Toast
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'info' } | null>(null);
  const showToast = (msg: string, type: 'success' | 'info' = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 2200);
  };

  // 模拟缓存大小
  const [cacheSize, setCacheSize] = useState('128.5 MB');

  // 清除缓存
  const handleClearCache = () => {
    setClearing(true);
    setTimeout(() => {
      setClearing(false);
      setShowClearCacheConfirm(false);
      setCacheSize('0 KB');
      showToast('已清除 128.5 MB 缓存');
    }, 1500);
  };

  // 退出登录
  const handleLogout = () => {
    setShowLogoutConfirm(false);
    showToast('已退出登录（演示）', 'info');
  };

  // 切换语言
  const switchLanguage = (lang: 'zh' | 'en') => {
    setLanguage(lang);
    setShowLangMenu(false);
    showToast(lang === 'zh' ? '已切换为简体中文' : 'Switched to English');
  };

  return (
    <div className="space-y-5 pb-8">
      <h2 className="text-xl font-bold text-slate-900">系统设置</h2>

      {/* ============ 账号卡片 ============ */}
      <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl p-4 text-white relative overflow-hidden">
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-14 h-14 bg-white/20 backdrop-blur rounded-full flex items-center justify-center text-2xl font-bold border-2 border-white/40">
            李
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-bold">李明</span>
              <span className="text-[10px] bg-white/20 px-1.5 py-0.5 rounded-full">G5</span>
            </div>
            <div className="text-xs opacity-80 mt-0.5">liming@matux.edu</div>
            <div className="text-[10px] opacity-70 mt-0.5">账号 ID: MX20260115</div>
          </div>
          <ChevronRight className="h-5 w-5 opacity-70" />
        </div>
        <User className="absolute -bottom-6 -right-6 h-32 w-32 opacity-10" />
      </div>

      {/* ============ 通用设置 ============ */}
      <SettingCard title="通用">
        {/* 语言选择 */}
        <div className="relative">
          <SettingRow
            icon={Globe}
            iconColor="text-blue-500"
            label="语言设置"
            desc={language === 'zh' ? '简体中文' : 'English'}
            onClick={() => setShowLangMenu(!showLangMenu)}
            right={
              <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform ${showLangMenu ? 'rotate-180' : ''}`} />
            }
          />
          <AnimatePresence>
            {showLangMenu && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden bg-slate-50"
              >
                {[
                  { key: 'zh' as const, label: '简体中文', flag: '🇨🇳' },
                  { key: 'en' as const, label: 'English', flag: '🇺🇸' },
                ].map((opt) => (
                  <motion.button
                    key={opt.key}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => switchLanguage(opt.key)}
                    className={`w-full px-4 py-2.5 flex items-center justify-between text-sm border-b last:border-0 ${
                      language === opt.key ? 'text-blue-600 font-bold' : 'text-slate-600'
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <span>{opt.flag}</span> {opt.label}
                    </span>
                    {language === opt.key && <Check className="h-4 w-4" />}
                  </motion.button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <SettingRow
          icon={Bell}
          iconColor="text-amber-500"
          label="消息通知"
          desc={notifications ? '接收课程提醒、签到通知' : '已关闭所有通知'}
          toggle={{ checked: notifications, onChange: (v) => { setNotifications(v); showToast(v ? '已开启通知' : '已关闭通知', 'info'); } }}
        />

        <SettingRow
          icon={Volume2}
          iconColor="text-purple-500"
          label="音效"
          desc="按钮点击、任务完成提示音"
          toggle={{ checked: soundEffects, onChange: setSoundEffects }}
        />
      </SettingCard>

      {/* ============ 外观与显示 ============ */}
      <SettingCard title="外观与显示">
        <SettingRow
          icon={Moon}
          iconColor="text-indigo-500"
          label="深色模式"
          desc={darkMode ? '已开启（演示，不实际切换）' : '护眼夜间模式'}
          toggle={{ checked: darkMode, onChange: (v) => { setDarkMode(v); showToast(v ? '已开启深色模式（演示）' : '已关闭深色模式', 'info'); } }}
        />
      </SettingCard>

      {/* ============ 学习与同步 ============ */}
      <SettingCard title="学习与同步">
        <SettingRow
          icon={Wifi}
          iconColor="text-green-500"
          label="自动同步"
          desc={autoSync ? '学习进度实时云端同步' : '仅 Wi-Fi 下同步'}
          toggle={{ checked: autoSync, onChange: (v) => { setAutoSync(v); showToast(v ? '已开启自动同步' : '已关闭自动同步', 'info'); } }}
        />
        <SettingRow
          icon={Smartphone}
          iconColor="text-cyan-500"
          label="省流量模式"
          desc="减少图片加载，节省移动数据"
          toggle={{ checked: dataSaver, onChange: setDataSaver }}
        />
        <SettingRow
          icon={Shield}
          iconColor="text-blue-500"
          label="隐私权限"
          desc="摄像头、麦克风、位置"
          onClick={() => showToast('请在浏览器设置中管理权限', 'info')}
        />
      </SettingCard>

      {/* ============ 存储管理 ============ */}
      <SettingCard title="存储管理">
        <SettingRow
          icon={RefreshCw}
          iconColor="text-teal-500"
          label="清除缓存"
          desc={`当前占用 ${cacheSize}`}
          onClick={() => setShowClearCacheConfirm(true)}
        />
      </SettingCard>

      {/* ============ 关于 ============ */}
      <SettingCard title="关于">
        <SettingRow
          icon={FileText}
          iconColor="text-slate-500"
          label="用户协议"
          onClick={() => showToast('暂未提供', 'info')}
        />
        <SettingRow
          icon={Shield}
          iconColor="text-slate-500"
          label="隐私政策"
          onClick={() => showToast('暂未提供', 'info')}
        />
        <SettingRow
          icon={HelpCircle}
          iconColor="text-slate-500"
          label="帮助与反馈"
          onClick={() => showToast('感谢你的反馈！', 'info')}
        />
        <SettingRow
          icon={Star}
          iconColor="text-amber-500"
          label="给我们评分"
          onClick={() => showToast('感谢支持 ❤️', 'info')}
        />
        <div className="p-4 text-center">
          <div className="text-xs text-slate-400">MatuX Education Platform</div>
          <div className="text-[10px] text-slate-300 mt-0.5">Version 2.1.0 (Build 20260629)</div>
        </div>
      </SettingCard>

      {/* ============ 退出登录按钮 ============ */}
      <motion.button
        whileTap={{ scale: 0.98 }}
        onClick={() => setShowLogoutConfirm(true)}
        className="w-full bg-red-50 text-red-600 py-3.5 rounded-xl font-bold text-sm flex items-center justify-center gap-2 border border-red-100 hover:bg-red-100 transition-colors"
      >
        <LogOut className="h-4 w-4" /> 退出登录
      </motion.button>

      {/* ============ 退出登录确认弹窗 ============ */}
      <AnimatePresence>
        {showLogoutConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowLogoutConfirm(false)}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6"
          >
            <motion.div
              initial={{ scale: 0.8, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl w-full max-w-xs p-5 text-center shadow-2xl"
            >
              <div className="w-14 h-14 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-3">
                <AlertTriangle className="h-7 w-7 text-red-500" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-1">确认退出登录？</h3>
              <p className="text-xs text-slate-500 mb-4">
                退出后需要重新登录才能继续学习。你的学习进度已自动同步到云端，不会丢失。
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowLogoutConfirm(false)}
                  className="flex-1 py-2.5 bg-slate-100 text-slate-600 rounded-xl font-semibold text-sm"
                >
                  取消
                </button>
                <button
                  onClick={handleLogout}
                  className="flex-1 py-2.5 bg-red-500 text-white rounded-xl font-semibold text-sm hover:bg-red-600 transition-colors"
                >
                  确认退出
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ============ 清除缓存确认弹窗 ============ */}
      <AnimatePresence>
        {showClearCacheConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => !clearing && setShowClearCacheConfirm(false)}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6"
          >
            <motion.div
              initial={{ scale: 0.8, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl w-full max-w-xs p-5 text-center shadow-2xl"
            >
              <div className="w-14 h-14 bg-teal-50 rounded-full flex items-center justify-center mx-auto mb-3">
                {clearing ? (
                  <RefreshCw className="h-7 w-7 text-teal-500 animate-spin" />
                ) : (
                  <RefreshCw className="h-7 w-7 text-teal-500" />
                )}
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-1">
                {clearing ? '正在清除...' : '清除缓存？'}
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                {clearing
                  ? '请稍候，正在清理临时文件'
                  : `将释放 ${cacheSize} 存储空间。学习记录和账号信息不会被清除。`}
              </p>
              {!clearing && (
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowClearCacheConfirm(false)}
                    className="flex-1 py-2.5 bg-slate-100 text-slate-600 rounded-xl font-semibold text-sm"
                  >
                    取消
                  </button>
                  <button
                    onClick={handleClearCache}
                    className="flex-1 py-2.5 bg-teal-500 text-white rounded-xl font-semibold text-sm hover:bg-teal-600 transition-colors"
                  >
                    确认清除
                  </button>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ============ Toast 提示 ============ */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 30, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 30, x: '-50%' }}
            className={`fixed bottom-24 left-1/2 z-50 px-4 py-2 rounded-full text-xs font-medium shadow-lg flex items-center gap-1.5 ${
              toast.type === 'success'
                ? 'bg-green-500 text-white'
                : 'bg-slate-800 text-white'
            }`}
          >
            {toast.type === 'success' && <Check className="h-3.5 w-3.5" />}
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
