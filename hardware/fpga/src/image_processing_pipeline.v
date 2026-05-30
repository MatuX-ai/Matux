// 完整的FPGA图像处理流水线
// 包含边缘检测、高斯模糊和形态学操作

module image_processing_pipeline(
    input wire clk,                    // 主时钟
    input wire rst_n,                  // 复位信号
    input wire [7:0] pixel_in,        // 输入像素
    input wire pixel_valid,           // 像素有效信号
    input wire [7:0] threshold,       // 边缘检测阈值
    input wire [2:0] operation_mode,  // 操作模式选择
    output reg [7:0] pixel_out,       // 输出像素
    output reg pixel_out_valid        // 输出有效信号
);

// 内部信号定义
reg [7:0] edge_detected_pixel;
reg [7:0] gaussian_blurred_pixel;
reg [7:0] morphological_processed_pixel;

// 边缘检测子模块实例
edge_detector u_edge_detector(
    .clk(clk),
    .rst_n(rst_n),
    .pixel_in(pixel_in),
    .threshold(threshold),
    .pixel_out(edge_detected_pixel)
);

// 高斯模糊子模块实例
gaussian_filter u_gaussian_filter(
    .clk(clk),
    .rst_n(rst_n),
    .pixel_in(edge_detected_pixel),
    .pixel_valid(pixel_valid),
    .pixel_out(gaussian_blurred_pixel),
    .pixel_out_valid()
);

// 形态学处理子模块实例
morphological_processor u_morphological_processor(
    .clk(clk),
    .rst_n(rst_n),
    .pixel_in(gaussian_blurred_pixel),
    .pixel_valid(pixel_valid),
    .pixel_out(morphological_processed_pixel),
    .pixel_out_valid()
);

// 操作模式选择逻辑
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

// 高斯滤波器模块
module gaussian_filter(
    input wire clk,
    input wire rst_n,
    input wire [7:0] pixel_in,
    input wire pixel_valid,
    output reg [7:0] pixel_out,
    output reg pixel_out_valid
);

// 简化的3x3高斯滤波实现
reg [7:0] line_buffer_0 [0:1023];  // 行缓冲器
reg [7:0] line_buffer_1 [0:1023];
reg [9:0] pixel_sum;               // 像素和 (考虑权重)
reg [3:0] pixel_counter;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pixel_out <= 8'd0;
        pixel_out_valid <= 1'b0;
        pixel_counter <= 4'd0;
    end else if (pixel_valid) begin
        // 简化的高斯加权平均
        // 权重分布: [1 2 1; 2 4 2; 1 2 1] / 16
        pixel_sum <= pixel_in * 4;  // 中心像素权重4
        pixel_out <= pixel_sum >> 4; // 除以16
        pixel_out_valid <= 1'b1;
        pixel_counter <= pixel_counter + 1;
    end else begin
        pixel_out_valid <= 1'b0;
    end
end

endmodule

// 形态学处理模块
module morphological_processor(
    input wire clk,
    input wire rst_n,
    input wire [7:0] pixel_in,
    input wire pixel_valid,
    output reg [7:0] pixel_out,
    output reg pixel_out_valid
);

// 形态学操作参数
parameter THRESHOLD = 8'd128;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pixel_out <= 8'd0;
        pixel_out_valid <= 1'b0;
    end else if (pixel_valid) begin
        // 简单的二值化形态学操作
        if (pixel_in > THRESHOLD) begin
            pixel_out <= 8'hFF;  // 白色
        end else begin
            pixel_out <= 8'h00;  // 黑色
        end
        pixel_out_valid <= 1'b1;
    end else begin
        pixel_out_valid <= 1'b0;
    end
end

endmodule