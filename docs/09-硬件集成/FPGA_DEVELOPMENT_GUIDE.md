# FPGA开发指南

## 概述

本文档详细介绍如何在iMato项目中开发、部署和维护FPGA硬件加速模块。

## FPGA架构设计

### 1. 模块层次结构

```
顶层模块 (fpga_top.v)
├── 图像处理流水线 (image_processing_pipeline.v)
│   ├── 边缘检测模块 (edge_detector.v)
│   ├── 高斯滤波模块 (gaussian_filter.v)
│   └── 形态学处理模块 (morphological_processor.v)
└── 控制接口
    ├── 时钟管理
    ├── 复位控制
    └── 模式选择
```

### 2. 核心模块详解

#### 2.1 边缘检测模块 (`edge_detector.v`)

```verilog
module edge_detector(
    input wire clk,              // 时钟信号 (50MHz)
    input wire rst_n,            // 异步复位 (低电平有效)
    input wire [7:0] pixel_in,   // 输入像素值 (0-255)
    input wire [7:0] threshold,  // 边缘检测阈值
    output reg [7:0] pixel_out   // 输出像素值
);

// 主要处理逻辑
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pixel_out <= 8'd0;  // 复位时输出黑色
    end else begin
        // 阈值边缘检测算法
        if (pixel_in > threshold) begin
            pixel_out <= 8'hFF;  // 白色 (边缘)
        end else begin
            pixel_out <= 8'h00;  // 黑色 (非边缘)
        end
    end
end

endmodule
```

**功能说明：**
- 实现基于阈值的简单边缘检测
- 处理8位灰度图像数据
- 支持可配置的检测阈值

#### 2.2 图像处理流水线 (`image_processing_pipeline.v`)

```verilog
module image_processing_pipeline(
    input wire clk,
    input wire rst_n,
    input wire [7:0] pixel_in,
    input wire pixel_valid,
    input wire [7:0] threshold,
    input wire [2:0] operation_mode,
    output reg [7:0] pixel_out,
    output reg pixel_out_valid
);

// 内部信号连接
wire [7:0] edge_detected_pixel;
wire [7:0] gaussian_blurred_pixel;
wire [7:0] morphological_processed_pixel;

// 子模块实例化
edge_detector u_edge_detector(
    .clk(clk),
    .rst_n(rst_n),
    .pixel_in(pixel_in),
    .threshold(threshold),
    .pixel_out(edge_detected_pixel)
);

gaussian_filter u_gaussian_filter(
    .clk(clk),
    .rst_n(rst_n),
    .pixel_in(edge_detected_pixel),
    .pixel_valid(pixel_valid),
    .pixel_out(gaussian_blurred_pixel),
    .pixel_out_valid()
);

morphological_processor u_morphological_processor(
    .clk(clk),
    .rst_n(rst_n),
    .pixel_in(gaussian_blurred_pixel),
    .pixel_valid(pixel_valid),
    .pixel_out(morphological_processed_pixel),
    .pixel_out_valid()
);

// 操作模式选择
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pixel_out <= 8'd0;
        pixel_out_valid <= 1'b0;
    end else if (pixel_valid) begin
        case (operation_mode)
            3'b000: begin  // 原始图像
                pixel_out <= pixel_in;
                pixel_out_valid <= 1'b1;
            end
            3'b001: begin  // 边缘检测
                pixel_out <= edge_detected_pixel;
                pixel_out_valid <= 1'b1;
            end
            3'b010: begin  // 高斯模糊
                pixel_out <= gaussian_blurred_pixel;
                pixel_out_valid <= 1'b1;
            end
            3'b011: begin  // 形态学处理
                pixel_out <= morphological_processed_pixel;
                pixel_out_valid <= 1'b1;
            end
            default: begin
                pixel_out <= pixel_in;
                pixel_out_valid <= 1'b1;
            end
        endcase
    end else begin
        pixel_out_valid <= 1'b0;
    end
end

endmodule
```

**功能说明：**
- 集成多个图像处理模块
- 支持多种处理模式选择
- 流水线式处理提高效率

### 3. 顶层模块 (`fpga_top.v`)

