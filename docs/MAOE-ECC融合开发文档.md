# MAOE Skill-Native Workflow Compiler 最终开发文档

> 项目：MAOE（Multi-Agent Orchestration Engine）  
> 定位：面向工程任务的 Skill 原生工作流编译、实验与分层调度引擎  
> 参赛方向：第六届“海聚英才”OPC 专项赛极客组  
> 文档类型：工程开发与实现规范  
> 版本：v1.0-final  
> 日期：2026-06-28

## 1. 文档目标

本文档定义 MAOE 下一阶段的完整开发架构。系统不再以“多 Agent 编排”为中心，而以 **Skill 原生工作流编译器** 为中心：先把工程目标编译为能力需求，再搜索、验证、组合和调度 Skills，生成可执行 Workflow，并在有限循环中比较不同成本与质量版本。

核心目标是把现有的任务拆解、复杂度评估、模型路由、Token 预算、DAG 执行和质量门机制，与 Everything Claude Code（ECC）的 Harness 思想融合，形成一个具备以下能力的系统：

1. 能理解用户目标，并自主决定下一步行动。
2. 能把异构 Skill 封装为具有统一输入、输出、前置条件、效果、成本和风险的 Skill Capsule。
3. 能根据 Workflow 的能力缺口检索 Skills，并完成兼容性检查、排序、组合和 DAG 编译。
4. 能生成经济、均衡、质量三种候选 Workflow，在有限实验循环中评估并选择 Pareto 最优版本。
5. 能根据任务类型、复杂度、风险、预算和历史表现分层选择 Agent、Skill、Tool 与模型。
6. 能在失败时诊断原因，替换 Skill、重排 Workflow、切换 Agent 或升级模型。
7. 能持续记录状态、成本、决策理由、产物、质量结果和每个 Skill 的实际贡献。
8. 能在公开路演中实时展示“为什么选择这些 Skills、为什么这样排列、为什么采用该版本”。
9. 能在无人持续输入的情况下，在明确边界内运行至完成或安全停止。


## 2. 设计原则

### 2.1 吸收 ECC 机制，不复制 ECC 规模

ECC 当前仓库已经发展为大型 Agent Harness 系统，包含大量 Agents、Skills、Commands、Hooks、Rules 和跨平台适配器。MAOE 不直接复制完整目录，而是抽取六个关键机制：

1. **分层加载**：始终加载最小规则，领域知识按需加载。
2. **Agent 专业化**：不同 Agent 有明确职责、工具和停止条件。
3. **Skill 复用**：把可重复工作流封装成可发现、可版本化的能力模块。
4. **Command 入口**：把高频复杂工作流封装为稳定命令。
5. **Hook 约束**：在关键生命周期节点自动执行检查、记录和恢复。
6. **Rules 强制执行**：安全、测试和质量要求不能只存在于文件中，必须由运行时验证。

### 2.2 “必读”不等于“文件存在”

一个规则文件存在于仓库，不代表 Agent 实际读取了它。MAOE 必须提供显式加载证据：

- 每个运行任务保存 `loaded_context` 清单。
- 每个文件保存内容哈希、加载时间和加载原因。
- 调度器只允许使用已注册、已加载、版本匹配的能力。
- Quality Gate 检查任务所需规则是否真正加载。
- 路演界面能显示本次任务实际加载了哪些规则和 Skills。

因此，MAOE 的加载逻辑是“Manifest 注册 + Loader 读取 + Trace 证明”，而不是“目录里有文件就假设模型知道”。

### 2.3 自主不等于无限权限

系统自主运行必须受三类边界约束：

- **目标边界**：只能执行用户目标所需工作。
- **资源边界**：受 Token、费用、时间、并发和重试上限约束。
- **安全边界**：部署、删除、权限、密钥和外部消息等操作必须进入风险策略。

### 2.4 对本方案的苛刻批评

在实现前必须承认以下问题：

1. “封装所有 Skill”不是可执行目标。不同 Skill 可能只是知识文档、命令包装、外部 API、长流程或 Agent Prompt，不能假设它们天然具有统一执行语义。
2. Skill 搜索不是创新。关键词或向量检索只能找到相似内容，不能证明 Skill 能接入当前 Workflow。
3. Skill 组合可能产生输入输出不匹配、规则冲突、上下文膨胀、循环依赖和权限叠加。
4. 生成多个版本会直接增加成本。如果没有候选上限、早停和共享中间结果，实验系统会比固定 Workflow 更浪费。
5. 分层 Agent 会产生委派、上下文复制和评估开销。简单任务不应进入完整层级。
6. LLM 自评不能作为唯一质量证据，否则优化器只是在迎合另一个模型。
7. 没有真实基准测试时，“省钱且高效”只是宣传，不是工程结论。

因此，MAOE 不承诺一次性兼容全部 Skills。比赛 MVP 只支持通过 Capsule Schema 验证的 Skills，并将“可组合性、可测量性、可回滚性”作为进入 Registry 的条件。

### 2.5 核心工程创新

MAOE 的创新主张收敛为四点：

1. **Skill Capsule Contract**：将 Prompt、脚本、工具和 Agent 流程统一封装为可类型检查的能力单元。
2. **Workflow Compiler**：从目标生成抽象能力图，再检索和装配 Skills，而不是先选 Agent 再临时调用工具。
3. **Controlled Workflow Experimentation**：只生成有限候选版本，通过共享执行、早停和 Pareto 评估控制试验成本。
4. **Joint Scheduler**：在同一决策中联合选择 Skill、Agent、模型、并发策略和 Token 预算。

这属于工程系统创新，不宣称发明多 Agent、DAG、Skill 或模型路由本身。

### 2.6 核心差异化主张

经过对近期黑客松获奖项目和活跃开源系统的对照，MAOE 尚可主张的核心差异是：

> 在本次检查的项目中，尚未发现一个系统同时完成“类型化 Skill Capsule、能力缺口规划、静态组合检查、候选 Workflow 差异执行、公共产物复用、成本质量 Pareto 选择”。MAOE 将把这六项能力实现为同一个可验证的工程闭环。

这不是全球首创声明，而是基于当前已检查项目的差异化判断。最终是否成立，必须由代码、端到端演示和对照实验共同证明。

六项能力之间不是简单并列关系：

