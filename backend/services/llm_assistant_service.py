"""
AI 学习助手服务
基于 XEduLLM 构建对话式 AI 助手，支持教育场景的智能问答
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """教育知识库"""

    def __init__(self):
        # 模拟知识库数据
        self.knowledge_items = {
            "ai_concepts": [
                {
                    "question": "什么是人工智能？",
                    "answer": "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行需要人类智能的任务的系统。这些任务包括视觉感知、语音识别、决策和语言翻译等。",
                    "tags": ["AI", "基本概念", "定义"],
                },
                {
                    "question": "什么是机器学习？",
                    "answer": "机器学习是人工智能的核心技术，它让计算机能够从数据中学习，而无需显式编程。通过训练算法识别数据中的模式，机器可以做出预测和决策。",
                    "tags": ["机器学习", "算法", "数据"],
                },
                {
                    "question": "什么是神经网络？",
                    "answer": "神经网络是一种受人脑结构启发的机器学习模型。它由多层相互连接的节点（神经元）组成，通过调整连接权重来学习复杂的模式。深度学习就是使用多层的神经网络。",
                    "tags": ["神经网络", "深度学习", "模型"],
                },
                {
                    "question": "什么是卷积神经网络（CNN）？",
                    "answer": "CNN 是一种专门处理网格状数据（如图像）的神经网络。它使用卷积层自动检测图像的特征（如边缘、纹理），非常适合图像分类、目标检测等任务。",
                    "tags": ["CNN", "图像识别", "卷积"],
                },
            ],
            "programming": [
                {
                    "question": "Python 是什么？",
                    "answer": "Python 是一种高级编程语言，以简洁易读著称。它广泛应用于 Web 开发、数据分析、人工智能等领域。Python 有丰富的库支持，特别适合 AI 初学者。",
                    "tags": ["Python", "编程", "语言"],
                },
                {
                    "question": "如何学习编程？",
                    "answer": "学习编程的建议：1) 选择一门适合的语言（如 Python）；2) 理解基础概念（变量、循环、函数）；3) 多做实践项目；4) 阅读他人代码；5) 参与开源社区；6) 保持持续学习的习惯。",
                    "tags": ["学习方法", "编程", "建议"],
                },
            ],
            "study_tips": [
                {
                    "question": "如何提高学习效率？",
                    "answer": "提高学习效率的方法：1) 制定明确的学习目标；2) 使用番茄工作法（25 分钟专注 +5 分钟休息）；3) 主动回忆而非被动阅读；4) 教授他人以加深理解；5) 保证充足睡眠；6) 定期复习。",
                    "tags": ["学习方法", "效率", "技巧"],
                },
                {
                    "question": "遇到困难怎么办？",
                    "answer": "遇到学习困难时：1) 分解问题，逐步解决；2) 查阅文档和教程；3) 向老师或同学请教；4) 在论坛提问（如 Stack Overflow）；5) 休息一下再回来思考；6) 记住困难是学习的一部分，坚持下去！",
                    "tags": ["困难", "解决问题", "心态"],
                },
            ],
        }

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        检索相关知识

        Args:
            query: 用户问题
            top_k: 返回结果数量

        Returns:
            相关知识列表
        """
        # 简单的关键词匹配（实际应使用向量检索）
        query_lower = query.lower()

        results = []
        for category, items in self.knowledge_items.items():
            for item in items:
                # 计算相似度（简化版本）
                score = 0
                for keyword in item["tags"]:
                    if keyword.lower() in query_lower:
                        score += 1

                if score > 0:
                    results.append(
                        {**item, "relevance_score": score, "category": category}
                    )

        # 按相关性排序
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return results[:top_k]


