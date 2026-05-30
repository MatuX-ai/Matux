// FPGA边缘检测模块
// 实现基本的阈值边缘检测算法

module edge_detector(
    input wire clk,              // 时钟信号
    input wire rst_n,            // 异步复位信号 (低电平有效)
    input wire [7:0] pixel_in,   // 输入像素值 (8位灰度)
    input wire [7:0] threshold,  // 边缘检测阈值
    output reg [7:0] pixel_out   // 输出像素值
);

// 主要处理逻辑
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // 复位状态下输出黑色
        pixel_out <= 8'd0;
    end else begin
        // 边缘检测逻辑：大于阈值输出白色，否则输出黑色
        if (pixel_in > threshold) begin
            pixel_out <= 8'hFF;  // 白色
        end else begin
            pixel_out <= 8'h00;  // 黑色
        end
    end
end

endmodule