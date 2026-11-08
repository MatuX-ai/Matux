; ============================================================================
; iMato NSIS 安装钩子脚本（v1.0.4 简化版）
; ============================================================================
; 说明：v1.0.4 移除了复杂的 Python 路径输入对话框（NSIS 3.0.4.1 在多字节
;       中文解析上存在回归问题，导致 installer.nsh 解析失败）。
;       Python 检测改为运行时在 Electron 端进行（启动时探测）。
;
;       本文件仅保留 .onInstSuccess 的最小空实现，确保 NSIS 能正常打包。
;       若未来需要恢复安装期 Python 提示，请使用 Unicode ASCII-only 文本并
;       确保文件保存为 UTF-8 with BOM。
; ============================================================================

Unicode true

!include "LogicLib.nsh"

; ----------------------------------------------------------------------------
; Upgrade safety (runs before the old version is uninstalled)
;
; v1.0.4 and earlier shipped backend/ai_service.db inside the install dir.
; New versions keep the database at %APPDATA%\matux-desktop\ai_service.db,
; and the NSIS uninstaller removes the old install dir first - so the backend
; side migration in config/settings.py would be too late. Copy the legacy
; database before the uninstaller runs, only when the user has none yet.
; ----------------------------------------------------------------------------
!macro customInit
  ${If} ${FileExists} "$INSTDIR\resources\backend\ai_service.db"
  ${AndIfNot} ${FileExists} "$APPDATA\matux-desktop\ai_service.db"
    CreateDirectory "$APPDATA\matux-desktop"
    CopyFiles /SILENT "$INSTDIR\resources\backend\ai_service.db" "$APPDATA\matux-desktop"
  ${EndIf}
!macroend

; ----------------------------------------------------------------------------
; 安装成功钩子（最小空实现，v1.0.4）
; Python 检测完全交给 Electron 端的 utils/install-state.js
; ----------------------------------------------------------------------------
Function .onInstSuccess
  ; 静默安装时（/S）不弹窗
  ${IfNot} ${Silent}
    ; 占位提示：安装完成
    ; 注意：v1.0.4 故意使用 ASCII-only 文本，避免 NSIS 多字节解析问题
    MessageBox MB_OK|MB_ICONINFORMATION "iMato Desktop installation complete. Please launch the app to configure Python."
  ${EndIf}
FunctionEnd