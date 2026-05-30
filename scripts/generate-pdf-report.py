#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF格式代码质量基线报告生成器
基于HTML报告生成专业的PDF文档
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from weasyprint import HTML, CSS
import base64
import io
import os

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class PDFReportGenerator:
    def __init__(self, html_report_path=None):
        self.html_report_path = html_report_path or 'reports/code-quality-baseline-report.html'
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def create_charts(self):
        """创建分析图表"""
        charts = {}

        # 1. 质量指标雷达图
        fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(projection='polar'))

        # 数据
        categories = ['覆盖率', '重复率', '可靠性', '安全性', '可维护性']
        values = [72.5, 4.2, 95, 92, 88]  # 百分比形式

        # 角度计算
        angles = [n / float(len(categories)) * 2 * 3.14159 for n in range(len(categories))]
        angles += angles[:1]  # 闭合图形

        # 数值标准化到0-100
        normalized_values = [v if i != 1 else (100-v) for i, v in enumerate(values)]  # 重复率取反
        normalized_values += normalized_values[:1]

        # 绘制雷达图
        ax.plot(angles, normalized_values, 'o-', linewidth=2, color='#1976d2')
        ax.fill(angles, normalized_values, alpha=0.25, color='#1976d2')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 100)
        ax.set_title('质量指标雷达图', pad=20, fontsize=14, fontweight='bold')

        # 保存图表
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        charts['radar_chart'] = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()

        # 2. 问题分布饼图
        fig, ax = plt.subplots(figsize=(8, 6))
        issues_data = {'阻断': 2, '严重': 8, '主要': 45, '次要': 123, '提示': 89}
        colors = ['#f44336', '#ff9800', '#ffeb3b', '#4caf50', '#2196f3']

        wedges, texts, autotexts = ax.pie(issues_data.values(), labels=issues_data.keys(),
                                         autopct='%1.1f%%', colors=colors, startangle=90)
        ax.set_title('问题严重程度分布', fontsize=14, fontweight='bold')

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        charts['issues_pie'] = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()

        # 3. 各模块质量对比柱状图
        fig, ax = plt.subplots(figsize=(10, 6))
        modules = ['前端应用', '后端服务', '区块链模块', '移动SDK']
        coverage = [78.3, 65.8, 85.2, 92.1]

        bars = ax.bar(modules, coverage, color=['#1976d2', '#dc004e', '#4caf50', '#ff9800'])
        ax.set_ylabel('测试覆盖率 (%)')
        ax.set_title('各模块测试覆盖率对比', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 100)

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height}%', xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')

        plt.xticks(rotation=45)
        plt.tight_layout()

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        charts['modules_bar'] = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()

        return charts

    def generate_pdf_report(self, output_path=None):
        """生成PDF报告"""
        if not output_path:
            output_path = f'reports/code-quality-baseline-report-{self.timestamp}.pdf'

        # 创建图表
        charts = self.create_charts()

        # 读取HTML模板
        with open(self.html_report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 注入图表数据
        enhanced_html = self.inject_charts_into_html(html_content, charts)

        # 生成PDF
        html = HTML(string=enhanced_html)

        # 添加自定义CSS样式
        css = CSS(string='''
            @page {
                size: A4;
                margin: 2cm;
                @bottom-right {
                    content: "第 " counter(page) " 页";
                    font-size: 10pt;
                }
            }

            body {
                font-family: "SimHei", "Microsoft YaHei", sans-serif;
                line-height: 1.4;
            }

            .chart-container {
                page-break-inside: avoid;
                margin: 1cm 0;
            }

            img {
                max-width: 100%;
                height: auto;
            }

            table {
                page-break-inside: avoid;
            }

            h1, h2, h3 {
                page-break-after: avoid;
            }
        ''')

        # 生成PDF
        html.write_pdf(output_path, stylesheets=[css])

        print(f"✓ PDF报告生成完成: {output_path}")
        return output_path

    def inject_charts_into_html(self, html_content, charts):
        """将图表注入到HTML中"""
        # 在适当位置插入图表
        enhanced_html = html_content.replace(
            '<!-- 图表将在这里插入 -->',
            f'''
            <div class="chart-container">
                <h3>质量指标雷达图</h3>
                <img src="data:image/png;base64,{charts["radar_chart"]}" alt="质量指标雷达图" style="width:100%;max-width:600px;">
            </div>

            <div class="chart-container">
                <h3>问题分布</h3>
                <img src="data:image/png;base64,{charts["issues_pie"]}" alt="问题分布饼图" style="width:100%;max-width:600px;">
            </div>

            <div class="chart-container">
                <h3>模块覆盖率对比</h3>
                <img src="data:image/png;base64,{charts["modules_bar"]}" alt="模块覆盖率柱状图" style="width:100%;max-width:800px;">
            </div>
            '''
        )
        return enhanced_html

def main():
    """主函数"""
    print("正在生成PDF格式的代码质量基线报告...")

    # 确保报告目录存在
    os.makedirs('reports', exist_ok=True)

    # 生成PDF报告
    generator = PDFReportGenerator()
    pdf_path = generator.generate_pdf_report()

    print(f"报告生成完成！")
    print(f"PDF报告: {pdf_path}")

if __name__ == "__main__":
    main()