```text
Skill Capsule
  ↓ 提供可计算的输入、输出、效果、风险和成本
能力缺口规划
  ↓ 得到与具体实现无关的 Capability Graph
静态组合检查
  ↓ 排除类型冲突、能力缺口、权限冲突和循环依赖
候选 Workflow 差异执行
  ↓ 只运行候选之间不同的子图
公共产物复用
  ↓ 控制多版本实验的额外成本
Pareto 选择
  ↓ 在质量、费用、延迟和风险之间选择最终方案
```

如果其中任何一项缺失，MAOE 都容易退化为已有方案：

- 没有 Capsule 和静态检查：退化为 Prompt 驱动的 Skill 串联。
- 没有能力缺口规划：退化为关键词搜索和 Agent 路由。
- 没有差异执行与产物复用：多版本实验会直接增加成本。
- 没有 Pareto 选择：所谓“省钱和功效平衡”无法被计算和解释。

## 3. 外部能力筛选与融合

### 3.1 筛选原则

外部能力只有满足以下条件才进入 MAOE：

1. 能直接提高完成率、可解释性、可靠性或演示质量。
2. 能通过独立模块实现，而不是把整个外部框架复制进项目。
3. 能在比赛周期内完成最小可用实现。
4. 能由测试、Trace 或 Benchmark 验证。
5. 不掩盖 MAOE 的核心差异，不把系统重新变成 Agent 配置集合。

筛选结果分为三类：

- **直接采用**：机制成熟，适合进入比赛 MVP。
- **改造采用**：保留核心思想，但按 MAOE 的编译器架构重新实现。
- **暂不采用**：价值存在，但会扩大范围或无法在比赛周期验证。

### 3.2 能力融合矩阵

| 来源 | 已实现能力 | MAOE 决策 | 融入模块 | 验收证据 |
|---|---|---|---|---|
| ECC | Agents、Skills、Commands、Hooks、Rules、分层加载、跨 Harness 适配 | 改造采用 | Loader、Registry、Hook Bus | 加载 Trace 能证明规则和 Skill 被实际读取 |
| Claude Code Workflow Orchestration | 按需加载、轻量启动、任务拆分、依赖分析、波次调度、结构化任务元数据 | 直接采用核心机制 | Planner、DAG Scheduler | 独立节点并行，冲突节点自动串行 |
| Maestro | Express/Standard 双路径、专业 Agent、持久状态、质量门、单一源码生成多运行时配置 | 改造采用 | Complexity Router、State Store、Adapter Generator | 简单任务绕过完整编排；同一 Manifest 可生成两个运行时适配器 |
| Agent Registry Inventory | Agent、Skill、模型和 MCP 统一目录、自动发现、版本化、GitOps、读写 API 分离 | 改造采用 | Skill Registry Control Plane | Skill 可登记、查询、版本锁定和撤销，不引入 Kubernetes 依赖 |
| GitHub Agentic Workflows | 声明式 Workflow、编译步骤、生成锁定文件 | 直接采用思想 | Workflow Compiler、Lockfile | 同一输入生成确定性 `workflow.lock.json` |
| XSkill | 从运行轨迹提炼任务级 Skill 和行动经验 | 后置采用 | Experience Miner | 只生成候选 Skill，不直接进入生产 Registry |
| SkillClaw | Skill 去重、验证、版本历史、共享和可视化 | 改造采用 | Skill Curator、Version Store | 重复 Skill 被合并；版本升级可回滚 |
| EvoSkill | 从失败轨迹发现和合成可复用 Skill | 后置采用 | Failure Miner | 失败模式达到阈值后产生待验证 Capsule |
| MCP Security Governance | 确定性评分、工具暴露统计、策略检查、LLM 独立解释 | 直接采用核心机制 | Policy Engine、Risk Scorer | 确定性分数与 LLM 解释分开显示 |
| Frugalia | 垂直闭环、定时与事件触发、安全前置检查、审批后执行、真实成本优化 | 直接采用产品方法 | Trigger Runtime、Approval Gate | 定时、事件、手动三种触发进入同一 Workflow |
| Engagement Hub | 父子 Agent、结构化 JSON、重复安全写入、人工确认、关联 ID、完整审计日志 | 直接采用工程机制 | Run Context、Audit Log、Human Gate | 每次动作可通过 correlation ID 重放和追踪 |

### 3.3 从 ECC 采用的最小 Harness

MAOE 不复制 ECC 的大规模目录，只保留比赛 MVP 必需部分：

```text
ECC Mechanism                  MAOE Implementation
────────────────────────────────────────────────────
Agent definitions          →  Agent Capsule
Skill documents            →  Skill Capsule
Commands                   →  Typed Workflow Entry
Hooks                      →  Event Hook Bus
Rules                      →  Executable Policy
Session memory             →  Run State + Checkpoint
Cross-harness adapters     →  Generated Runtime Adapter
```

关键变化是把 Markdown 描述转换为可执行契约。规则不能只靠模型记住，必须由 Policy Engine 检查；Skill 不能只靠描述匹配，必须通过 Capsule Schema 和组合检查。

### 3.4 从动态编排项目采用的能力

直接吸收以下成熟模式：

- 使用轻量 Stub 启动，完整编排说明按需加载，减少固定上下文成本。
- 将任务节点按依赖关系分为执行波次。
- 默认隔离执行节点；只有确实需要共享上下文时才启用协作 Agent。
- 简单任务走 Express Path，避免创建多 Agent 团队。
- 每个 Agent 只返回结构化结果和产物路径，不把完整会话复制回主上下文。
- 保存阶段报告、验证结果和阻塞原因，禁止静默失败。

MAOE 不采用关键词匹配 Agent 作为最终方案。关键词只用于候选召回，最终选择由 Capsule 契约、历史表现、预算和风险共同决定。

### 3.5 从 Registry 与 GitOps 项目采用的能力

Skill Registry 采用控制面设计：

- Git 仓库作为 Skill Capsule 的事实来源。
- Registry 保存索引、版本、认证等级、运行统计和撤销状态。
- 读 API 与管理 API 分离。
- Workflow Lockfile 固定本次运行使用的 Skill、Agent、模型和版本。
- Registry 更新不自动影响正在运行的 Workflow。
- Skill 被撤销后，新的 Workflow 禁止选择，历史运行仍可重放。

比赛 MVP 使用 SQLite 和本地文件，不引入 Kubernetes CRD。未来企业版再提供远程 Registry 和多环境同步。

