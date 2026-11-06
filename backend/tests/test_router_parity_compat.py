"""PR-C2：兼容性断言自身的测试（tests/test_router_parity.py 的配套用例）。

tests/test_router_parity.py 的 T1 / T2 / T3 已重设计为「按入口当前形态选断言」：
入口形态由 :func:`detect_entry_form` 判定，共四种：

===========  ==========================================  ==============
形态          含义                                        期望行为
===========  ==========================================  ==============
legacy_inline  源码里手写 include_router(...)             走源码集合断言
registry       源码里调用 register_all_routers(...)        走注册模式断言
mixed          两者都有                                    必须失败
unknown        两者都没有                                  必须失败
===========  ==========================================  ==============

本文件用 tmp_path 下临时生成的 mock 源码覆盖上述四种形态，验证：

1. 形态判定：detect_entry_form() 对四种形态的返回值正确；
2. 断言行为：T1 / T2 / T3 的断言函数在四种形态下该过的过、该红的红；
3. 无污染：mock 源码不会影响真实入口的形态判定。

mock 源码由本文件在运行时生成（不落库、不进仓库），因此不会引入真实依赖导入。

用法::

    cd backend && pytest tests/test_router_parity_compat.py -v
"""

from pathlib import Path
import sys
from typing import Set, Tuple

import pytest
from test_router_parity import (
    AI_EDU_MAIN_FILE,
    FORM_LEGACY_INLINE,
    FORM_MIXED,
    FORM_REGISTRY,
    FORM_UNKNOWN,
    LEGACY_ROUTES_FILE,
    SIDE_AI_EDU,
    SIDE_LEGACY,
    assert_active_set_consistent,
    assert_entry_covers_table,
    assert_entry_has_no_extra,
    detect_entry_form,
    side_entry_mode,
    side_expected_missing,
    side_table_pairs,
)

# 兜底：确保 tests 目录在 sys.path 中（pytest 默认已插入，此处仅作保底）
_tests_dir = str(Path(__file__).resolve().parent)
if _tests_dir not in sys.path:
    sys.path.insert(0, _tests_dir)


# ==================== mock 源码生成 ====================


def _write_legacy_inline_source(path: Path, pairs: Set[Tuple[str, str]]) -> None:
    """生成「只有 include_router」的 mock 入口源码。

    每个 router 用独立别名导入：_import_aliases 以本地别名为键，
    同名 router 会相互覆盖，导致集合比对失真。
    """
    lines = [
        '"""mock：只有 include_router 的入口源码（由测试生成）。"""',
        "",
        "app = object()",
        "",
    ]
    aliases = []
    for index, (module_path, attr) in enumerate(sorted(pairs)):
        alias = "mock_router_%d" % index
        aliases.append(alias)
        lines.append("from %s import %s as %s" % (module_path, attr, alias))
    lines.append("")
    for alias in aliases:
        lines.append("app.include_router(%s)" % alias)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _write_registry_source(path: Path, mode: str) -> None:
    """生成「只有 register_all_routers」的 mock 入口源码。"""
    path.write_text(
        '"""mock：只有 register_all_routers 的入口源码（由测试生成）。"""\n'
        "\n"
        "from core.router_registry import register_all_routers\n"
        "\n"
        "app = object()\n"
        "\n"
        'register_all_routers(app, mode="%s")\n' % mode,
        encoding="utf-8",
        newline="\n",
    )


def _write_mixed_source(path: Path) -> None:
    """生成「混合形态」的 mock 入口源码（两种调用并存）。"""
    path.write_text(
        '"""mock：混合形态的入口源码（由测试生成）。"""\n'
        "\n"
        "from core.router_registry import register_all_routers\n"
        "\n"
        "app = object()\n"
        "\n"
        "app.include_router(app)\n"
        'register_all_routers(app, mode="legacy")\n',
        encoding="utf-8",
        newline="\n",
    )


def _write_unknown_source(path: Path) -> None:
    """生成「未知形态」的 mock 入口源码（两种调用都没有）。"""
    path.write_text(
        '"""mock：未知形态的入口源码（由测试生成）。"""\n' "\n" "app = object()\n",
        encoding="utf-8",
        newline="\n",
    )


def _legacy_expected_pairs() -> Set[Tuple[str, str]]:
    """legacy 侧「源码里应当出现」的 (模块, 属性) 集合。"""
    return side_table_pairs(SIDE_LEGACY) - side_expected_missing(SIDE_LEGACY)


def _aiedu_expected_pairs() -> Set[Tuple[str, str]]:
    """main_ai_edu 侧「源码里应当出现」的 (模块, 属性) 集合。"""
    return side_table_pairs(SIDE_AI_EDU) - side_expected_missing(SIDE_AI_EDU)


