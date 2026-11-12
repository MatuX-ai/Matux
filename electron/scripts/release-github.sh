#!/bin/bash
# =============================================================================
# iMato 桌面端 GitHub Release 发布脚本
#
# 用途：把 release/ 下的 electron-builder 三件套（exe / exe.blockmap / latest.yml）
#       发布到 GitHub Releases，并输出公开下载 URL。
#
# 用法：
#   bash electron/scripts/release-github.sh              # 默认 dry-run：只校验，不发布
#   bash electron/scripts/release-github.sh --execute    # 真正执行发布
#   bash electron/scripts/release-github.sh --help
#
# 设计约束：
#   1. **默认不发布**：必须显式 --execute 才会调用 gh release create。
#   2. **三件套校验**：exe / exe.blockmap / latest.yml 必须齐备且 sha512 自洽。
#   3. **门禁耦合**：发布说明仍带 "<!--STATUS-->待 Round 7 门禁放行" 标记时拒绝发布。
#   4. **防错位（Round 4 教训）**：比对「安装包构建时刻对应的 commit」与「目标 tag commit」的差异：
#      - 含运行时源码差异 → 拒绝发布（疑似被 soak 的二进制与被发布的 tag 不是同一份代码）；
#      - 仅打包配置差异 → 逐个核对「工作区版本 vs target 版本」，一致即说明变更已包含在本次构建中、tag 可复现。
#   5. **无 force**：不删除既有 release，不覆盖既有 tag。
#
# 前置条件：
#   - gh CLI 已登录且对目标仓库有 repo 权限（gh auth status）
#   - release/ 下三件套已由 electron-builder 生成并通过 scripts/rename-artifacts.js 校验
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
CYAN=$'\033[0;36m'
NC=$'\033[0m'

VERSION=""
REPO="MatuX-ai/Matux"
NOTES_FILE=""
TARGET=""
EXECUTE=0
ALLOW_PENDING_NOTES=0
ALLOW_STALE_BUILD=0

PENDING_MARKER='<!--STATUS-->待 Round 7 门禁放行'

usage() {
    sed -n '2,32p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

step() { printf '%s==>%s %s\n' "$CYAN" "$NC" "$1"; }
info() { printf '    %s\n' "$1"; }
ok()   { printf '%s  [OK]%s %s\n' "$GREEN" "$NC" "$1"; }
warn() { printf '%s  [WARN]%s %s\n' "$YELLOW" "$NC" "$1"; }
fail() { printf '%s  [FAIL]%s %s\n' "$RED" "$NC" "$1"; exit 1; }

# ---------------------------------------------------------------- 参数解析
while [ $# -gt 0 ]; do
    case "$1" in
        --version)
            VERSION="${2:-}"; shift 2 ;;
        --repo)
            REPO="${2:-}"; shift 2 ;;
        --notes)
            NOTES_FILE="${2:-}"; shift 2 ;;
        --target)
            TARGET="${2:-}"; shift 2 ;;
        --execute)
            EXECUTE=1; shift ;;
        --allow-pending-notes)
            ALLOW_PENDING_NOTES=1; shift ;;
        --allow-stale-build)
            ALLOW_STALE_BUILD=1; shift ;;
        --dry-run)
            EXECUTE=0; shift ;;
        -h|--help)
            usage; exit 0 ;;
        *)
            fail "未知参数：$1（用 --help 查看用法）" ;;
    esac
done

REL_DIR="release"

# ---------------------------------------------------------------- 0. 工具链
step "0/8 检查工具链"

command -v gh >/dev/null 2>&1 || fail "未找到 gh CLI，请先安装 GitHub CLI 并登录（gh auth login）"
command -v node >/dev/null 2>&1 || fail "未找到 node（npm run release:rename 依赖 node）"
command -v npm >/dev/null 2>&1 || fail "未找到 npm"

info "gh:   $(command -v gh)  ($(gh --version | head -n 1))"
info "node: $(command -v node) ($(node --version))"
info "npm:  $(npm --version)"

if ! gh auth status >/dev/null 2>&1; then
    fail "gh CLI 未登录或凭据失效，请先执行 gh auth login"
