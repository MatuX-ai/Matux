// FPGA顶层模块
// 集成所有图像处理组件

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

// FPGA配置和约束文件模板
/*
// 时钟约束
create_clock -period 20.000 -name clk_50m [get_ports clk_50m]

// 输入延迟约束
set_input_delay -clock clk_50m -max 5.0 [get_ports video_*]
set_input_delay -clock clk_50m -min 1.0 [get_ports video_*]

// 输出延迟约束
set_output_delay -clock clk_50m -max 3.0 [get_ports video_out*]
set_output_delay -clock clk_50m -min 0.5 [get_ports video_out*]

// 时序例外
set_false_path -from [get_ports rst_n]
*/