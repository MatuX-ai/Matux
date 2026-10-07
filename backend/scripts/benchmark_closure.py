"""
课件图谱闭包表 - 性能测试

测试闭包表在不同数据量下的查询效率和数据一致性。

测试场景：
1. 小规模：100 个节点，3 层深度
2. 中规模：500 个节点，5 层深度
3. 大规模：1000 个节点，7 层深度
4. 超大规模：5000 个节点，10 层深度

测试指标：
- 创建节点耗时
- 查询祖先节点耗时
- 查询后代节点耗时
- 查询子树耗时
- 移动节点耗时
- 删除节点耗时
- 闭包表一致性验证

使用方法：
    python -m scripts.benchmark_closure [--scale small|medium|large|xlarge]
"""

import asyncio
import logging
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from utils.database import AsyncSessionLocal, engine
from models.courseware_clousure import CoursewareNode, CoursewareClosure
from repositories.courseware_repository import CoursewareRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("benchmark_closure")


# 测试配置
SCALES = {
    "small": {"total_nodes": 100, "max_depth": 3, "max_children": 5},
    "medium": {"total_nodes": 500, "max_depth": 5, "max_children": 6},
    "large": {"total_nodes": 1000, "max_depth": 7, "max_children": 4},
    "xlarge": {"total_nodes": 5000, "max_depth": 10, "max_children": 3},
}