### 3.6 从 Skill 学习项目采用的能力

MAOE 采用“候选生成与生产晋升分离”的模式：

```text
运行轨迹 / 失败轨迹
  ↓
Experience Miner
  ↓
候选 Skill Capsule
  ↓
去重与冲突检查
  ↓
沙箱基准验证
  ↓
人工或策略批准
  ↓
Verified Registry
```

自主学习不能直接修改生产 Skill。每次晋升必须保留来源轨迹、测试结果、版本差异和回滚点。

### 3.7 从获奖垂直项目采用的工程机制

近期获奖项目共同说明：评委更容易认可“完整解决一个真实问题”，而不是“拥有很多 Agent”。MAOE 的演示也必须是垂直闭环：

1. 接收一个真实 Python 工程目标。
2. 读取仓库并形成 Goal IR。
3. 检索 Skill Capsule。
4. 拒绝一个输入输出不兼容的 Skill。
5. 编译 Economy、Balanced、Quality 三个 Workflow。
6. 共享分析和依赖安装等公共产物。
7. 执行推荐版本并注入一次可恢复失败。
8. 替换 Skill 或局部重编译失败子图。
9. 通过测试、静态检查和 Reviewer 验收。
10. 展示最终成本、质量、耗时、审计日志和 correlation ID。

### 3.8 明确不采用的能力

比赛版本暂不采用：

- 数十或数百个专业 Agent。
- Kubernetes 原生控制面和多集群部署。
- 未经验证的自动 Skill 晋升。
- 全平台同时适配。
- Agent 之间无限自由通信。
- 依赖 LLM 的唯一质量评分。
- 每个任务都运行三个完整版本。
- 为展示复杂度而引入的区块链、支付或分布式共识。

## 4. 总体架构

```text
┌───────────────────────────────────────────────────────────────┐
│ Interface Layer                                               │
│ CLI / REST API / Web Demo / OpenCode Adapter                  │
├───────────────────────────────────────────────────────────────┤
│ Context and Capability Bootstrap                              │
│ Manifest Loader / Seven Core Files / Skill Capability Index   │
├───────────────────────────────────────────────────────────────┤
│ Skill-Native Workflow Compiler                                │
│ Goal IR / Capability Graph / Skill Search / Type Check / DAG   │
├───────────────────────────────────────────────────────────────┤
│ Candidate Workflow Laboratory                                 │
│ Economy / Balanced / Quality / Evaluator / Pareto Selector     │
├───────────────────────────────────────────────────────────────┤
│ Hierarchical Orchestration Runtime                            │
│ DAG Scheduler / Agent Layers / Event Bus / State Machine       │
├───────────────────────────────────────────────────────────────┤
│ Joint Optimization Services                                  │
│ Skill Router / Model Router / Token Economist / Memory         │
├───────────────────────────────────────────────────────────────┤
│ Execution, Verification and Recovery                         │
│ Agents / Tools / Quality Gate / Replace / Retry / Rollback     │
├───────────────────────────────────────────────────────────────┤
│ Observability and Demo                                        │
│ Trace / Cost / Timeline / DAG / Artifacts / Decision Reasons  │
└───────────────────────────────────────────────────────────────┘
```

### 4.1 核心执行闭环

```text
用户目标
  ↓
加载项目上下文与强制规则
  ↓
目标解释并生成 Goal IR
  ↓
构建抽象能力图和验收标准
  ↓
搜索 Skill Capsule 并完成类型检查
  ↓
生成经济、均衡、质量三种候选 Workflow
  ↓
预测并筛除明显劣势版本
  ↓
为候选节点联合选择 Agent、模型、并发策略和预算
  ↓
执行可并行节点
  ↓
收集工具结果与产物
  ↓
质量验证
  ├─ 通过：提交节点结果，解锁后继节点
  ├─ 可恢复失败：补上下文或同级重试
  ├─ Skill 不适配：替换 Skill 并局部重编译
  ├─ 能力不足：升级模型或更换 Agent
  └─ 超出边界：安全停止并报告阻塞
  ↓
比较候选版本并选择 Pareto 最优 Workflow
  ↓
生成结果、Skill 贡献、决策记录、成本报告与演示数据
```

## 5. 七个核心加载文件

MAOE 采用 ECC 的项目级 Harness 思路，规定七个核心文件。它们不是全部上下文，而是启动阶段的最小控制面。

| 文件 | 作用 | 加载策略 |
|---|---|---|
| `MAOE.md` | 项目目标、范围、架构摘要 | 每次任务始终加载 |
| `AGENTS.md` | Agent 职责、工具、输入输出和委派规则 | 每次任务始终加载 |
| `RULES.md` | 安全、测试、代码质量和权限规则 | 每次任务始终加载 |
| `SOUL.md` | 系统决策价值：成本、质量、透明度和克制 | 每次任务始终加载 |
| `WORKING-CONTEXT.md` | 当前里程碑、已知问题、近期决策 | 会话启动和恢复时加载 |
| `COMMANDS-QUICK-REF.md` | 稳定工作流入口及参数 | 规划阶段加载索引，命中后加载正文 |
| `.maoe/manifest.yaml` | Skills、Agents、Hooks、Tools 和版本注册表 | 由 Loader 解析，禁止直接拼接全文 |

### 5.1 加载结果数据结构

```json
{
  "run_id": "run-20260628-001",
  "loaded_context": [
    {
      "path": "RULES.md",
      "sha256": "...",
      "reason": "mandatory",
      "loaded_at": "2026-06-28T01:00:00+08:00"
    },
    {
      "path": "skills/python-tdd/SKILL.md",
      "sha256": "...",
      "reason": "task_language=python and change_type=feature",
      "loaded_at": "2026-06-28T01:00:02+08:00"
    }
  ]
}
```

### 5.2 上下文预算

Loader 必须执行以下预算策略：

- 始终加载文件总量控制在上下文预算的 10% 以内。
- Agent 描述只加载名称、用途和触发条件。
- Skill 初始只加载元数据，命中后再加载正文。
- 大型参考资料以文件路径和摘要传递，不整份内联。
- 每个阶段结束后生成结构化摘要，再进行上下文压缩。

## 6. 目录结构

