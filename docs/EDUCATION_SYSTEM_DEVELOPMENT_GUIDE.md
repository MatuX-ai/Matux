# 教育培训管理系统开发指南

## 📚 目录

1. [概述](#概述)
2. [架构设计](#架构设计)
3. [已实现功能](#已实现功能)
4. [快速开始](#快速开始)
5. [API 使用示例](#api-使用示例)
6. [下一步计划](#下一步计划)

---

## 概述

iMato 教育培训管理系统 (EduAdmin Pro) 是专为培训机构设计的专业版管理系统，提供智能排课、学员管理、教师薪酬等核心功能。

**版本**: v2.0 专业版  
**技术栈**: 
- 后端：Python FastAPI + SQLAlchemy
- 前端：Angular 21 + TypeScript
- 算法：遗传算法优化排课

---

## 架构设计

### 目录结构

```
g:/iMato/
├── backend/education/              # 教育业务后端模块
│   ├── models/                     # 数据模型
│   │   ├── schedule.py            # 排课模型
│   │   ├── student.py             # 学员模型
│   │   └── teacher.py             # 教师模型
│   ├── services/                   # 业务服务层
│   │   └── scheduling/            # 排课引擎
│   │       ├── genetic_algorithm.py  # 遗传算法
│   │       ├── conflict_detector.py  # 冲突检测
│   │       └── scheduler.py          # 调度服务
│   ├── routes/                     # API 路由
│   │   ├── schedules.py           # 排课 API
│   │   ├── students.py            # 学员 API
│   │   └── teachers.py            # 教师 API
│   ├── schemas/                    # Pydantic Schema
│   │   └── schedule_schema.py     # 排课相关 Schema
│   └── config.py                   # 配置信息
│
└── src/app/education/              # 教育业务前端模块
    ├── models/                     # TypeScript 模型
    │   ├── scheduling.models.ts   # 排课模型
    │   ├── student.models.ts      # 学员模型
    │   └── teacher.models.ts      # 教师模型
    ├── management/                 # 管理页面组件
    │   ├── scheduling/            # 排课管理
    │   ├── students/              # 学员管理
    │   └── teachers/              # 教师管理
    └── education.module.ts         # 模块定义
```

---

## 已实现功能

### ✅ Phase 1 T1.1 - 数据结构与排课引擎

#### 1. 数据模型 (已完成)

**后端模型** (`backend/education/models/`):
- `CourseSchedule` - 课程排课表
- `ScheduleConflict` - 课表冲突记录
- `StudentProfile` - 学员档案
- `ParentInfo` - 家长信息
- `Teacher` - 教师信息
- `TeachingRecord` - 授课记录
- `TeacherSalary` - 教师工资

**前端模型** (`src/app/education/models/`):
- `CourseSchedule` - 课表接口
- `SchedulingConstraints` - 约束条件
- `StudentProfile` - 学员接口
- `Teacher` - 教师接口

#### 2. 遗传算法排课引擎 (已完成)

**文件**: `backend/education/services/scheduling/genetic_algorithm.py`

**核心功能**:
- ✅ 种群初始化 (随机生成 N 个课表方案)
- ✅ 适应度评估 (计算得分，考虑硬约束和软约束)
- ✅ 选择操作 (锦标赛选择，保留优质个体)
- ✅ 交叉操作 (单点交叉，交换基因)
- ✅ 变异操作 (随机改变时间槽)
- ✅ 迭代优化 (最多 1000 代)

**算法参数**:
```python
population_size = 100      # 种群大小
generations = 1000         # 迭代代数
mutation_rate = 0.1        # 变异率
crossover_rate = 0.8       # 交叉率
elite_rate = 0.1           # 精英率
```

#### 3. 冲突检测引擎 (已完成)

**文件**: `backend/education/services/scheduling/conflict_detector.py`

**检测类型**:
- ✅ 教师时间冲突 (同一教师同一时间多处授课)
- ✅ 教室时间冲突 (同一教室同一时间多个班级)
- ✅ 学生时间冲突 (同一学生同一时间多门课程)
- ✅ 容量冲突 (班级人数超过教室容量)

**特色功能**:
- 实时检测 (< 100ms)
- 可用时间段查询
- 时间重叠判断

#### 4. API 接口 (已完成框架)

**排课 API** (`/api/v1/schedules`):
- `POST /generate` - 生成课表
- `GET /conflicts` - 获取冲突列表
- `PUT /{id}/adjust` - 调整课表
- `GET /statistics` - 统计信息

**学员 API** (`/api/v1/students`):
- `GET /` - 查询列表
- `POST /` - 创建学员
- `PUT /{id}` - 更新信息
- `DELETE /{id}` - 删除学员
- `POST /import` - 批量导入

**教师 API** (`/api/v1/teachers`):
- `GET /` - 查询列表
- `GET /{id}/workload` - 工作量统计
- `GET /{id}/salary` - 工资查询

---

## 快速开始

### 1. 数据库迁移

需要创建以下数据库表:

```sql
-- 课程排课表
CREATE TABLE courses_schedules (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id),
    teacher_id INTEGER REFERENCES teachers(id),
    classroom_id INTEGER REFERENCES classrooms(id),
    class_id INTEGER REFERENCES classes(id),
    day_of_week INTEGER,
    start_time TIME,
    end_time TIME,
    start_date DATE,
    end_date DATE,
    recurrence_pattern VARCHAR(50),
    is_confirmed BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 课表冲突表
CREATE TABLE schedule_conflicts (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES courses_schedules(id),
    conflict_type VARCHAR(50),
    description VARCHAR(500),
    related_schedule_ids VARCHAR(1000),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- 学员表
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    gender VARCHAR(10),
    birth_date DATE,
    grade VARCHAR(50),
    school VARCHAR(200),
    phone VARCHAR(20),
    email VARCHAR(100),
    status VARCHAR(20) DEFAULT '在读',
    enrollment_date DATE,
    current_class_id INTEGER REFERENCES classes(id),
    total_purchased_hours INTEGER DEFAULT 0,
    total_consumed_hours INTEGER DEFAULT 0,
    remaining_hours INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 家长信息表
CREATE TABLE parent_info (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    name VARCHAR(100),
    relationship_type VARCHAR(20),
    phone VARCHAR(20),
    email VARCHAR(100),
    wechat VARCHAR(50),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 教师表
CREATE TABLE teachers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    hire_date DATE,
    employment_type VARCHAR(20) DEFAULT 'full_time',
    base_salary DECIMAL(10,2) DEFAULT 0,
    position_allowance DECIMAL(10,2) DEFAULT 0,
    max_weekly_hours INTEGER DEFAULT 40,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 授课记录表
CREATE TABLE teaching_records (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER REFERENCES teachers(id),
    teaching_date DATE,
    duration_minutes INTEGER,
    course_type VARCHAR(50),
    class_size INTEGER,
    hourly_rate DECIMAL(10,2),
    teaching_income DECIMAL(10,2),
    month VARCHAR(7),
    is_confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 教师工资表
CREATE TABLE teacher_salaries (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER REFERENCES teachers(id),
    month VARCHAR(7),
    base_salary DECIMAL(10,2),
    teaching_income DECIMAL(10,2),
    performance_bonus DECIMAL(10,2),
    deductions DECIMAL(10,2),
    net_salary DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2. 注册路由

在 `backend/main.py` 中添加:

```python
from education.routes import schedules_router, students_router, teachers_router

app.include_router(schedules_router)
app.include_router(students_router)
app.include_router(teachers_router)
```

### 3. 注册模块

在 `src/app/app.module.ts` 中添加:

```typescript
import { EducationModule } from './education/education.module';

@NgModule({
  imports: [
    BrowserModule,
    EducationModule,
    // ... 其他模块
  ]
})
export class AppModule { }
```

---

## API 使用示例

### 1. 生成课表

```bash
curl -X POST http://localhost:8000/api/v1/schedules/generate \
  -H "Content-Type: application/json" \
  -d '{
    "courses": [
      {
        "id": "C001",
        "name": "数学",
        "total_hours": 60,
        "course_type": "medium_class",
        "teacher_ids": ["T001"]
      }
    ],
    "teachers": [
      {
        "id": "T001",
        "name": "张老师",
        "max_weekly_hours": 20,
        "teaching_subjects": ["数学"]
      }
    ],
    "classrooms": [
      {
        "id": "R001",
        "name": "教室 A101",
        "capacity": 30,
        "equipment": ["projector"]
      }
    ],
    "classes": [
      {
        "id": "CL001",
        "name": "初三 (1) 班",
        "student_count": 25
      }
    ],
    "constraints": {
      "hard_constraints": [],
      "soft_constraints": []
    },
    "options": {
      "population_size": 100,
      "generations": 1000,
      "mutation_rate": 0.1
    }
  }'
```

**响应示例**:

```json
{
  "success": true,
  "schedule": [
    {
      "course_id": "C001",
      "course_name": "数学",
      "teacher_id": "T001",
      "teacher_name": "张老师",
      "classroom_id": "R001",
      "classroom_name": "教室 A101",
      "day_of_week": 1,
      "start_time": "09:00",
      "end_time": "10:00",
      "recurrence_pattern": "weekly",
      "is_confirmed": false
    }
  ],
  "conflicts": [],
  "score": 95.5,
  "message": "课表生成成功"
}
```

### 2. 调整课表

```bash
curl -X PUT http://localhost:8000/api/v1/schedules/C001/adjust \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": "C001",
    "new_time_slot": {
      "day_of_week": 2,
      "start_time": "14:00",
      "end_time": "15:00"
    }
  }'
```

### 3. 查询学员列表

```bash
curl -X GET "http://localhost:8000/api/v1/students?page=1&page_size=20&grade=初三"
```

---

## 下一步计划

### ⏳ 进行中

- [ ] T1.1.4 排课 API 接口实现 (完成框架，待填充业务逻辑)
- [ ] 数据库迁移脚本编写
- [ ] 前端组件开发

### 📋 待启动

#### Week 3-4: 课表可视化组件

- [ ] T1.2.1 课表日历组件 (日/周/月视图)
- [ ] T1.2.2 冲突高亮显示
- [ ] T1.2.3 课表导出打印 (PDF/Excel)
- [ ] T1.2.4 移动端适配

#### Week 5-7: 学员管理系统

- [ ] T2.1.1 学员 CRUD 界面
- [ ] T2.1.2 家长信息管理
- [ ] T2.1.3 批量导入功能
- [ ] T2.2.1 签到功能 (二维码/IC 卡/人脸)
- [ ] T2.2.3 课时扣减逻辑

#### Week 8-10: 收费管理 + 教师薪酬

- [ ] T4.1.1 课程购买流程
- [ ] T3.2.2 工资自动计算

---

## 技术要点

### 遗传算法优化策略

1. **编码方式**: 整数编码，每个基因代表一门课程的安排
2. **选择策略**: 锦标赛选择 (tournament_size=5)
3. **交叉策略**: 单点交叉 (crossover_rate=0.8)
4. **变异策略**: 随机变异 (mutation_rate=0.1)
5. **精英保留**: 保留最优 10% 个体直接复制到下一代

### 性能优化

- 种群大小：100 (可配置 50-500)
- 迭代次数：1000 (可配置 100-5000)
- 并行计算：可使用 multiprocessing 加速适应度评估
- 内存优化：使用 generator 逐步生成种群

### 约束处理

**硬约束** (不可违反):
- 教师同一时间只能在一个教室
- 教室容量必须 >= 班级人数
- 学生不能同时上两门课
- 教师不可排课时间

**软约束** (尽量满足):
- 教师偏好时间段 (权重 0.8)
- 教室设备匹配度 (权重 0.6)
- 避免连续上课超过 4 节 (权重 0.5)
- 同一天同一班级不超过 2 次课 (权重 0.4)

---

## 开发团队

**技术架构**: AI Assistant  
**开发日期**: 2026-03-27  
**版本**: v2.0.0-alpha

---

## 联系方式

如有问题，请查阅项目文档或联系开发团队。