# ==================== 形态判定 ====================


class TestDetectEntryForm:
    """detect_entry_form 对四种入口形态的判定。"""

    def test_legacy_only_is_detected(self, tmp_path):
        """只有 include_router -> legacy_inline。"""
        source = tmp_path / "mock_legacy_only.py"
        _write_legacy_inline_source(source, {("routes.demo_routes", "router")})
        assert detect_entry_form(source) == FORM_LEGACY_INLINE

    def test_registry_only_is_detected(self, tmp_path):
        """只有 register_all_routers -> registry。"""
        source = tmp_path / "mock_registry_only.py"
        _write_registry_source(source, side_entry_mode(SIDE_LEGACY))
        assert detect_entry_form(source) == FORM_REGISTRY

    def test_mixed_is_detected(self, tmp_path):
        """两者都有 -> mixed。"""
        source = tmp_path / "mock_mixed.py"
        _write_mixed_source(source)
        assert detect_entry_form(source) == FORM_MIXED

    def test_unknown_is_detected(self, tmp_path):
        """两者都没有 -> unknown。"""
        source = tmp_path / "mock_unknown.py"
        _write_unknown_source(source)
        assert detect_entry_form(source) == FORM_UNKNOWN

    def test_real_entries_are_detected(self):
        """真实入口当前仍是 legacy_inline 形态（4a / 4b 落地后会自动切换）。"""
        assert detect_entry_form(LEGACY_ROUTES_FILE) == FORM_LEGACY_INLINE
        assert detect_entry_form(AI_EDU_MAIN_FILE) == FORM_LEGACY_INLINE


# ==================== legacy_inline 分支 ====================


class TestLegacyInlineBranch:
    """legacy_inline 形态下 T1 / T2 / T3 的断言行为。"""

    def test_legacy_inline_passes_when_source_matches_table(self, tmp_path):
        """源码集合与表一致 -> 正反向断言都通过。"""
        source = tmp_path / "mock_legacy_only.py"
        _write_legacy_inline_source(source, _legacy_expected_pairs())
        assert_entry_covers_table(source, SIDE_LEGACY)
        assert_entry_has_no_extra(source, SIDE_LEGACY)

    def test_legacy_inline_passes_for_aiedu_side(self, tmp_path):
        """main_ai_edu 侧同理：源码集合与表一致 -> 正反向断言都通过。"""
        source = tmp_path / "mock_legacy_only.py"
        _write_legacy_inline_source(source, _aiedu_expected_pairs())
        assert_entry_covers_table(source, SIDE_AI_EDU)
        assert_entry_has_no_extra(source, SIDE_AI_EDU)

    def test_legacy_inline_fails_when_entry_missing(self, tmp_path):
        """源码少一项 -> 正向断言失败（漂移可见）。"""
        source = tmp_path / "mock_legacy_only.py"
        expected = _legacy_expected_pairs()
        dropped = sorted(expected)[0]
        _write_legacy_inline_source(source, expected - {dropped})
        with pytest.raises(AssertionError):
            assert_entry_covers_table(source, SIDE_LEGACY)

    def test_legacy_inline_fails_when_extra_present(self, tmp_path):
        """源码多一项 -> 反向断言失败（绕过 ROUTER_TABLE 被拦下）。"""
        source = tmp_path / "mock_legacy_only.py"
        expected = _legacy_expected_pairs()
        extra = ("routes.not_in_router_table", "router")
        _write_legacy_inline_source(source, expected | {extra})
        with pytest.raises(AssertionError):
            assert_entry_has_no_extra(source, SIDE_LEGACY)

    def test_t3_legacy_inline_branch_passes(self, tmp_path):
        """T3：legacy_inline 下 active == 源码集合 - pending。"""
        source = tmp_path / "mock_legacy_only.py"
        _write_legacy_inline_source(source, _legacy_expected_pairs())
        assert_active_set_consistent(source, SIDE_LEGACY)

    def test_t3_legacy_inline_branch_passes_for_aiedu_side(self, tmp_path):
        """T3：main_ai_edu 侧同理。"""
        source = tmp_path / "mock_legacy_only.py"
        _write_legacy_inline_source(source, _aiedu_expected_pairs())
        assert_active_set_consistent(source, SIDE_AI_EDU)


# ==================== registry 分支 ====================