fi
ok "gh auth status 正常"

# ---------------------------------------------------------------- 1. 仓库可见性
step "1/8 确认目标仓库"

if ! REPO_JSON="$(gh repo view "$REPO" --json name,visibility,defaultBranchRef 2>/dev/null)"; then
    fail "无法访问仓库 $REPO（权限不足或仓库不存在）"
fi
VISIBILITY="$(printf '%s' "$REPO_JSON" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>console.log(JSON.parse(s).visibility))')"
DEFAULT_BRANCH="$(printf '%s' "$REPO_JSON" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const j=JSON.parse(s);console.log((j.defaultBranchRef&&j.defaultBranchRef.name)||"-")})')"
ok "仓库 $REPO 存在，visibility=$VISIBILITY，默认分支=$DEFAULT_BRANCH"
if [ "$VISIBILITY" = "PUBLIC" ]; then
    info "仓库为 PUBLIC：Release 资产下载链接公开，任何人可直接访问，无需登录 GitHub。"
else
    info "仓库为 PRIVATE：Release 资产下载需登录 GitHub 并具备仓库读权限，官网链接须提示用户登录。"
fi

# ---------------------------------------------------------------- 2. 版本与三件套路径
step "2/8 解析版本与三件套路径"

YML="$REL_DIR/latest.yml"
if [ ! -f "$YML" ]; then
    fail "$YML 不存在：请先在 electron/ 下执行 npm run dist（或 release 构建）"
fi

if [ -z "$VERSION" ]; then
    VERSION="$(sed -n 's/^version:[[:space:]]*//p' "$YML" | tr -d '\r' | head -n 1)"
    [ -n "$VERSION" ] || fail "无法从 $YML 解析 version，请用 --version 显式指定"
    info "version 未显式指定，从 $YML 解析得到：$VERSION"
else
    info "version（显式指定）：$VERSION"
fi

EXE="$REL_DIR/iMato-Setup-$VERSION.exe"
BLOCKMAP="$EXE.blockmap"

[ -f "$EXE" ]       || fail "$EXE 不存在"
[ -f "$BLOCKMAP" ]  || fail "$BLOCKMAP 不存在"
[ -f "$YML" ]       || fail "$YML 不存在"
ok "三件套齐备：$(basename "$EXE") / $(basename "$BLOCKMAP") / $(basename "$YML")"

# ---------------------------------------------------------------- 3. latest.yml 自洽
step "3/8 校验 latest.yml 自洽性"

YML_VERSION="$(sed -n 's/^version:[[:space:]]*//p' "$YML" | tr -d '\r' | head -n 1)"
YML_PATH="$(sed -n 's/^path:[[:space:]]*//p' "$YML" | tr -d '\r' | head -n 1)"
YML_SHA="$(sed -n 's/^sha512:[[:space:]]*//p' "$YML" | tr -d '\r' | head -n 1)"
YML_SIZE="$(sed -n 's/^[[:space:]]*size:[[:space:]]*//p' "$YML" | tr -d '\r' | head -n 1)"

[ "$YML_VERSION" = "$VERSION" ] \
    || fail "latest.yml version=$YML_VERSION 与目标版本 $VERSION 不一致"
[ "$YML_PATH" = "iMato-Setup-$VERSION.exe" ] \
    || fail "latest.yml path=$YML_PATH 与安装包名 iMato-Setup-$VERSION.exe 不一致（命名须为连字符）"
ok "latest.yml version/path 与安装包名一致"

# ---------------------------------------------------------------- 4. sha512 校验
step "4/8 校验 sha512（scripts/rename-artifacts.js）"

if ! (cd electron && npm run release:rename); then
    fail "sha512 校验失败：electron/scripts/rename-artifacts.js 报告不匹配"
fi
ok "rename-artifacts.js 校验通过（strict 模式，sha512/size/path 三项自洽）"

CALC_SHA="$(node -e 'const c=require("crypto"),f=require("fs");process.stdout.write(c.createHash("sha512").update(f.readFileSync(process.argv[1])).digest("base64"))' "$EXE")"
CALC_SIZE="$(wc -c < "$EXE" | tr -d '[:space:]')"
[ "$CALC_SHA" = "$YML_SHA" ] \
    || fail "磁盘 sha512 与 latest.yml 不一致（磁盘=$CALC_SHA / yml=$YML_SHA）"
