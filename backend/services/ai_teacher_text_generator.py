"""
【P3-B】AI 教师文本生成器（共享模块）

从 ai_teacher_routes._generate_personalized_reply 抽取的共享文案生成逻辑，
供 chat 接口与 recommender 共用，避免重复代码。

特点：
- 纯函数，无副作用
- 集成 persona（昵称/语言风格/emoji 程度）
- 集成 RAG 知识上下文（可选）
- 支持多种诊断类型的模板化输出
"""

from typing import Dict, Optional


def address_for(persona: Dict[str, str]) -> str:
    """根据 persona 决定称呼"""
    mode = persona.get("address_mode", "name")
    if mode == "classmate":
        return "同学"
    if mode == "nickname" and persona.get("nickname"):
        return persona["nickname"]
    return "你"


def emoji_for(persona: Dict[str, str]) -> str:
    """根据 persona 决定 emoji"""
    usage = persona.get("emoji_usage", "moderate")
    if usage == "heavy":
        return "🎉💡✨"
    if usage == "moderate":
        return "💡"
    return ""


def celebration_text(
    persona: Dict[str, str],
    title: str,
    description: str,
    emoji_hint: str = "🎉",
) -> Dict[str, str]:
    """
    生成 celebration 文案（节点 mastered / 成就解锁 / 套装完成）

    Returns:
        {"title": ..., "message": ...}
    """
    addr = address_for(persona)
    emoji = emoji_for(persona) or emoji_hint
    message = (
        f"{emoji} {addr}刚刚完成了「{title}」！{description}\n\n"
        f"继续加油，期待你解锁更多成就！"
    )
    return {"title": f"🎊 {title}", "message": message}


def suggestion_text(
    persona: Dict[str, str],
    diagnosis_type: str,
    description: str,
    action: str,
) -> Dict[str, str]:
    """
    生成 suggestion 文案（前置缺失 / 高原期 / 能力失衡 / 概念混淆）

    Returns:
        {"title": ..., "message": ..., "severity": ...}
    """
    addr = address_for(persona)
    emoji = emoji_for(persona)

    label_map = {
        "prerequisite_missing": "💡 学习建议",
        "concept_confusion": "💡 概念巩固",
        "learning_plateau": "💡 换个方式",
        "skill_imbalance": "💡 能力补强",
        "attention_decline": "💡 休息一下",
        "ai_overdependence": "💡 独立思考",
    }

    severity = "info"
    if diagnosis_type in ("prerequisite_missing", "learning_plateau", "attention_decline"):
        severity = "warning"
    if diagnosis_type in ("concept_confusion",) and "频繁" in description:
        severity = "warning"

    title = label_map.get(diagnosis_type, "💡 学习建议")
    message = (
        f"{addr}，{description}\n\n"
        f"建议：{action}{emoji}"
    )
    return {"title": title, "message": message, "severity": severity}


def nudge_text(
    persona: Dict[str, str],
    nudge_type: str,
    days_idle: Optional[int] = None,
    skill_name: Optional[str] = None,
) -> Dict[str, str]:
    """
    生成 nudge 文案（comeback / miss_you / take_break / try_new）

    Returns:
        {"title": ..., "message": ...}
    """
    addr = address_for(persona)
    emoji = emoji_for(persona)

    if nudge_type == "comeback":
        days = days_idle or 1
        title = "👋 我们想念你啦"
        message = (
            f"{emoji} {addr}已经 {days} 天没来学习了！\n\n"
            f"回来花 5 分钟做个小练习，状态就回来啦。"
        )
    elif nudge_type == "miss_you":
        days = days_idle or 3
        title = "💙 想念你"
        message = (
            f"{emoji} {addr}已经 {days} 天没来啦！\n\n"
            f"今天的你已经准备就绪，要不要挑战一个小目标？"
        )
    elif nudge_type == "take_break":
        title = "🌱 休息一下"
        message = (
            f"{emoji} {addr}最近的注意力有些分散哦。\n\n"
            f"要不要换个轻松点的任务，或者先休息 5 分钟？"
        )
    elif nudge_type == "try_new":
        title = "✨ 试试新内容"
        sk = skill_name or "新知识点"
        message = (
            f"{emoji} {addr}要不要试试「{sk}」？\n\n"
            f"换个主题，说不定会有新灵感！"
        )
    else:
        title = "💡 学习提示"
        message = f"{emoji} {addr}，继续加油！"

    return {"title": title, "message": message}


# ==================== 兼容旧接口 ====================


def generate_personalized_reply(
    message: str,
    profile_seed: str,
    address_mode: str,
    persona: Dict[str, str],
    knowledge_context: str = "",
) -> str:
    """
    兼容旧 ai_teacher_routes._generate_personalized_reply 接口
    保持行为一致（用于 chat 接口不破坏）
    """
    persona = dict(persona)
    persona["address_mode"] = address_mode
    return generate_chat_reply(message, profile_seed, persona, knowledge_context)


def generate_chat_reply(
    message: str,
    profile_seed: str,
    persona: Dict[str, str],
    knowledge_context: str = "",
) -> str:
    """chat 回复生成（共享给 chat 与 recommender）"""
    language_style = persona.get("language_style", "lively")
    hint_level = persona.get("hint_level", "guided_thinking")
    emoji_usage = persona.get("emoji_usage", "moderate")
    emoji = "💡" if emoji_usage != "none" else ""
    address = "同学" if persona.get("address_mode") == "classmate" else "你"

    if knowledge_context:
        if "循环" in message or "loop" in message.lower():
            return (
                f"{address}，关于循环，我帮你找到了一些知识：{emoji}\n\n"
                f"{knowledge_context}\n\n"
                f"还记得你上次用动画学懂了条件判断吗？循环其实很像条件判断的重复版。"
                f"要不要先在 Blockly 里试试循环积木？"
            )
        return (
            f"{address}，这是个好问题！{emoji} 让我结合知识库帮你理清思路：\n\n"
            f"{knowledge_context}\n\n"
            f"你觉得从哪个角度来思考比较好呢？"
        )

    if "循环" in message or "loop" in message.lower():
        if hint_level == "direct_answer":
            return f"for 循环语法：for i in range(n): 其中 range(n) 生成 0 到 n-1 的序列。{emoji}"
        elif hint_level == "direction_only":
            return f"试试在 Blockly 里拖几个循环积木，然后看看生成的 Python 代码。{emoji}"
        else:
            return (
                f"{address}，循环是一个很重要的概念！{emoji} "
                f"还记得你上次用动画学懂了条件判断吗？循环其实很像条件判断的重复版。"
                f"要不要先在 Blockly 里试试循环积木，看看它和 Python 代码怎么对应？"
            )

    if "函数" in message or "function" in message.lower():
        if hint_level == "direct_answer":
            return f"函数定义语法：def function_name(parameters): 然后缩进写函数体。{emoji}"
        return f"{address}，函数就像一个打包好的工具箱，定义一次可以反复使用。{emoji} 你已经掌握了循环，函数是下一个自然步骤！"

    if "难" in message or "不会" in message:
        return (
            f"编程有时候确实让人头大，连我写了几百万行代码也会有这种感觉。{emoji} "
            f"咱们先把这个大问题拆成几个小步骤，一步步来？"
        )

    return f"{address}，这是个好问题！{emoji} 让我帮你理清思路，你觉得可以从哪个角度来思考呢？"