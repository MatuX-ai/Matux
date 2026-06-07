/**
 * MatuX Electron UI 模块统一导出
 *
 * @deprecated 请使用 src/ui/index.js
 */

// 重新导出到新位置（向后兼容）
const ui = require('../src/ui');

module.exports = ui;