class ClosureBenchmark:
    """闭包表性能基准测试"""

    def __init__(self, session: AsyncSession, scale: str = "large"):
        self.session = session
        self.repo = CoursewareRepository(session)
        self.config = SCALES.get(scale, SCALES["large"])
        self.results: Dict[str, Any] = {
            "scale": scale,
            "config": self.config,
            "metrics": {},
        }
        self.node_ids: List[int] = []
        self.root_ids: List[int] = []

    async def setup(self):
        """创建测试数据"""
        logger.info(f"准备测试数据: scale={self.results['scale']}, "
                    f"target_nodes={self.config['total_nodes']}")

        # 清除旧数据
        await self.session.execute(text("DELETE FROM courseware_closures"))
        await self.session.execute(text("DELETE FROM courseware_nodes"))
        await self.session.flush()

        total = self.config["total_nodes"]
        max_depth = self.config["max_depth"]
        max_children = self.config["max_children"]

        # 创建根节点
        num_roots = max(1, total // (max_depth * max_children))
        roots = []
        for i in range(num_roots):
            if len(self.node_ids) >= total:
                break
            root = await self.repo.create_node(
                title=f"测试课程-{i + 1}",
                node_type="course",
                order_index=i,
                parent_id=None,
            )
            self.node_ids.append(root.id)
            self.root_ids.append(root.id)
            roots.append(root)

        # 递归创建子节点
        remaining = total - len(self.node_ids)
        nodes_per_root = max(1, remaining // len(roots))

        for root in roots:
            if remaining <= 0:
                break
            count = min(nodes_per_root, remaining)
            created = await self._create_subtree(
                root.id, count, max_depth, max_children, 1
            )
            remaining -= created

        logger.info(f"测试数据创建完成: {len(self.node_ids)} 个节点, "
                    f"{len(self.root_ids)} 个根节点")

        # 统计闭包条目
        closure_count = await self.session.execute(
            select(func.count()).select_from(CoursewareClosure)
        )
        self.results["closure_entries"] = closure_count.scalar() or 0

    async def _create_subtree(
        self,
        parent_id: int,
        remaining: int,
        max_depth: int,
        max_children: int,
        current_depth: int,
    ) -> int:
        """递归创建子树"""
        if remaining <= 0 or current_depth > max_depth:
            return 0

        created = 0
        num_children = min(random.randint(1, max_children), remaining)

        for i in range(num_children):
            if remaining - created <= 0:
                break

            node = await self.repo.create_node(
                title=f"节点-{len(self.node_ids) + 1}",
                node_type=random.choice(["chapter", "section", "lesson", "quiz"]),
                order_index=i,
                parent_id=parent_id,
            )
            self.node_ids.append(node.id)
            created += 1

            # 递归创建孙子节点
            sub_created = await self._create_subtree(
                node.id,
                remaining - created,
                max_depth,
                max_children,
                current_depth + 1,
            )
            created += sub_created

        return created

    async def benchmark_create(self) -> Dict[str, float]:
        """测试创建节点性能"""
        logger.info("测试: 创建节点...")

        start = time.time()
        node = await self.repo.create_node(
            title="性能测试-新节点",
            node_type="lesson",
            parent_id=random.choice(self.node_ids),
        )
        duration = (time.time() - start) * 1000  # ms

        return {"create_node_ms": round(duration, 2)}

    async def benchmark_get_ancestors(self, iterations: int = 20) -> Dict[str, float]:
        """测试查询祖先节点性能"""
        logger.info(f"测试: 查询祖先节点 (x{iterations})...")

        # 选择深度较大的节点进行测试
        deep_nodes = []
        for node_id in random.sample(self.node_ids, min(50, len(self.node_ids))):
            depth = await self.repo.get_node_depth(node_id)
            if depth >= 2:
                deep_nodes.append(node_id)

        if not deep_nodes:
            deep_nodes = self.node_ids[:10]

        test_nodes = random.choices(deep_nodes, k=iterations)

        times = []
        for node_id in test_nodes:
            start = time.time()
            ancestors = await self.repo.get_ancestors(node_id)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)

        avg = sum(times) / len(times)
        return {
            "get_ancestors_avg_ms": round(avg, 2),
            "get_ancestors_min_ms": round(min(times), 2),
            "get_ancestors_max_ms": round(max(times), 2),
            "get_ancestors_iterations": iterations,
        }

    async def benchmark_get_descendants(self, iterations: int = 20) -> Dict[str, float]:
        """测试查询后代节点性能"""
        logger.info(f"测试: 查询后代节点 (x{iterations})...")

        # 选择不同深度的节点
        test_nodes = random.choices(self.node_ids, k=iterations)

        times = []
        counts = []
        for node_id in test_nodes:
            start = time.time()
            descendants = await self.repo.get_descendants(node_id)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            counts.append(len(descendants))

        avg = sum(times) / len(times)
        avg_count = sum(counts) / len(counts)
        return {
            "get_descendants_avg_ms": round(avg, 2),
            "get_descendants_min_ms": round(min(times), 2),
            "get_descendants_max_ms": round(max(times), 2),
            "get_descendants_avg_count": round(avg_count, 0),
            "get_descendants_iterations": iterations,
        }

    async def benchmark_get_subtree(self, iterations: int = 10) -> Dict[str, float]:
        """测试查询子树性能"""
        logger.info(f"测试: 查询子树 (x{iterations})...")

        test_nodes = random.choices(self.root_ids, k=min(iterations, len(self.root_ids)))

        times = []
        for node_id in test_nodes:
            start = time.time()
            subtree = await self.repo.get_subtree(node_id)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)

        avg = sum(times) / len(times)
        return {
            "get_subtree_avg_ms": round(avg, 2),
            "get_subtree_min_ms": round(min(times), 2),
            "get_subtree_max_ms": round(max(times), 2),
        }

    async def benchmark_move_node(self, iterations: int = 10) -> Dict[str, float]:
        """测试移动节点性能"""
        logger.info(f"测试: 移动节点 (x{iterations})...")

        times = []
        for _ in range(iterations):
            # 选择一个叶子节点和目标父节点
            node_id = random.choice(self.node_ids)
            descendants = await self.repo.get_all_descendant_ids(node_id)

            # 选择不在子树中的目标父节点
            available = [n for n in self.node_ids if n not in descendants]
            if not available:
                continue
            new_parent = random.choice(available)

            start = time.time()
            await self.repo.move_node(node_id, new_parent)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)

        if not times:
            return {"move_node_avg_ms": 0}

        avg = sum(times) / len(times)
        return {
            "move_node_avg_ms": round(avg, 2),
            "move_node_min_ms": round(min(times), 2),
            "move_node_max_ms": round(max(times), 2),
        }

    async def benchmark_get_level(self, iterations: int = 20) -> Dict[str, float]:
        """测试按层级查询性能"""
        logger.info(f"测试: 按层级查询 (x{iterations})...")

        test_nodes = random.choices(self.root_ids, k=min(iterations, len(self.root_ids)))

        times = []
        for node_id in test_nodes:
            depth = await self.repo.get_node_depth(node_id)
            max_level = min(depth, self.config["max_depth"])

            for level in range(1, max_level + 1):
                start = time.time()
                nodes = await self.repo.get_nodes_at_level(node_id, level)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)

        avg = sum(times) / len(times)
        return {
            "get_level_nodes_avg_ms": round(avg, 2),
            "get_level_nodes_min_ms": round(min(times), 2),
            "get_level_nodes_max_ms": round(max(times), 2),
        }

    async def benchmark_validate(self) -> Dict[str, Any]:
        """测试一致性验证性能"""
        logger.info("测试: 一致性验证...")

        start = time.time()
        validation = await self.repo.validate_closure_table()
        duration = (time.time() - start) * 1000

        return {
            "validate_ms": round(duration, 2),
            "is_valid": validation["is_valid"],
            "total_nodes": validation["total_nodes"],
            "total_closure_entries": validation["total_closure_entries"],
        }

    async def run_all(self):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info(f"闭包表性能测试 - 规模: {self.results['scale']}")
        logger.info(f"配置: {self.config}")
        logger.info("=" * 60)

        # 准备数据
        setup_start = time.time()
        await self.setup()
        setup_time = time.time() - setup_start
        self.results["metrics"]["setup_seconds"] = round(setup_time, 2)

        # 运行各项测试
        self.results["metrics"]["create"] = await self.benchmark_create()
        self.results["metrics"]["ancestors"] = await self.benchmark_get_ancestors()
        self.results["metrics"]["descendants"] = await self.benchmark_get_descendants()
        self.results["metrics"]["subtree"] = await self.benchmark_get_subtree()
        self.results["metrics"]["move"] = await self.benchmark_move_node()
        self.results["metrics"]["level"] = await self.benchmark_get_level()
        self.results["metrics"]["validate"] = await self.benchmark_validate()

        # 打印结果
        self._print_results()

    def _print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 60)
        print("性能测试结果")
        print("=" * 60)
        print(f"规模: {self.results['scale']}")
        print(f"节点数: {len(self.node_ids)}")
        print(f"闭包条目: {self.results['closure_entries']}")
        print(f"数据准备耗时: {self.results['metrics']['setup_seconds']}s")
        print("-" * 60)

        m = self.results["metrics"]

        print(f"\n创建节点:")
        print(f"  耗时: {m['create']['create_node_ms']}ms")

        print(f"\n查询祖先 ({m['ancestors'].get('get_ancestors_iterations', '?')} 次):")
        print(f"  平均: {m['ancestors']['get_ancestors_avg_ms']}ms")
        print(f"  最小: {m['ancestors']['get_ancestors_min_ms']}ms")
        print(f"  最大: {m['ancestors']['get_ancestors_max_ms']}ms")

        print(f"\n查询后代 ({m['descendants'].get('get_descendants_iterations', '?')} 次):")
        print(f"  平均: {m['descendants']['get_descendants_avg_ms']}ms")
        print(f"  平均结果数: {m['descendants']['get_descendants_avg_count']}")

        print(f"\n查询子树 ({m['subtree'].get('get_subtree_iterations', '?')} 次):")
        print(f"  平均: {m['subtree']['get_subtree_avg_ms']}ms")

        print(f"\n移动节点 ({m['move'].get('move_node_iterations', '?')} 次):")
        print(f"  平均: {m['move']['move_node_avg_ms']}ms")

        print(f"\n按层级查询:")
        print(f"  平均: {m['level']['get_level_nodes_avg_ms']}ms")

        print(f"\n一致性验证:")
        print(f"  耗时: {m['validate']['validate_ms']}ms")
        print(f"  有效: {m['validate']['is_valid']}")
        print("=" * 60)


async def run_benchmark(scale: str = "large"):
    """运行基准测试"""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            benchmark = ClosureBenchmark(session, scale=scale)
            await benchmark.run_all()

            # 回滚测试数据
            await session.rollback()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="课件图谱闭包表性能测试")
    parser.add_argument(
        "--scale", choices=["small", "medium", "large", "xlarge"],
        default="large", help="测试规模"
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_benchmark(scale=args.scale))
        return 0
    except Exception as e:
        logger.error(f"性能测试失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())