"""
遗传算法排课引擎
================

使用遗传算法优化课程安排，解决多约束条件下的排课问题。

算法流程:
1. 初始化种群：随机生成 N 个课表方案
2. 适应度评估：计算每个方案的得分 (考虑硬约束和软约束)
3. 选择操作：保留优质个体
4. 交叉操作：交换两个个体的部分基因
5. 变异操作：随机改变某些基因
6. 迭代优化：重复步骤 2-5，直到达到最大迭代次数
7. 返回最优解
"""

from typing import List, Dict, Tuple, Optional
import random
from datetime import time
import logging

logger = logging.getLogger(__name__)


class Individual:
    """个体类 - 代表一个课表方案"""

    def __init__(self, genes: List[Dict] = None):
        """
        初始化个体

        Args:
            genes: 基因列表，每个基因代表一门课程的安排
                   格式：[{course_id, teacher_id, classroom_id, day_of_week, start_time, end_time}, ...]
        """
        self.genes = genes or []
        self.fitness_score = 0.0
        self.conflicts_count = 0

    def copy(self) -> 'Individual':
        """复制个体"""
        new_individual = Individual()
        new_individual.genes = [gene.copy() for gene in self.genes]
        new_individual.fitness_score = self.fitness_score
        new_individual.conflicts_count = self.conflicts_count
        return new_individual