```verilog
module fpga_top(
    input wire clk_50m,           // 50MHz主时钟
    input wire rst_n,             // 复位信号
    input wire [7:0] video_data,  // 视频输入数据
    input wire video_de,          // 数据使能信号
    input wire video_hs,          // 水平同步
    input wire video_vs,          // 垂直同步
    input wire [7:0] threshold,   // 处理阈值
    input wire [2:0] mode_select, // 模式选择
    output wire [7:0] video_out,  // 视频输出
    output wire video_out_de,     // 输出使能
    output wire video_out_hs,     // 输出水平同步
    output wire video_out_vs      // 输出垂直同步
);

// 内部信号
wire [7:0] processed_pixel;
wire pixel_valid;

// 图像处理流水线实例
image_processing_pipeline u_image_processor(
    .clk(clk_50m),
    .rst_n(rst_n),
    .pixel_in(video_data),
    .pixel_valid(video_de),
    .threshold(threshold),
    .operation_mode(mode_select),
    .pixel_out(processed_pixel),
    .pixel_out_valid(pixel_valid)
);

// 输出信号赋值
assign video_out = processed_pixel;
assign video_out_de = video_de;
assign video_out_hs = video_hs;
assign video_out_vs = video_vs;

endmodule
```

## 开发环境搭建

### 1. 软件工具要求

#### 1.1 FPGA开发工具链
- **Xilinx Vivado** (推荐版本 2022.1+)
- **Intel Quartus Prime** (如使用Intel FPGA)
- **开源工具**: Yosys + NextPNR (适用于Lattice等FPGA)

#### 1.2 仿真工具
- **ModelSim/QuestaSim**
- **Verilator** (开源替代方案)
- **Icarus Verilog**

#### 1.3 Python开发环境
```bash
# 安装必要的Python包
pip install numpy pytest cocotb
```

### 2. 项目结构组织

```
fpga/
├── src/                    # RTL源代码
│   ├── edge_detector.v
│   ├── gaussian_filter.v
│   ├── morphological_processor.v
│   ├── image_processing_pipeline.v
│   └── fpga_top.v
├── sim/                    # 仿真文件
│   ├── tb_edge_detector.v
│   ├── tb_image_pipeline.v
│   └── wave.do
├── syn/                    # 综合约束文件
│   ├── fpga_top.xdc        # Xilinx约束文件
│   └── fpga_top.sdc        # Intel约束文件
├── scripts/                # 自动化脚本
│   ├── build.tcl          # Vivado构建脚本
│   └── simulate.do        # ModelSim仿真脚本
└── docs/                   # 技术文档
    └── fpga_design_guide.md
```

## 仿真验证

### 1. 测试平台编写

#### 1.1 边缘检测模块测试平台

```verilog
// tb_edge_detector.v
`timescale 1ns/1ps

