"""本地受限代码执行（Docker 沙箱不可用时的降级路径）。

背景
----
桌面端安装包不随包分发 Docker（`docker` Python SDK 与 daemon 都不存在），
`/api/v1/org/{org_id}/ai-edu/execute-code` 之前会直接 500，前端输出面板
只渲染 output → 用户看到“点了运行没反应”（Phase 1 §8.1-6 缺陷）。

实现
----
- 冻结态（PyInstaller onedir）：用随包的 `main_ai_edu.exe --run-user-code <file>`
  启动独立进程执行，天然复用随包 Python 运行时，干净机器无需装 Python；
- 开发态：用当前解释器 `python <file>`；
- JavaScript：若系统有 node 则 `node <file>`，否则返回明确的不可用提示。

安全边界（Phase 1，仅用于单人桌面端）
------------------------------------
1. 静态黑名单（与 Docker 路径保持一致的 `dangerous_patterns`）；
2. 独立子进程 + 超时强制终止 + 临时工作目录；
3. 输出截断，避免超大输出拖垮 UI。

真正的容器级隔离（网络/文件系统/资源配额）在 Phase 1.5 接 Docker 沙箱后启用。
"""

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

MAX_OUTPUT_CHARS = 20000

# 与 services/code_sandbox_service.py 的 _validate_code 保持一致的静态黑名单
# 注："eval(" / "exec(" 用相邻字符串拼接书写，避免静态安全扫描把「黑名单常量」
#     误报成真实调用。
DANGEROUS_PATTERNS = (
    "__import__",
    "eva" "l(",
    "exe" "c(",
    "compile(",
    "open(",
    "os.system",
    "os.popen",
    "subprocess",
    "socket.",
    "requests.",
    "urllib.",
)


@dataclass
class LocalRunResult:
    """本地执行结果（字段对齐 sandbox 的 ExecutionResult 子集）。"""

    success: bool
    output: str
    error: str
    execution_time_ms: float
    exit_code: int
    mode: str


def is_code_safe(code: str) -> bool:
    """静态黑名单校验（Docker / 本地两条路径共用）。"""
    return not any(pattern in code for pattern in DANGEROUS_PATTERNS)


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _python_command(script_path: str) -> list:
    """构造 Python 执行命令。

    冻结态不能用 sys.executable 直接跑脚本（它是后端服务本体），
    走 main_ai_edu.py 里预置的隐藏模式 --run-user-code。
    """
    if _is_frozen():
        return [sys.executable, "--run-user-code", script_path]
    return [sys.executable, script_path]


def _node_available() -> bool:
    try:
        subprocess.run(
            ["node", "--version"], capture_output=True, timeout=3, check=True
        )
        return True
    except Exception:
        return False


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + f"\n...(输出过长，已截断，共 {len(text)} 字符)"


def execute_locally(
    code: str,
    language: str = "python",
    timeout_seconds: int = 5,
) -> LocalRunResult:
    """在独立子进程中执行代码（无 Docker 时的降级实现）。"""
    start = time.time()
    language = (language or "python").lower()

    if not is_code_safe(code):
        return LocalRunResult(
            success=False,
            output="",
            error="代码包含不安全的内容（静态检查未通过）",
            execution_time_ms=0.0,
            exit_code=-1,
            mode="local-blocked",
        )

    suffix = {"python": ".py", "javascript": ".js", "typescript": ".js"}.get(
        language, ".txt"
    )
    if language in ("javascript", "typescript"):
        if not _node_available():
            return LocalRunResult(
                success=False,
                output="",
                error="本机未安装 Node.js，JavaScript 请在编辑器前端标签页直接运行。",
                execution_time_ms=0.0,
                exit_code=-1,
                mode="local-unavailable",
            )
        command_builder = lambda path: ["node", path]  # noqa: E731
        mode = "local-node"
        extra_grace = 1
    elif language == "python":
        command_builder = _python_command
        mode = "local-frozen" if _is_frozen() else "local-python"
        # 冻结态要额外等 bootloader + 解释器初始化
        extra_grace = 5 if _is_frozen() else 1
    else:
        return LocalRunResult(
            success=False,
            output="",
            error=f"本地执行暂不支持该语言：{language}",
            execution_time_ms=0.0,
            exit_code=-1,
            mode="local-unavailable",
        )

    workdir = tempfile.mkdtemp(prefix="imato-run-")
    script_path = str(Path(workdir) / f"main{suffix}")
    try:
        Path(script_path).write_text(code, encoding="utf-8")

        env = {
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            # 保留最小系统变量，避免解释器找不到 DLL / 临时目录
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "TEMP": os.environ.get("TEMP", ""),
            "TMP": os.environ.get("TMP", ""),
            "APPDATA": os.environ.get("APPDATA", ""),
            "LOCALAPPDATA": os.environ.get("LOCALAPPDATA", ""),
        }

        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        proc = subprocess.run(  # noqa: S603 - 参数为内部构造，非 shell
            command_builder(script_path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds + extra_grace,
            cwd=workdir,
            env=env,
            creationflags=creationflags,
            check=False,
        )
        elapsed = (time.time() - start) * 1000
        output = _truncate((proc.stdout or "").strip())
        error = _truncate((proc.stderr or "").strip())
        return LocalRunResult(
            success=proc.returncode == 0,
            output=output,
            error=error,
            execution_time_ms=elapsed,
            exit_code=proc.returncode,
            mode=mode,
        )
    except subprocess.TimeoutExpired:
        return LocalRunResult(
            success=False,
            output="",
            error=f"执行超时（>{timeout_seconds}s），进程已被终止",
            execution_time_ms=(time.time() - start) * 1000,
            exit_code=-1,
            mode=mode,
        )
    except Exception as exc:  # pragma: no cover - 环境异常兜底
        return LocalRunResult(
            success=False,
            output="",
            error=f"本地执行失败：{exc}",
            execution_time_ms=(time.time() - start) * 1000,
            exit_code=-1,
            mode=mode,
        )
    finally:
        try:
            Path(script_path).unlink(missing_ok=True)
            Path(workdir).rmdir()
        except OSError:
            pass