class GeneticSchedulingAlgorithm:
    """遗传算法排课引擎"""

    def __init__(
        self,
        population_size: int = 100,
        generations: int = 1000,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        elite_rate: float = 0.1
    ):
        """
        初始化遗传算法

        Args:
            population_size: 种群大小
            generations: 迭代代数
            mutation_rate: 变异率
            crossover_rate: 交叉率
            elite_rate: 精英率 (保留的最优个体比例)
        """
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_rate = elite_rate

        # 资源数据
        self.courses = []
        self.teachers = []
        self.classrooms = []
        self.classes = []

        # 约束条件
        self.hard_constraints = []
        self.soft_constraints = []

        # 时间槽映射
        self.time_slots = self._generate_time_slots()

    def _generate_time_slots(self) -> List[Tuple[int, time, time]]:
        """生成所有可能的时间槽 [(day_of_week, start_time, end_time), ...]"""
        time_slots = []

        # 假设每天 8:00-21:00，每小时一个时间段
        for day in range(7):  # 周一到周日
            for hour in range(8, 21):  # 8:00-20:00
                start = time(hour, 0)
                end = time(hour + 1, 0)
                time_slots.append((day, start, end))

        return time_slots

    def generate(
        self,
        courses: List[Dict],
        teachers: List[Dict],
        classrooms: List[Dict],
        classes: List[Dict],
        hard_constraints: List[Dict] = None,
        soft_constraints: List[Dict] = None
    ) -> Tuple[List[Dict], List[Dict], float]:
        """
        生成优化的课表

        Args:
            courses: 课程列表
            teachers: 教师列表
            classrooms: 教室列表
            classes: 班级列表
            hard_constraints: 硬约束列表
            soft_constraints: 软约束列表

        Returns:
            (schedule, conflicts, score): 课表、冲突列表、优化得分
        """
        logger.info(f"开始排课，课程数：{len(courses)}, 迭代次数：{self.generations}")

        # 1. 保存输入数据
        self.courses = {c['id']: c for c in courses}
        self.teachers = {t['id']: t for t in teachers}
        self.classrooms = {c['id']: c for c in classrooms}
        self.classes = {c['id']: c for c in classes}
        self.hard_constraints = hard_constraints or []
        self.soft_constraints = soft_constraints or []

        # 2. 初始化种群
        population = self._initialize_population()
        logger.info(f"初始种群完成，大小：{len(population)}")

        # 3. 进化迭代
        best_individual = None
        best_score = 0.0

        for generation in range(self.generations):
            # 适应度评估
            for individual in population:
                self._evaluate_fitness(individual)

            # 更新最优解
            current_best = max(population, key=lambda x: x.fitness_score)
            if current_best.fitness_score > best_score:
                best_score = current_best.fitness_score
                best_individual = current_best.copy()

            # 终止条件：找到完美解 (无冲突)
            if best_individual.conflicts_count == 0:
                logger.info(f"第{generation}代找到完美解，得分：{best_score}")
                break

            # 选择、交叉、变异
            population = self._evolve(population)

            # 每 100 代输出一次进度
            if generation % 100 == 0:
                logger.info(f"第{generation}代，最佳得分：{best_score}, 冲突数：{best_individual.conflicts_count}")

        logger.info(f"排课完成，最佳得分：{best_score}, 冲突数：{best_individual.conflicts_count if best_individual else 'N/A'}")

        # 4. 返回结果
        if best_individual:
            schedule = self._decode_individual(best_individual)
            conflicts = self._get_conflicts(best_individual)
            return schedule, conflicts, best_score
        else:
            return [], [], 0.0

    def _initialize_population(self) -> List[Individual]:
        """初始化种群 - 随机生成 N 个课表方案"""
        population = []

        for _ in range(self.population_size):
            individual = self._create_random_individual()
            population.append(individual)

        return population

    def _create_random_individual(self) -> Individual:
        """创建一个随机个体"""
        genes = []

        # 为每门课程随机分配时间、教室和教师
        for course_id, course in self.courses.items():
            if not self.time_slots:
                continue

            # 随机选择时间槽
            time_slot = random.choice(self.time_slots)
            day, start_time, end_time = time_slot

            # 随机选择教师 (教授该课程的教师)
            teacher_ids = course.get('teacher_ids', [])
            teacher_id = random.choice(teacher_ids) if teacher_ids else list(self.teachers.keys())[0]

            # 随机选择教室
            classroom_id = random.choice(list(self.classrooms.keys()))

            # 随机选择班级
            class_id = random.choice(list(self.classes.keys()))

            genes.append({
                'course_id': course_id,
                'teacher_id': teacher_id,
                'classroom_id': classroom_id,
                'class_id': class_id,
                'day_of_week': day,
                'start_time': start_time,
                'end_time': end_time
            })

        return Individual(genes=genes)

    def _evaluate_fitness(self, individual: Individual) -> float:
        """评估个体适应度"""
        # 1. 检测冲突
        conflicts = self._detect_conflicts(individual)
        individual.conflicts_count = len(conflicts)

        # 2. 计算硬约束违反惩罚 (每个冲突扣 10 分)
        hard_penalty = individual.conflicts_count * 10

        # 3. 计算软约束违反惩罚
        soft_penalty = self._calculate_soft_constraint_penalty(individual)

        # 4. 计算适应度得分 (满分 100)
        fitness_score = max(0, 100 - hard_penalty - soft_penalty)
        individual.fitness_score = fitness_score

        return fitness_score

    def _detect_conflicts(self, individual: Individual) -> List[Dict]:
        """检测冲突"""
        conflicts = []
        genes = individual.genes

        # 按时间分组
        time_groups = {}
        for gene in genes:
            key = (gene['day_of_week'], gene['start_time'], gene['end_time'])
            if key not in time_groups:
                time_groups[key] = []
            time_groups[key].append(gene)

        # 检查每个时间段的冲突
        for time_key, genes_at_time in time_groups.items():
            if len(genes_at_time) <= 1:
                continue

            # 教师冲突检测
            teacher_ids = [g['teacher_id'] for g in genes_at_time]
            if len(teacher_ids) != len(set(teacher_ids)):
                conflicts.append({
                    'type': 'teacher_conflict',
                    'time': time_key,
                    'genes': genes_at_time
                })

            # 教室冲突检测
            classroom_ids = [g['classroom_id'] for g in genes_at_time]
            if len(classroom_ids) != len(set(classroom_ids)):
                conflicts.append({
                    'type': 'classroom_conflict',
                    'time': time_key,
                    'genes': genes_at_time
                })

        return conflicts

    def _calculate_soft_constraint_penalty(self, individual: Individual) -> float:
        """计算软约束违反惩罚"""
        penalty = 0.0

        # TODO: 实现各种软约束的惩罚计算
        # 例如：教师偏好时间段、教室设备匹配度等

        return penalty

    def _evolve(self, population: List[Individual]) -> List[Individual]:
        """进化操作：选择、交叉、变异"""
        new_population = []

        # 1. 保留精英 (最优的个体直接复制到下一代)
        elite_count = int(len(population) * self.elite_rate)
        sorted_population = sorted(population, key=lambda x: x.fitness_score, reverse=True)
        elites = [ind.copy() for ind in sorted_population[:elite_count]]
        new_population.extend(elites)

        # 2. 交叉和变异产生剩余个体
        while len(new_population) < self.population_size:
            # 选择父代 (锦标赛选择)
            parent1 = self._tournament_selection(population)
            parent2 = self._tournament_selection(population)

            # 交叉
            child1, child2 = self._crossover(parent1, parent2)

            # 变异
            self._mutate(child1)
            self._mutate(child2)

            new_population.append(child1)
            if len(new_population) < self.population_size:
                new_population.append(child2)

        return new_population

    def _tournament_selection(self, population: List[Individual], tournament_size: int = 5) -> Individual:
        """锦标赛选择"""
        candidates = random.sample(population, min(tournament_size, len(population)))
        return max(candidates, key=lambda x: x.fitness_score)

    def _crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """交叉操作 - 单点交叉"""
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        # 随机选择交叉点
        crossover_point = random.randint(1, len(parent1.genes) - 1)

        # 创建子代
        child1_genes = parent1.genes[:crossover_point] + parent2.genes[crossover_point:]
        child2_genes = parent2.genes[:crossover_point] + parent1.genes[crossover_point:]

        child1 = Individual(genes=child1_genes)
        child2 = Individual(genes=child2_genes)

        return child1, child2

    def _mutate(self, individual: Individual) -> None:
        """变异操作 - 随机改变某些基因"""
        for gene in individual.genes:
            if random.random() < self.mutation_rate:
                # 随机改变时间槽
                if self.time_slots:
                    new_time_slot = random.choice(self.time_slots)
                    gene['day_of_week'] = new_time_slot[0]
                    gene['start_time'] = new_time_slot[1]
                    gene['end_time'] = new_time_slot[2]

                # 随机改变教室
                if random.random() < 0.5:
                    gene['classroom_id'] = random.choice(list(self.classrooms.keys()))

    def _decode_individual(self, individual: Individual) -> List[Dict]:
        """将个体解码为课表"""
        schedule = []

        for gene in individual.genes:
            course = self.courses.get(gene['course_id'])
            teacher = self.teachers.get(gene['teacher_id'])
            classroom = self.classrooms.get(gene['classroom_id'])
            class_group = self.classes.get(gene['class_id'])

            if not all([course, teacher, classroom, class_group]):
                continue

            schedule.append({
                'course_id': gene['course_id'],
                'course_name': course.get('name'),
                'teacher_id': gene['teacher_id'],
                'teacher_name': teacher.get('name'),
                'classroom_id': gene['classroom_id'],
                'classroom_name': classroom.get('name'),
                'class_id': gene['class_id'],
                'class_name': class_group.get('name'),
                'day_of_week': gene['day_of_week'],
                'start_time': gene['start_time'].strftime('%H:%M'),
                'end_time': gene['end_time'].strftime('%H:%M'),
                'recurrence_pattern': 'weekly',
                'is_confirmed': False
            })

        return schedule

    def _get_conflicts(self, individual: Individual) -> List[Dict]:
        """获取冲突列表"""
        conflicts = self._detect_conflicts(individual)

        formatted_conflicts = []
        for conflict in conflicts:
            formatted_conflicts.append({
                'conflict_type': conflict['type'],
                'description': f"{conflict['type']} at {conflict['time']}",
                'related_schedule_ids': [g['course_id'] for g in conflict['genes']]
            })

        return formatted_conflicts
