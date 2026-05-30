from datetime import datetime, timedelta
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from langchain.memory import ConversationBufferMemory

from ..config.settings import get_settings
from ..database.tenant_aware_session import get_db_session
from ..models.ai_completion import (
    ContextAnalysisResult,
    ProgrammingLanguage,
    UserHistoryRecord,
)

logger = logging.getLogger(__name__)


class CompletionMemory:
    """基于LangChain的记忆链系统，用于代码补全上下文管理"""

    def __init__(self):
        self.settings = get_settings()
        self.memory_buffer = ConversationBufferMemory(
            memory_key="chat_history",
            input_key="input",
            output_key="output",
            return_messages=True,
        )
        self.cache_ttl = timedelta(hours=self.settings.COMPLETION_CACHE_TTL_HOURS or 24)

    async def add_user_history(self, record: UserHistoryRecord) -> bool:
        """
        添加用户历史记录到记忆系统

        Args:
            record: 用户历史记录

        Returns:
            是否成功添加
        """
        try:
            async with get_db_session() as db:
                # 检查是否存在相同记录
                existing_record = await db.execute(
                    "SELECT id, usage_count FROM user_code_history "
                    "WHERE user_id = :user_id AND code_snippet = :code_snippet "
                    "AND language = :language",
                    {
                        "user_id": record.user_id,
                        "code_snippet": record.code_snippet,
                        "language": record.language.value,
                    },
                )
                result = existing_record.fetchone()

                if result:
                    # 更新现有记录
                    await db.execute(
                        "UPDATE user_code_history SET "
                        "usage_count = usage_count + 1, "
                        "last_used = :last_used, "
                        "context = :context "
                        "WHERE id = :id",
                        {
                            "id": result.id,
                            "last_used": record.last_used,
                            "context": record.context,
                        },
                    )
                else:
                    # 插入新记录
                    await db.execute(
                        "INSERT INTO user_code_history "
                        "(user_id, code_snippet, context, language, usage_count, last_used, created_at) "
                        "VALUES (:user_id, :code_snippet, :context, :language, :usage_count, :last_used, :created_at)",
                        {
                            "user_id": record.user_id,
                            "code_snippet": record.code_snippet,
                            "context": record.context,
                            "language": record.language.value,
                            "usage_count": record.usage_count,
                            "last_used": record.last_used,
                            "created_at": record.created_at,
                        },
                    )

                await db.commit()
                return True

        except Exception as e:
            logger.error(f"添加用户历史记录失败: {e}")
            return False

    async def get_user_patterns(
        self, user_id: int, language: ProgrammingLanguage, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取用户的代码模式和偏好

        Args:
            user_id: 用户ID
            language: 编程语言
            limit: 返回记录数限制

        Returns:
            用户代码模式列表
        """
        try:
            async with get_db_session() as db:
                result = await db.execute(
                    "SELECT code_snippet, context, usage_count, last_used "
                    "FROM user_code_history "
                    "WHERE user_id = :user_id AND language = :language "
                    "ORDER BY usage_count DESC, last_used DESC "
                    "LIMIT :limit",
                    {"user_id": user_id, "language": language.value, "limit": limit},
                )

                patterns = []
                for row in result.fetchall():
                    patterns.append(
                        {
                            "code_snippet": row.code_snippet,
                            "context": row.context,
                            "usage_count": row.usage_count,
                            "last_used": row.last_used,
                        }
                    )

                return patterns

        except Exception as e:
            logger.error(f"获取用户模式失败: {e}")
            return []

    async def cache_completion(
        self,
        prefix: str,
        completions: List[Dict[str, Any]],
        confidence_scores: List[float],
        language: Optional[ProgrammingLanguage] = None,
    ) -> bool:
        """
        缓存补全结果

        Args:
            prefix: 代码前缀
            completions: 补全结果列表
            confidence_scores: 置信度分数列表
            language: 编程语言

        Returns:
            是否缓存成功
        """
        try:
            prefix_hash = self._generate_prefix_hash(prefix)
            expires_at = datetime.utcnow() + self.cache_ttl

            async with get_db_session() as db:
                # 检查缓存是否已存在
                existing_cache = await db.execute(
                    "SELECT id FROM completion_cache WHERE prefix_hash = :prefix_hash",
                    {"prefix_hash": prefix_hash},
                )

                if existing_cache.fetchone():
                    # 更新现有缓存
                    await db.execute(
                        "UPDATE completion_cache SET "
                        "completions_json = :completions_json, "
                        "confidence_scores_json = :confidence_scores_json, "
                        "expires_at = :expires_at "
                        "WHERE prefix_hash = :prefix_hash",
                        {
                            "prefix_hash": prefix_hash,
                            "completions_json": json.dumps(completions),
                            "confidence_scores_json": json.dumps(confidence_scores),
                            "expires_at": expires_at,
                        },
                    )
                else:
                    # 插入新缓存
                    await db.execute(
                        "INSERT INTO completion_cache "
                        "(prefix_hash, completions_json, confidence_scores_json, "
                        "created_at, expires_at, language) "
                        "VALUES (:prefix_hash, :completions_json, :confidence_scores_json, "
                        ":created_at, :expires_at, :language)",
                        {
                            "prefix_hash": prefix_hash,
                            "completions_json": json.dumps(completions),
                            "confidence_scores_json": json.dumps(confidence_scores),
                            "created_at": datetime.utcnow(),
                            "expires_at": expires_at,
                            "language": language.value if language else None,
                        },
                    )

                await db.commit()
                return True

        except Exception as e:
            logger.error(f"缓存补全结果失败: {e}")
            return False

    async def get_cached_completion(
        self, prefix: str
    ) -> Optional[Tuple[List[Dict[str, Any]], List[float]]]:
        """
        从缓存获取补全结果

        Args:
            prefix: 代码前缀

        Returns:
            (补全结果列表, 置信度分数列表) 或 None
        """
        try:
            prefix_hash = self._generate_prefix_hash(prefix)
            current_time = datetime.utcnow()

            async with get_db_session() as db:
                result = await db.execute(
                    "SELECT completions_json, confidence_scores_json, hit_count "
                    "FROM completion_cache "
                    "WHERE prefix_hash = :prefix_hash AND expires_at > :current_time",
                    {"prefix_hash": prefix_hash, "current_time": current_time},
                )

                row = result.fetchone()
                if row:
                    # 更新命中计数
                    await db.execute(
                        "UPDATE completion_cache SET hit_count = hit_count + 1 "
                        "WHERE prefix_hash = :prefix_hash",
                        {"prefix_hash": prefix_hash},
                    )
                    await db.commit()

                    completions = json.loads(row.completions_json)
                    confidence_scores = json.loads(row.confidence_scores_json)

                    return completions, confidence_scores

            return None

        except Exception as e:
            logger.error(f"获取缓存补全结果失败: {e}")
            return None

    async def cleanup_expired_cache(self) -> int:
        """
        清理过期的缓存条目

        Returns:
            清理的条目数量
        """
        try:
            current_time = datetime.utcnow()

            async with get_db_session() as db:
                result = await db.execute(
                    "DELETE FROM completion_cache WHERE expires_at <= :current_time",
                    {"current_time": current_time},
                )

                deleted_count = result.rowcount
                await db.commit()

                logger.info(f"清理了 {deleted_count} 个过期缓存条目")
                return deleted_count

        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return 0

    def _generate_prefix_hash(self, prefix: str) -> str:
        """
        生成前缀的哈希值

        Args:
            prefix: 代码前缀

        Returns:
            SHA256哈希值
        """
        return hashlib.sha256(prefix.encode("utf-8")).hexdigest()

    async def analyze_context_patterns(
        self, context_lines: List[str], language: ProgrammingLanguage
    ) -> ContextAnalysisResult:
        """
        分析上下文中的代码模式

        Args:
            context_lines: 上下文代码行
            language: 编程语言

        Returns:
            上下文分析结果
        """
        try:
            # 合并上下文行进行分析
            context_text = "\n".join(context_lines)

            # 基础语法分析
            analysis = ContextAnalysisResult(
                scope_level=self._detect_scope_level(context_lines),
                syntax_context=self._detect_syntax_context(context_lines, language),
                variable_declarations=self._extract_variable_declarations(
                    context_lines, language
                ),
                function_signatures=self._extract_function_signatures(
                    context_lines, language
                ),
                imported_modules=self._extract_imports(context_lines, language),
                current_indentation=self._get_current_indentation(context_lines),
            )

            return analysis

        except Exception as e:
            logger.error(f"上下文模式分析失败: {e}")
            # 返回默认分析结果
            return ContextAnalysisResult(
                scope_level="unknown",
                syntax_context="unknown",
                variable_declarations=[],
                function_signatures=[],
                imported_modules=[],
                current_indentation=0,
            )

    def _detect_scope_level(self, context_lines: List[str]) -> str:
        """检测作用域级别"""
        if not context_lines:
            return "global"

        last_line = context_lines[-1].strip()

        # 检查常见的作用域关键字
        class_indicators = ["class ", "def ", "function ", "fn "]
        if any(indicator in last_line for indicator in class_indicators):
            return "class"
        elif "def " in last_line or "function " in last_line:
            return "function"
        elif "{" in last_line and "}" not in last_line:
            return "block"
        else:
            return "global"

    def _detect_syntax_context(
        self, context_lines: List[str], language: ProgrammingLanguage
    ) -> str:
        """检测语法上下文"""
        context_text = " ".join(context_lines).lower()

        # 根据不同语言检测上下文
        if language == ProgrammingLanguage.PYTHON:
            if "import " in context_text:
                return "import"
            elif "class " in context_text:
                return "class_definition"
            elif "def " in context_text:
                return "function_definition"
            elif "if " in context_text or "elif " in context_text:
                return "conditional"
            elif "for " in context_text or "while " in context_text:
                return "loop"
        elif language == ProgrammingLanguage.JAVASCRIPT:
            if "import " in context_text or "require(" in context_text:
                return "import"
            elif "class " in context_text:
                return "class_definition"
            elif "function " in context_text:
                return "function_definition"

        return "general"

    def _extract_variable_declarations(
        self, context_lines: List[str], language: ProgrammingLanguage
    ) -> List[str]:
        """提取变量声明"""
        declarations = []

        if language == ProgrammingLanguage.PYTHON:
            for line in context_lines:
                if "=" in line and not line.strip().startswith("#"):
                    var_name = line.split("=")[0].strip()
                    if var_name and not var_name.startswith(("if", "for", "while")):
                        declarations.append(var_name)
        elif language == ProgrammingLanguage.JAVASCRIPT:
            for line in context_lines:
                if (
                    "let " in line or "const " in line or "var " in line
                ) and "=" in line:
                    parts = line.split("=")
                    if len(parts) >= 2:
                        decl_part = parts[0].strip()
                        var_name = decl_part.split()[-1]
                        declarations.append(var_name)

        return declarations[:10]  # 限制返回数量

    def _extract_function_signatures(
        self, context_lines: List[str], language: ProgrammingLanguage
    ) -> List[str]:
        """提取函数签名"""
        signatures = []

        for line in context_lines:
            line = line.strip()
            if language == ProgrammingLanguage.PYTHON and line.startswith("def "):
                func_name = line[4:].split("(")[0].strip()
                signatures.append(func_name)
            elif language == ProgrammingLanguage.JAVASCRIPT and line.startswith(
                "function "
            ):
                func_name = line[9:].split("(")[0].strip()
                signatures.append(func_name)

        return signatures[:5]  # 限制返回数量

    def _extract_imports(
        self, context_lines: List[str], language: ProgrammingLanguage
    ) -> List[str]:
        """提取导入模块"""
        imports = []

        for line in context_lines:
            line = line.strip()
            if language == ProgrammingLanguage.PYTHON and line.startswith("import "):
                module = line[7:].strip()
                imports.append(module.split()[0])
            elif language == ProgrammingLanguage.JAVASCRIPT and line.startswith(
                "import "
            ):
                # 提取from部分
                if "from " in line:
                    module = line.split("from ")[1].strip().strip("'\"")
                    imports.append(module)

        return imports[:10]  # 限制返回数量

    def _get_current_indentation(self, context_lines: List[str]) -> int:
        """获取当前缩进级别"""
        if not context_lines:
            return 0

        last_line = context_lines[-1]
        indent_level = 0

        # 计算空格缩进
        for char in last_line:
            if char == " ":
                indent_level += 1
            elif char == "\t":
                indent_level += 4  # 假设tab等于4个空格
            else:
                break

        return indent_level // 4  # 转换为缩进层级


# 全局实例
completion_memory = CompletionMemory()
