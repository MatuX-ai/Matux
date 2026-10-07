Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$titlePattern = '*MatuX Design System*'
$outPath = 'g:\iMato\screenshots\electron-login-page.png'

if (-not (Test-Path 'g:\iMato\screenshots')) {
    New-Item -ItemType Directory -Path 'g:\iMato\screenshots' -Force | Out-Null
}

# 枚举所有顶级窗口
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;
public class WinEnum {
    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")]
    public static extern int GetWindowTextLength(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")]
    public static extern bool GetClientRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")]
    public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdcBlt, uint nFlags);
    [DllImport("user32.dll")]
    public static extern IntPtr GetDC(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);
    [DllImport("gdi32.dll")]
    public static extern bool BitBlt(IntPtr hdcDest, int xDest, int yDest, int width, int height, IntPtr hdcSrc, int xSrc, int ySrc, int rop);
    [DllImport("user32.dll")]
    public static extern IntPtr GetWindowDC(IntPtr hWnd);
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    public static List<IntPtr> hWnds = new List<IntPtr>();
    public static List<string> titles = new List<string>();
    public static IntPtr found = IntPtr.Zero;
    public static string foundTitle = null;
    public static void Find(string pattern) {
        hWnds.Clear(); titles.Clear(); found = IntPtr.Zero; foundTitle = null;
        EnumWindows((h, l) => {
            if (!IsWindowVisible(h)) return true;
            int len = GetWindowTextLength(h);
            if (len <= 0) return true;
            StringBuilder sb = new StringBuilder(len + 1);
            GetWindowText(h, sb, sb.Capacity);
            string t = sb.ToString();
            hWnds.Add(h); titles.Add(t);
            if (t.IndexOf(pattern, StringComparison.OrdinalIgnoreCase) >= 0) {
                found = h; foundTitle = t;
            }
            return true;
        }, IntPtr.Zero);
    }
}
"@

[WinEnum]::Find('MatuX Design System')

Write-Host ('Found window: ' + [WinEnum]::foundTitle)
Write-Host ('Handle: ' + [WinEnum]::found)

if ([WinEnum]::found -eq [IntPtr]::Zero) {
    # 输出所有可见窗口供调试
    Write-Host '--- Visible Windows ---'
    for ($i = 0; $i -lt [WinEnum]::hWnds.Count; $i++) {
        Write-Host ([WinEnum]::hWnds[$i].ToString() + ' :: ' + [WinEnum]::titles[$i])
    }
    exit 1
}

$h = [WinEnum]::found
$rect = New-Object WinEnum+RECT
[void][WinEnum]::GetWindowRect($h, [ref]$rect)
$w = $rect.Right - $rect.Left
$ht = $rect.Bottom - $rect.Top
Write-Host ('Window size: ' + $w + 'x' + $ht + '  at (' + $rect.Left + ',' + $rect.Top + ')')

if ($w -le 0 -or $ht -le 0) { Write-Host 'Invalid window size'; exit 2 }

$bmp = New-Object System.Drawing.Bitmap $w, $ht
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $gfx.GetHdc()
# PW_RENDERFULLCONTENT = 0x00000002, helps with hardware-accelerated windows
[void][WinEnum]::PrintWindow($h, $hdc, 2)
$gfx.ReleaseHdc($hdc)
$gfx.Dispose()
$bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Host ('Saved: ' + $outPath)