```text
maoe/
├── MAOE.md
├── AGENTS.md
├── RULES.md
├── SOUL.md
├── WORKING-CONTEXT.md
├── COMMANDS-QUICK-REF.md
├── .maoe/
│   ├── manifest.yaml
│   ├── runtime.yaml
│   ├── model-registry.yaml
│   ├── skill-registry.json
│   ├── policies/
│   │   ├── permissions.yaml
│   │   ├── escalation.yaml
│   │   └── quality-gates.yaml
│   └── schemas/
│       ├── agent.schema.json
│       ├── skill.schema.json
│       ├── command.schema.json
│       └── event.schema.json
├── agents/
│   ├── planner.md
│   ├── architect.md
│   ├── code-agent.md
│   ├── test-agent.md
│   ├── review-agent.md
│   ├── debug-agent.md
│   ├── research-agent.md
│   └── loop-operator.md
├── skills/
│   ├── task-decomposition/
│   ├── cost-aware-routing/
│   ├── python-tdd/
│   ├── quality-verification/
│   └── recovery-loop/
├── commands/
│   ├── build.md
│   ├── plan.md
│   ├── route.md
│   ├── run.md
│   ├── resume.md
│   └── report.md
├── hooks/
│   ├── hooks.yaml
│   └── handlers/
├── src/maoe/
│   ├── bootstrap/
│   ├── compiler/
│   │   ├── goal_ir.py
│   │   ├── capability_graph.py
│   │   ├── skill_retriever.py
│   │   ├── type_checker.py
│   │   └── workflow_compiler.py
│   ├── decision/
│   ├── scheduler/
│   ├── registry/
│   ├── experiments/
│   │   ├── candidate_generator.py
│   │   ├── evaluator.py
│   │   ├── pareto_selector.py
│   │   └── early_stopper.py
│   ├── runtime/
│   ├── observability/
│   └── adapters/
├── tests/
├── benchmarks/
└── demo/
```

## 7. Agent 系统

### 7.1 Agent 定义规范

每个 Agent 使用 Markdown + YAML frontmatter 定义，保持可读、可版本化：

```yaml
---
name: code-agent
description: 实现已批准的代码节点，不负责改变需求或架构
capabilities: [python, refactor, implementation]
tools: [read_file, search, apply_patch, run_tests]
preferred_tier: balanced
max_retries: 2
risk_level: medium
input_schema: schemas/code-agent-input.json
output_schema: schemas/agent-result.json
stop_conditions:
  - acceptance_tests_pass
  - blocked_by_missing_requirement
  - budget_exhausted
---
```

Agent 正文只描述职责、执行顺序、禁止事项和交付格式。所有 Agent 必须返回统一结构：

```json
{
  "status": "success|warning|error|blocked",
  "summary": "一句话结果",
  "artifacts": ["path/to/file"],
  "evidence": ["test command and result"],
  "next_actions": [],
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0,
    "cost": 0
  }
}
```

### 7.2 第一阶段 Agent 集合

| Agent | 职责 | 典型触发条件 |
|---|---|---|
| Planner | 目标澄清、任务拆分、DAG 与验收标准 | 复杂目标或多文件任务 |
| Skill Curator | 将原始 Skill 转换、验证并登记为 Capsule | 新 Skill 导入或版本升级 |
| Workflow Compiler | 从能力图绑定 Skills 并生成候选 DAG | Goal IR 已生成 |
| Architect | 架构决策、接口边界、风险分析 | 高复杂度或跨模块变更 |
| Code Agent | 按计划实现代码 | 已有明确节点和验收标准 |
| Test Agent | 生成和运行单元、集成、端到端测试 | 新功能或修复完成后 |
| Review Agent | 独立审查正确性、维护性和需求覆盖 | 代码节点准备完成时 |
| Debug Agent | 根据失败证据定位根因并最小修复 | 测试、构建或运行失败 |
| Research Agent | 查阅官方文档和已有实现 | 外部 API 或不确定技术点 |
| Loop Operator | 监控自主循环、识别停滞和触发终止 | 长任务和无人值守运行 |

### 7.3 Agent 分层

Agent 层级只在任务复杂度需要时启用：

```text
L0 Deterministic Tool
   格式化、读取、测试命令等确定性动作

L1 Worker Agent
   Code、Test、Debug、Research 等单职责执行者

L2 Workflow Agent
   Planner、Workflow Compiler、Reviewer、Loop Operator

L3 Arbiter Agent
   只处理架构冲突、高风险决策和最终质量仲裁
```

调度规则：能由 Tool 完成的任务不启用 Worker；能由 Worker 完成的任务不启用完整 Agent 团队；只有跨节点冲突或高风险问题才升级到 Arbiter。

### 7.4 Agent 选择

Agent 选择不是固定映射，而是约束优化：

```text
agent_score =
  capability_match × 0.35
  + historical_success × 0.20
  + tool_fit × 0.15
  + context_fit × 0.10
  + expected_quality × 0.15
  - expected_cost × 0.05
```

若两个 Agent 分数接近，可由 Planner 产生候选方案，再由 Policy Engine 依据风险和预算决定。

## 8. Skill 系统

### 8.1 Skill 与 Agent 的区别

- Agent 是承担责任的执行角色。
- Skill 是 Agent 可加载的知识和流程。
- Command 是用户或系统触发完整工作流的稳定入口。
- Tool 是执行确定性动作的原子能力。

### 8.2 Skill 元数据

```yaml
---
name: python-tdd
description: Python 功能开发的测试驱动流程
triggers:
  languages: [python]
  task_types: [feature, bugfix]
requires: [pytest]
compatible_agents: [code-agent, test-agent, debug-agent]
context_cost: 1800
version: 1.0.0
---
```

### 8.3 Skill 发现流程

1. Planner 提取任务标签。
2. Skill Registry 根据标签、依赖和语言检索候选 Skill。
3. Token Economist 评估加载成本。
4. Policy Engine 过滤权限不匹配或风险过高的 Skill。
5. Loader 加载必要 Skill 正文并写入 Trace。
6. Agent 执行后记录 Skill 对完成率、重试和成本的影响。

### 8.4 Skill Capsule Contract

所有可调度 Skill 必须通过统一 Capsule 契约。原始 ECC Skill、项目 Skill 或第三方 Skill 先由 Adapter 转换，再进入 Registry。

