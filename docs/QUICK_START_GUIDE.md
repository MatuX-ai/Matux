# 快速开始指南 - 教育培训管理系统

## 🎯 目标

本指南帮助您快速启动和测试已实现的排课系统核心功能。

---

## 📋 前置条件

### 环境要求
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+ (或其他数据库)

### 依赖安装

```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd ..
npm install
```

---

## 🚀 第一步：注册教育业务模块

### 1. 在 main.py 中注册路由

编辑 `backend/main.py`:

```python
from fastapi import FastAPI
from education.routes import schedules_router, students_router, teachers_router

app = FastAPI()

# 注册教育业务路由
app.include_router(schedules_router)
app.include_router(students_router)
app.include_router(teachers_router)

@app.get("/")
async def root():
    return {"message": "iMato EduAdmin Pro API", "version": "2.0.0"}
```

### 2. 在 app.module.ts 中注册模块

编辑 `src/app/app.module.ts`:

```typescript
import { EducationModule } from './education/education.module';

@NgModule({
  declarations: [
    AppComponent,
    // ...
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    EducationModule,  // 添加这行
    // ... 其他模块
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
```

---

## 🧪 第二步：测试遗传算法

### 创建测试脚本

创建文件 `backend/test_scheduling.py`:

```python
"""
测试遗传算法排课引擎
"""
import sys
sys.path.append('..')

from education.services.scheduling import GeneticSchedulingAlgorithm

# 准备测试数据
courses = [
    {"id": f"C{i:03d}", "name": f"课程{i}", "total_hours": 60, "course_type": "medium_class", "teacher_ids": ["T001"]}
    for i in range(1, 21)  # 20 门课程
]

teachers = [
    {
        "id": "T001",
        "name": "张老师",
        "available_time_slots": [],
        "max_weekly_hours": 20,
        "teaching_subjects": ["数学"]
    }
]

classrooms = [
    {"id": f"R{i:03d}", "name": f"教室{i}", "capacity": 30, "equipment": []}
    for i in range(1, 6)  # 5 个教室
]

classes = [
    {"id": f"CL{i:03d}", "name": f"班级{i}", "student_count": 25, "students": []}
    for i in range(1, 6)  # 5 个班级
]

# 创建算法实例
algorithm = GeneticSchedulingAlgorithm(
    population_size=100,
    generations=500,  # 测试时减少迭代次数
    mutation_rate=0.1
)

# 运行算法
print("开始生成课表...")
schedule, conflicts, score = algorithm.generate(
    courses=courses,
    teachers=teachers,
    classrooms=classrooms,
    classes=classes
)

# 输出结果
print(f"\n=== 排课结果 ===")
print(f"生成课程数：{len(schedule)}")
print(f"冲突数：{len(conflicts)}")
print(f"优化得分：{score:.2f}")

if conflicts:
    print(f"\n冲突详情:")
    for conflict in conflicts:
        print(f"  - {conflict['conflict_type']}: {conflict['description']}")

# 保存结果到 JSON 文件
import json

result = {
    "success": len(conflicts) == 0,
    "schedule": schedule,
    "conflicts": conflicts,
    "score": score
}

with open('scheduling_result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n结果已保存到 scheduling_result.json")
```

### 运行测试

```bash
cd backend
python test_scheduling.py
```

### 预期输出

```
开始生成课表...
第 0 代，最佳得分：45.0, 冲突数：5
第 100 代，最佳得分：72.0, 冲突数：2
第 200 代，最佳得分：85.0, 冲突数：1
第 300 代，最佳得分：92.0, 冲突数：0
第 400 代，最佳得分：95.0, 冲突数：0

=== 排课结果 ===
生成课程数：20
冲突数：0
优化得分：95.00

结果已保存到 scheduling_result.json
```

---

## 🌐 第三步：测试 API 接口

### 1. 启动后端服务

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 访问 Swagger UI

打开浏览器访问：http://localhost:8000/docs

### 3. 测试课表生成接口

**请求**:
```http
POST http://localhost:8000/api/v1/schedules/generate
Content-Type: application/json

{
  "courses": [
    {
      "id": "C001",
      "name": "数学",
      "total_hours": 60,
      "course_type": "medium_class",
      "teacher_ids": ["T001"]
    },
    {
      "id": "C002",
      "name": "英语",
      "total_hours": 60,
      "course_type": "medium_class",
      "teacher_ids": ["T002"]
    }
  ],
  "teachers": [
    {
      "id": "T001",
      "name": "张老师",
      "max_weekly_hours": 20,
      "teaching_subjects": ["数学"]
    },
    {
      "id": "T002",
      "name": "李老师",
      "max_weekly_hours": 20,
      "teaching_subjects": ["英语"]
    }
  ],
  "classrooms": [
    {
      "id": "R001",
      "name": "教室 A101",
      "capacity": 30
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
}
```

