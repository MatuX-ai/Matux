"""
性能监控模块
实时监控硬件加速器的性能指标
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any
from collections import deque
from datetime import datetime
import psutil
import numpy as np

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """硬件加速器性能监控器"""
    
    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.metrics_history = {
            'cpu_usage': deque(maxlen=1000),
            'memory_usage': deque(maxlen=1000),
            'disk_io': deque(maxlen=1000),
            'network_io': deque(maxlen=1000)
        }
        self.accelerator_metrics = {}
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
    def start_monitoring(self):
        """开始性能监控"""
        if self.is_monitoring:
            logger.warning("性能监控已在运行")
            return
            
        self.is_monitoring = True
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
            
        logger.info("性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while not self.stop_event.wait(self.monitoring_interval):
            try:
                self._collect_system_metrics()
                self._collect_accelerator_metrics()
            except Exception as e:
                logger.error(f"监控过程中发生错误: {str(e)}")
    
    def _collect_system_metrics(self):
        """收集系统级性能指标"""
        timestamp = datetime.now()
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=None)
        self.metrics_history['cpu_usage'].append({
            'timestamp': timestamp.isoformat(),
            'value': cpu_percent
        })
        
        # 内存使用率
        memory = psutil.virtual_memory()
        self.metrics_history['memory_usage'].append({
            'timestamp': timestamp.isoformat(),
            'value': memory.percent,
            'used_mb': memory.used / (1024 * 1024),
            'total_mb': memory.total / (1024 * 1024)
        })
        
        # 磁盘IO
        disk_io = psutil.disk_io_counters()
        if disk_io:
            self.metrics_history['disk_io'].append({
                'timestamp': timestamp.isoformat(),
                'read_bytes': disk_io.read_bytes,
                'write_bytes': disk_io.write_bytes,
                'read_count': disk_io.read_count,
                'write_count': disk_io.write_count
            })
        
        # 网络IO
        net_io = psutil.net_io_counters()
        self.metrics_history['network_io'].append({
            'timestamp': timestamp.isoformat(),
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        })
    
    def _collect_accelerator_metrics(self):
        """收集加速器特定指标"""
        # 这里可以扩展为收集特定加速器的硬件指标
        # 如FPGA温度、GPU利用率等
        pass
    
    def register_accelerator(self, name: str, accelerator):
        """注册加速器以进行专门监控"""
        self.accelerator_metrics[name] = {
            'instance': accelerator,
            'metrics': deque(maxlen=1000),
            'last_update': datetime.now()
        }
        logger.info(f"已注册加速器监控: {name}")
    
    def unregister_accelerator(self, name: str):
        """取消注册加速器监控"""
        if name in self.accelerator_metrics:
            del self.accelerator_metrics[name]
            logger.info(f"已取消注册加速器监控: {name}")
    
    def update_accelerator_metrics(self, name: str, metrics: Dict[str, Any]):
        """更新特定加速器的指标"""
        if name in self.accelerator_metrics:
            metrics_entry = {
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics
            }
            self.accelerator_metrics[name]['metrics'].append(metrics_entry)
            self.accelerator_metrics[name]['last_update'] = datetime.now()
    
    def get_system_metrics(self, metric_type: str = None, 
                          time_window_minutes: int = 5) -> List[Dict]:
        """获取系统性能指标"""
        if metric_type and metric_type in self.metrics_history:
            history = self.metrics_history[metric_type]
        elif not metric_type:
            # 返回所有指标的最新值
            return self._get_latest_metrics()
        else:
            return []
        
        # 过滤时间窗口内的数据
        cutoff_time = datetime.now().timestamp() - (time_window_minutes * 60)
        filtered_metrics = [
            m for m in history 
            if datetime.fromisoformat(m['timestamp']).timestamp() >= cutoff_time
        ]
        
        return filtered_metrics
    
    def _get_latest_metrics(self) -> List[Dict]:
        """获取最新的各项指标"""
        latest_metrics = []
        
        for metric_type, history in self.metrics_history.items():
            if history:
                latest_metrics.append({
                    'type': metric_type,
                    'latest': history[-1],
                    'count': len(history)
                })
        
        return latest_metrics
    
    def get_accelerator_metrics(self, name: str = None, 
                               time_window_minutes: int = 5) -> Dict[str, Any]:
        """获取加速器性能指标"""
        result = {}
        
        accelerators_to_check = [name] if name else self.accelerator_metrics.keys()
        
        cutoff_time = datetime.now().timestamp() - (time_window_minutes * 60)
        
        for accel_name in accelerators_to_check:
            if accel_name in self.accelerator_metrics:
                accel_data = self.accelerator_metrics[accel_name]
                filtered_metrics = [
                    m for m in accel_data['metrics']
                    if datetime.fromisoformat(m['timestamp']).timestamp() >= cutoff_time
                ]
                
                result[accel_name] = {
                    'metrics': filtered_metrics,
                    'count': len(filtered_metrics),
                    'last_update': accel_data['last_update'].isoformat()
                }
        
        return result
    
    def get_performance_alerts(self) -> List[Dict]:
        """获取性能警告"""
        alerts = []
        
        # CPU使用率过高警告
        if self.metrics_history['cpu_usage']:
            recent_cpu = [m['value'] for m in list(self.metrics_history['cpu_usage'])[-10:]]
            avg_cpu = np.mean(recent_cpu) if recent_cpu else 0
            if avg_cpu > 80:
                alerts.append({
                    'type': 'high_cpu_usage',
                    'severity': 'warning',
                    'message': f'CPU使用率过高: {avg_cpu:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
        
        # 内存使用率过高警告
        if self.metrics_history['memory_usage']:
            recent_memory = [m['value'] for m in list(self.metrics_history['memory_usage'])[-10:]]
            avg_memory = np.mean(recent_memory) if recent_memory else 0
            if avg_memory > 85:
                alerts.append({
                    'type': 'high_memory_usage',
                    'severity': 'warning',
                    'message': f'内存使用率过高: {avg_memory:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
        
        # 加速器离线警告
        for name, data in self.accelerator_metrics.items():
            time_since_update = (datetime.now() - data['last_update']).total_seconds()
            if time_since_update > 30:  # 30秒无更新
                alerts.append({
                    'type': 'accelerator_offline',
                    'severity': 'error',
                    'message': f'加速器 {name} 已离线 {time_since_update:.0f} 秒',
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts
    
    def get_system_health_report(self) -> Dict[str, Any]:
        """获取系统健康状况报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': self._calculate_system_stats(),
            'accelerator_status': self._calculate_accelerator_stats(),
            'alerts': self.get_performance_alerts(),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _calculate_system_stats(self) -> Dict[str, Any]:
        """计算系统统计信息"""
        stats = {}
        
        for metric_type, history in self.metrics_history.items():
            if history:
                values = [m.get('value', 0) for m in history if 'value' in m]
                if values:
                    stats[metric_type] = {
                        'current': values[-1],
                        'average': np.mean(values),
                        'min': np.min(values),
                        'max': np.max(values),
                        'std_dev': np.std(values)
                    }
        
        return stats
    
    def _calculate_accelerator_stats(self) -> Dict[str, Any]:
        """计算加速器统计信息"""
        stats = {}
        
        for name, data in self.accelerator_metrics.items():
            if data['metrics']:
                # 这里可以根据具体指标计算统计信息
                stats[name] = {
                    'updates_count': len(data['metrics']),
                    'last_update': data['last_update'].isoformat(),
                    'uptime_seconds': (datetime.now() - data['last_update']).total_seconds()
                }
        
        return stats
    
    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        alerts = self.get_performance_alerts()
        
        # 基于警告生成建议
        high_cpu_alerts = [a for a in alerts if a['type'] == 'high_cpu_usage']
        if high_cpu_alerts:
            recommendations.append("建议优化算法或增加计算资源")
        
        high_memory_alerts = [a for a in alerts if a['type'] == 'high_memory_usage']
        if high_memory_alerts:
            recommendations.append("建议释放内存或增加内存容量")
        
        offline_alerts = [a for a in alerts if a['type'] == 'accelerator_offline']
        if offline_alerts:
            recommendations.append("检查硬件连接和驱动程序状态")
        
        # 基于性能趋势生成建议
        if self.metrics_history['cpu_usage'] and len(self.metrics_history['cpu_usage']) > 100:
            recent_cpu = [m['value'] for m in list(self.metrics_history['cpu_usage'])[-20:]]
            older_cpu = [m['value'] for m in list(self.metrics_history['cpu_usage'])[-100:-80]]
            
            if np.mean(recent_cpu) > np.mean(older_cpu) * 1.2:
                recommendations.append("检测到CPU负载持续上升趋势")
        
        return recommendations
    
    def cleanup(self):
        """清理监控资源"""
        self.stop_monitoring()
        self.metrics_history.clear()
        self.accelerator_metrics.clear()
        logger.info("性能监控器资源已清理")