```yaml
id: python.pytest.unit-test-generator
version: 1.0.0
kind: workflow
description: 为 Python 模块生成并执行 pytest 单元测试

capabilities:
  provides: [test.plan, test.generate, test.execute]
  requires: [source.python, filesystem.write, shell.pytest]

inputs:
  source_files:
    type: array[path]
    required: true
  acceptance_criteria:
    type: array[string]
    required: true

outputs:
  test_files:
    type: array[path]
  test_report:
    type: test-report/v1

preconditions:
  - python_project_detected
  - pytest_available

effects:
  filesystem: write
  network: none
  external_side_effects: false

resources:
  expected_tokens: 5000
  expected_seconds: 90
  expected_cost: 0.01

risk:
  level: medium
  rollback: git_restore_generated_tests

quality:
  validators: [pytest_exit_zero, coverage_non_regression]
  minimum_score: 0.85
```

Capsule 的关键不是统一文件格式，而是提供可计算的组合语义：`requires` 必须由上游节点或运行环境满足，`provides` 必须能填补能力图中的缺口，`effects` 决定权限和冲突，`quality.validators` 决定如何验收。

### 8.5 Skill 认证等级

| 等级 | 条件 | 调度策略 |
|---|---|---|
| Unverified | 只有元数据，未运行验证 | 不进入自主模式 |
| Compatible | Schema、依赖和权限检查通过 | 可进入沙箱实验 |
| Verified | 基准任务达到最低完成率 | 可进入候选 Workflow |
| Trusted | 多次运行稳定且无高风险记录 | 可在低风险任务中自动选择 |

### 8.6 Skill Capability Graph

Registry 不只保存 Skill 列表，还建立能力图：

```text
source.python
  ├─[python-analyzer]→ code.structure
  ├─[test-generator]→ test.files
  └─[security-scanner]→ security.report

code.structure + requirement.spec
  └─[code-agent-skill]→ source.modified

source.modified + test.files
  └─[pytest-runner]→ test.report
```

搜索分两阶段进行：

1. **召回**：按 capability、标签、语言和语义相似度寻找候选。
2. **重排**：按契约匹配度、历史成功率、成本、延迟、风险和上下文开销排序。

建议评分：

```text
skill_score =
  contract_match × 0.30
  + capability_coverage × 0.20
  + historical_success × 0.15
  + quality_score × 0.15
  + environment_fit × 0.10
  - normalized_cost × 0.05
  - normalized_risk × 0.05
```

### 8.7 Workflow Compiler

Workflow Compiler 采用五步编译流程：

1. **Goal Lowering**：把自然语言目标转换成 Goal IR。
2. **Capability Planning**：生成不绑定具体 Skill 的抽象能力图。
3. **Skill Binding**：为每个能力节点召回和绑定候选 Skills。
4. **Static Validation**：执行输入输出类型、依赖、权限、冲突和循环检查。
5. **Executable DAG Emission**：生成包含 Agent、模型、预算、验证器和回滚动作的可执行 DAG。

Goal IR 示例：

```json
{
  "goal": "为 FastAPI 项目增加 JWT 登录并通过测试",
  "deliverables": ["source.modified", "test.report", "security.report"],
  "constraints": {
    "budget": 0.5,
    "deadline_seconds": 900,
    "network_write": false
  },
  "quality": {
    "tests_pass": true,
    "security_high_findings": 0
  }
}
```

### 8.8 组合类型检查

编译失败必须发生在执行前。至少检查：

- 上游 `provides` 是否满足下游 `requires`。
- 数据 schema 和版本是否兼容。
- 两个并行 Skill 是否写入相同文件或共享资源。
- Rule 和权限是否冲突。
- 依赖图是否成环。
- 总成本、Token 和预计时间是否超预算。
- 每个关键产物是否有对应 Validator。

### 8.9 三版本受控实验

系统最多生成三个候选版本：

| 版本 | 目标 | 策略 |
|---|---|---|
| Economy | 最低成本下达到最低质量门 | 少量 Skills、轻量模型、较高复用 |
| Balanced | 成本与质量综合最优 | 默认候选，允许一次升级 |
| Quality | 最大化成功率和审查强度 | 强模型、独立 Reviewer、更多验证 |

三个版本不是从头重复执行。Compiler 识别公共前缀和可复用产物，只对有差异的子图进行实验。

```text
Shared Prefix
  ├─ Economy Branch
  ├─ Balanced Branch
  └─ Quality Branch
       ↓
Unified Evaluator
       ↓
Pareto Selector
```

### 8.10 实验循环与早停

```text
生成候选
  → 静态成本与风险预测
  → 删除被严格支配的候选
  → 执行最便宜的可行候选
  → 质量达标则记录 Pareto 点
  → 质量不足时只执行差异子图
  → 达到预算、质量或循环上限后停止
```

硬限制：

- 候选版本最多 3 个。
- Workflow 重编译最多 2 次。
- 单节点重试最多 2 次。
- 可复用产物按内容哈希缓存。
- 达到用户质量阈值后，不再运行预期收益低于成本的候选。

### 8.11 Pareto 选择

每个候选记录四个主要指标：质量、成本、延迟和风险。Selector 不把它们粗暴压成单一分数，而先计算 Pareto 前沿，再根据用户偏好选择：

```text
maximize quality, reliability
minimize cost, latency, risk

subject to:
  cost <= user_budget
  latency <= deadline
  quality >= minimum_quality
  risk <= allowed_risk
```

用户最终获得：推荐版本、低成本版本和高质量版本的差异，而不是三个无法解释的结果。

## 9. Command 系统

Commands 只承担稳定入口和参数解析，不复制 Skill 正文。第一阶段提供：

| Command | 功能 |
|---|---|
| `maoe plan "目标"` | 生成 DAG、验收标准、预算和风险计划 |
| `maoe run "目标"` | 规划并执行完整自主循环 |
| `maoe route "任务"` | 仅展示 Agent、Skill 和模型路由结果 |
| `maoe resume RUN_ID` | 从检查点恢复任务 |
| `maoe status RUN_ID` | 查看节点、成本、风险和活动 Agent |
| `maoe report RUN_ID` | 导出决策、Token、质量和产物报告 |
| `maoe skills search "能力"` | 检索并解释候选 Skill Capsule |
| `maoe skills validate PATH` | 验证 Skill 契约、依赖和风险 |
| `maoe compile "目标"` | 输出三种候选 Workflow，不执行 |
| `maoe experiment RUN_ID` | 在预算内运行候选差异子图 |