class MockXEduLLM:
    """Mock XEduLLM 服务（用于演示和测试）"""

    @staticmethod
    async def generate_response(
        message: str,
        context: Optional[List[Dict[str, str]]] = None,
        knowledge_base: KnowledgeBase = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        生成 AI 助手回复

        Args:
            message: 用户消息
            context: 对话上下文
            knowledge_base: 知识库
            temperature: 生成温度

        Returns:
            AI 回复及相关信息
        """
        start_time = datetime.utcnow()

        # 1. 检索相关知识
        relevant_knowledge = []
        if knowledge_base:
            relevant_knowledge = knowledge_base.search(message, top_k=2)

        # 2. 构建回复（基于规则和模板）
        response_text = await MockXEduLLM._generate_response_text(
            message, relevant_knowledge, context, temperature
        )

        # 3. 计算响应时间
        inference_time = (datetime.utcnow() -
                          start_time).total_seconds() * 1000

        return {
            "reply": response_text,
            "model": "chatglm-6b-mock",
            "confidence": 0.85,
            "inference_time_ms": inference_time,
            "knowledge_used": len(relevant_knowledge) > 0,
            "context_aware": context is not None and len(context) > 0,
        }

    @staticmethod
    async def _generate_response_text(
        message: str,
        relevant_knowledge: List[Dict],
        context: Optional[List[Dict]],
        temperature: float,
    ) -> str:
        """生成回复文本"""

        message_lower = message.lower()

        # 1. 如果有相关知识，优先使用
        if relevant_knowledge:
            best_match = relevant_knowledge[0]
            return f"{best_match['answer']}\n\n（来自知识库：{best_match['question']}）"

        # 2. 基于关键词的规则回复
        if "什么是" in message_lower or "what is" in message_lower:
            return "这是一个很好的问题！让我为您解释一下...\n\n由于我的知识库中没有确切答案，建议您：\n1. 查阅相关教材\n2. 在课堂中提问\n3. 与同学讨论\n\n我会持续学习，下次能给您更好的回答！"

        elif "如何" in message_lower or "how to" in message_lower:
            return "要完成这个任务，您可以按照以下步骤操作：\n\n1. 明确您的目标\n2. 分解为小步骤\n3. 逐步实践\n4. 遇到问题及时求助\n\n具体方法会因您的情况而异，欢迎提供更多细节！"

        elif "帮助" in message_lower or "help" in message_lower:
            return "我很乐意帮助您！请告诉我您遇到的具体问题，比如：\n- 对某个概念不理解\n- 编程时遇到错误\n- 不知道如何开始学习\n\n我会尽力为您解答！"

        elif "谢谢" in message_lower or "thank you" in message_lower:
            return "不客气！很高兴能帮助到您。如果还有其他问题，随时问我哦！😊"

        elif "再见" in message_lower or "bye" in message_lower:
            return "再见！祝您学习愉快，有任何问题都可以随时回来找我！👋"

        else:
            # 通用回复
            return "我明白了。关于这个问题，我认为需要从多个角度来理解。\n\n您能提供更多背景信息吗？或者您具体想了解哪个方面？这样我可以给您更有针对性的回答。"


class LLMAssistantService:
    """AI 学习助手服务类"""

    def __init__(self, db_session: Session = None):
        """
        初始化助手服务

        Args:
            db_session: 数据库会话（可选）
        """
        self.db = db_session
        self.knowledge_base = KnowledgeBase()
        self.conversation_history: Dict[int,
                                        List[Dict]] = {}  # user_id -> history

        # 初始化 Token 计费装饰器
        if db_session:
            from services.token_service import TokenService
            from utils.decorators import TokenBillingDecorator
            token_service = TokenService(db_session)
            self.billing = TokenBillingDecorator(token_service)
        else:
            self.billing = None

    async def chat(
        self,
        user_id: int,
        message: str,
        current_lesson_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        与学生对话

        Args:
            user_id: 用户 ID
            message: 学生问题
            current_lesson_context: 当前课程上下文

        Returns:
            AI 助手的回答
        """
        logger.info(f"收到用户{user_id}的问题：{message[:50]}...")

        # Token 计费检查（如果启用）
        if self.billing and self.billing.billing_enabled:
            # 估算 Token 消耗：每 100 字符约 10 tokens
            estimated_tokens = max(10, (len(message) // 100) * 10)

            balance = self.billing.token_service.get_or_create_user_balance(
                user_id)
            if balance.remaining_tokens < estimated_tokens:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "code": "INSUFFICIENT_TOKENS",
                        "message": f"Token 余额不足，当前剩余：{balance.remaining_tokens}，需要：{estimated_tokens}",
                        "required": estimated_tokens,
                        "available": balance.remaining_tokens,
                        "usage_type": "ai_teacher"
                    }
                )

        # 1. 获取对话历史
        context = self.conversation_history.get(user_id, [])[-5:]  # 最近 5 轮

        # 2. 构建系统提示词
        system_prompt = self._build_system_prompt(current_lesson_context)

        # 3. 调用 LLM 生成回复
        response = await MockXEduLLM.generate_response(
            message=message,
            context=context,
            knowledge_base=self.knowledge_base,
            temperature=0.7,
        )

        # 4. 更新对话历史
        self._update_conversation_history(user_id, message, response["reply"])

        # 5. 记录对话日志（用于优化）
        await self._log_conversation(user_id, message, response, current_lesson_context)

        # 6. Token 扣费（如果启用）
        if self.billing and self.billing.billing_enabled:
            estimated_tokens = max(10, (len(message) // 100) * 10)
            success, msg = self.billing.token_service.consume_tokens(
                user_id=user_id,
                token_amount=estimated_tokens,
                usage_type="ai_teacher",
                usage_description=f"AI 对话：{message[:50]}...",
                resource_type="conversation"
            )

            if success:
                response['billing'] = {
                    'tokens_consumed': estimated_tokens,
                    'remaining_balance': balance.remaining_tokens - estimated_tokens,
                    'usage_type': "ai_teacher"
                }
                logger.info(
                    f"用户 {user_id} AI 对话扣费成功：{estimated_tokens} tokens")
            else:
                logger.warning(f"用户 {user_id} AI 对话扣费失败：{msg}")

        return response

    def _build_system_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """根据上下文构建系统提示词"""

        base_prompt = """你是一位专业的 AI 教育助手，负责解答学生在学习过程中的问题。

你的特点：
1. 耐心友好，用通俗易懂的方式解释概念
2. 鼓励学生思考和探索，而不是直接给出答案
3. 结合具体例子和实践场景
4. 注意引导学生的兴趣
5. 使用积极正面的语言"""

        if context:
            lesson_info = f"\n学生正在学习：{context.get('title', '未知课程')}"
            base_prompt += lesson_info

            if context.get("difficulty"):
                base_prompt += f"\n课程难度：{context['difficulty']}"

        return base_prompt

    def _update_conversation_history(
        self, user_id: int, user_message: str, ai_response: str
    ):
        """更新对话历史"""

        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        self.conversation_history[user_id].append(
            {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        self.conversation_history[user_id].append(
            {
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # 保持历史记录不超过 20 条
        if len(self.conversation_history[user_id]) > 20:
            self.conversation_history[user_id] = self.conversation_history[user_id][
                -20:
            ]

    async def _log_conversation(
        self, user_id: int, message: str, response: Dict, context: Optional[Dict]
    ):
        """记录对话日志（用于后续分析和优化）"""

        log_entry = {
            "user_id": user_id,
            "message": message,
            "response": response["reply"],
            "model": response["model"],
            "confidence": response["confidence"],
            "inference_time_ms": response["inference_time_ms"],
            "knowledge_used": response["knowledge_used"],
            "context_lesson": context.get("title") if context else None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 这里应该写入数据库或日志系统
        logger.debug(f"对话日志：{log_entry}")

    def clear_history(self, user_id: int):
        """清除用户对话历史"""

        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
            logger.info(f"已清除用户{user_id}的对话历史")

    def get_statistics(self) -> Dict[str, Any]:
        """获取助手使用统计"""

        total_users = len(self.conversation_history)
        total_conversations = sum(
            len(history) // 2  # 每轮对话包含 2 条消息
            for history in self.conversation_history.values()
        )

        return {
            "total_users": total_users,
            "total_conversations": total_conversations,
            "avg_conversations_per_user": (
                total_conversations / total_users if total_users > 0 else 0
            ),
        }


def get_llm_assistant_service(db: Session = None) -> LLMAssistantService:
    """获取 AI 学习助手服务实例"""
    return LLMAssistantService(db)