class TestRegistryBranch:
    """registry 形态下 T1 / T2 / T3 的断言行为。"""

    def test_registry_accepts_matching_mode(self, tmp_path):
        """mode 与该侧匹配 -> 断言通过。"""
        source = tmp_path / "mock_registry_only.py"
        _write_registry_source(source, side_entry_mode(SIDE_LEGACY))
        assert_entry_covers_table(source, SIDE_LEGACY)
        assert_entry_has_no_extra(source, SIDE_LEGACY)

    def test_registry_accepts_matching_mode_for_aiedu_side(self, tmp_path):
        """main_ai_edu 侧 mode="lazy" -> 断言通过。"""
        source = tmp_path / "mock_registry_only.py"
        _write_registry_source(source, side_entry_mode(SIDE_AI_EDU))
        assert_entry_covers_table(source, SIDE_AI_EDU)
        assert_entry_has_no_extra(source, SIDE_AI_EDU)

    def test_registry_rejects_mismatched_mode(self, tmp_path):
        """mode 与该侧不匹配 -> 断言失败（4a 把 lazy 写成 legacy 会在这里被拦下）。"""
        source = tmp_path / "mock_registry_only.py"
        _write_registry_source(source, side_entry_mode(SIDE_AI_EDU))
        with pytest.raises(AssertionError):
            assert_entry_covers_table(source, SIDE_LEGACY)
        with pytest.raises(AssertionError):
            assert_entry_has_no_extra(source, SIDE_LEGACY)

    def test_registry_rejects_mismatched_mode_for_aiedu_side(self, tmp_path):
        """main_ai_edu 侧写成 mode="legacy" -> 断言失败。"""
        source = tmp_path / "mock_registry_only.py"
        _write_registry_source(source, side_entry_mode(SIDE_LEGACY))
        with pytest.raises(AssertionError):
            assert_entry_covers_table(source, SIDE_AI_EDU)

    def test_t3_registry_branch_passes(self, tmp_path):
        """T3：registry 下「实际注册的 active 集合」== 表内对应模式的 active 集合。"""
        source = tmp_path / "mock_registry_only.py"
        _write_registry_source(source, side_entry_mode(SIDE_LEGACY))
        assert_active_set_consistent(source, SIDE_LEGACY)

    def test_t3_registry_branch_passes_for_aiedu_side(self, tmp_path):
        """T3：main_ai_edu 侧同理。"""
        source = tmp_path / "mock_registry_only.py"
        _write_registry_source(source, side_entry_mode(SIDE_AI_EDU))
        assert_active_set_consistent(source, SIDE_AI_EDU)


# ==================== mixed / unknown 分支 ====================


class TestMixedAndUnknownForms:
    """混合形态与未知形态必须直接失败。"""

    def test_mixed_form_fails_for_legacy_side(self, tmp_path):
        """mixed：legacy 侧的正向 / 反向 / T3 断言全部失败。"""
        source = tmp_path / "mock_mixed.py"
        _write_mixed_source(source)
        with pytest.raises(AssertionError):
            assert_entry_covers_table(source, SIDE_LEGACY)
        with pytest.raises(AssertionError):
            assert_entry_has_no_extra(source, SIDE_LEGACY)
        with pytest.raises(AssertionError):
            assert_active_set_consistent(source, SIDE_LEGACY)

    def test_mixed_form_fails_for_aiedu_side(self, tmp_path):
        """mixed：main_ai_edu 侧同样全部失败。"""
        source = tmp_path / "mock_mixed.py"
        _write_mixed_source(source)
        with pytest.raises(AssertionError):
            assert_entry_covers_table(source, SIDE_AI_EDU)
        with pytest.raises(AssertionError):
            assert_entry_has_no_extra(source, SIDE_AI_EDU)
        with pytest.raises(AssertionError):
            assert_active_set_consistent(source, SIDE_AI_EDU)

    def test_unknown_form_fails_for_legacy_side(self, tmp_path):
        """unknown：legacy 侧的正向 / 反向 / T3 断言全部失败。"""
        source = tmp_path / "mock_unknown.py"
        _write_unknown_source(source)
        with pytest.raises(AssertionError):
            assert_entry_covers_table(source, SIDE_LEGACY)
        with pytest.raises(AssertionError):
            assert_entry_has_no_extra(source, SIDE_LEGACY)
        with pytest.raises(AssertionError):
            assert_active_set_consistent(source, SIDE_LEGACY)

    def test_unknown_form_fails_for_aiedu_side(self, tmp_path):
        """unknown：main_ai_edu 侧同样全部失败。"""
        source = tmp_path / "mock_unknown.py"
        _write_unknown_source(source)
        with pytest.raises(AssertionError):
            assert_entry_covers_table(source, SIDE_AI_EDU)
        with pytest.raises(AssertionError):
            assert_entry_has_no_extra(source, SIDE_AI_EDU)
        with pytest.raises(AssertionError):
            assert_active_set_consistent(source, SIDE_AI_EDU)