**预期响应**:
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
      "is_confirmed": false,
      "has_conflict": false,
      "conflicts": []
    }
  ],
  "conflicts": [],
  "score": 95.5,
  "message": "课表生成成功"
}
```

### 4. 使用 cURL 测试

```bash
curl -X POST http://localhost:8000/api/v1/schedules/generate \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

其中 `test_data.json` 包含上述请求数据。

---

## 💾 第四步：数据库迁移

### 创建迁移脚本

创建文件 `backend/education/migrations/create_education_tables.sql`:

```sql
-- 创建课程排课表
CREATE TABLE IF NOT EXISTS courses_schedules (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    classroom_id INTEGER,
    class_id INTEGER,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    recurrence_pattern VARCHAR(50) DEFAULT 'weekly',
    is_confirmed BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER
);

-- 创建索引
CREATE INDEX idx_schedule_teacher ON courses_schedules(teacher_id);
CREATE INDEX idx_schedule_classroom ON courses_schedules(classroom_id);
CREATE INDEX idx_schedule_class ON courses_schedules(class_id);
CREATE INDEX idx_schedule_day_time ON courses_schedules(day_of_week, start_time, end_time);

-- 创建课表冲突表
CREATE TABLE IF NOT EXISTS schedule_conflicts (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES courses_schedules(id),
    conflict_type VARCHAR(50) NOT NULL,
    description VARCHAR(500) NOT NULL,
    related_schedule_ids VARCHAR(1000),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by INTEGER
);

-- 创建学员表
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    birth_date DATE,
    grade VARCHAR(50),
    school VARCHAR(200),
    phone VARCHAR(20),
    email VARCHAR(100),
    id_card_number VARCHAR(18),
    avatar_url VARCHAR(500),
    status VARCHAR(20) DEFAULT '在读',
    enrollment_date DATE NOT NULL,
    graduation_date DATE,
    current_class_id INTEGER,
    total_purchased_hours INTEGER DEFAULT 0,
    total_consumed_hours INTEGER DEFAULT 0,
    remaining_hours INTEGER DEFAULT 0,
    emergency_contact VARCHAR(100),
    emergency_phone VARCHAR(20),
    custom_fields TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER
);

-- 创建家长信息表
CREATE TABLE IF NOT EXISTS parent_info (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    relationship_type VARCHAR(20) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    wechat VARCHAR(50),
    qq VARCHAR(20),
    address VARCHAR(500),
    is_primary BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建教师表
CREATE TABLE IF NOT EXISTS teachers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10),
    birth_date DATE,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    id_card_number VARCHAR(18),
    hire_date DATE NOT NULL,
    employment_type VARCHAR(20) DEFAULT 'full_time',
    base_salary DECIMAL(10,2) DEFAULT 0,
    position_allowance DECIMAL(10,2) DEFAULT 0,
    teacher_certificate VARCHAR(500),
    qualifications TEXT,
    teaching_subjects VARCHAR(500),
    max_weekly_hours INTEGER DEFAULT 40,
    preferred_teaching_times TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active',
    avatar_url VARCHAR(500),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER
);

-- 创建授课记录表
CREATE TABLE IF NOT EXISTS teaching_records (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER REFERENCES teachers(id),
    schedule_id INTEGER REFERENCES courses_schedules(id),
    course_id INTEGER NOT NULL,
    class_id INTEGER,
    teaching_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL,
    course_type VARCHAR(50) NOT NULL,
    class_size INTEGER NOT NULL,
    hourly_rate DECIMAL(10,2) DEFAULT 0,
    teaching_income DECIMAL(10,2) DEFAULT 0,
    month VARCHAR(7) NOT NULL,
    status VARCHAR(20) DEFAULT 'completed',
    is_confirmed BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    confirmed_by INTEGER
);

-- 创建教师工资表
CREATE TABLE IF NOT EXISTS teacher_salaries (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER REFERENCES teachers(id),
    month VARCHAR(7) NOT NULL UNIQUE,
    base_salary DECIMAL(10,2) DEFAULT 0,
    teaching_income DECIMAL(10,2) DEFAULT 0,
    performance_bonus DECIMAL(10,2) DEFAULT 0,
    attendance_bonus DECIMAL(10,2) DEFAULT 0,
    renewal_bonus DECIMAL(10,2) DEFAULT 0,
    competition_bonus DECIMAL(10,2) DEFAULT 0,
    late_deduction DECIMAL(10,2) DEFAULT 0,
    accident_deduction DECIMAL(10,2) DEFAULT 0,
    complaint_deduction DECIMAL(10,2) DEFAULT 0,
    other_deductions DECIMAL(10,2) DEFAULT 0,
    gross_salary DECIMAL(10,2) DEFAULT 0,
    social_security DECIMAL(10,2) DEFAULT 0,
    housing_fund DECIMAL(10,2) DEFAULT 0,
    tax DECIMAL(10,2) DEFAULT 0,
    net_salary DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    paid_date DATE,
    paid_by INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入测试数据
INSERT INTO teachers (id, name, phone, hire_date, base_salary, teaching_subjects) VALUES
(1, '张老师', '13800138001', '2020-09-01', 5000, '["数学"]'),
(2, '李老师', '13800138002', '2021-09-01', 5000, '["英语"]');

INSERT INTO students (id, name, gender, enrollment_date, current_class_id, remaining_hours) VALUES
(1, '张三', 'male', '2025-09-01', 1, 60),
(2, '李四', 'female', '2025-09-01', 1, 60);

INSERT INTO parent_info (student_id, name, relationship_type, phone, is_primary) VALUES
(1, '张父', '父亲', '13900139001', true),
(2, '李母', '母亲', '13900139002', true);
```