[ "$CALC_SIZE" = "$YML_SIZE" ] \
    || fail "磁盘 size 与 latest.yml 不一致（磁盘=$CALC_SIZE / yml=$YML_SIZE）"
ok "磁盘 sha512/size 与 latest.yml 完全一致（size=$CALC_SIZE）"

# ---------------------------------------------------------------- 5. 发布说明与门禁
step "5/8 校验发布说明与门禁标记"

if [ -z "$NOTES_FILE" ]; then
    NOTES_FILE="tmp/release-$VERSION-notes.md"
fi
[ -f "$NOTES_FILE" ] || fail "$NOTES_FILE 不存在（可用 --notes 指定）"
ok "发布说明：$NOTES_FILE"

if grep -qF "$PENDING_MARKER" "$NOTES_FILE"; then
    if [ "$ALLOW_PENDING_NOTES" -eq 1 ]; then
        warn "发布说明仍带未放行标记（已用 --allow-pending-notes 放行）"
    else
        fail "发布说明仍带 '$PENDING_MARKER' 标记：Round 7 门禁尚未放行，拒绝发布（如确需放行请加 --allow-pending-notes）"
    fi
else
    ok "发布说明无未放行标记（门禁已放行）"
fi

# ---------------------------------------------------------------- 6. 已存在性与 commit 对齐
step "6/8 检查既有 release 与 commit 对齐"

TAG="v$VERSION"
if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
    fail "Release $TAG 已存在：脚本不做覆盖/force，请改用 gh release upload 增量补传"
fi
ok "Release $TAG 尚未创建"

if [ -z "$TARGET" ]; then
    TARGET="$(git rev-parse "origin/$DEFAULT_BRANCH" 2>/dev/null || true)"
    [ -n "$TARGET" ] || fail "无法解析 origin/$DEFAULT_BRANCH，请用 --target 显式指定 commit"
    info "target 未显式指定，取 origin/$DEFAULT_BRANCH = ${TARGET:0:7}"
else
    info "target（显式指定）：${TARGET:0:7}"
fi

COMMIT_TIME="$(git show -s --format=%cI "$TARGET" 2>/dev/null || true)"
[ -n "$COMMIT_TIME" ] || fail "无法读取 commit $TARGET 的提交时间"

# 「二进制 ↔ tag」等价性判定（Round 4 教训）：
#   取安装包构建时刻之前最后一个 commit 作为「二进制对应的代码状态」，
#   再与 target 比对差异文件：仅打包配置 / 文档变更 → 放行；含运行时源码变更 → 拦截。
EXE_MTIME="$(stat -c %Y "$EXE" 2>/dev/null || echo 0)"
EXE_MTIME_ISO="$(date -d "@$EXE_MTIME" +%Y-%m-%dT%H:%M:%S 2>/dev/null || echo '')"
BUILD_COMMIT="$(git rev-list -1 --before="$EXE_MTIME_ISO" HEAD 2>/dev/null || true)"

if [ -z "$BUILD_COMMIT" ]; then
    fail "无法定位安装包构建时刻（$EXE_MTIME_ISO）对应的 commit，无法校验 tag 与二进制等价性"
fi

info "安装包构建时刻：$EXE_MTIME_ISO"
info "二进制对应 commit：${BUILD_COMMIT:0:7}  $(git show -s --format=%s "$BUILD_COMMIT")"
info "目标 tag commit：${TARGET:0:7}  $(git show -s --format=%s "$TARGET" 2>/dev/null || echo '-')"

DIFF_FILES="$(git diff --name-only "$BUILD_COMMIT" "$TARGET" 2>/dev/null || true)"
DIFF_NONEMPTY="$(printf '%s' "$DIFF_FILES" | tr -d '[:space:]')"

if [ -z "$DIFF_NONEMPTY" ]; then
    ok "tag commit 与二进制对应 commit 完全一致（${BUILD_COMMIT:0:7}）"
