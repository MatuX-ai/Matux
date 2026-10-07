'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Bluetooth, Wifi, CheckCircle, AlertCircle, RefreshCw, Zap } from 'lucide-react';
import { DeviceMode } from '../../types';
import { useState } from 'react';

interface DeviceConnectPageProps {
  mode: DeviceMode;
  onNavigate?: (page: string) => void;
}

type ConnectStep = 'scan' | 'pair' | 'verify' | 'complete';

export function DeviceConnectPage({ mode, onNavigate }: DeviceConnectPageProps) {
  const isPhone = mode === 'phone';
  const [currentStep, setCurrentStep] = useState<ConnectStep>('scan');
  const [isScanning, setIsScanning] = useState(false);
  const [foundDevices, setFoundDevices] = useState([
    { name: 'ESP32-DevKit', mac: 'AA:BB:CC:DD:EE:FF', rssi: -42, connected: false },
    { name: 'ESP32-CAM', mac: '11:22:33:44:55:66', rssi: -58, connected: false }
  ]);

  const handleScan = () => {
    setIsScanning(true);
    setTimeout(() => {
      setIsScanning(false);
      setCurrentStep('pair');
    }, 2000);
  };

  const handlePair = (deviceIndex: number) => {
    const updated = [...foundDevices];
    updated[deviceIndex].connected = true;
    setFoundDevices(updated);
    setCurrentStep('verify');
  };

  if (isPhone) {
    return (
      <div className="px-5 space-y-5">
        {/* Progress Steps */}
        <div className="flex justify-between items-center mb-6">
          {[
            { step: 'scan', label: '扫描', icon: Wifi },
            { step: 'pair', label: '配对', icon: Bluetooth },
            { step: 'verify', label: '验证', icon: CheckCircle },
            { step: 'complete', label: '完成', icon: Zap }
          ].map((item, i) => {
            const isActive = currentStep === item.step;
            const isCompleted = ['scan', 'pair', 'verify', 'complete'].indexOf(currentStep) > 
                               ['scan', 'pair', 'verify', 'complete'].indexOf(item.step);
            
            return (
              <div key={i} className="flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  isActive ? 'bg-blue-600 text-white' : 
                  isCompleted ? 'bg-green-500 text-white' : 
                  'bg-slate-200 text-slate-400'
                }`}>
                  <item.icon className="h-5 w-5" />
                </div>
                <span className={`text-[9px] mt-1 ${isActive ? 'text-blue-600 font-bold' : 'text-slate-500'}`}>
                  {item.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Step Content */}
        <AnimatePresence mode="wait">
          {currentStep === 'scan' && (
            <motion.div
              key="scan"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-4"
            >
              <div className="bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl p-6 text-white text-center">
                <Wifi className="h-16 w-16 mx-auto mb-3 opacity-80" />
                <h3 className="text-xl font-bold mb-2">扫描附近设备</h3>
                <p className="text-sm text-blue-100 mb-4">确保 ESP32 已通电并处于配对模式</p>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={handleScan}
                  disabled={isScanning}
                  className="bg-white text-blue-600 px-6 py-3 rounded-xl font-bold text-sm hover:shadow-lg transition-all disabled:opacity-50 flex items-center gap-2 mx-auto"
                >
                  {isScanning ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      扫描中...
                    </>
                  ) : (
                    '开始扫描'
                  )}
                </motion.button>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <h4 className="font-bold text-sm text-blue-900 mb-2">配对提示</h4>
                <ul className="text-xs text-blue-800 space-y-1">
                  <li>✓ 长按 ESP32 上的 BOOT 按钮 3 秒</li>
                  <li>✓ LED 指示灯应快速闪烁</li>
                  <li>✓ 保持手机与设备距离在 5 米内</li>
                </ul>
              </div>
            </motion.div>
          )}

          {currentStep === 'pair' && (
            <motion.div
              key="pair"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-3"
            >
              <h3 className="font-bold text-slate-900 text-base">发现的设备</h3>
              {foundDevices.map((device, i) => (
                <motion.div
                  key={i}
                  whileTap={{ scale: 0.98 }}
                  className="bg-white rounded-xl border p-4 cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => !device.connected && handlePair(i)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                        device.connected ? 'bg-green-100' : 'bg-blue-100'
                      }`}>
                        <Bluetooth className={`h-6 w-6 ${device.connected ? 'text-green-600' : 'text-blue-600'}`} />
                      </div>
                      <div>
                        <h4 className="font-bold text-sm">{device.name}</h4>
                        <p className="text-[10px] text-slate-500">{device.mac}</p>
                        <p className="text-[10px] text-slate-500">信号强度: {device.rssi} dBm</p>
                      </div>
                    </div>
                    {device.connected ? (
                      <CheckCircle className="h-6 w-6 text-green-500" />
                    ) : (
                      <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-xs font-medium">
                        连接
                      </button>
                    )}
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}

          {currentStep === 'verify' && (
            <motion.div
              key="verify"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-4"
            >
              <div className="bg-green-50 border border-green-200 rounded-2xl p-6 text-center">
                <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-3" />
                <h3 className="text-xl font-bold text-green-900 mb-2">连接成功！</h3>
                <p className="text-sm text-green-700 mb-4">ESP32-DevKit 已成功配对</p>
                <div className="grid grid-cols-2 gap-3 text-left">
                  <div className="bg-white rounded-lg p-3">
                    <div className="text-[10px] text-slate-500 mb-1">设备名称</div>
                    <div className="text-sm font-bold">ESP32-DevKit</div>
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <div className="text-[10px] text-slate-500 mb-1">MAC 地址</div>
                    <div className="text-sm font-bold">AA:BB:CC:DD:EE:FF</div>
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <div className="text-[10px] text-slate-500 mb-1">固件版本</div>
                    <div className="text-sm font-bold">v2.1.0</div>
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <div className="text-[10px] text-slate-500 mb-1">电池电量</div>
                    <div className="text-sm font-bold text-green-600">85%</div>
                  </div>
                </div>
              </div>

              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={() => setCurrentStep('complete')}
                className="w-full bg-gradient-to-r from-green-500 to-green-600 text-white py-3 rounded-xl font-bold"
              >
                开始使用
              </motion.button>
            </motion.div>
          )}

          {currentStep === 'complete' && (
            <motion.div
              key="complete"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="text-center py-10"
            >
              <Zap className="h-20 w-20 text-yellow-500 mx-auto mb-4 animate-pulse" />
              <h3 className="text-2xl font-bold text-slate-900 mb-2">准备就绪！</h3>
              <p className="text-sm text-slate-600 mb-6">现在可以开始控制你的 ESP32 设备了</p>
              <div className="space-y-3">
                <button
                  onClick={() => onNavigate?.('sensors')}
                  className="w-full bg-blue-600 text-white py-3 rounded-xl font-bold hover:bg-blue-700 transition-colors"
                >
                  查看传感器数据
                </button>
                <button className="w-full bg-purple-600 text-white py-3 rounded-xl font-bold">
                  测试语音指令
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // 平板模式 - 更丰富的展示
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-slate-900">设备连接 📡</h2>
      </div>

      {/* Connection Wizard */}
      <div className="bg-white rounded-2xl border p-8">
        <div className="flex justify-between items-center mb-8">
          {[
            { step: 'scan', label: '1. 扫描设备', desc: '发现附近的 ESP32' },
            { step: 'pair', label: '2. 选择设备', desc: '点击要连接的设备' },
            { step: 'verify', label: '3. 验证连接', desc: '确认设备信息' },
            { step: 'complete', label: '4. 完成设置', desc: '开始使用设备' }
          ].map((item, i) => {
            const isActive = currentStep === item.step;
            const isCompleted = ['scan', 'pair', 'verify', 'complete'].indexOf(currentStep) > 
                               ['scan', 'pair', 'verify', 'complete'].indexOf(item.step);
            
            return (
              <div key={i} className="flex-1 text-center relative">
                {i < 3 && (
                  <div className={`absolute top-5 left-[60%] w-[80%] h-0.5 ${
                    isCompleted ? 'bg-green-500' : 'bg-slate-200'
                  }`}></div>
                )}
                <div className={`w-10 h-10 rounded-full flex items-center justify-center mx-auto mb-2 relative z-10 ${
                  isActive ? 'bg-blue-600 text-white' : 
                  isCompleted ? 'bg-green-500 text-white' : 
                  'bg-slate-200 text-slate-400'
                }`}>
                  {isCompleted ? <CheckCircle className="h-5 w-5" /> : <span className="font-bold">{i + 1}</span>}
                </div>
                <h4 className={`font-bold text-sm mb-1 ${isActive ? 'text-blue-600' : 'text-slate-900'}`}>
                  {item.label}
                </h4>
                <p className="text-xs text-slate-500">{item.desc}</p>
              </div>
            );
          })}
        </div>

        {/* Step Content Area */}
        <AnimatePresence mode="wait">
          {currentStep === 'scan' && (
            <motion.div
              key="scan"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-10"
            >
              <Wifi className="h-24 w-24 text-blue-500 mx-auto mb-4" />
              <h3 className="text-2xl font-bold text-slate-900 mb-3">扫描附近设备</h3>
              <p className="text-slate-600 mb-6 max-w-md mx-auto">
                确保您的 ESP32 设备已通电并处于配对模式。长按 BOOT 按钮 3 秒，LED 指示灯应快速闪烁。
              </p>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleScan}
                disabled={isScanning}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-xl font-bold text-lg hover:shadow-xl transition-all disabled:opacity-50 inline-flex items-center gap-2"
              >
                {isScanning ? (
                  <>
                    <RefreshCw className="h-5 w-5 animate-spin" />
                    正在扫描...
                  </>
                ) : (
                  '开始扫描'
                )}
              </motion.button>
            </motion.div>
          )}

          {currentStep === 'pair' && (
            <motion.div
              key="pair"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <h3 className="text-xl font-bold text-slate-900 mb-4">发现的设备</h3>
              <div className="grid grid-cols-2 gap-4">
                {foundDevices.map((device, i) => (
                  <motion.div
                    key={i}
                    whileHover={{ y: -2 }}
                    className={`bg-white rounded-xl border-2 p-6 cursor-pointer transition-all ${
                      device.connected ? 'border-green-500 bg-green-50' : 'border-slate-200 hover:border-blue-400'
                    }`}
                    onClick={() => !device.connected && handlePair(i)}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <Bluetooth className={`h-12 w-12 ${device.connected ? 'text-green-600' : 'text-blue-600'}`} />
                      {device.connected && <CheckCircle className="h-8 w-8 text-green-500" />}
                    </div>
                    <h4 className="font-bold text-lg mb-1">{device.name}</h4>
                    <p className="text-sm text-slate-500 mb-2">{device.mac}</p>
                    <div className="flex items-center gap-2 text-xs text-slate-600">
                      <span>信号强度:</span>
                      <span className="font-semibold">{device.rssi} dBm</span>
                    </div>
                    {!device.connected && (
                      <button className="mt-4 w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors">
                        连接此设备
                      </button>
                    )}
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {(currentStep === 'verify' || currentStep === 'complete') && (
            <motion.div
              key="complete"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-10"
            >
              <Zap className="h-24 w-24 text-yellow-500 mx-auto mb-4 animate-pulse" />
              <h3 className="text-3xl font-bold text-slate-900 mb-3">连接成功！</h3>
              <p className="text-slate-600 mb-8">ESP32-DevKit 已准备就绪</p>
              
              <div className="grid grid-cols-4 gap-4 max-w-3xl mx-auto mb-8">
                {[
                  { label: '设备名称', value: 'ESP32-DevKit' },
                  { label: 'MAC 地址', value: 'AA:BB:CC:DD:EE:FF' },
                  { label: '固件版本', value: 'v2.1.0' },
                  { label: '电池电量', value: '85%', highlight: true }
                ].map((item, i) => (
                  <div key={i} className="bg-slate-50 rounded-xl p-4">
                    <div className="text-xs text-slate-500 mb-1">{item.label}</div>
                    <div className={`text-lg font-bold ${item.highlight ? 'text-green-600' : 'text-slate-900'}`}>
                      {item.value}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-4 justify-center">
                <button
                  onClick={() => onNavigate?.('sensors')}
                  className="bg-blue-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-blue-700 transition-colors"
                >
                  查看传感器数据
                </button>
                <button className="bg-purple-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-purple-700 transition-colors">
                  测试语音指令
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
