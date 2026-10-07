# 截取指定窗口的截图
param(
    [string]$WindowTitle = "MatuX Design System",
    [string]$OutputPath = "g:\iMato\screenshots\electron-main-window.png"
)

# 确保输出目录存在
$dir = Split-Path -Path $OutputPath -Parent
if (!(Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Drawing;
using System.Drawing.Imaging;

public class WindowCapture {
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern bool GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern int GetWindowTextLength(IntPtr hWnd);

    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }
}
"@ -ReferencedAssemblies System.Drawing,System.Windows.Forms

# 先枚举所有顶级窗口，找到标题匹配的
$foundHandle = [IntPtr]::Zero
$foundTitle = ""

$enumProc = [WindowCapture+EnumWindowsProc]{
    param($hWnd, $lParam)
    if ([WindowCapture]::IsWindowVisible($hWnd)) {
        $len = [WindowCapture]::GetWindowTextLength($hWnd)
        if ($len -gt 0) {
            $sb = New-Object System.Text.StringBuilder ($len + 1)
            [void][WindowCapture]::GetWindowText($hWnd, $sb, $sb.Capacity)
            $title = $sb.ToString()
            if ($title -like "*$WindowTitle*") {
                $script:foundHandle = $hWnd
                $script:foundTitle = $title
                return $false  # 找到后停止枚举
            }
        }
    }
    return $true
}

[void][WindowCapture]::EnumWindows($enumProc, [IntPtr]::Zero)

if ($foundHandle -eq [IntPtr]::Zero) {
    Write-Host "未找到标题包含 '$WindowTitle' 的窗口，尝试按进程查找..."
    # 备用方法：通过进程查找
    $procs = Get-Process | Where-Object { $_.MainWindowTitle -like "*$WindowTitle*" }
    if ($procs) {
        $procs | ForEach-Object { Write-Host "  进程: PID=$($_.Id), Title='$($_.MainWindowTitle)'" }
    } else {
        Write-Host "  也没有找到匹配的进程"
    }
    exit 1
}

Write-Host "找到窗口: '$foundTitle' (Handle: $foundHandle)"

# 获取窗口尺寸
$rect = New-Object WindowCapture+RECT
[void][WindowCapture]::GetWindowRect($foundHandle, [ref]$rect)

$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
Write-Host "窗口位置: Left=$($rect.Left), Top=$($rect.Top), Width=$width, Height=$height"

if ($width -le 0 -or $height -le 0) {
    Write-Host "窗口尺寸无效，尝试截取主屏幕"
    # 截取主屏幕
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $width = $screen.Width
    $height = $screen.Height
    $rect.Left = 0
    $rect.Top = 0
}

# 截取窗口区域
$bmp = New-Object System.Drawing.Bitmap $width, $height
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$gfx.CopyFromScreen($rect.Left, $rect.Top, 0, 0, (New-Object System.Drawing.Size $width, $height))
$bmp.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
$gfx.Dispose()
$bmp.Dispose()

Write-Host "截图已保存: $OutputPath"
Write-Host "文件大小: $((Get-Item $OutputPath).Length) bytes"
