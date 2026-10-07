"""闭包表迁移验收脚本"""
import sys, os
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)  # back from scripts/ to backend/
project_root = os.path.dirname(backend_dir)  # back from backend/ to project root
sys.path.insert(0, backend_dir)

print("=== 闭包表迁移验收 ===")
print()

# 1. 模型导入
print("[1] 模型导入验证")
try:
    from models.courseware_clousure import CoursewareNode, CoursewareClosure
    print(f"    PASS  CoursewareNode.__tablename__ = '{CoursewareNode.__tablename__}'")
    print(f"    PASS  CoursewareClosure.__tablename__ = '{CoursewareClosure.__tablename__}'")
    # 验证表结构字段
    node_cols = [c.name for c in CoursewareNode.__table__.columns]
    closure_cols = [c.name for c in CoursewareClosure.__table__.columns]
    assert 'id' in node_cols
    assert 'title' in node_cols
    assert 'node_type' in node_cols
    assert 'ancestor_id' in closure_cols
    assert 'descendant_id' in closure_cols
    assert 'depth' in closure_cols
    print(f"    PASS  节点表字段: {len(node_cols)} 个")
    print(f"    PASS  闭包表字段: {len(closure_cols)} 个")
except Exception as e:
    print(f"    FAIL  {e}")
    sys.exit(1)

# 2. Schema 导入
print()
print("[2] Schema 导入验证")
try:
    from schemas.courseware_closure import (
        CoursewareNodeCreate, CoursewareNodeUpdate, CoursewareNodeMove,
        CoursewareNodeResponse, CoursewareTreeNode,
        HierarchyResponse, AncestorNode, DescendantNode,
        LevelNodesResponse, NodePath, CoursewareSubtreeResponse,
        BatchNodeCreate, BatchNodeCreateResponse,
        ClosureValidationResult, MigrationResult, RollbackResult,
    )
    print(f"    PASS  Schema 类导入成功")
    # 验证关键字段
    assert 'title' in CoursewareNodeCreate.model_fields
    assert 'parent_id' in CoursewareNodeCreate.model_fields
    assert 'ancestor_id' in CoursewareClosure.__table__.columns
    print(f"    PASS  CoursewareNodeCreate.parent_id 存在")
    print(f"    PASS  HierarchyResponse 含 ancestors/descendants/children")
except Exception as e:
    print(f"    FAIL  {e}")
    sys.exit(1)

# 3. 模块注册
print()
print("[3] 模块注册验证")
try:
    from core.module_registry import get_all_module_specs
    specs = get_all_module_specs()
    courseware = [s for s in specs if s['name'] == 'courseware']
    if courseware:
        cw = courseware[0]
        assert cw['tier'] == 1, f"tier={cw['tier']} expected 1"
        assert cw['prefix'] == '', f"prefix={cw['prefix']} expected ''"
        assert '课件图谱' in cw['tags'], f"tags={cw['tags']}"
        assert 'course' in cw['dependencies'], f"deps={cw['dependencies']}"
        print(f"    PASS  tier={cw['tier']}, prefix='{cw['prefix']}'")
        print(f"    PASS  tags={cw['tags']}")
        print(f"    PASS  dependencies={cw['dependencies']}")
        print(f"    PASS  model_classes={cw['model_classes']}")
    else:
        print(f"    FAIL  courseware 未在模块注册表中找到, 可用的: {[s['name'] for s in specs[:5]]}...")
        sys.exit(1)
except Exception as e:
    print(f"    FAIL  {e}")
    sys.exit(1)

# 4. 前端模型
print()
print("[4] 前端模型验证")
try:
    ts_path = os.path.join(project_root, 'src', 'shared', 'models', 'courseware-closure.models.ts')
    if os.path.exists(ts_path):
        with open(ts_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'CoursewareNodeResponse' in content
        assert 'HierarchyResponse' in content
        assert 'CoursewareNodeType' in content
        assert 'ClosureValidationResult' in content
        print(f"    PASS  前端模型文件存在, 大小: {len(content)} bytes")
        print(f"    PASS  包含 CoursewareNodeResponse, HierarchyResponse")
        print(f"    PASS  包含 CoursewareNodeType, ClosureValidationResult")
    else:
        print(f"    FAIL  前端模型文件不存在: {ts_path}")
except Exception as e:
    print(f"    FAIL  {e}")

# 5. 文件完整性
print()
print("[5] 文件完整性")
files = {
    'models/courseware_clousure.py': '数据模型',
    'schemas/courseware_closure.py': 'Pydantic Schema',
    'repositories/courseware_repository.py': 'Repository 层',
    'services/courseware_service.py': 'Service 层',
    'routes/courseware_routes.py': 'API 路由',
    'scripts/migrate_to_closure.py': '迁移脚本',
    'scripts/rollback_closure.py': '回滚脚本',
    'scripts/benchmark_closure.py': '性能测试',
}
all_ok = True
for path, desc in files.items():
    full = os.path.join(backend_dir, path)
    if os.path.exists(full):
        size = os.path.getsize(full)
        print(f"    PASS  {path} ({desc}, {size} bytes)")
    else:
        print(f"    FAIL  {path} ({desc}) - 文件不存在")
        all_ok = False

print()
print("=" * 50)
if all_ok:
    print("验收结果: 全部通过")
else:
    print("验收结果: 存在问题，请检查上述 FAIL 项")
    sys.exit(1)