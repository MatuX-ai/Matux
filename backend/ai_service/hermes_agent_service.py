"""
Hermes Agent 服务模块

集成Hermes Agent (Nous Research) 实现AI导师功能
支持持久记忆、自动技能创建和多模型接入
"""

import asyncio
import json
import logging
import socket
from typing import Any, Dict, List, Optional
from enum import Enum

import httpx

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("hermes_agent")

# Hermes Agent API配置
HERMES_DEFAULT_HOST = "http://localhost:8080"
HERMES_API_VERSION = "v1"


class HermesToolType(str, Enum):
    """Hermes Agent 工具类型"""
    CODE_EXPLAIN = "code_explain"
    CODE_OPTIMIZE = "code_optimize"
    AI_TUTOR = "ai_tutor"
    WEB_SEARCH = "web_search"
    FILE_READ = "file_read"
    CODE_EXECUTE = "code_execute"


class HermesAgentService:
    """Hermes Agent 服务封装类"""

    def __init__(self):
        self.host = getattr(settings, 'HERMES_HOST', HERMES_DEFAULT_HOST)
        self.api_key = getattr(settings, 'HERMES_API_KEY', '')
        self.model = getattr(settings, 'HERMES_MODEL', 'hermes-3')
        self.enabled: bool = bool(self.api_key) or self._check_local_hermes()
        self._client: Optional[httpx.AsyncClient] = None

    def _check_local_hermes(self) -> bool:
        """检查本地Hermes Agent是否可用"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 8080))
            sock.close()
            return result == 0
        except Exception:
            return False

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.host,
                headers=headers,
                timeout=60.0
            )
        return self._client

    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _build_tutor_system_prompt(self) -> str:
        """构建编程导师的系统提示词"""
        return """你是一位专业的编程导师，专门帮助学生学习编程。

你的特点：
1. 耐心、友好、善于启发式教学
2. 擅长用简单的例子解释复杂的概念
3. 会根据学生的水平调整解释的深度
4. 喜欢用代码示例来演示
5. 会提供后续学习建议

可用的工具：
- code_explain: 解释代码的功能和工作原理
- code_optimize: 优化代码性能和可读性
- web_search: 搜索最新的技术文档和教程
- code_execute: 执行代码验证结果

请根据用户的问题，选择合适的工具来帮助他们学习。"""

    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        use_tools: bool = True
    ) -> Dict[str, Any]:
        """
        与Hermes Agent对话

        Args:
            message: 用户消息
            context: 上下文信息（如代码、编程语言等）
            use_tools: 是否启用工具调用

        Returns:
            包含响应和工具调用结果的字典
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Hermes Agent 未启用",
                "message": message
            }

        client = await self._get_client()

        # 构建消息
        messages = [
            {"role": "system", "content": self._build_tutor_system_prompt()}
        ]

        # 添加上下文
        if context:
            context_str = json.dumps(context, ensure_ascii=False)
            messages.append({
                "role": "system",
                "content": f"上下文信息：{context_str}"
            })

        messages.append({"role": "user", "content": message})

        # 构建请求
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        # 添加工具定义
        if use_tools:
            payload["tools"] = self._get_tool_definitions()

        try:
            response = await client.post(
                f"/{HERMES_API_VERSION}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # 安全访问API响应
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("Empty response from Hermes API")

            first_choice = choices[0]
            message_data = first_choice.get("message", {})
            content = message_data.get("content", "")

            return {
                "success": True,
                "message": content,
                "tool_calls": first_choice.get("tool_calls", []),
                "usage": data.get("usage", {})
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Hermes API错误: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"API错误: {e.response.status_code}",
                "message": message
            }
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Hermes API响应解析失败: {str(e)}, 响应: {data}")
            return {
                "success": False,
                "error": f"API响应格式异常: {str(e)}",
                "message": message
            }
        except Exception as e:
            logger.error(f"Hermes Agent调用失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": message
            }

    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取工具定义 - 用于Hermes Agent的工具调用"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "explain_code",
                    "description": "解释代码的功能和工作原理",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "要解释的代码"
                            },
                            "language": {
                                "type": "string",
                                "description": "编程语言（如python, javascript, java）",
                                "default": "python"
                            },
                            "detail_level": {
                                "type": "string",
                                "description": "详细程度（brief/normal/detailed）",
                                "default": "normal"
                            }
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "optimize_code",
                    "description": "优化代码性能和可读性",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "要优化的代码"
                            },
                            "language": {
                                "type": "string",
                                "description": "编程语言",
                                "default": "python"
                            },
                            "goals": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "优化目标（performance/readability/security）",
                                "default": ["performance", "readability"]
                            }
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "answer_programming_question",
                    "description": "回答编程问题，提供详细的解释和示例",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "用户的问题"
                            },
                            "language": {
                                "type": "string",
                                "description": "相关的编程语言",
                                "default": "python"
                            },
                            "context_code": {
                                "type": "string",
                                "description": "相关的代码片段（可选）"
                            }
                        },
                        "required": ["question"]
                    }
                }
            }
        ]

    async def explain_code(
        self,
        code: str,
        language: str = "python",
        detail_level: str = "normal"
    ) -> Dict[str, Any]:
        """解释代码（直接调用）"""
        prompt = f"""请解释以下{language}代码：

```{language}
{code}
```

详细程度：{detail_level}

请用JSON格式返回，包含：
- explanation: 代码解释
- code_elements: 代码元素分析
- complexity: 复杂度评估
- suggestions: 改进建议"""

        result = await self.chat(prompt, context={"task": "code_explain"})
        return result

    async def optimize_code(
        self,
        code: str,
        language: str = "python",
        goals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """优化代码（直接调用）"""
        goals_text = "、".join(goals or ["performance", "readability"])
        prompt = f"""请优化以下{language}代码：

```{language}
{code}
```

优化目标：{goals_text}

请用JSON格式返回，包含：
- optimized_code: 优化后的代码
- improvements: 改进项列表
- explanation: 优化说明"""

        result = await self.chat(prompt, context={"task": "code_optimize"})
        return result

    async def answer_question(
        self,
        question: str,
        language: str = "python",
        context_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """回答编程问题（直接调用）"""
        context = {"task": "ai_tutor", "language": language}
        if context_code:
            context["code"] = context_code

        prompt = f"""请回答以下编程问题：

问题：{question}
编程语言：{language}

请用JSON格式返回，包含：
- answer: 详细回答
- code_examples: 代码示例
- related_topics: 相关主题
- next_steps: 后续学习建议"""

        result = await self.chat(prompt, context=context)
        return result

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        if not self.enabled:
            return {
                "status": "disabled",
                "reason": "未配置Hermes API密钥且本地服务不可用"
            }

        try:
            client = await self._get_client()
            response = await client.get("/health")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "hermes_version": response.json().get("version", "unknown"),
                    "local_available": self._check_local_hermes()
                }
            else:
                return {
                    "status": "unhealthy",
                    "code": response.status_code
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# 全局单例
_hermes_service: Optional[HermesAgentService] = None


def get_hermes_service() -> HermesAgentService:
    """获取Hermes Agent服务单例"""
    global _hermes_service
    if _hermes_service is None:
        _hermes_service = HermesAgentService()
    return _hermes_service


async def close_hermes_service():
    """关闭Hermes Agent服务"""
    global _hermes_service
    if _hermes_service:
        await _hermes_service.close()
        _hermes_service = None