### 执行迁移

```bash
# 连接到数据库
psql -U postgres -d imato

# 执行迁移脚本
\i education/migrations/create_education_tables.sql
```

---

## 🎨 第五步：前端测试

### 1. 启动开发服务器

```bash
ng serve --host 0.0.0.0
```

### 2. 访问应用

打开浏览器访问：http://localhost:4200

### 3. 创建测试组件

创建文件 `src/app/education/management/scheduling/schedule-test.component.ts`:

```typescript
import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'edu-schedule-test',
  template: `
    <div class="container">
      <h1>排课系统测试</h1>
      
      <button (click)="generateSchedule()" [disabled]="loading">
        {{ loading ? '生成中...' : '生成课表' }}
      </button>
      
      <div *ngIf="result">
        <h2>结果</h2>
        <p>成功：{{ result.success }}</p>
        <p>课程数：{{ result.schedule.length }}</p>
        <p>冲突数：{{ result.conflicts.length }}</p>
        <p>得分：{{ result.score }}</p>
        
        <h3>课表列表</h3>
        <ul>
          <li *ngFor="let s of result.schedule">
            {{ s.course_name }} - {{ s.teacher_name }} - 
            周{{ s.day_of_week }} {{ s.start_time }}-{{ s.end_time }}
          </li>
        </ul>
      </div>
    </div>
  `,
  styles: [`
    .container { padding: 20px; }
    button { padding: 10px 20px; margin: 10px 0; }
    h1, h2, h3 { color: #333; }
  `]
})
export class ScheduleTestComponent implements OnInit {
  loading = false;
  result: any = null;
  
  constructor(private http: HttpClient) {}
  
  ngOnInit() {}
  
  generateSchedule() {
    this.loading = true;
    
    const testData = {
      courses: [
        { id: 'C001', name: '数学', total_hours: 60, course_type: 'medium_class', teacher_ids: ['T001'] }
      ],
      teachers: [
        { id: 'T001', name: '张老师', max_weekly_hours: 20, teaching_subjects: ['数学'] }
      ],
      classrooms: [
        { id: 'R001', name: '教室 A101', capacity: 30 }
      ],
      classes: [
        { id: 'CL001', name: '初三 (1) 班', student_count: 25 }
      ],
      constraints: {
        hard_constraints: [],
        soft_constraints: []
      },
      options: {
        population_size: 100,
        generations: 1000,
        mutation_rate: 0.1
      }
    };
    
    this.http.post('/api/v1/schedules/generate', testData)
      .subscribe({
        next: (res) => {
          this.result = res;
          this.loading = false;
        },
        error: (err) => {
          console.error(err);
          this.loading = false;
        }
      });
  }
}
```

---

## ✅ 验证清单

- [ ] 后端服务启动成功
- [ ] Swagger UI 可访问
- [ ] 遗传算法测试通过 (无报错)
- [ ] API 接口测试通过 (返回 200)
- [ ] 数据库表创建成功
- [ ] 前端服务启动成功
- [ ] 测试组件可访问

---

## 🐛 常见问题

### Q1: 遗传算法运行很慢

**A**: 减少迭代次数和种群大小:
```python
algorithm = GeneticSchedulingAlgorithm(
    population_size=50,   # 减少到 50
    generations=200       # 减少到 200
)
```

### Q2: API 返回 404

**A**: 检查路由是否正确注册:
```python
# 确保在 main.py 中有这行
app.include_router(schedules_router)
```

### Q3: 前端编译错误

**A**: 确保安装了所有依赖:
```bash
npm install @angular/cdk @angular/material
```

---

## 📞 获取帮助

如遇到问题，请查阅:
- [EDUCATION_SYSTEM_DEVELOPMENT_GUIDE.md](./EDUCATION_SYSTEM_DEVELOPMENT_GUIDE.md)
- [T1.1_DATA_STRUCTURE_COMPLETE_REPORT.md](./T1.1_DATA_STRUCTURE_COMPLETE_REPORT.md)

---

**最后更新**: 2026-03-27  
**版本**: v2.0.0-alpha
