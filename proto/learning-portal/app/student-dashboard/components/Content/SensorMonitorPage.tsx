'use client';

import { motion } from 'framer-motion';
import {
  Activity, Thermometer, Droplets, Zap, Mic, Volume2, TrendingUp,
  Pause, Play, BarChart3, AlertTriangle, Download,
} from 'lucide-react';
import { DeviceMode } from '../../types';
import { useState, useEffect, useMemo } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts';

interface SensorMonitorPageProps {
  mode: DeviceMode;
}

// 单次传感器读数
interface SensorReading {
  time: string;
  temperature: number;
  humidity: number;
  light: number;
  sound: number;
}

// 传感器配置（颜色/单位/量程/阈值/轴归属）
interface SensorConfig {
  key: keyof Omit<SensorReading, 'time'>;
  label: string;
  unit: string;
  color: string;
  yAxis: 'left' | 'right';
  thresholdMin: number;
  thresholdMax: number;
  icon: typeof Thermometer;
}

const sensorConfigs: SensorConfig[] = [
  { key: 'temperature', label: '温度', unit: '°C', color: '#f97316', yAxis: 'left', thresholdMin: 10, thresholdMax: 40, icon: Thermometer },
  { key: 'humidity', label: '湿度', unit: '%', color: '#3b82f6', yAxis: 'left', thresholdMin: 30, thresholdMax: 80, icon: Droplets },
  { key: 'sound', label: '声音', unit: 'dB', color: '#a855f7', yAxis: 'left', thresholdMin: 0, thresholdMax: 80, icon: Volume2 },
  { key: 'light', label: '光照', unit: 'lux', color: '#eab308', yAxis: 'right', thresholdMin: 100, thresholdMax: 800, icon: Zap },
];

// 预填历史数据（24 个点，每 2s 一个 = 48s 历史）
const generateInitialHistory = (count: number): SensorReading[] =>
  Array.from({ length: count }, (_, i) => {
    const t = i * 2;
    return {
      time: `${String(Math.floor(t / 60)).padStart(2, '0')}:${String(t % 60).padStart(2, '0')}`,
      temperature: +(25 + Math.sin(i / 2) * 1.5).toFixed(1),
      humidity: Math.round(62 + Math.cos(i / 3) * 4),
      light: Math.round(450 + Math.sin(i / 1.5) * 30),
      sound: Math.round(35 + Math.cos(i / 2) * 6),
    };
  });

