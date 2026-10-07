#!/usr/bin/env python3
"""生成合规的256x256 ICO图标用于Electron构建"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(output_path: str):
    """创建合规ICO图标"""
    
    size = 256
    
    # 创建主图像 (RGBA支持透明)
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 渐变背景 - STEM蓝色主题
    for y in range(size):
        # 从深蓝到亮蓝渐变
        ratio = y / size
        r = int(15 + ratio * 30)   # 15-45
        g = int(23 + ratio * 80)   # 23-103
        b = int(58 + ratio * 150)  # 58-208
        draw.rectangle([(0, y), (size, y+1)], fill=(r, g, b, 255))
    
    # 绘制圆角矩形边框
    margin = 20
    corner_radius = 40
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=corner_radius,
        outline=(255, 255, 255, 200),
        width=4
    )
    
    # 绘制 "iM" 文字
    try:
        # 尝试使用系统字体
        font_size = 100
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "iM"
    # 获取文字边界框
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 居中文字
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 10
    
    # 绘制文字阴影
    draw.text((x + 3, y + 3), text, fill=(0, 0, 0, 100), font=font)
    # 绘制主文字
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    # 输出路径
    ico_path = os.path.join(output_path, 'icon.ico')
    
    # 创建不同尺寸的图标
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    ico_images = []
    
    for target_size in sizes:
        resized = img.resize(target_size, Image.Resampling.LANCZOS)
        ico_images.append(resized)
    
    # 保存ICO
    ico_images[0].save(
        ico_path,
        format='ICO',
        sizes=sizes
    )
    
    print(f"图标已生成: {ico_path}")
    print(f"主尺寸: 256x256")
    
    return ico_path

if __name__ == '__main__':
    # 输出到electron build目录
    output_dir = r'g:\iMato\electron\build'
    os.makedirs(output_dir, exist_ok=True)
    
    ico_path = create_icon(output_dir)
    
    # 验证文件
    if os.path.exists(ico_path):
        file_size = os.path.getsize(ico_path)
        print(f"文件大小: {file_size} bytes")