Command 必须有类型化参数、明确退出码和机器可读 JSON 输出。

### 9.1 Skill 调度 API

```http
POST /api/v1/goals/parse
POST /api/v1/skills/search
POST /api/v1/skills/validate
POST /api/v1/workflows/compile
POST /api/v1/workflows/{id}/run
POST /api/v1/runs/{id}/experiment
GET  /api/v1/runs/{id}
GET  /api/v1/runs/{id}/pareto
POST /api/v1/runs/{id}/feedback
```

`POST /api/v1/workflows/compile` 返回：

```json
{
  "goal_ir": {},
  "capability_graph": {},
  "candidates": [
    {
      "variant": "economy",
      "workflow_id": "wf-economy-01",
      "skills": [],
      "dag": {},
      "estimated_cost": 0.08,
      "estimated_seconds": 120,
      "predicted_quality": 0.78,
      "risks": []
    }
  ],
  "recommendation": "balanced"
}
```

## 10. 自主决策引擎

### 10.1 决策输入

每次决策读取以下信息：

- 用户目标与明确约束。
- Goal IR、能力图和候选 Workflow。
- Skill Capsule 的契约、认证等级和历史表现。
- 当前 DAG 状态和已完成产物。
- Agent 与 Skill 能力注册表。
- 模型可用性、费用、上下文和成功率。
- 剩余 Token、费用、时间和重试预算。
- 最近一次失败类型及恢复历史。
- 安全策略与权限等级。

### 10.2 决策输出

```json
{
  "decision_id": "dec-018",
  "action": "execute_subtask",
  "subtask_id": "st-4",
  "workflow_variant": "balanced",
  "agent": "test-agent",
  "skills": ["python-tdd", "quality-verification"],
  "model_tier": "fast",
  "parallel_group": "layer-2",
  "budget": {"tokens": 6000, "cost": 0.02},
  "reason": "任务确定性高且已有实现产物，轻量模型足够完成测试生成",
  "fallback": "升级 balanced tier 并委派 debug-agent",
  "replaceable_skill_candidates": ["python.unittest.generator"],
  "stop_condition": "tests_pass_or_two_failures"
}
```

### 10.3 决策状态机

```text
CREATED
  → CONTEXT_LOADED
  → PLANNED
  → READY
  → RUNNING
      ├─ WAITING_DEPENDENCY
      ├─ VERIFYING
      ├─ RETRYING
      ├─ ESCALATING
      └─ BLOCKED
  → COMPLETED | FAILED | STOPPED
```

每次状态变化必须发出事件并写入 Decision Ledger，禁止静默跳转。

## 11. 自动调度

### 11.1 DAG 调度

Task Parser 输出节点及依赖关系。Scheduler 使用拓扑分层：

- 同一层且无资源冲突的节点并行执行。
- 修改同一文件或共享状态的节点串行执行。
- 测试、审查节点只能在对应实现节点完成后启动。
- 高风险节点进入独立队列。
- 节点失败不会自动污染后继节点。

### 11.2 并发控制

```yaml
runtime:
  max_concurrency: 4
  max_parallel_llm_calls: 3
  per_provider_limit: 2
  file_locking: true
  worktree_isolation: optional
```

### 11.3 调度优先级

```text
priority =
  critical_path_weight
  + dependency_unlock_value
  + user_priority
  + experiment_information_gain
  + failure_recovery_urgency
  - expected_cost
  - resource_contention
```

### 11.4 联合调度目标

调度器不能先固定 Workflow，再分别优化 Agent 和模型。它应对完整执行策略联合决策：

```text
ExecutionPolicy =
  WorkflowVariant
  + SkillBinding
  + AgentAssignment
  + ModelTier
  + ParallelPlan
  + TokenBudget
```

优化器第一阶段采用可解释的规则和 Pareto 搜索，不在比赛版本中引入不可验证的强化学习。运行数据积累后，可升级为 contextual bandit，对 Skill、Agent 和模型组合的成功率进行在线更新。

## 12. 模型路由与 Token 经济系统

### 12.1 模型分层

| 层级 | 用途 | 示例任务 |
|---|---|---|
| Fast | 低风险、确定性、机械任务 | 格式化、测试生成、摘要 |
| Balanced | 常规编码和调试 | 单模块实现、普通修复 |
| Powerful | 复杂推理和跨模块变更 | 重构、复杂故障分析 |
| Critical | 架构、高风险审查、最终仲裁 | 架构决策、安全关键任务 |

模型名称由 Registry 配置，业务逻辑只依赖层级和能力，禁止在调度器中硬编码供应商。

### 12.2 路由因素

- 任务复杂度。
- 错误代价和可逆性。
- 所需上下文长度。
- 是否需要视觉、代码或强推理能力。
- 历史成功率。
- 剩余预算。
- 供应商健康状态和延迟。
- Skill 的历史成本、成功率和上下文开销。
- 候选 Workflow 的公共前缀与缓存命中率。

### 12.3 渐进式升级

```text
Fast 执行
  ├─ 质量通过：结束
  └─ 质量失败：分析失败类型
       ├─ Prompt/上下文不足：补上下文后同级重试一次
       ├─ 能力不足：升级 Balanced
       ├─ 复杂推理不足：升级 Powerful
       └─ 高风险冲突：Critical 仲裁或安全停止
```

升级必须有原因，不能因为一次网络错误直接切换最昂贵模型。

## 13. Hook 与事件系统

借鉴 ECC 的生命周期 Hook，MAOE 定义统一事件总线：

| 事件 | 默认 Hook |
|---|---|
| `run.created` | 建立运行目录和 Decision Ledger |
| `context.loaded` | 校验七个核心文件及哈希 |
| `plan.created` | 验证 DAG、预算和验收标准 |
| `agent.before` | 检查权限、上下文和工具白名单 |
| `tool.before` | 计算风险，拦截危险操作 |
| `tool.after` | 记录结果、耗时、产物和错误 |
| `subtask.completed` | 运行节点级 Quality Gate |
| `subtask.failed` | 触发恢复分类器 |
| `run.compacting` | 保存检查点和结构化摘要 |
| `run.idle` | 检测停滞和死循环 |
| `run.completed` | 运行全局验收并生成报告 |

Hook 必须满足：幂等、超时、可禁用、可审计、不能无限递归。

## 14. 质量门与恢复循环

### 14.1 Quality Gate

每个节点必须提供：