export function SensorMonitorPage({ mode }: SensorMonitorPageProps) {
  const isPhone = mode === 'phone';
  const [sensorData, setSensorData] = useState({
    temperature: 25.3,
    humidity: 62,
    light: 450,
    sound: 35
  });
  const [history, setHistory] = useState<SensorReading[]>(generateInitialHistory(24));
  const [voiceCommand, setVoiceCommand] = useState('');
  const [isListening, setIsListening] = useState(false);

  // 趋势图增强状态
  const [visibleSensors, setVisibleSensors] = useState<Set<string>>(
    new Set(['temperature', 'humidity', 'light', 'sound'])
  );
  const [isPaused, setIsPaused] = useState(false);
  const [maxSamples, setMaxSamples] = useState(20);

  // 模拟传感器数据更新 + 追加历史
  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(() => {
      setSensorData(prev => {
        const next = {
          temperature: +(prev.temperature + (Math.random() - 0.5)).toFixed(1),
          humidity: Math.round(prev.humidity + (Math.random() - 0.5) * 3),
          light: Math.round(prev.light + (Math.random() - 0.5) * 20),
          sound: Math.round(prev.sound + (Math.random() - 0.5) * 10)
        };
        const now = new Date();
        const reading: SensorReading = {
          time: `${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`,
          ...next,
        };
        setHistory(h => [...h.slice(-(maxSamples - 1)), reading]);
        return next;
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [isPaused, maxSamples]);

  // 统计计算（当前可见传感器的 min/max/avg）
  const stats = useMemo(() => {
    const result: Record<string, { min: number; max: number; avg: number; current: number }> = {};
    for (const cfg of sensorConfigs) {
      const values = history.map(h => h[cfg.key]);
      result[cfg.key] = {
        min: Math.min(...values),
        max: Math.max(...values),
        avg: +(values.reduce((a, b) => a + b, 0) / values.length).toFixed(1),
        current: values[values.length - 1],
      };
    }
    return result;
  }, [history]);

  // 异常检测（超出阈值）
  const alerts = useMemo(() => {
    return sensorConfigs
      .filter(cfg => {
        const v = stats[cfg.key].current;
        return v < cfg.thresholdMin || v > cfg.thresholdMax;
      })
      .map(cfg => ({
        label: cfg.label,
        value: stats[cfg.key].current,
        unit: cfg.unit,
        type: stats[cfg.key].current > cfg.thresholdMax ? 'high' : 'low',
      }));
  }, [stats]);

  const toggleSensor = (key: string) => {
    setVisibleSensors(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleVoiceCommand = (command: string) => {
    setVoiceCommand(command);
    setTimeout(() => setVoiceCommand(''), 3000);
  };

  const handleExport = () => {
    // 原型：模拟导出 CSV
    const headers = 'time,temperature,humidity,light,sound\n';
    const rows = history.map(h =>
      `${h.time},${h.temperature},${h.humidity},${h.light},${h.sound}`
    ).join('\n');
    console.log('导出 CSV:', headers + rows);
    alert(`已导出 ${history.length} 条采样数据（CSV 格式）`);
  };

  // ============ 趋势图卡片（手机+平板共用） ============
  const TrendChart = ({ height }: { height: number }) => {
    const visibleConfigs = sensorConfigs.filter(c => visibleSensors.has(c.key));
    const showLeftAxis = visibleConfigs.some(c => c.yAxis === 'left');
    const showRightAxis = visibleConfigs.some(c => c.yAxis === 'right');

    return (
      <LineChart data={history} margin={{ top: 10, right: showRightAxis ? 10 : 5, bottom: 5, left: showLeftAxis ? -15 : 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="time" tick={{ fontSize: isPhone ? 9 : 11 }} interval="preserveStartEnd" />
        {showLeftAxis && (
          <YAxis yAxisId="left" tick={{ fontSize: isPhone ? 9 : 11 }} domain={[0, 100]} />
        )}
        {showRightAxis && (
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: isPhone ? 9 : 11 }} domain={[0, 1000]} />
        )}
        <Tooltip
          contentStyle={{
            fontSize: isPhone ? 11 : 12,
            borderRadius: 10,
            border: '1px solid #e2e8f0',
          }}
        />
        <Legend wrapperStyle={{ fontSize: isPhone ? 9 : 12 }} />
        {/* 阈值参考线（仅可见传感器） */}
        {visibleConfigs.map(cfg => (
          <ReferenceLine
            key={`max-${cfg.key}`}
            yAxisId={cfg.yAxis}
            y={cfg.thresholdMax}
            stroke={cfg.color}
            strokeDasharray="5 3"
            strokeOpacity={0.4}
          />
        ))}
        {visibleConfigs.map(cfg => (
          <Line
            key={cfg.key}
            yAxisId={cfg.yAxis}
            type="monotone"
            dataKey={cfg.key}
            stroke={cfg.color}
            strokeWidth={isPhone ? 2 : 2.5}
            dot={false}
            activeDot={{ r: isPhone ? 4 : 5 }}
            name={`${cfg.label} (${cfg.unit})`}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    );
  };

  // ============ 传感器切换按钮 ============
  const SensorToggles = () => (
    <div className="flex flex-wrap gap-2">
      {sensorConfigs.map(cfg => {
        const active = visibleSensors.has(cfg.key);
        const Icon = cfg.icon;
        return (
          <motion.button
            key={cfg.key}
            whileTap={{ scale: 0.95 }}
            onClick={() => toggleSensor(cfg.key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border-2 transition-all ${
              active
                ? 'border-transparent text-white'
                : 'border-slate-200 text-slate-400 bg-white hover:border-slate-300'
            }`}
            style={active ? { backgroundColor: cfg.color } : {}}
          >
            <Icon className="h-3.5 w-3.5" />
            {cfg.label}
          </motion.button>
        );
      })}
    </div>
  );

  // ============ 统计卡片 ============
  const StatsCards = () => (
    <div className={`grid ${isPhone ? 'grid-cols-2' : 'grid-cols-4'} gap-3`}>
      {sensorConfigs.filter(c => visibleSensors.has(c.key)).map(cfg => {
        const s = stats[cfg.key];
        const isAlert = s.current < cfg.thresholdMin || s.current > cfg.thresholdMax;
        const Icon = cfg.icon;
        return (
          <motion.div
            key={cfg.key}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl border p-3"
            style={{ borderColor: isAlert ? '#fca5a5' : '#e2e8f0' }}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Icon className="h-3.5 w-3.5" style={{ color: cfg.color }} />
                <span className="text-xs font-semibold text-slate-700">{cfg.label}</span>
              </div>
              {isAlert && <AlertTriangle className="h-3.5 w-3.5 text-red-500" />}
            </div>
            <div className="text-xl font-bold" style={{ color: cfg.color }}>
              {s.current}<span className="text-xs ml-0.5">{cfg.unit}</span>
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 mt-1">
              <span>min {s.min}</span>
              <span>avg {s.avg}</span>
              <span>max {s.max}</span>
            </div>
          </motion.div>
        );
      })}
    </div>
  );

  // ============ 手机模式 ============
  if (isPhone) {
    return (
      <div className="px-5 space-y-5">
        {/* Real-time Status */}
        <div className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-5 text-white">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-lg">实时数据监控</h3>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isPaused ? 'bg-yellow-300' : 'bg-white animate-pulse'}`}></div>
              <span className="text-xs">{isPaused ? '已暂停' : '在线'}</span>
            </div>
          </div>
          <p className="text-sm text-green-100">ESP32-DevKit · 最后更新: 刚刚</p>
        </div>

        {/* Sensor Cards */}
        <div className="grid grid-cols-2 gap-3">
          {[
            { name: '温度', value: `${sensorData.temperature}°C`, icon: Thermometer, color: 'from-orange-500 to-red-500' },
            { name: '湿度', value: `${sensorData.humidity}%`, icon: Droplets, color: 'from-blue-500 to-cyan-500' },
            { name: '光照', value: `${sensorData.light} lux`, icon: Zap, color: 'from-yellow-500 to-orange-500' },
            { name: '声音', value: `${sensorData.sound} dB`, icon: Volume2, color: 'from-purple-500 to-pink-500' }
          ].map((sensor, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -2 }}
              className={`bg-gradient-to-br ${sensor.color} rounded-xl p-4 text-white`}
            >
              <sensor.icon className="h-6 w-6 mb-2 opacity-80" />
              <div className="text-2xl font-bold mb-1">{sensor.value}</div>
              <div className="text-xs opacity-90">{sensor.name}</div>
            </motion.div>
          ))}
        </div>

        {/* 告警提示 */}
        {alerts.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 border border-red-200 rounded-xl p-3"
          >
            <div className="flex items-center gap-2 text-red-700 mb-1">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-xs font-bold">传感器告警 ({alerts.length})</span>
            </div>
            {alerts.map((a, i) => (
              <p key={i} className="text-[11px] text-red-600">
                {a.label} {a.type === 'high' ? '超出' : '低于'}安全范围：当前 {a.value}{a.unit}
              </p>
            ))}
          </motion.div>
        )}

        {/* 增强趋势图 */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <span className="w-1 h-5 bg-gradient-to-b from-blue-600 to-purple-600 rounded-full"></span>
              趋势图
              <TrendingUp className="h-4 w-4 text-slate-400" />
            </h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsPaused(!isPaused)}
                className={`p-1.5 rounded-lg ${isPaused ? 'bg-green-100 text-green-600' : 'bg-slate-100 text-slate-500'}`}
              >
                {isPaused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
              </button>
              <button onClick={handleExport} className="p-1.5 rounded-lg bg-slate-100 text-slate-500">
                <Download className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {/* 传感器切换 */}
          <div className="mb-3"><SensorToggles /></div>

          {/* 统计卡片 */}
          <div className="mb-3"><StatsCards /></div>

          {/* 时间范围选择 */}
          <div className="flex gap-1.5 mb-3">
            {[20, 40, 60].map(n => (
              <button
                key={n}
                onClick={() => setMaxSamples(n)}
                className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-all ${
                  maxSamples === n ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500'
                }`}
              >
                {n} 采样
              </button>
            ))}
          </div>

          {/* 图表 */}
          <div className="bg-white rounded-2xl border p-3">
            <ResponsiveContainer width="100%" height={180}>
              <TrendChart height={180} />
            </ResponsiveContainer>
            <p className="text-[10px] text-slate-400 mt-1 text-center">
              虚线 = 安全阈值上限 · {isPaused ? '已暂停' : '每 2s 更新'}
            </p>
          </div>
        </div>

        {/* Voice Command Section */}
        <div>
          <h3 className="font-bold text-slate-900 text-base mb-3">TinyML 语音指令</h3>

          {voiceCommand && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-green-50 border border-green-200 rounded-xl p-4 mb-3"
            >
              <div className="flex items-center gap-2 text-green-700">
                <Mic className="h-5 w-5" />
                <span className="text-sm font-medium">识别到: "{voiceCommand}"</span>
              </div>
            </motion.div>
          )}

          <div className="space-y-2">
            {[
              { command: '开灯', action: 'LED ON', emoji: '💡' },
              { command: '关灯', action: 'LED OFF', emoji: '🌑' },
              { command: '读取温度', action: 'READ TEMP', emoji: '🌡️' },
              { command: '启动风扇', action: 'FAN ON', emoji: '🌀' }
            ].map((item, i) => (
              <motion.button
                key={i}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleVoiceCommand(item.command)}
                className="w-full bg-white border rounded-xl p-3 flex items-center justify-between hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{item.emoji}</span>
                  <div className="text-left">
                    <div className="text-sm font-bold">{item.command}</div>
                    <div className="text-[10px] text-slate-500">{item.action}</div>
                  </div>
                </div>
                <Mic className="h-5 w-5 text-slate-400" />
              </motion.button>
            ))}
          </div>

          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => setIsListening(!isListening)}
            className={`w-full mt-3 py-3 rounded-xl font-bold flex items-center justify-center gap-2 ${
              isListening
                ? 'bg-red-500 text-white animate-pulse'
                : 'bg-blue-600 text-white'
            }`}
          >
            <Mic className="h-5 w-5" />
            {isListening ? '正在聆听...' : '开始语音识别'}
          </motion.button>
        </div>

        {/* Quick Actions */}
        <div>
          <h3 className="font-bold text-slate-900 text-base mb-3">快捷控制</h3>
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: 'LED', icon: '💡', active: true },
              { label: '蜂鸣器', icon: '🔊', active: false },
              { label: '电机', icon: '⚙️', active: false }
            ].map((action, i) => (
              <motion.button
                key={i}
                whileTap={{ scale: 0.95 }}
                className={`rounded-xl p-3 text-center border ${
                  action.active
                    ? 'bg-green-50 border-green-300'
                    : 'bg-white border-slate-200'
                }`}
              >
                <div className="text-2xl mb-1">{action.icon}</div>
                <div className={`text-xs font-medium ${action.active ? 'text-green-700' : 'text-slate-700'}`}>
                  {action.label}
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ============ 平板模式 ============
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-slate-900">传感器监控 📊</h2>
        <div className="flex items-center gap-3 bg-green-50 border border-green-200 px-4 py-2 rounded-xl">
          <div className={`w-3 h-3 rounded-full ${isPaused ? 'bg-yellow-500' : 'bg-green-500 animate-pulse'}`}></div>
          <span className="text-sm font-medium text-green-700">{isPaused ? '已暂停' : '设备在线'}</span>
          <span className="text-xs text-green-600">ESP32-DevKit</span>
        </div>
      </div>

      {/* 告警提示 */}
      {alerts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-start gap-3"
        >
          <AlertTriangle className="h-6 w-6 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-bold text-red-700 text-sm mb-1">传感器告警 ({alerts.length})</p>
            <div className="space-y-0.5">
              {alerts.map((a, i) => (
                <p key={i} className="text-xs text-red-600">
                  {a.label} {a.type === 'high' ? '超出' : '低于'}安全范围：当前 {a.value}{a.unit}
                </p>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Sensor Dashboard */}
      <div className="grid grid-cols-4 gap-5">
        {[
          { name: '温度', value: sensorData.temperature, unit: '°C', icon: Thermometer, color: 'from-orange-500 to-red-500', range: '0-50°C' },
          { name: '湿度', value: sensorData.humidity, unit: '%', icon: Droplets, color: 'from-blue-500 to-cyan-500', range: '0-100%' },
          { name: '光照强度', value: sensorData.light, unit: 'lux', icon: Zap, color: 'from-yellow-500 to-orange-500', range: '0-1000 lux' },
          { name: '声音强度', value: sensorData.sound, unit: 'dB', icon: Volume2, color: 'from-purple-500 to-pink-500', range: '0-100 dB' }
        ].map((sensor, i) => (
          <motion.div
            key={i}
            whileHover={{ y: -4 }}
            className={`bg-gradient-to-br ${sensor.color} rounded-2xl p-6 text-white relative overflow-hidden`}
          >
            <sensor.icon className="h-12 w-12 mb-4 opacity-80" />
            <div className="text-4xl font-bold mb-2">
              {sensor.value}<span className="text-xl ml-1">{sensor.unit}</span>
            </div>
            <div className="text-sm opacity-90 mb-1">{sensor.name}</div>
            <div className="text-xs opacity-75">量程: {sensor.range}</div>
            <Activity className="absolute bottom-4 right-4 h-16 w-16 opacity-10" />
          </motion.div>
        ))}
      </div>

      {/* 增强趋势图 */}
      <div className="bg-white rounded-2xl border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-indigo-600" />
            传感器趋势图
          </h3>
          <div className="flex items-center gap-3">
            {/* 时间范围选择 */}
            <div className="flex gap-1.5">
              {[20, 40, 60].map(n => (
                <button
                  key={n}
                  onClick={() => setMaxSamples(n)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    maxSamples === n ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
            {/* 暂停/继续 */}
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                isPaused ? 'bg-green-100 text-green-600 hover:bg-green-200' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
              }`}
            >
              {isPaused ? <><Play className="h-3.5 w-3.5" /> 继续</> : <><Pause className="h-3.5 w-3.5" /> 暂停</>}
            </button>
            {/* 导出 */}
            <button
              onClick={handleExport}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-500 hover:bg-slate-200 transition-all"
            >
              <Download className="h-3.5 w-3.5" /> 导出
            </button>
          </div>
        </div>

        {/* 传感器切换 + 统计 */}
        <div className="flex items-center justify-between mb-4">
          <SensorToggles />
          <span className="text-xs text-slate-400 flex items-center gap-1">
            <BarChart3 className="h-3 w-3" />
            {isPaused ? '已暂停' : '每 2s 更新'} · 近 {maxSamples} 次
          </span>
        </div>

        {/* 统计卡片 */}
        <div className="mb-4"><StatsCards /></div>

        {/* 图表 */}
        <ResponsiveContainer width="100%" height={320}>
          <TrendChart height={320} />
        </ResponsiveContainer>

        <p className="text-xs text-slate-400 mt-2 text-center">
          左轴：温度(°C) / 湿度(%) / 声音(dB) · 右轴：光照(lux) · 虚线 = 安全阈值上限
        </p>
      </div>

      {/* Voice Control Panel */}
      <div className="bg-white rounded-2xl border p-6">
        <h3 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Mic className="h-6 w-6 text-blue-600" />
          TinyML 语音控制中心
        </h3>

        {voiceCommand && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-green-50 border border-green-200 rounded-xl p-4 mb-4"
          >
            <div className="flex items-center gap-3 text-green-700">
              <Mic className="h-6 w-6" />
              <div>
                <div className="font-bold">识别成功</div>
                <div className="text-sm">指令: "{voiceCommand}" · 置信度: 95%</div>
              </div>
            </div>
          </motion.div>
        )}

        <div className="grid grid-cols-4 gap-4">
          {[
            { command: '开灯', action: 'LED ON', desc: '点亮板载 LED', emoji: '💡' },
            { command: '关灯', action: 'LED OFF', desc: '关闭板载 LED', emoji: '🌑' },
            { command: '读取温度', action: 'READ TEMP', desc: '获取当前温度', emoji: '🌡️' },
            { command: '启动风扇', action: 'FAN ON', desc: '开启直流电机', emoji: '🌀' },
            { command: '停止风扇', action: 'FAN OFF', desc: '关闭直流电机', emoji: '⏹️' },
            { command: '蜂鸣器响', action: 'BEEP ON', desc: '激活蜂鸣器', emoji: '🔊' },
            { command: '读取湿度', action: 'READ HUM', desc: '获取当前湿度', emoji: '💧' },
            { command: '系统状态', action: 'STATUS', desc: '查询设备状态', emoji: 'ℹ️' }
          ].map((item, i) => (
            <motion.button
              key={i}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => handleVoiceCommand(item.command)}
              className="bg-slate-50 border rounded-xl p-4 text-left hover:shadow-md transition-all group"
            >
              <div className="text-3xl mb-2">{item.emoji}</div>
              <div className="font-bold text-sm mb-1 group-hover:text-blue-600 transition-colors">
                {item.command}
              </div>
              <div className="text-[10px] text-slate-500 mb-1">{item.action}</div>
              <div className="text-[10px] text-slate-400">{item.desc}</div>
            </motion.button>
          ))}
        </div>

        <div className="mt-6 flex gap-4">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setIsListening(!isListening)}
            className={`flex-1 py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 ${
              isListening
                ? 'bg-red-500 text-white animate-pulse'
                : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:shadow-xl'
            }`}
          >
            <Mic className="h-6 w-6" />
            {isListening ? '正在聆听... (点击停止)' : '开始语音识别'}
          </motion.button>
          <button className="px-6 py-4 bg-slate-100 rounded-xl font-medium text-slate-700 hover:bg-slate-200 transition-colors">
            查看识别日志
          </button>
        </div>
      </div>

      {/* Device Control */}
      <div className="bg-white rounded-2xl border p-6">
        <h3 className="text-xl font-bold text-slate-900 mb-4">设备控制面板</h3>
        <div className="grid grid-cols-6 gap-4">
          {[
            { label: '板载 LED', icon: '💡', active: true, pin: 'GPIO 2' },
            { label: '蜂鸣器', icon: '🔊', active: false, pin: 'GPIO 5' },
            { label: '直流电机', icon: '⚙️', active: false, pin: 'GPIO 12' },
            { label: '舵机', icon: '🔄', active: false, pin: 'GPIO 13' },
            { label: 'RGB LED', icon: '🌈', active: true, pin: 'GPIO 14' },
            { label: '继电器', icon: '🔌', active: false, pin: 'GPIO 15' }
          ].map((device, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -2 }}
              className={`rounded-xl p-4 text-center border-2 cursor-pointer transition-all ${
                device.active
                  ? 'bg-green-50 border-green-400'
                  : 'bg-white border-slate-200 hover:border-blue-300'
              }`}
            >
              <div className="text-3xl mb-2">{device.icon}</div>
              <div className={`text-xs font-bold mb-1 ${device.active ? 'text-green-700' : 'text-slate-700'}`}>
                {device.label}
              </div>
              <div className="text-[10px] text-slate-500">{device.pin}</div>
              <div className={`mt-2 text-[10px] font-medium ${device.active ? 'text-green-600' : 'text-slate-400'}`}>
                {device.active ? '● 运行中' : '○ 已停止'}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
