# CircuitJS1 第三方组件说明（NOTICE）

本目录是第三方开源项目 **CircuitJS1（电路仿真器）** 的 Web 产物，随 MatuX 桌面端离线分发，
用于「电路虚拟实验」页面（/circuit-lab）的元件拖拽与实时仿真能力。

## 来源

| 项 | 内容 |
| --- | --- |
| 上游项目 | CircuitJS1（Circuit Simulator） |
| 源码仓库 | https://github.com/sharpie7/circuitjs1 |
| 产物来源 | https://www.falstad.com/circuit/ 官方托管的已编译 Web 版本（circuitjs116） |
| 获取日期 | 2026-11-09 |
| 版本标识 | 产物目录名 `circuitjs116`；主包 `circuitjs-D4ylC0oc.js`（1,186,510 B） |
| 许可证 | GPL-2.0（全文见同目录 `LICENSE`） |

## 目录内容

```
circuitjs1.html                      入口页（已清理外链）
iframe.html                          右侧信息栏（显示选中元件的数值）
circuitjs116/circuitjs-*.js          编译后的仿真内核（Vite/ES module）
circuitjs116/circuitjs-*.css         样式
circuitjs116/font/                   图标字体（fontello）
circuitjs116/images/                 菜单栏背景图
circuitjs116/setuplist.txt           示例电路清单
circuitjs116/circuits/*.txt          367 个示例电路（欧姆定律、RC/RL、滤波器等）
circuitjs116/locale/locale_zh.txt    简体中文界面语言包
```

## 本地修改点（相对上游产物）

1. 删除 `circuitjs1.html` 与 `iframe.html` 中的第三方外链脚本：
   - `https://www.dropbox.com/static/api/2/dropins.js`（Dropbox 导入/导出，离线不可用）
   - `https://static.cloudflareinsights.com/beacon.min.js`（访问统计，隐私与离线均不需要）
2. 删除 `circuitjs1.html` 中指向 `/circuit/manifest.json` 的 PWA manifest 链接（绝对路径不适用于应用内相对部署）。
3. 补齐离线运行所需资源：`iframe.html`、`circuitjs116/images/hborder.png`、`circuitjs116/locale/locale_zh.txt`。

> 仿真内核 `circuitjs-D4ylC0oc.js` 未做任何修改（未改源码、未改数值模型）。
> 因此电路中电压/电流等数值与上游 CircuitJS1 完全一致，不存在 MatuX 自定义的近似或硬编码。

## 合规说明

- GPL-2.0 允许在闭源应用中分发，前提是随附完整许可证文本、保留版权声明，并可获取对应源码。
- 本目录已随附 `LICENSE`（GPL-2.0 全文）与本 NOTICE，应用内「电路虚拟实验」页提供「开源许可」入口展示上述信息与源码地址。
- 仿真内核为独立 iframe 加载的独立进程内页面，与 MatuX 业务代码无编译期耦合。