- 明确验收标准。
- 产物路径。
- 可重复验证命令。
- 测试或静态检查结果。
- Agent 自评与独立 Reviewer 结果。

Quality Gate 不能在 JSON 解析失败时默认通过。解析失败应返回 `warning`，并进入确定性检查或重新评估。

### 14.2 失败分类

| 类型 | 恢复动作 |
|---|---|
| 临时网络错误 | 指数退避后重试 |
| 上下文不足 | 检索相关文件并补充上下文 |
| 工具参数错误 | 根据 schema 修正参数 |
| 测试失败 | 委派 Debug Agent 分析根因 |
| 模型能力不足 | 升级模型层级 |
| 计划错误 | 回滚到 Planner，重建受影响子图 |
| 预算耗尽 | 降级非关键任务或安全停止 |
| 权限不足 | 阻塞并请求明确授权 |

### 14.3 防死循环

- 同一节点最多三次执行。
- 同一错误指纹最多出现两次。
- 连续两次无产物变化判定为停滞。
- 总运行时间、Token 和费用均有硬上限。
- Loop Operator 独立于执行 Agent 监控循环状态。

## 15. 记忆与检查点

MAOE 保存两类状态：

1. **运行状态**：DAG、节点结果、预算、活动 Agent、错误和检查点。
2. **可复用知识**：经过验证的恢复策略、路由表现和 Skill 成功记录。

目录建议：

```text
.maoe/runs/{run_id}/
├── state.json
├── decisions.jsonl
├── events.jsonl
├── context.json
├── artifacts.json
├── costs.json
├── checkpoint.json
└── report.json
```

系统不得把一次成功经验直接提升为全局规则。必须经过“观察、提议、验证、晋升、回滚”流程。

## 16. 可观测性与公开演示

为了支持公开路演和答辩，运行时必须提供结构化状态，而不是只输出终端日志。

### 16.1 路演界面必须展示

- 用户目标。
- 实时 DAG 和节点状态。
- 当前 Agent 及其职责。
- 已加载 Skills 和规则。
- 每次模型路由选择及理由。
- Token、成本、耗时和预算剩余。
- 并行任务状态。
- 质量门评分、失败原因和升级过程。
- 最终产物及可重复验证证据。

### 16.2 状态 API

```http
GET /api/runs/{run_id}
GET /api/runs/{run_id}/events
GET /api/runs/{run_id}/graph
GET /api/runs/{run_id}/costs
GET /api/runs/{run_id}/artifacts
```

前端只消费这些稳定 JSON，不解析日志文本。

### 16.3 演示稳定性

- 提供 Live 模式和 Replay 模式。
- Live 模式调用真实模型。
- Replay 模式读取已保存事件，网络异常时仍能完整演示。
- 两种模式使用同一前端和同一事件 schema。
- 演示任务控制在 3 至 5 个 DAG 节点、3 分钟内完成。

## 17. 安全与权限

### 17.1 权限等级

| 等级 | 操作 | 默认策略 |
|---|---|---|
| Low | 读取、搜索、运行只读检查 | 自动允许 |
| Medium | 编辑工作区文件、运行测试 | 在沙箱内自动允许 |
| High | 安装依赖、网络写操作、提交代码 | 根据任务授权判断 |
| Critical | 删除、部署、密钥、权限、外部消息 | 必须显式授权 |

### 17.2 密钥策略

- 源码、Prompt、Trace 和演示数据中禁止出现真实密钥。
- 所有供应商密钥通过环境变量或密钥管理器加载。
- 日志层统一脱敏 Authorization、Cookie、Token 和 Key 字段。
- 路演使用独立限额 key。

## 18. 与当前 MAOE 代码的映射

当前代码已经具备原型基础，但距离本设计仍有差距：

| 当前模块 | 已有能力 | 下一步 |
|---|---|---|
| `parser/task_parser.py` | LLM 任务拆解 | 增加验收标准、风险和资源声明 |
| 尚不存在 | Goal IR 和 Capability Graph | 新建 `compiler/` 并定义稳定 schema |
| 尚不存在 | Skill Capsule Registry | 新建 Capsule Adapter、Validator 和 Index |
| 尚不存在 | Workflow Compiler | 实现检索、绑定、类型检查和 DAG 输出 |
| 尚不存在 | Candidate Laboratory | 实现三版本生成、差异执行、早停和 Pareto 选择 |
| `evaluator/complexity_eval.py` | 五级复杂度评估 | 增加确定性特征和置信度校准 |
| `router/model_router.py` | 复杂度到模型层级映射 | 接入能力、健康度、历史表现和预算 |
| `economist/token_economist.py` | 静态 Token 分配 | 记录真实消耗并动态再分配 |
| `orchestrator/agent_orchestrator.py` | DAG 分层并行执行 | 拆出 Scheduler、Policy Engine 和 Agent Registry |
| `quality/quality_gate.py` | LLM 质量检查和升级 | 禁止解析失败默认通过，加入确定性验证器 |
| `llm/client.py` | OpenAI 兼容请求 | 加重试、熔断、供应商适配和用量事件 |
| `main.py` | CLI 入口 | 增加 plan、status、resume、report 命令 |

当前 28 项单元测试可作为回归基线，但不能代表端到端系统已完成。

## 19. 实施顺序

### Phase 1：Skill Capsule 最小闭环

1. 定义 Capsule Schema、Goal IR、Capability Graph 和 Workflow DAG。
2. 选择 8 至 12 个与 Python 工程开发直接相关的 ECC Skills 做 Adapter。
3. 实现 Capsule Validator 和 Skill Registry。
4. 实现按 capability 和契约匹配的检索接口。

验收：输入一个 Python 工程目标，系统能检索 Skills，并解释每个 Skill 为什么匹配或为什么被拒绝。

### Phase 2：Workflow Compiler

1. 实现 Goal Lowering 和抽象能力规划。
2. 实现 Skill Binding、输入输出类型检查和冲突检测。
3. 生成 Economy、Balanced、Quality 三种候选 Workflow。
4. 输出可执行 DAG、预估成本、质量和风险。

验收：同一目标能得到三种可解释、可验证且不超过预算的候选 Workflow。

### Phase 3：联合调度与实验循环

1. 从现有 Orchestrator 拆出 Scheduler 和 Decision Engine。
2. 联合选择 Skill、Agent、模型、并发和 Token 预算。
3. 实现公共前缀复用、差异子图执行和内容哈希缓存。
4. 实现早停和 Pareto Selector。