module tb_edge_detector;
    
    // 测试信号
    reg clk;
    reg rst_n;
    reg [7:0] pixel_in;
    reg [7:0] threshold;
    wire [7:0] pixel_out;
    
    // 被测模块实例
    edge_detector uut (
        .clk(clk),
        .rst_n(rst_n),
        .pixel_in(pixel_in),
        .threshold(threshold),
        .pixel_out(pixel_out)
    );
    
    // 时钟生成
    initial begin
        clk = 0;
        forever #10 clk = ~clk;  // 50MHz时钟
    end
    
    // 测试序列
    initial begin
        // 初始化
        rst_n = 0;
        pixel_in = 0;
        threshold = 128;
        
        // 复位释放
        #100 rst_n = 1;
        
        // 测试用例1: 像素值小于阈值
        pixel_in = 100;
        #20;
        if (pixel_out !== 8'h00) begin
            $display("ERROR: Expected 0x00, got 0x%02x", pixel_out);
        end
        
        // 测试用例2: 像素值大于阈值
        pixel_in = 200;
        #20;
        if (pixel_out !== 8'hFF) begin
            $display("ERROR: Expected 0xFF, got 0x%02x", pixel_out);
        end
        
        // 测试用例3: 像素值等于阈值
        pixel_in = 128;
        #20;
        if (pixel_out !== 8'hFF) begin
            $display("ERROR: Expected 0xFF, got 0x%02x", pixel_out);
        end
        
        $display("测试完成");
        $finish;
    end
    
    // 波形记录
    initial begin
        $dumpfile("edge_detector_tb.vcd");
        $dumpvars(0, tb_edge_detector);
    end
    
endmodule
```

#### 1.2 Python CoCoTB测试

```python
# test_edge_detector.py
import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

@cocotb.test()
async def test_edge_detector_basic(dut):
    """基本边缘检测测试"""
    
    # 启动时钟
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    # 复位序列
    dut.rst_n.value = 0
    dut.pixel_in.value = 0
    dut.threshold.value = 128
    
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # 测试用例1: 像素值小于阈值
    dut.pixel_in.value = 100
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # 等待一个时钟周期
    
    assert dut.pixel_out.value == 0, f"期望输出0，实际输出{dut.pixel_out.value}"
    
    # 测试用例2: 像素值大于阈值
    dut.pixel_in.value = 200
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    assert dut.pixel_out.value == 255, f"期望输出255，实际输出{dut.pixel_out.value}"
    
    dut._log.info("基本边缘检测测试通过")

@cocotb.test()
async def test_edge_detector_threshold_variations(dut):
    """不同阈值测试"""
    
    clock = Clock(dut.clk, 20, units="ns")
    cocotb.start_soon(clock.start())
    
    dut.rst_n.value = 1
    
    # 测试不同阈值设置
    thresholds = [64, 128, 192]
    test_pixels = [50, 100, 150, 200, 250]
    
    for threshold in thresholds:
        dut.threshold.value = threshold
        await RisingEdge(dut.clk)
        
        for pixel in test_pixels:
            dut.pixel_in.value = pixel
            await RisingEdge(dut.clk)
            await RisingEdge(dut.clk)
            
            expected = 255 if pixel > threshold else 0
            assert dut.pixel_out.value == expected, \
                f"阈值{threshold}, 像素{pixel}: 期望{expected}, 实际{dut.pixel_out.value}"
    
    dut._log.info("阈值变化测试通过")
```

### 2. 运行仿真

```bash
# 使用ModelSim运行仿真
vsim -c -do "do simulate.do"

# 使用CoCoTB运行Python测试
make SIM=questa TOPLEVEL_LANG=verilog MODULE=test_edge_detector

# 查看波形
vsim -view edge_detector_tb.vcd
```

## 综合与实现

### 1. 约束文件编写

#### 1.1 Xilinx约束文件 (`fpga_top.xdc`)

```tcl
# 时钟约束
create_clock -period 20.000 -name clk_50m [get_ports clk_50m]

# 输入延迟约束
set_input_delay -clock clk_50m -max 5.0 [get_ports video_*]
set_input_delay -clock clk_50m -min 1.0 [get_ports video_*]

# 输出延迟约束
set_output_delay -clock clk_50m -max 3.0 [get_ports video_out*]
set_output_delay -clock clk_50m -min 0.5 [get_ports video_out*]

# 时序例外
set_false_path -from [get_ports rst_n]

# 面积和功耗优化
set_property SEVERITY {Warning} [get_drc_checks UCIO-1]
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
```

#### 1.2 Intel约束文件 (`fpga_top.sdc`)

```tcl
# 时钟约束
create_clock -period 20.000 -name clk_50m [get_ports clk_50m]

# 输入输出延迟
set_input_delay -clock clk_50m 5.0 [get_ports video_*]
set_output_delay -clock clk_50m 3.0 [get_ports video_out*]

# 多周期路径
set_multicycle_path -setup -from [get_ports rst_n] 2
```

### 2. 综合脚本

#### 2.1 Vivado自动化脚本 (`build.tcl`)

```tcl
# build.tcl - Vivado自动化构建脚本

# 设置项目参数
set project_name "iMato_FPGA"
set part "xc7a35ticsg324-1L"  # 根据实际FPGA型号调整
set src_dir "./src"
set constr_dir "./syn"

# 创建项目
create_project $project_name ./project -part $part -force

# 添加源文件
add_files -norecurse [glob $src_dir/*.v]
add_files -fileset constrs_1 -norecurse $constr_dir/fpga_top.xdc

# 设置顶层模块
set_property top fpga_top [current_fileset]

# 运行综合
launch_runs synth_1 -jobs 4
wait_on_run synth_1

# 运行实现
launch_runs impl_1 -jobs 4
wait_on_run impl_1

# 生成比特流
launch_runs impl_1 -to_step write_bitstream
wait_on_run impl_1

# 导出报告
open_run impl_1
report_timing_summary -file timing_report.txt
report_utilization -file utilization_report.txt

puts "构建完成"
```

#### 2.2 命令行执行

```bash
# 启动Vivado并运行脚本
vivado -mode batch -source build.tcl

# 或者交互式运行
vivado -mode gui
# 在GUI中执行: source build.tcl
```

## 硬件部署与调试

### 1. 比特流烧录

```bash
# 使用Vivado Hardware Manager
open_hw
connect_hw_server
open_hw_target
current_hw_device [get_hw_devices xc7a35t_0]
refresh_hw_device -update_hw_probes false [lindex [get_hw_devices xc7a35t_0] 0]
set_property PROGRAM.FILE {./project/iMato_FPGA.runs/impl_1/fpga_top.bit} [get_hw_devices xc7a35t_0]
program_hw_devices [get_hw_devices xc7a35t_0]
```

### 2. 在线调试

#### 2.1 使用ChipScope/VIO

```verilog
// 添加调试核
ila_0 your_debug_core (
    .clk(clk_50m),
    .probe0(pixel_in),
    .probe1(pixel_out),
    .probe2(threshold)
);
```

#### 2.2 实时监控脚本

```python
# fpga_debug.py
import serial
import numpy as np
import matplotlib.pyplot as plt

class FPGADebugger:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.serial_port = serial.Serial(port, baudrate)
        
    def capture_frame(self, width=640, height=480):
        """捕获一帧处理后的图像"""
        # 发送捕获命令
        self.serial_port.write(b'CAPTURE\n')
        
        # 接收图像数据
        image_data = self.serial_port.read(width * height)
        image_array = np.frombuffer(image_data, dtype=np.uint8)
        return image_array.reshape((height, width))
    
    def set_threshold(self, threshold):
        """设置边缘检测阈值"""
        command = f'THRESHOLD {threshold}\n'.encode()
        self.serial_port.write(command)
    
    def visualize_results(self, original, processed):
        """可视化处理结果"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        ax1.imshow(original, cmap='gray')
        ax1.set_title('原始图像')
        ax2.imshow(processed, cmap='gray')
        ax2.set_title('处理后图像')
        plt.show()

# 使用示例
debugger = FPGADebugger()
original = debugger.capture_frame()
debugger.set_threshold(128)
processed = debugger.capture_frame()
debugger.visualize_results(original, processed)
```

## 性能优化建议

### 1. 资源利用优化

```verilog
// 使用流水线提高吞吐量
module pipelined_multiplier(
    input wire clk,
    input wire rst_n,
    input wire [7:0] a,
    input wire [7:0] b,
    output reg [15:0] result
);

reg [7:0] a_pipe1, a_pipe2;
reg [7:0] b_pipe1, b_pipe2;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        a_pipe1 <= 0;
        a_pipe2 <= 0;
        b_pipe1 <= 0;
        b_pipe2 <= 0;
        result <= 0;
    end else begin
        // 三级流水线
        a_pipe1 <= a;
        a_pipe2 <= a_pipe1;
        b_pipe1 <= b;
        b_pipe2 <= b_pipe1;
        result <= a_pipe2 * b_pipe2;
    end
end

endmodule
```

### 2. 时序优化

```tcl
# 在约束文件中添加时序优化
set_property ASYNC_REG TRUE [get_cells -hierarchical *sync*]
set_multicycle_path -setup -from [get_pins threshold_reg/C] 2
```

## 故障排除

### 1. 常见问题及解决方案

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 综合失败 | 语法错误 | 检查Verilog语法，使用lint工具 |
| 时序违例 | 时钟频率过高 | 降低时钟频率或优化逻辑 |
| 资源不足 | 设计过大 | 优化代码，移除冗余逻辑 |
| 功能错误 | 逻辑设计错误 | 加强仿真验证 |

### 2. 调试技巧

```bash
# 生成详细的综合报告
report_drc -file drc_report.txt
report_timing -max_paths 10 -file timing_paths.txt
report_utilization -file resource_usage.txt

# 使用Vivado Analyzer分析性能瓶颈
start_gui
open_project ./project/iMato_FPGA.xpr
open_run impl_1
show_tool_window {Analysis and Synthesis}
```

## 版本控制与协作

### 1. Git工作流

```bash
# 创建功能分支
git checkout -b feature/fpga-edge-detection

# 提交代码变更
git add .
git commit -m "feat(fpga): 实现边缘检测模块"

# 代码审查后合并
git checkout main
git merge feature/fpga-edge-detection
git push origin main
```

### 2. 文档维护

保持以下文档及时更新：
- RTL设计文档
- 仿真测试报告
- 综合实现报告
- 用户使用手册

---

*本文档最后更新时间：2026年2月27日*
*版本：1.0.0*