# 该脚本用于从 g:\iMato 混合仓库中剥离 OpenMTSciEd 项目并保留提交历史

Write-Host "正在准备 OpenMTSciEd Git 迁移..." -ForegroundColor Green

# 1. 确保安装了 git-filter-repo
if (-not (Get-Command git-filter-repo -ErrorAction SilentlyContinue)) {
    Write-Host "未检测到 git-filter-repo，正在安装..." -ForegroundColor Yellow
    pip install git-filter-repo
}

# 2. 克隆当前仓库到一个临时目录进行过滤（避免破坏原仓库）
$TEMP_DIR = "g:\iMato\OpenMTSciEd_Migration_Temp"
if (Test-Path $TEMP_DIR) {
    Remove-Item -Recurse -Force $TEMP_DIR
}

Write-Host "正在克隆仓库到临时目录..." -ForegroundColor Cyan
git clone g:\iMato $TEMP_DIR
Set-Location $TEMP_DIR

# 3. 执行路径过滤和重命名
Write-Host "正在提取 OpenMTSciEd 目录并重命名为根目录..." -ForegroundColor Cyan
git filter-repo --path OpenMTSciEd/ --path-rename OpenMTSciEd/:./ --force

# 4. 清理不再需要的远程关联
git remote remove origin

Write-Host "迁移完成！" -ForegroundColor Green
Write-Host "新仓库位于: $TEMP_DIR" -ForegroundColor Green
Write-Host "请检查无误后，将其推送到新的 GitHub 仓库。" -ForegroundColor Yellow
