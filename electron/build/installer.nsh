; ============================================================================
; iMato NSIS 安装钩子脚本
; ============================================================================
; 说明：v1.0.4 移除了复杂的 Python 路径输入对话框（NSIS 3.0.4.1 在多字节
;       中文解析上存在回归问题，导致 installer.nsh 解析失败）。
;       Python 检测改为运行时在 Electron 端进行（启动时探测）。
;
;       【1.0.5 修复 P0 升级丢库】
;       旧实现在 customInit 里用 "$APPDATA\matux-desktop" 作为迁移目标。
;       但旧安装若是 per-machine（HKLM 注册），electron-builder 的
;       setInstallModePerAllUsers 会执行 SetShellVarContext all —— 此时
;       $APPDATA 变成了 C:\ProgramData（公共 AppData），旧库被复制到
;       C:\ProgramData\matux-desktop\ai_service.db，而应用是以当前用户身份
;       启动、只读 %APPDATA%\matux-desktop，于是"迁移成功但数据丢失"。
;       现在一律用 $PROFILE\AppData\Roaming 拼用户级路径（不受 shell 上下文
;       影响），并额外在 $COMMONAPPDATA 留一份兜底暂存（后端启动时也会读）。
;
;       保持：所有运行时字符串为 ASCII-only（规避 NSIS 多字节解析问题），
;       注释允许中文；文件保存为 UTF-8 with BOM。
; ============================================================================

Unicode true

!include "LogicLib.nsh"

; ----------------------------------------------------------------------------
; 迁移诊断变量（顶层声明，避免在宏内 Var 导致重复定义）
;
; 注意：electron-builder 会先用 BUILD_UNINSTALLER 定义编译一遍卸载器。
;       卸载器阶段不会插入 customInit，若仍声明这些变量会触发
;       NSIS "warning 6001: Variable not referenced or never set"，
;       而 electron-builder 把 NSIS warning 视为构建错误。
;       因此 Var 声明与迁移宏整体只在 installer 阶段编译。
; ----------------------------------------------------------------------------
!ifndef BUILD_UNINSTALLER
Var imatoMigLogHandle
Var imatoMigSource
!endif

!define IMATO_MIGRATION_LOG "$TEMP\imato-installer-migration.log"

; ----------------------------------------------------------------------------
; 追加一行迁移日志（失败不抛出，避免影响安装）
; ----------------------------------------------------------------------------
!ifndef BUILD_UNINSTALLER
!macro imatoLog TEXT
  ClearErrors
  FileOpen $imatoMigLogHandle "${IMATO_MIGRATION_LOG}" a
  ${IfNot} ${Errors}
    FileWrite $imatoMigLogHandle "${TEXT}$\r$\n"
    FileClose $imatoMigLogHandle
  ${EndIf}
!macroend

