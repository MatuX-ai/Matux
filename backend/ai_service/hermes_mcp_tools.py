"""
Hermes Agent MCP 工具封装

将iMato的AI导师功能封装为MCP工具，供Hermes Agent调用
支持与本地或远程Hermes Agent服务集成
"""

import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .hermes_agent_service import get_hermes_service, HermesAgentService
from .ai_manager import AIManager, CodeGenerationRequest, ModelProvider

logger = logging.getLogger("hermes_mcp_tools")


@dataclass
class MCPToolDefinition:
    """MCP工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]


class AITutorMCPTools:
    """AI导师 MCP 工具集

    将现有的AI导师功能封装为可被Hermes Agent调用的MCP工具
    """

    def __init__(self):
        self.hermes_service: HermesAgentService = get_hermes_service()
        self.ai_manager = AIManager()
        self._tools: Optional[List[MCPToolDefinition]] = None

    def get_tool_definitions(self) -> List[MCPToolDefinition]:
        """获取所有工具定义"""
        if self._tools is None:
            self._tools = [
                MCPToolDefinition(
                    name="imato_explain_code",
                    description="解释代码功能和工作原理，支持多种编程语言",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "要解释的代码"
                            },
                            "language": {
                                "type": "string",
                                "description": "编程语言 (python, javascript, java, go, rust, c, cpp, csharp, typescript, php, ruby, swift, kotlin)",
                                "default": "python"
                            },
                            "detail_level": {
                                "type": "string",
                                "description": "详细程度 (brief/normal/detailed)",
                                "default": "normal"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                MCPToolDefinition(
                    name="imato_optimize_code",
                    description="优化代码性能、可读性和安全性",
                    input_schema={
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
                                "description": "优化目标: performance(性能), readability(可读性), security(安全性), best-practice(最佳实践)",
                                "default": ["performance", "readability"]
                            }
                        },
                        "required": ["code"]
                    }
                ),
                MCPToolDefinition(
                    name="imato_ai_tutor",
                    description="智能编程辅导 - 回答用户的编程问题",
                    input_schema={
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
                                "description": "相关的代码上下文（可选）"
                            }
                        },
                        "required": ["question"]
                    }
                ),
                MCPToolDefinition(
                    name="imato_search_documentation",
                    description="搜索编程文档和技术教程",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词"
                            },
                            "language": {
                                "type": "string",
                                "description": "编程语言/技术栈",
                                "default": "python"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                MCPToolDefinition(
                    name="imato_generate_code",
                    description="根据需求生成代码",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "requirement": {
                                "type": "string",
                                "description": "代码需求描述"
                            },
                            "language": {
                                "type": "string",
                                "description": "编程语言",
                                "default": "python"
                            },
                            "framework": {
                                "type": "string",
                                "description": "使用的框架（可选）"
                            }
                        },
                        "required": ["requirement"]
                    }
                )
            ]
        return self._tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行MCP工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        logger.info(f"执行MCP工具: {tool_name}, 参数: {arguments}")

        try:
            if tool_name == "imato_explain_code":
                return await self._explain_code(
                    arguments.get("code", ""),
                    arguments.get("language", "python"),
                    arguments.get("detail_level", "normal")
                )
            elif tool_name == "imato_optimize_code":
                return await self._optimize_code(
                    arguments.get("code", ""),
                    arguments.get("language", "python"),
                    arguments.get("goals", ["performance", "readability"])
                )
            elif tool_name == "imato_ai_tutor":
                return await self._ai_tutor(
                    arguments.get("question", ""),
                    arguments.get("language", "python"),
                    arguments.get("context_code")
                )
            elif tool_name == "imato_search_documentation":
                return await self._search_documentation(
                    arguments.get("query", ""),
                    arguments.get("language", "python")
                )
            elif tool_name == "imato_generate_code":
                return await self._generate_code(
                    arguments.get("requirement", ""),
                    arguments.get("language", "python"),
                    arguments.get("framework")
                )
            else:
                return {
                    "success": False,
                    "error": f"未知工具: {tool_name}"
                }
        except Exception as e:
            logger.error(f"工具执行失败: {tool_name}, 错误: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _explain_code(
        self,
        code: str,
        language: str,
        detail_level: str
    ) -> Dict[str, Any]:
        """解释代码"""
        # 优先使用Hermes Agent
        if self.hermes_service.enabled:
            result = await self.hermes_service.explain_code(code, language, detail_level)
            if result.get("success"):
                return self._parse_json_response(result.get("message", "{}"))

        # 回退到原有实现
        prompt = f"""请解释以下{language}代码：