else
    RUNTIME_RE='\.(py|pyi|ts|tsx|js|jsx|mjs|cjs|vue|html|css|scss|json)$'
    CONFIG_RE='(^|/)[^/]+\.spec$|^electron/electron-builder\.yml$|^electron/package\.json$'

    RUNTIME_DIFF="$(printf '%s\n' "$DIFF_FILES" | grep -E "$RUNTIME_RE" || true)"
    CONFIG_DIFF="$(printf '%s\n' "$DIFF_FILES" | grep -E "$CONFIG_RE" || true)"
    OTHER_DIFF="$(printf '%s\n' "$DIFF_FILES" | grep -Ev "$RUNTIME_RE|$CONFIG_RE" || true)"

    if [ -n "$(printf '%s' "$RUNTIME_DIFF" | tr -d '[:space:]')" ]; then
        if [ "$ALLOW_STALE_BUILD" -eq 1 ]; then
            warn "tag commit 与二进制存在**运行时源码**差异（已用 --allow-stale-build 放行）："
            printf '        - %s\n' $RUNTIME_DIFF
        else
            fail "tag commit 与二进制存在**运行时源码**差异（疑似 tag 与被发布二进制错位，Round 4 教训）："
            printf '        - %s\n' $RUNTIME_DIFF
            fail "确认无误可加 --allow-stale-build 强制放行"
        fi
    else
        ok "无运行时源码差异（tag 与二进制在代码层等价）"
    fi

    # 打包配置：核对「工作区版本」与「target 版本」
    #   一致 → 构建时用的就是该配置，tag 可复现；
    #   不一致 → 该配置变更未包含在本次二进制。
    if [ -n "$(printf '%s' "$CONFIG_DIFF" | tr -d '[:space:]')" ]; then
        for f in $CONFIG_DIFF; do
            WT_HASH="$(git hash-object "$f" 2>/dev/null || echo '')"
            TG_HASH="$(git rev-parse "$TARGET:$f" 2>/dev/null || echo '')"
            if [ -n "$TG_HASH" ] && [ "$WT_HASH" = "$TG_HASH" ]; then
                ok "打包配置 $f：工作区版本 == $TARGET 版本（变更已包含在本次构建中，tag 可复现）"
            else
                warn "打包配置 $f：工作区版本 != $TARGET 版本（该配置变更**未**包含在本次二进制，tag 不可复现）"
            fi
        done
    fi

    if [ -n "$(printf '%s' "$OTHER_DIFF" | tr -d '[:space:]')" ]; then
        info "其余非运行时差异（不影响二进制内容）："
        printf '        - %s\n' $OTHER_DIFF
    fi
fi

# ---------------------------------------------------------------- 7. 发布
step "7/8 创建 GitHub Release"

TITLE="iMato Desktop v$VERSION"
CREATE_CMD=(gh release create "$TAG" "$EXE" "$BLOCKMAP" "$YML"
            --repo "$REPO"
            --title "$TITLE"
            --notes-file "$NOTES_FILE"
            --target "$TARGET"
            --latest)

if [ "$EXECUTE" -eq 0 ]; then
    warn "DRY-RUN：未执行发布（加 --execute 才会真正创建 Release）"
    info "将执行："
    printf '        %s\n' "${CREATE_CMD[*]}"
    info "下载页（发布后）：https://github.com/$REPO/releases/tag/$TAG"
    step "8/8 输出 asset URL（dry-run 跳过）"
    info "dry-run 结束：无任何远端写操作。"
    exit 0
fi

info "上传三件套到 $REPO 的 Release $TAG（安装包约 ${CALC_SIZE} 字节，可能需要数分钟）..."
"${CREATE_CMD[@]}"
ok "Release $TAG 创建成功"

# ---------------------------------------------------------------- 8. 输出 URL
step "8/8 输出 asset URL"

RELEASE_URL="$(gh release view "$TAG" --repo "$REPO" --json url --jq '.url')"
info "下载页：$RELEASE_URL"
printf '    %s\n' "--- asset 下载 URL ---"
gh release view "$TAG" --repo "$REPO" --json assets --jq '.assets[] | .url'
ok "发布流程完成"
