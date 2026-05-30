"""
教育数据可视化组件
集成Matplotlib、Plotly等图表库，创建交互式仪表板
"""

import base64
from datetime import datetime
import io
import logging
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go

from ..analytics.stem_analyzer import STEMCapabilityAnalyzer

logger = logging.getLogger(__name__)

# 设置matplotlib中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


class EduDataVisualizer:
    """教育数据可视化器"""

    def __init__(self):
        self.analyzer = STEMCapabilityAnalyzer()
        self.color_palette = {
            "primary": "#2196F3",
            "secondary": "#4CAF50",
            "accent": "#FF9800",
            "warning": "#F44336",
            "info": "#00BCD4",
            "success": "#8BC34A",
            "grades": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
        }

    def create_dashboard_visualizations(
        self, analysis_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        创建完整的仪表板可视化

        Args:
            analysis_data: 分析数据

        Returns:
            图表Base64编码字典
        """
        try:
            visualizations = {}

            # 1. STEM综合得分仪表盘
            visualizations["stem_dashboard"] = self._create_stem_dashboard(
                analysis_data
            )

            # 2. 学科能力雷达图
            visualizations["subject_radar"] = self._create_subject_radar_chart(
                analysis_data
            )

            # 3. 区域对比热力图
            visualizations["regional_heatmap"] = self._create_regional_heatmap(
                analysis_data
            )

            # 4. 成绩分布直方图
            visualizations["score_distribution"] = (
                self._create_score_distribution_chart(analysis_data)
            )

            # 5. 趋势分析折线图
            visualizations["trend_analysis"] = self._create_trend_chart(analysis_data)

            # 6. 能力等级饼图
            visualizations["capability_pie"] = self._create_capability_pie_chart(
                analysis_data
            )

            logger.info(f"仪表板可视化创建完成: {len(visualizations)} 个图表")
            return visualizations

        except Exception as e:
            logger.error(f"创建仪表板可视化失败: {e}")
            return {}

    def _create_stem_dashboard(self, data: Dict[str, Any]) -> str:
        """创建STEM综合得分仪表盘"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle("STEM学科能力综合分析仪表盘", fontsize=16, fontweight="bold")

            # 1. 综合得分仪表图
            ax1 = axes[0, 0]
            stem_score = data.get("stem_overall_score", 0)
            self._create_gauge_chart(ax1, stem_score, "STEM综合能力得分")

            # 2. 学科得分柱状图
            ax2 = axes[0, 1]
            subject_data = data.get("subject_analyses", {})
            self._create_subject_bar_chart(ax2, subject_data)

            # 3. 区域对比散点图
            ax3 = axes[1, 0]
            regional_data = data.get("regional_comparison", [])
            self._create_regional_scatter_plot(ax3, regional_data)

            # 4. 趋势箭头指示器
            ax4 = axes[1, 1]
            self._create_trend_indicators(ax4, data)

            plt.tight_layout()

            # 转换为base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png", dpi=300, bbox_inches="tight")
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()

            return img_base64

        except Exception as e:
            logger.error(f"创建STEM仪表盘失败: {e}")
            return self._create_error_placeholder("STEM仪表盘")

    def _create_subject_radar_chart(self, data: Dict[str, Any]) -> str:
        """创建学科能力雷达图"""
        try:
            subject_analyses = data.get("subject_analyses", {})
            if not subject_analyses:
                return self._create_error_placeholder("学科雷达图")

            # 准备雷达图数据
            subjects = []
            scores = []
            max_scores = []

            for subject_key, analysis in subject_analyses.items():
                subjects.append(subject_key.upper())
                scores.append(analysis.get("average_score", 0))
                max_scores.append(100)  # 最大值设为100

            # 创建雷达图
            fig = go.Figure()

            fig.add_trace(
                go.Scatterpolar(
                    r=scores + [scores[0]],  # 闭合图形
                    theta=subjects + [subjects[0]],
                    fill="toself",
                    name="实际得分",
                    line_color=self.color_palette["primary"],
                )
            )

            fig.add_trace(
                go.Scatterpolar(
                    r=max_scores + [max_scores[0]],
                    theta=subjects + [subjects[0]],
                    fill=None,
                    name="满分基准",
                    line_dash="dash",
                    line_color=self.color_palette["secondary"],
                )
            )

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                title="STEM学科能力雷达图",
                width=600,
                height=500,
            )

            # 转换为base64
            img_bytes = fig.to_image(format="png", width=600, height=500)
            return base64.b64encode(img_bytes).decode()

        except Exception as e:
            logger.error(f"创建雷达图失败: {e}")
            return self._create_error_placeholder("学科雷达图")

    def _create_regional_heatmap(self, data: Dict[str, Any]) -> str:
        """创建区域对比热力图"""
        try:
            regional_data = data.get("regional_comparison", [])
            if not regional_data:
                return self._create_error_placeholder("区域热力图")

            # 准备热力图数据
            regions = []
            subjects = ["MATH", "SCIENCE", "TECHNOLOGY", "ENGINEERING"]
            heatmap_data = []

            for region_info in regional_data[:10]:  # 限制显示前10个区域
                regions.append(
                    region_info.get("region_name", "Unknown")[:15]
                )  # 截断长名称
                subject_scores = region_info.get("subject_scores", {})
                row_data = [
                    subject_scores.get("math", 0),
                    subject_scores.get("science", 0),
                    subject_scores.get("technology", 0),
                    subject_scores.get("engineering", 0),
                ]
                heatmap_data.append(row_data)

            if not heatmap_data:
                return self._create_error_placeholder("区域热力图")

            # 创建热力图
            fig = go.Figure(
                data=go.Heatmap(
                    z=heatmap_data,
                    x=subjects,
                    y=regions,
                    colorscale="Viridis",
                    text=heatmap_data,
                    texttemplate="%{text:.1f}",
                    textfont={"size": 10},
                    hoverongaps=False,
                )
            )

            fig.update_layout(
                title="区域STEM学科能力热力图",
                xaxis_title="学科",
                yaxis_title="区域",
                width=700,
                height=500,
            )

            # 转换为base64
            img_bytes = fig.to_image(format="png", width=700, height=500)
            return base64.b64encode(img_bytes).decode()

        except Exception as e:
            logger.error(f"创建热力图失败: {e}")
            return self._create_error_placeholder("区域热力图")

    def _create_score_distribution_chart(self, data: Dict[str, Any]) -> str:
        """创建成绩分布直方图"""
        try:
            subject_analyses = data.get("subject_analyses", {})
            if not subject_analyses:
                return self._create_error_placeholder("成绩分布图")

            # 创建子图
            n_subjects = len(subject_analyses)
            cols = min(2, n_subjects)
            rows = (n_subjects + cols - 1) // cols

            fig, axes = plt.subplots(rows, cols, figsize=(12, 6 * rows))
            if n_subjects == 1:
                axes = [axes]
            elif rows == 1:
                axes = axes.flatten()
            else:
                axes = axes.flatten()

            # 为每个学科创建分布图
            for idx, (subject_key, analysis) in enumerate(subject_analyses.items()):
                if idx >= len(axes):
                    break

                ax = axes[idx]
                distribution = analysis.get("score_distribution", {})

                if distribution:
                    labels = list(distribution.keys())
                    values = list(distribution.values())

                    bars = ax.bar(
                        range(len(labels)),
                        values,
                        color=self.color_palette["grades"][: len(labels)],
                    )
                    ax.set_xlabel("成绩等级")
                    ax.set_ylabel("学生人数")
                    ax.set_title(f"{subject_key.upper()} 成绩分布")
                    ax.set_xticks(range(len(labels)))
                    ax.set_xticklabels(labels, rotation=45, ha="right")

                    # 添加数值标签
                    for bar, value in zip(bars, values):
                        ax.text(
                            bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + 0.5,
                            str(value),
                            ha="center",
                            va="bottom",
                        )

            plt.tight_layout()

            # 转换为base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png", dpi=300, bbox_inches="tight")
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()

            return img_base64

        except Exception as e:
            logger.error(f"创建分布图失败: {e}")
            return self._create_error_placeholder("成绩分布图")

    def _create_trend_chart(self, data: Dict[str, Any]) -> str:
        """创建趋势分析图表"""
        try:
            trend_data = data.get("trend_analysis", {})
            if not trend_data:
                return self._create_error_placeholder("趋势分析图")

            fig = go.Figure()

            # 为每个学科添加趋势线
            colors = [
                self.color_palette["primary"],
                self.color_palette["secondary"],
                self.color_palette["accent"],
                self.color_palette["info"],
            ]

            for idx, (subject_key, trend_info) in enumerate(trend_data.items()):
                predictions = trend_info.get("predicted_scores", [])
                conf_intervals = trend_info.get("confidence_intervals", [])

                if predictions:
                    x_points = list(range(len(predictions)))
                    color = colors[idx % len(colors)]

                    # 预测线
                    fig.add_trace(
                        go.Scatter(
                            x=x_points,
                            y=predictions,
                            mode="lines+markers",
                            name=f"{subject_key.upper()} 预测",
                            line=dict(color=color, width=3),
                        )
                    )

                    # 置信区间
                    if conf_intervals:
                        upper_bounds = [ci[1] for ci in conf_intervals]
                        lower_bounds = [ci[0] for ci in conf_intervals]

                        fig.add_trace(
                            go.Scatter(
                                x=x_points + x_points[::-1],
                                y=upper_bounds + lower_bounds[::-1],
                                fill="toself",
                                fillcolor=color.replace("#", "rgba(") + ",0.2)",
                                line=dict(color="rgba(255,255,255,0)"),
                                name=f"{subject_key.upper()} 置信区间",
                                showlegend=False,
                            )
                        )

            fig.update_layout(
                title="STEM学科能力发展趋势预测",
                xaxis_title="时间周期",
                yaxis_title="预测得分",
                yaxis=dict(range=[0, 100]),
                width=800,
                height=500,
            )

            # 转换为base64
            img_bytes = fig.to_image(format="png", width=800, height=500)
            return base64.b64encode(img_bytes).decode()

        except Exception as e:
            logger.error(f"创建趋势图失败: {e}")
            return self._create_error_placeholder("趋势分析图")

    def _create_capability_pie_chart(self, data: Dict[str, Any]) -> str:
        """创建能力等级饼图"""
        try:
            stem_score = data.get("stem_overall_score", 0)
            capability_level = data.get("capability_level", "unknown")

            # 定义等级划分
            level_descriptions = {
                "excellent": "优秀 (>90)",
                "good": "良好 (80-89)",
                "fair": "一般 (70-79)",
                "poor": "较差 (60-69)",
                "very_poor": "很差 (<60)",
            }

            # 计算各级别人数（模拟数据）
            total_students = 1000  # 假设总数
            level_counts = {
                "excellent": int(total_students * 0.15),
                "good": int(total_students * 0.25),
                "fair": int(total_students * 0.35),
                "poor": int(total_students * 0.20),
                "very_poor": int(total_students * 0.05),
            }

            # 创建饼图
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=list(level_descriptions.values()),
                        values=list(level_counts.values()),
                        hole=0.4,
                        marker_colors=[
                            self.color_palette["success"],
                            self.color_palette["secondary"],
                            self.color_palette["info"],
                            self.color_palette["accent"],
                            self.color_palette["warning"],
                        ],
                    )
                ]
            )

            fig.update_layout(
                title=f"STEM能力等级分布 (综合得分: {stem_score:.1f})",
                annotations=[
                    dict(
                        text=f"{capability_level.upper()}",
                        x=0.5,
                        y=0.5,
                        font_size=20,
                        showarrow=False,
                    )
                ],
                width=500,
                height=500,
            )

            # 转换为base64
            img_bytes = fig.to_image(format="png", width=500, height=500)
            return base64.b64encode(img_bytes).decode()

        except Exception as e:
            logger.error(f"创建饼图失败: {e}")
            return self._create_error_placeholder("能力等级图")

    def _create_gauge_chart(self, ax, value: float, title: str):
        """创建仪表图"""
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 10)

        # 创建半圆弧
        theta = np.linspace(0, np.pi, 100)
        x = 50 + 40 * np.cos(theta)
        y = 5 + 40 * np.sin(theta)

        # 根据值得分颜色
        if value >= 90:
            color = self.color_palette["success"]
        elif value >= 80:
            color = self.color_palette["secondary"]
        elif value >= 70:
            color = self.color_palette["info"]
        elif value >= 60:
            color = self.color_palette["accent"]
        else:
            color = self.color_palette["warning"]

        ax.plot(x, y, "k-", linewidth=2)
        ax.fill_between(x, 5, y, alpha=0.3, color=color)

        # 添加指针
        pointer_angle = np.pi * (1 - value / 100)
        pointer_x = 50 + 35 * np.cos(pointer_angle)
        pointer_y = 5 + 35 * np.sin(pointer_angle)
        ax.plot([50, pointer_x], [5, pointer_y], "r-", linewidth=3)

        # 添加文本
        ax.text(
            50,
            3,
            f"{value:.1f}",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )
        ax.text(50, 1, title, ha="center", va="center", fontsize=12)

        ax.set_aspect("equal")
        ax.axis("off")

    def _create_subject_bar_chart(self, ax, subject_data: Dict[str, Any]):
        """创建学科柱状图"""
        if not subject_data:
            return

        subjects = list(subject_data.keys())
        scores = [
            analysis.get("average_score", 0) for analysis in subject_data.values()
        ]

        bars = ax.bar(
            subjects, scores, color=self.color_palette["grades"][: len(subjects)]
        )
        ax.set_ylabel("平均得分")
        ax.set_title("各学科能力得分")
        ax.set_ylim(0, 100)

        # 添加数值标签
        for bar, score in zip(bars, scores):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{score:.1f}",
                ha="center",
                va="bottom",
            )

        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    def _create_regional_scatter_plot(self, ax, regional_data: List[Dict[str, Any]]):
        """创建区域散点图"""
        if not regional_data:
            return

        x_data = [region.get("student_count", 0) for region in regional_data]
        y_data = [region.get("average_stem_score", 0) for region in regional_data]
        sizes = [region.get("schools_count", 10) * 10 for region in regional_data]
        labels = [region.get("region_name", "")[:10] for region in regional_data]

        scatter = ax.scatter(
            x_data, y_data, s=sizes, alpha=0.6, c=y_data, cmap="viridis"
        )
        ax.set_xlabel("学生数量")
        ax.set_ylabel("STEM平均得分")
        ax.set_title("区域教育水平散点图")

        # 添加颜色条
        plt.colorbar(scatter, ax=ax)

    def _create_trend_indicators(self, ax, data: Dict[str, Any]):
        """创建趋势指示器"""
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")

        subject_analyses = data.get("subject_analyses", {})

        for idx, (subject_key, analysis) in enumerate(subject_analyses.items()):
            improvement_rate = analysis.get("improvement_rate", 0)
            y_pos = 8 - idx * 2

            # 根据改善率选择箭头方向和颜色
            if improvement_rate > 5:
                arrow = "↑"
                color = self.color_palette["success"]
            elif improvement_rate < -5:
                arrow = "↓"
                color = self.color_palette["warning"]
            else:
                arrow = "→"
                color = self.color_palette["info"]

            ax.text(2, y_pos, f"{subject_key.upper()}:", fontsize=12, ha="left")
            ax.text(
                6,
                y_pos,
                f"{arrow} {improvement_rate:+.1f}%",
                fontsize=14,
                ha="left",
                color=color,
                weight="bold",
            )

    def _create_error_placeholder(self, chart_name: str) -> str:
        """创建错误占位图"""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(
            0.5, 0.5, f"{chart_name}\n数据不足", ha="center", va="center", fontsize=16
        )
        ax.axis("off")

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png")
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()

        return img_base64


