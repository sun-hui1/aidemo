# 架构重构说明

## 背景
针对"代码生成、审查等功能是否应该放在单独模块中"的问题，进行了架构优化。

## 新架构设计

### 三层架构

```
┌─────────────────────────────────────────┐
│            Agent Layer (对话层)          │
│  - ChatAgent: LLM 交互                  │
│  - Skill Registry: 技能注册             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           Skill Layer (适配层)          │
│  - CodeSkill: 将 Engine 转为 LLM 工具    │
│  - FileSkill: 文件操作适配              │
│  - WeatherSkill: 外部 API 适配           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Engine Layer (业务层)          │
│  - CodeEngine: 核心业务逻辑             │
│    - CodeAnalyzer: 分析                 │
│    - CodeGenerator: 生成                │
│    - CodeReviewer: 审查                 │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           Tools Layer (工具层)          │
│  - CodeTools: 静态方法工具集            │
│  - 直接调用，无需实例化                  │
└─────────────────────────────────────────┘
```

### 各层职责

#### 1. Engine Layer (engines/)
- **职责**: 实现核心业务逻辑
- **特点**: 
  - 专注于算法和逻辑实现
  - 不依赖 LLM 或 Skill 系统
  - 可独立测试和使用
- **示例**: `CodeEngine.analyze_file()`, `CodeEngine.review_code()`

#### 2. Tools Layer (tools/) - **新增**
- **职责**: 提供便捷的工具函数接口
- **特点**:
  - 静态方法，无需实例化
  - 直接封装 Engine 能力
  - 适用于脚本调用、单元测试等场景
- **示例**: `CodeTools.generate_function()`, `CodeTools.review_code()`

#### 3. Skill Layer (skills/)
- **职责**: 将 Engine 能力转换为 LLM 可调用的工具格式
- **特点**:
  - 定义工具 schema (JSON Schema)
  - 参数验证和转换
  - 结果格式化
  - 错误处理标准化
- **示例**: `CodeSkill.get_tools()`, `CodeSkill.call()`

#### 4. Agent Layer (agent/)
- **职责**: LLM 对话管理
- **特点**:
  - 维护对话上下文
  - 调用 Skill Registry
  - 处理工具调用结果

## 为什么需要 Skill 层？

### Skill 层的必要性

1. **LLM 接口标准化**
   - LLM 需要特定的工具格式 (JSON Schema)
   - Skill 层统一处理工具定义
   - Engine 不需要关心 LLM 的接口要求

2. **解耦引擎与 LLM**
   - Engine 可以独立于 LLM 存在
   - 便于单元测试
   - 支持多种调用方式 (直接调用/Skill 调用)

3. **增强可扩展性**
   - 新增技能只需继承 BaseSkill
   - 不影响 Engine 实现
   - 支持热插拔

4. **参数验证和转换**
   - LLM 返回的参数可能不完整
   - Skill 层负责验证和默认值处理
   - 保护 Engine 免受无效输入影响

### 对比：直接使用 Engine vs 通过 Skill 调用

| 场景 | 推荐方式 | 原因 |
|------|---------|------|
| 脚本调用 | `CodeTools.generate_function()` | 简洁，无需实例化 |
| 单元测试 | `CodeEngine.analyze_file()` | 直接测试业务逻辑 |
| LLM 工具调用 | `CodeSkill.get_tools()` | 需要 JSON Schema 定义 |
| 批量处理 | `CodeTools.review_code()` | 静态方法更方便 |

## 使用示例

### 1. 直接工具调用 (推荐用于脚本)
```python
from tools.code_tools import CodeTools

# 生成代码
code = CodeTools.generate_function(
    description='计算两个数的和',
    function_name='add_numbers'
)

# 审查代码
result = CodeTools.review_code(code)
print(f"得分：{result['score']}")
```

### 2. Engine 直接调用 (推荐用于测试)
```python
from engines.code_engine import CodeEngine

engine = CodeEngine()
analysis = engine.analyze_file('my_code.py')
print(analysis['metrics'])
```

### 3. Skill 调用 (LLM 使用)
```python
from skills.code_skill import CodeSkill
from core.skill_registry import SkillRegistry

skill = CodeSkill()
registry = SkillRegistry()
registry.register(skill)

# LLM 会看到这些工具定义
tools = skill.get_tools()
# 每个工具包含 name, description, parameters (JSON Schema)
```

## 文件结构

```
/workspace/
├── engines/              # 业务引擎层
│   └── code_engine/
│       ├── __init__.py   # CodeEngine 统一入口
│       ├── analyzer.py   # 代码分析实现
│       ├── generator.py  # 代码生成实现
│       └── reviewer.py   # 代码审查实现
├── tools/                # 工具层 (新增)
│   ├── __init__.py
│   └── code_tools.py     # CodeTools 静态工具集
├── skills/               # 技能适配层
│   ├── base_skill.py     # 基础技能类
│   ├── code_skill.py     # 代码技能 (封装 CodeEngine)
│   ├── file_skill.py     # 文件技能
│   └── weather_skill.py  # 天气技能
├── agent/                # 对话管理层
│   ├── chat_agent.py
│   └── skill_registry.py
└── core/                 # 基础设施层
    ├── llm_client.py
    └── memory_store.py
```

## 优势总结

1. **职责清晰**: 每层有明确的职责边界
2. **易于测试**: Engine 和 Tools 可独立测试
3. **灵活调用**: 支持多种调用方式
4. **可扩展**: 新增功能不影响现有代码
5. **符合最佳实践**: 分层架构，单一职责原则

## 后续计划

### 已完成 ✅
- [x] 创建 tools/code_tools.py 静态工具层
- [x] 验证三层架构 (Engine/Tools/Skill)
- [x] 所有技能正常注册 (15 个工具)
- [x] 三种使用方式验证通过
- [x] CodeExecSkill 工具格式修复 (execute_python, execute_shell)
- [x] 架构文档更新 (ARCHITECTURE_REFACTOR.md)

### 待完成 📋

#### 高优先级
- [ ] CodeGenerator 的 `modify_function` 方法完善
  - 当前实现较简单，需增强参数替换、返回值修改等功能
- [ ] CodeReviewer 审查规则扩充
  - 增加 PEP8 风格检查
  - 增加安全漏洞检测规则
  - 增加性能问题检测
- [ ] 单元测试覆盖
  - engines/code_engine/ 各模块单元测试
  - tools/code_tools.py 工具函数测试
  - skills/ 各技能适配层测试

#### 中优先级
- [ ] 功能扩展
  - 数据库操作技能 (DatabaseSkill)
  - Git 操作技能 (GitSkill)
  - API 调用技能 (APISkill)
- [ ] 性能优化
  - 语义记忆向量化效率提升
  - 上下文 token 优化策略
  - 懒加载和缓存机制

#### 低优先级
- [ ] 文档完善
  - API 参考文档
  - 贡献指南
  - 使用示例集
- [ ] 工具链
  - pre-commit hooks
  - CI/CD 配置
  - 代码质量检查 (flake8, black, mypy)