```{language}
{code}
```

详细程度：{detail_level}

请用JSON格式返回，包含explanation, code_elements, complexity, suggestions字段。"""

        ai_request = CodeGenerationRequest(
            prompt=prompt,
            provider=ModelProvider.DEEPSEEK,
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=2000
        )

        result = await self.ai_manager.generate_code(ai_request)
        return self._parse_json_response(result.code)

    async def _optimize_code(
        self,
        code: str,
        language: str,
        goals: List[str]
    ) -> Dict[str, Any]:
        """优化代码"""
        if self.hermes_service.enabled:
            result = await self.hermes_service.optimize_code(code, language, goals)
            if result.get("success"):
                return self._parse_json_response(result.get("message", "{}"))

        # 回退到原有实现
        prompt = f"""请优化以下{language}代码：

```{language}
{code}
```

优化目标：{', '.join(goals)}

请用JSON格式返回，包含optimized_code, improvements, explanation字段。"""

        ai_request = CodeGenerationRequest(
            prompt=prompt,
            provider=ModelProvider.DEEPSEEK,
            model="deepseek-chat",
            temperature=0.5,
            max_tokens=3000
        )

        result = await self.ai_manager.generate_code(ai_request)
        return self._parse_json_response(result.code)

    async def _ai_tutor(
        self,
        question: str,
        language: str,
        context_code: Optional[str]
    ) -> Dict[str, Any]:
        """智能辅导"""
        if self.hermes_service.enabled:
            result = await self.hermes_service.answer_question(
                question, language, context_code
            )
            if result.get("success"):
                return self._parse_json_response(result.get("message", "{}"))

        # 回退到原有实现
        prompt = f"""你是一位专业的编程导师。请回答用户的问题：

问题：{question}
编程语言：{language}
{f'相关代码：\n```{language}\n{context_code}\n```' if context_code else ''}

请用JSON格式返回，包含answer, code_examples, related_topics, next_steps字段。"""

        ai_request = CodeGenerationRequest(
            prompt=prompt,
            provider=ModelProvider.DEEPSEEK,
            model="deepseek-chat",
            temperature=0.8,
            max_tokens=2000
        )

        result = await self.ai_manager.generate_code(ai_request)
        return self._parse_json_response(result.code)

    async def _search_documentation(
        self,
        query: str,
        language: str
    ) -> Dict[str, Any]:
        """搜索文档"""
        # 使用Hermes Agent的web搜索能力
        if self.hermes_service.enabled:
            result = await self.hermes_service.chat(
                f"搜索{language}相关的{query}文档和教程，请提供简要说明和链接",
                context={"task": "web_search"}
            )
            if result.get("success"):
                return {
                    "success": True,
                    "answer": result.get("message", ""),
                    "sources": []
                }

        # 回退：直接返回搜索提示
        return {
            "success": True,
            "answer": f"请在搜索引擎中搜索：{language} {query}",
            "sources": []
        }

    async def _generate_code(
        self,
        requirement: str,
        language: str,
        framework: Optional[str]
    ) -> Dict[str, Any]:
        """生成代码"""
        prompt = f"""请生成满足以下需求的{language}代码：

需求：{requirement}
{f'框架：{framework}' if framework else ''}

请用JSON格式返回，包含code字段。"""

        ai_request = CodeGenerationRequest(
            prompt=prompt,
            provider=ModelProvider.DEEPSEEK,
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=3000
        )

        result = await self.ai_manager.generate_code(ai_request)
        return self._parse_json_response(result.code)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            # 尝试提取JSON
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"无法解析JSON响应: {str(e)}, 内容: {response[:100]}...")
            return {
                "success": False,
                "error": f"JSON解析失败: {str(e)}",
                "raw_response": response
            }


# 全局单例
_ai_tutor_tools: Optional[AITutorMCPTools] = None


def get_ai_tutor_tools() -> AITutorMCPTools:
    """获取AI导师MCP工具单例"""
    global _ai_tutor_tools
    if _ai_tutor_tools is None:
        _ai_tutor_tools = AITutorMCPTools()
    return _ai_tutor_tools