class InteractiveDashboard:
    """交互式仪表板"""

    def __init__(self):
        self.visualizer = EduDataVisualizer()

    def generate_interactive_dashboard(self, analysis_data: Dict[str, Any]) -> str:
        """
        生成交互式HTML仪表板

        Args:
            analysis_data: 分析数据

        Returns:
            HTML仪表板字符串
        """
        try:
            # 生成所有可视化图表
            visualizations = self.visualizer.create_dashboard_visualizations(
                analysis_data
            )

            # 构建HTML仪表板
            html_content = self._build_dashboard_html(analysis_data, visualizations)

            return html_content

        except Exception as e:
            logger.error(f"生成交互式仪表板失败: {e}")
            return self._get_error_dashboard(str(e))

    def _build_dashboard_html(
        self, data: Dict[str, Any], visualizations: Dict[str, str]
    ) -> str:
        """构建HTML仪表板"""
        stem_score = data.get("stem_overall_score", 0)
        capability_level = data.get("capability_level", "unknown")

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>教育数据分析仪表板</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .dashboard-header {{
            background: linear-gradient(135deg, #2196F3 0%, #21CBF3 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .dashboard-title {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .dashboard-subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .metrics-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            color: #666;
            font-size: 1.1em;
        }}
        .charts-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}
        .chart-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .chart-title {{
            font-size: 1.4em;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #2196F3;
            padding-bottom: 10px;
        }}
        .chart-image {{
            width: 100%;
            height: auto;
            border-radius: 5px;
        }}
        .recommendations {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .recommendations h2 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .recommendation-item {{
            background: #e3f2fd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #2196F3;
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="dashboard-title">🎓 教育数据分析仪表板</div>
        <div class="dashboard-subtitle">基于联邦学习的STEM能力评估报告</div>
        <div style="margin-top: 15px; font-size: 1.1em;">
            生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>

    <div class="metrics-container">
        <div class="metric-card">
            <div class="metric-label">STEM综合得分</div>
            <div class="metric-value" style="color: #2196F3;">{stem_score:.1f}</div>
            <div>满分100分</div>
        </div>

        <div class="metric-card">
            <div class="metric-label">能力等级</div>
            <div class="metric-value" style="color: #4CAF50;">{capability_level.upper()}</div>
            <div>整体评估</div>
        </div>

        <div class="metric-card">
            <div class="metric-label">数据质量</div>
            <div class="metric-value" style="color: #FF9800;">
                {data.get('data_quality_metrics', {}).get('completion_rate', 0)*100:.1f}%
            </div>
            <div>完整性</div>
        </div>

        <div class="metric-card">
            <div class="metric-label">分析建议</div>
            <div class="metric-value" style="color: #9C27B0;">
                {len(data.get('recommendations', []))}
            </div>
            <div>条改进建议</div>
        </div>
    </div>

    <div class="charts-container">
        <div class="chart-card">
            <div class="chart-title">📊 STEM综合分析仪表盘</div>
            <img class="chart-image" src="data:image/png;base64,{visualizations.get('stem_dashboard', '')}" alt="STEM仪表盘">
        </div>

        <div class="chart-card">
            <div class="chart-title">🎯 学科能力雷达图</div>
            <img class="chart-image" src="data:image/png;base64,{visualizations.get('subject_radar', '')}" alt="学科雷达图">
        </div>

        <div class="chart-card">
            <div class="chart-title">🗺️ 区域能力热力图</div>
            <img class="chart-image" src="data:image/png;base64,{visualizations.get('regional_heatmap', '')}" alt="区域热力图">
        </div>

        <div class="chart-card">
            <div class="chart-title">📈 成绩分布分析</div>
            <img class="chart-image" src="data:image/png;base64,{visualizations.get('score_distribution', '')}" alt="成绩分布">
        </div>

        <div class="chart-card">
            <div class="chart-title">🔮 发展趋势预测</div>
            <img class="chart-image" src="data:image/png;base64,{visualizations.get('trend_analysis', '')}" alt="趋势分析">
        </div>

        <div class="chart-card">
            <div class="chart-title">🥧 能力等级分布</div>
            <img class="chart-image" src="data:image/png;base64,{visualizations.get('capability_pie', '')}" alt="能力饼图">
        </div>
    </div>

    <div class="recommendations">
        <h2>💡 改进建议</h2>
        """

        # 添加建议项
        recommendations = data.get("recommendations", [])
        if recommendations:
            for rec in recommendations:
                html += f'<div class="recommendation-item">{rec}</div>'
        else:
            html += '<div class="recommendation-item">暂无具体建议，请参考详细分析报告。</div>'

        html += """
    </div>
</body>
</html>
        """

        return html

    def _get_error_dashboard(self, error_message: str) -> str:
        """获取错误仪表板"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>仪表板错误</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
        .error-box {{
            background: #ffebee;
            border: 2px solid #f44336;
            padding: 30px;
            border-radius: 10px;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <div class="error-box">
        <h2 style="color: #f44336;">仪表板生成失败</h2>
        <p>错误信息: {error_message}</p>
        <p>请检查数据完整性和系统配置。</p>
    </div>
</body>
</html>
        """


# 全局实例
data_visualizer = EduDataVisualizer()
interactive_dashboard = InteractiveDashboard()


if __name__ == "__main__":
    # 测试可视化组件
    test_data = {
        "stem_overall_score": 82.5,
        "capability_level": "good",
        "subject_analyses": {
            "math": {"average_score": 85.2, "improvement_rate": 3.2},
            "science": {"average_score": 81.8, "improvement_rate": 1.5},
            "technology": {"average_score": 79.5, "improvement_rate": -0.8},
            "engineering": {"average_score": 83.1, "improvement_rate": 2.1},
        },
        "regional_comparison": [
            {
                "region_name": "北京市",
                "average_stem_score": 88.5,
                "student_count": 5000,
                "schools_count": 50,
            },
            {
                "region_name": "上海市",
                "average_stem_score": 86.2,
                "student_count": 4500,
                "schools_count": 45,
            },
        ],
        "data_quality_metrics": {"completion_rate": 0.95},
        "recommendations": [
            "加强技术学科的教学资源配置",
            "推广数学学科的成功教学模式",
            "关注薄弱地区教育均衡发展",
        ],
    }

    logger = logging.getLogger(__name__)

    try:
        dashboard_html = interactive_dashboard.generate_interactive_dashboard(test_data)
        logger.info("仪表板HTML生成成功，HTML长度：%d 字符", len(dashboard_html))

        # 保存到文件测试
        with open("test_dashboard.html", "w", encoding="utf-8") as f:
            f.write(dashboard_html)
        logger.info("仪表板已保存到 test_dashboard.html")

    except Exception as e:
        logger.error("测试失败：%s", e, exc_info=True)