验收：系统在硬预算内比较至少两种候选，并解释最终版本选择。

### Phase 4：质量、恢复与可观测演示

1. 修正 Quality Gate 解析失败默认通过的问题。
2. 实现 Skill 替换、局部重编译、Agent 切换和模型升级。
3. 输出统一 Event JSONL 和 Run Status API。
4. 建立 Skill 排布、候选 Workflow、Agent、成本和质量可视化。
5. 实现检查点、恢复和 Replay 模式。

验收：断网情况下仍可通过 Replay 完整展示一次运行。

## 20. 测试体系

### 20.1 单元测试

- Loader 是否真的读取并校验必读文件。
- Registry 是否拒绝重复、缺失或版本不兼容条目。
- Capsule 的 requires、provides、effects 和 validators 是否完整。
- Workflow Compiler 是否拒绝类型不兼容和能力缺口。
- 三版本候选是否遵守数量、预算和公共前缀复用限制。
- 路由、预算、升级和停止条件是否正确。
- DAG 是否检测循环依赖和资源冲突。
- 日志是否完成密钥脱敏。

### 20.2 集成测试

- Planner → Scheduler → Agent → Quality Gate 完整链路。
- Hook 事件顺序和幂等性。
- 中断后从检查点恢复。
- 多供应商失败后的回退。

### 20.3 端到端测试

至少准备三类公开演示任务：

1. 小型 Python 功能开发。
2. 带失败注入的 Bug 修复。
3. 跨文件功能开发与测试。

每类任务使用以下基线比较：

1. 固定 Workflow + 固定轻量模型。
2. 固定 Workflow + 固定强模型。
3. 只做模型路由、不做 Skill 编译。
4. MAOE Skill 编译 + 联合调度。

### 20.4 核心指标

- 任务完成率。
- Pass@1 和 Pass@3。
- 每个成功任务的 Token 与费用。
- 平均重试次数。
- 模型升级率。
- 并行执行带来的时间缩短。
- 必读文件实际加载率。
- 决策可解释记录完整率。
- Skill 检索 Precision@K 和有效绑定率。
- Workflow 编译失败率与静态拦截问题数。
- 候选公共产物复用率。
- 相对固定强模型的成本下降比例。
- 在同等质量阈值下的完成时间变化。

### 20.5 创新成立的最低证据

只有满足以下条件，才能在答辩中声称“工程优化有效”：

- 在同一任务集和同一质量门下进行比较。
- MAOE 相对固定强模型降低真实费用或 Token。
- MAOE 相对固定轻量模型提高完成率或质量。
- 多版本实验的额外成本被早停和产物复用抵消。
- 至少展示一次 Skill 不兼容被编译器提前拦截。
- 至少展示一次运行时失败后替换 Skill 并局部重编译成功。

在取得数据前，文档和路演只能表述为“设计目标”，不能写成已经实现的结果。

## 21. 完成定义

MAOE 比赛 MVP 只有同时满足以下条件才算完成：

- 七个核心文件由 Loader 实际加载并产生证据。
- Agents、Skills、Commands 均通过 Manifest 注册。
- 进入自主调度的 Skill 均通过 Capsule Schema 和认证检查。
- 自然语言目标能被编译为 Goal IR、Capability Graph 和可执行 DAG。
- 编译器能发现能力缺口、类型不兼容、资源冲突和循环依赖。
- 系统能生成不超过三个受控候选 Workflow。
- 候选版本能共享公共产物，并通过早停限制额外成本。
- 用户只输入一次目标，系统可运行至完成或明确阻塞。
- DAG 能自动并行调度无依赖节点。
- 路由选择包含可展示的理由和预算。
- 失败能够进入有限恢复循环，不会无限重试。
- 所有节点经过确定性检查或独立质量验证。
- 状态、成本、事件和产物可通过 API 查询。
- Live 和 Replay 两种演示模式均可工作。
- Benchmark 包含固定轻量、固定强模型、仅模型路由三类基线。
- 单元、集成和端到端测试全部通过。
- 源码和日志中不存在真实密钥。

## 22. ECC 融合边界

MAOE 明确不做以下事情：

- 不复制 ECC 的全部 Agents、Skills 和 Commands。
- 不把所有 Skill 默认塞进上下文。
- 不依赖 Claude Code 单一平台。
- 不用自然语言 Prompt 替代运行时权限控制。
- 不把“模型说完成了”视为工程完成。
- 不以自动化名义绕过高风险操作授权。

MAOE 对 ECC 的核心继承是：把 Agent 开发从“一个大 Prompt”提升为“有加载、有注册、有约束、有验证、有观测的 Harness 系统”。MAOE 的独立工程方向是把异构 Skill 编译成可执行 Workflow，并将 Skill、Agent、模型、并发和预算纳入同一套受控实验与联合调度闭环。

## 23. 参考实现

外部项目核查截面：2026-06-28。下列项目用于能力对照和工程借鉴，不代表其授权、背书或与 MAOE 存在合作关系。

- Everything Claude Code：<https://github.com/affaan-m/everything-claude-code>
- Claude Code Workflow Orchestration：<https://github.com/barkain/claude-code-workflow-orchestration>
- Maestro Orchestrate：<https://github.com/josstei/maestro-orchestrate>
- Agent Registry Inventory：<https://github.com/den-vasyliev/agentregistry-inventory>
- GitHub Agentic Workflows：<https://github.com/github/gh-aw>
- GitHub Agentic Workflows 文档：<https://github.github.com/gh-aw/>
- XSkill：<https://github.com/XSkill-Agent/XSkill>
- SkillClaw：<https://github.com/AMAP-ML/SkillClaw>
- EvoSkill：<https://github.com/sentient-agi/EvoSkill>

ECC 中重点对照的内容包括 `CLAUDE.md`、`AGENTS.md`、`.opencode/README.md`、`skills/agent-harness-construction/SKILL.md` 和 `docs/ECC-2.0-REFERENCE-ARCHITECTURE.md`。MAOE 只吸收其中可验证的 Harness 机制，不复制其组件数量和项目叙事。

“本次检查未发现相同六项闭环”只对上述项目和本次调研样本负责。对外表述必须保留该限定，不得改写成“全球首创”或“行业唯一”。