; ----------------------------------------------------------------------------
; 旧库迁移主体（在 customInit 中插入执行）
;
; 执行时机：electron-builder 模板 installer.nsi 的 .onInit 里
;   initMultiUser（还原 $INSTDIR / 设置 shell 上下文）
;   -> customInit（本宏，此时 check64BitAndSetRegView 已执行，注册表视图正确）
;   -> 安装 Section 内 uninstallOldVersion（旧卸载器删除旧安装目录）
; 因此本宏运行时旧库仍在磁盘上，必须在此之前完成复制。
; ----------------------------------------------------------------------------
!macro imatoMigrateLegacyDb
  !insertmacro imatoLog "---- iMato installer legacy-db migration ----"
  !insertmacro imatoLog "INSTDIR=$INSTDIR"
  !insertmacro imatoLog "APPDATA=$APPDATA"
  !insertmacro imatoLog "PROFILE=$PROFILE"

  ; 用户级目标（应用实际读取的路径）：%APPDATA%\matux-desktop\ai_service.db
  ; 注意：不能用 $APPDATA（per-machine 安装时它等于 C:\ProgramData）
  StrCpy $R0 "$PROFILE\AppData\Roaming\matux-desktop\ai_service.db"

  ${If} ${FileExists} "$R0"
    !insertmacro imatoLog "SKIP: user database already exists -> $R0"
  ${Else}
    StrCpy $imatoMigSource ""

    ; 候选 1：当前 $INSTDIR（initMultiUser 已按旧安装注册表还原）
    ${If} ${FileExists} "$INSTDIR\resources\backend\ai_service.db"
      StrCpy $imatoMigSource "$INSTDIR\resources\backend\ai_service.db"
    ${EndIf}

    ; 候选 2：HKCU 里记录的上一次安装位置
    ${If} $imatoMigSource == ""
      ReadRegStr $R1 HKCU "${INSTALL_REGISTRY_KEY}" InstallLocation
      !insertmacro imatoLog "HKCU InstallLocation=$R1"
      ${If} $R1 != ""
        ${If} ${FileExists} "$R1\resources\backend\ai_service.db"
          StrCpy $imatoMigSource "$R1\resources\backend\ai_service.db"
        ${EndIf}
      ${EndIf}
    ${EndIf}

    ; 候选 3：HKLM 里记录的上一次安装位置（per-machine 老安装）
    ${If} $imatoMigSource == ""
      ReadRegStr $R1 HKLM "${INSTALL_REGISTRY_KEY}" InstallLocation
      !insertmacro imatoLog "HKLM InstallLocation=$R1"
      ${If} $R1 != ""
        ${If} ${FileExists} "$R1\resources\backend\ai_service.db"
          StrCpy $imatoMigSource "$R1\resources\backend\ai_service.db"
        ${EndIf}
      ${EndIf}
    ${EndIf}

    ; 候选 4：两种常见默认安装目录（注册表项缺失/改名时兜底）
    ${If} $imatoMigSource == ""
      ${If} ${FileExists} "$LOCALAPPDATA\Programs\iMato\resources\backend\ai_service.db"
        StrCpy $imatoMigSource "$LOCALAPPDATA\Programs\iMato\resources\backend\ai_service.db"
      ${ElseIf} ${FileExists} "$PROGRAMFILES64\iMato\resources\backend\ai_service.db"
        StrCpy $imatoMigSource "$PROGRAMFILES64\iMato\resources\backend\ai_service.db"
      ${ElseIf} ${FileExists} "$PROGRAMFILES\iMato\resources\backend\ai_service.db"
        StrCpy $imatoMigSource "$PROGRAMFILES\iMato\resources\backend\ai_service.db"
      ${EndIf}
    ${EndIf}

    ${If} $imatoMigSource == ""
      !insertmacro imatoLog "RESULT=no-legacy-database-found"
    ${Else}
      !insertmacro imatoLog "SOURCE=$imatoMigSource"

      ; 主目标：当前用户的 Roaming（应用读取位置）
      CreateDirectory "$PROFILE\AppData\Roaming\matux-desktop"
      CopyFiles /SILENT "$imatoMigSource" "$PROFILE\AppData\Roaming\matux-desktop"
      ${If} ${FileExists} "$R0"
        !insertmacro imatoLog "RESULT=ok user-db-created=$R0"
      ${Else}
        !insertmacro imatoLog "RESULT=failed cannot-copy-to=$R0"
      ${EndIf}

      ; 兜底暂存：公共 ProgramData（per-machine / 提权到其他管理员账户时，
      ; 用户 Roaming 可能是管理员的目录；后端启动时会再读一次这里）。
      ; 注：NSIS 3.0.4.1 没有 $COMMONAPPDATA 常量，用环境变量 ProgramData 取值。
      ReadEnvStr $R2 "ProgramData"
      ${If} $R2 != ""
        ${IfNot} ${FileExists} "$R2\matux-desktop\ai_service.db"
          CreateDirectory "$R2\matux-desktop"
          CopyFiles /SILENT "$imatoMigSource" "$R2\matux-desktop"
          ${If} ${FileExists} "$R2\matux-desktop\ai_service.db"
            !insertmacro imatoLog "STAGED=$R2\matux-desktop\ai_service.db"
          ${EndIf}
        ${EndIf}
      ${EndIf}
    ${EndIf}
  ${EndIf}
!macroend

; ----------------------------------------------------------------------------
; 安装初始化钩子：在旧版本卸载器执行前完成旧库迁移
; ----------------------------------------------------------------------------
!macro customInit
  !insertmacro imatoMigrateLegacyDb
!macroend
!endif ; !ifndef BUILD_UNINSTALLER

; ----------------------------------------------------------------------------
; 安装成功钩子（最小空实现）
; Python 检测完全交给 Electron 端的 utils/install-state.js
; ----------------------------------------------------------------------------
Function .onInstSuccess
  ; 静默安装时（/S）不弹窗
  ${IfNot} ${Silent}
    ; 注意：v1.0.4 故意使用 ASCII-only 文本，避免 NSIS 多字节解析问题
    MessageBox MB_OK|MB_ICONINFORMATION "iMato Desktop installation complete. Please launch the app to configure Python."
  ${EndIf}
FunctionEnd
