# MAOE 源码逐文件讲解（学习版）

> 目标读者:你 —— 想把这套从 `~/Documents/maoe` 复制过来的代码**事无巨细**地看懂。
> 阅读策略:每节先一句话定位"这个文件是干嘛的",再用 mermaid/ASCII 图示讲它在系统里的位置,最后逐函数/逐类拆解。**所有文件名和符号都做成了可点击链接**,你可以一路跳读源码。
> 默认假设:你已经能跑 `uv sync --extra dev`、`pytest`、`maoe --help`。

---

## 0. 三十秒看完整张地图

```
                    ┌─────────────────────────────────────────┐
                    │           用户 ($ maoe run "...")        │
                    └────────────────────┬────────────────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  src/maoe/main.py   │   ← CLI 入口 (click)
                              └──────────┬──────────┘
                                         │
                                         │ engine = MAOEEngine()
                                         │ await engine.run(desc)
                                         ▼
                       ┌─────────────────────────────────────┐
                       │  orchestrator/agent_orchestrator    │   "总指挥"
                       │  ┌────────┐ ┌────────┐ ┌────────┐  │
                       │  │ Parser │ │Evaluat.│ │ Router │  │
                       │  └────┬───┘ └────┬───┘ └────┬───┘  │
                       │       │          │          │       │
                       │  ┌────▼───┐ ┌────▼───┐ ┌────▼───┐  │
                       │  │Econom. │ │Quality │ │Executor│  │
                       │  └────────┘ └────────┘ └────────┘  │
                       └──────────────┬──────────────────────┘
                                      │ HTTPS
                                      ▼
                       ┌─────────────────────────────────┐
                       │ llm/client.py  →  代理 LLM API  │
                       └─────────────────────────────────┘

           (旁路子系统：编译期类型检查、Skill 候选实验、运行态持久化)
           compiler/  experiments/  registry/  runtime/  bootstrap/
```

**两条平行的执行管线**(这是看懂这个工程最重要的认知):

1. **运行管线**(目前 `maoe run` 走的路) — `parser → evaluator → router → economist → executor + quality + escalation`。这条管线**已经能跑、有 LLM 真实调用**。
2. **编译管线**(目前还没有 CLI 入口,但有完整测试) — `bootstrap → registry → compiler(GoalIR→CapabilityGraph→Candidates→TypeChecker) → experiments(EarlyStopper+ParetoSelector) → runtime(RunStore)`。这条管线的设计哲学:**先静态算清楚,再花钱跑**。

理解了这两条管线是并存的、还没合并,你后续读代码就不会迷路。

---

## 1. 目录速查表

```
op/
├── .maoe/                       # 工程元数据
│   ├── manifest.yaml            # 七个核心控制面 + agents/skills/commands 的清单
│   └── skill-registry.json      # SkillRegistry.write_snapshot() 导出的快照
├── MAOE.md / AGENTS.md / RULES.md / SOUL.md / WORKING-CONTEXT.md / COMMANDS-QUICK-REF.md
│                                # ECC 哲学：把"规矩、性格、上下文"也当代码管
├── agents/*.md                  # 8 个角色提示词
├── skills/*/SKILL.md + capsule.yaml
│                                # 10 个能力胶囊（YAML 契约 + 提示词）
├── src/maoe/                    # Python 实现（下面逐文件讲）
├── benchmarks/                  # 端到端跑分套件
├── tests/                       # pytest 测试
├── docs/                        # 你正在看的文档
└── pyproject.toml               # uv/hatchling 构建配置
```

---

## 2. CLI 入口层

### 2.1 [`src/maoe/main.py`](../src/maoe/main.py)

**职责**:用 click 把三个子命令(`run / config / benchmark`)挂到 `maoe` 二进制上。

关键代码段:

| 函数 | 行号 | 你要看的细节 |
|---|---|---|
| 顶部 try-import | [L20-L42](../src/maoe/main.py#L20-L42) | 把 `benchmarks/` 目录动态加入 `sys.path`,失败也不崩,只是 `benchmark` 子命令不会注册。**这是为了把 benchmarks 和 maoe 解耦** — maoe 可以不带 benchmark 单独发布。 |
| `_setup_logging()` | [L46-L49](../src/maoe/main.py#L46-L49) | 用 loguru 替换默认 logger,根据 `-v` 决定是 DEBUG 还是 settings.log_level。 |
| `cli()` | [L52-L54](../src/maoe/main.py#L52-L54) | click group,没逻辑。 |
| `run()` | [L57-L91](../src/maoe/main.py#L57-L91) | **核心入口**。`engine = MAOEEngine()` → `await engine.run(description)`,再 print/JSON。注意 `finally: engine.close()` — 不关 httpx client 会泄漏 socket。 |
| `config()` | [L94-L107](../src/maoe/main.py#L94-L107) | 不调 LLM,纯打印当前 settings。验证 .env 是否读到的"低成本检查点"。 |
| `benchmark()` | [L113-L155](../src/maoe/main.py#L113-L155) | 只有 `_BENCHMARKS_AVAILABLE=True` 才注册。-p 选 profile,-t 选单任务,跑完出 JSON+MD 双报告。 |

**学习建议**:看完这个文件,你应该能回答:
- "为什么 `maoe benchmark` 在裸 maoe 包里看不到?" → benchmarks 在 try-import 里。
- "engine.close() 漏掉会怎样?" → `httpx.AsyncClient` 不释放,大量 run 会撑爆 fd 上限。

### 2.2 [`src/maoe/config/settings.py`](../src/maoe/config/settings.py) + [`__init__.py`](../src/maoe/config/__init__.py)

**职责**:pydantic-settings 单例,从 `.env` / 环境变量加载所有可调参数(api_key、base_url、并发度、token 预算、log 等级…)。

你只需要记住:**整个工程任何地方 `from maoe.config import settings` 都拿到同一个对象**。改配置就改 `.env` 或 export。

---

## 3. 数据模型层 (`src/maoe/models/`)

这是整套系统的"宪法"。**没有命令式逻辑,只有 pydantic 模型 + 枚举**。改这里就是改契约,所有上游必须跟着改。

### 3.1 [`models/task.py`](../src/maoe/models/task.py) — 运行管线的"工单"

```
Task
├── id, description, status, total_cost, total_tokens
└── subtasks: list[SubTask]

SubTask
├── id, description, dependencies: list[str]
├── status: TaskStatus  (PENDING/RUNNING/COMPLETED/FAILED/ESCALATED)
├── complexity_score/level   # 由 evaluator 填
├── assigned_model/tier      # 由 router 填
├── token_budget             # 由 economist 填
├── output, quality_pass     # 由 executor + quality 填
├── attempts/max_attempts/escalation_count
```

关键类 [`TaskGraph`](../src/maoe/models/task.py#L46-L74):
- `add_subtask()` — 维护 `adjacency` 字典。
- `get_execution_order()` — **拓扑分层**。返回 `list[list[SubTask]]`,每层内的子任务可以并行。检测到环就抛 `ValueError("Circular dependency detected")`。
- 这是 [`agent_orchestrator.run()`](../src/maoe/orchestrator/agent_orchestrator.py#L75) 调度执行的核心数据结构。

### 3.2 [`models/complexity.py`](../src/maoe/models/complexity.py) — 复杂度评分

```
ComplexityLevel  IntEnum  1 TRIVIAL → 5 CRITICAL
ComplexityScore  pydantic { level, score(0-1), reasoning, factors{} }
```
`.label` 属性把枚举名小写,给 router 用作 `assigned_tier` 字符串。

### 3.3 [`models/routing.py`](../src/maoe/models/routing.py) — 模型与定价

最重要的常量是 [`DEFAULT_MODELS`](../src/maoe/models/routing.py#L30-L62)。**四档模型 + 单价**写死在这里:

| Tier | Model | input/1k | output/1k | max_tokens |
|---|---|---|---|---|
| FAST | gpt-4o-mini | $0.00015 | $0.0006 | 16384 |
| BALANCED | gpt-4o | $0.0025 | $0.01 | 32768 |
| POWERFUL | gpt-5 | $0.01 | $0.04 | 65536 |
| CRITICAL | gpt-5.5 | $0.05 | $0.15 | 131072 |

> ⚠️ gpt-5 / gpt-5.5 是这套代码假设的名字。**实际代理 `openai-next.com` 是否提供这两个 model id 你需要自己验。** 改名只需要改这个文件 + `llm/client.py` 里的 `COST_PER_1K`。

### 3.4 [`models/capsule.py`](../src/maoe/models/capsule.py) — Skill Capsule(编译管线核心契约)

这是 ECC 哲学的具象化:**每个 skill 不是文档,是一份带类型的契约**。

```
SkillCapsule
├── id (kebab-case)        + version (semver)
├── kind: KNOWLEDGE/TOOL/WORKFLOW
├── capabilities: CapabilityContract
│   ├── provides: list[str]   # 这个 skill 输出哪些能力
│   ├── requires: list[str]   # 它需要哪些能力作前置
│   └── schemas: dict[str,str]  # 每个能力的 schema id (类型检查用)
├── inputs / outputs            # 字段名 → InputSpec(type, required)
├── effects: EffectSpec         # filesystem/network/external_side_effects/writes
├── resources: ResourceSpec     # expected_tokens/seconds/cost  ← 编译器用这个估算 wf 总成本
├── risk: RiskSpec              # level (LOW/MEDIUM/HIGH/CRITICAL) + rollback
├── quality: QualitySpec        # validators[] + minimum_score
├── certification: 0..3         # UNVERIFIED→TRUSTED
├── compatible_agents, languages, task_types, tags
└── historical_success: 0..1
```

校验规则(`@model_validator validate_contract`):
- `schemas` 里出现的能力必须在 `provides|requires` 里声明,否则报错。
- **risk ≥ MEDIUM 必须填 rollback** — 这就是 SOUL.md 里"风险必须有回滚"原则的代码强制。

### 3.5 [`models/workflow.py`](../src/maoe/models/workflow.py) — 编译管线核心数据

工作流从 goal 到最终方案的全部中间产物都在这里:

```
GoalIR           ← 用户目标的结构化表达
 ├── goal, deliverables, environment_capabilities
 ├── constraints: GoalConstraints  (budget$, token_budget, deadline_s, allowed_risk)
 ├── quality: GoalQuality          (min_score, tests_pass, security_high_findings)
 ├── language, task_type, acceptance_criteria
 └── fingerprint  ← 排序 json → sha256，做缓存键

CapabilityGraph  ← 反推"达成 deliverables 需要哪些能力 → 需要哪些 skill"
 ├── nodes: CapabilityNode[]
 ├── edges: CapabilityEdge[]
 └── required_outputs

WorkflowNode     ← 编译器最终生成的、要执行的节点（绑定 skill 版本与 agent）
 ├── id, skill_id, skill_version, agent, model_tier
 ├── dependencies (节点级 DAG 边)
 ├── requires/provides (能力契约副本，runtime 类型检查也要用)
 ├── validators, rollback, expected_tokens/seconds/cost, risk, writes

WorkflowDAG      ← node_map() / layers() (拓扑分层)
CandidateWorkflow  ← economy/balanced/quality 三档方案之一
CompileResult    ← 编译器最终输出，含 lock_digest（决策可复现的 sha256）
```

注意:`WorkflowDAG.layers()`([L88-L100](../src/maoe/models/workflow.py#L88-L100)) 跟 `TaskGraph.get_execution_order()` 几乎一样,但前者返回 `list[list[str]]`(节点 id),后者返回 `list[list[SubTask]]`。**两个管线的拓扑实现是独立的**,将来可以合并。

---

## 4. LLM 客户端 [`src/maoe/llm/client.py`](../src/maoe/llm/client.py)

**职责**:把 OpenAI 兼容协议封装成 `chat()` / `chat_json()` 两个 async 方法,顺便统计 usage 和 cost。

关键设计:

| 点 | 实现 | 为什么 |
|---|---|---|
| 懒加载 client | [L48-L54](../src/maoe/llm/client.py#L48-L54) `_get_client()` | 不在 `__init__` 建 httpx,避免事件循环未启动时报错。 |
| 每模型 token 上限 | [`MODEL_LIMITS`](../src/maoe/llm/client.py#L22-L27) | 调用方传 `max_tokens=99999`,这里会自动 `min(...)` 截到模型上限。 |
| 全程累计 usage | [L88-L95](../src/maoe/llm/client.py#L88-L95) | `self._input_tokens / _output_tokens / _cost` 累加,orchestrator 用 `usage_snapshot()` 做"用了多少钱"的差分。 |
| `chat_json()` | [L106-L118](../src/maoe/llm/client.py#L106-L118) | 比 `chat()` 多塞 `response_format={"type":"json_object"}`。所有"让 LLM 回 JSON"的地方(parser/evaluator/quality)都走这个。 |
| close() | [L120-L124](../src/maoe/llm/client.py#L120-L124) | `engine.close()` 链式调用到这里。 |

**学习建议**:这套实现没有重试、没有限流、没有错误分支细化。**如果代理 408/429,会原地抛**。生产化要在这里加 tenacity。

---

## 5. 运行管线(目前 `maoe run` 真正走的路径)

### 5.1 [`parser/task_parser.py`](../src/maoe/parser/task_parser.py) — 把自然语言拆成子任务 DAG

- Prompt 模板 [`DECOMPOSE_PROMPT`](../src/maoe/parser/task_parser.py#L12-L26) 要求 LLM 返回 `{"subtasks":[{id, description, dependencies}, ...]}`。
- `parse()` [L40-L56](../src/maoe/parser/task_parser.py#L40-L56) 给 task 一个 `task-<8位 hex>` 的 id,直接 `Task(id, description, subtasks=...)`。
- `_decompose_with_llm()` [L58-L86](../src/maoe/parser/task_parser.py#L58-L86) 解析 JSON 失败就降级成"整个 task 当一个 subtask"(`st-1`)。
- 默认 `max_subtasks=8` — 这个上限是为了控制成本。

### 5.2 [`evaluator/complexity_eval.py`](../src/maoe/evaluator/complexity_eval.py) — 给每个子任务打分

- Prompt [`COMPLEXITY_PROMPT`](../src/maoe/evaluator/complexity_eval.py#L10-L20):让 LLM 输出 `level(1-5) + score(0-1) + factors{scope, difficulty, dependencies, domain_knowledge}`。
- 解析失败的兜底:`ComplexityLevel.MODERATE, score=0.5`,保证流水线不中断。

### 5.3 [`router/model_router.py`](../src/maoe/router/model_router.py) — 复杂度 → 模型

- 静态映射表 [`COMPLEXITY_TO_TIER`](../src/maoe/router/model_router.py#L14-L20):TRIVIAL/SIMPLE→FAST, MODERATE→BALANCED, COMPLEX→POWERFUL, CRITICAL→CRITICAL。
- `route()` [L40-L73](../src/maoe/router/model_router.py#L40-L73):算出 model + 预估 cost,返回 `RoutingDecision`。`force_tier` 参数让 benchmark profile 可以强制全用 fast。
- `escalate()` [L75-L101](../src/maoe/router/model_router.py#L75-L101):升一级 tier。**没有跨级跳**(MEDIUM 失败一次只到 POWERFUL,再失败才到 CRITICAL)。orchestrator 在 quality gate 不过时调用它。

### 5.4 [`economist/token_economist.py`](../src/maoe/economist/token_economist.py) — 全局 token 预算瓜分

- `_global_budget=100_000` 默认值。
- `allocate()` [L46-L88](../src/maoe/economist/token_economist.py#L46-L88) 的瓜分公式:

```
weight_i = COMPLEXITY_TOKEN_MULTIPLIER[level]  ×  TIER_BUDGET_SHARE[tier]
budget_i = global × (weight_i / Σweight)
budget_i = clamp(budget_i, 1000, 64000)
cost_i   = budget_i × TIER_BUDGET_SHARE[tier] × 0.0001    # 粗估
```

`COMPLEXITY_TOKEN_MULTIPLIER` [L9-L15](../src/maoe/economist/token_economist.py#L9-L15) 是 `{1:0.3, 2:0.5, 3:1.0, 4:2.0, 5:4.0}`。复杂度每升一级,预算大约翻倍。

总成本 > $0.10 就在 `report.warnings` 加一条提示。

### 5.5 [`quality/quality_gate.py`](../src/maoe/quality/quality_gate.py) — 质量门 + Subtask 执行器

**两个类放在同一文件**:

`SubtaskExecutor` [L99-L122](../src/maoe/quality/quality_gate.py#L99-L122):
- 用 `EXECUTE_PROMPT` 模板,system="Execute the sub-task precisely.",max_tokens 直接传 LLM。
- 返回字符串 output。

`QualityGate` [L57-L97](../src/maoe/quality/quality_gate.py#L57-L97):
- 先做"output 短于 10 字符"的廉价过滤,直接判 fail。
- 否则调 `chat_json` 让 gpt-4o-mini 给 `{pass, score, reasoning, issues}`。
- JSON 解析失败也判 fail。
- 返回 `QualityVerdict(passed, score 0-1, reasoning, issues[])`。

### 5.6 [`orchestrator/agent_orchestrator.py`](../src/maoe/orchestrator/agent_orchestrator.py) — 把上面六个角色串成一条流水线

这是**整个运行管线的"main"函数**。

```python
class MAOEEngine:
    def __init__(self):
        self._llm = LLMClient()
        self._parser = TaskParser(self._llm)
        self._evaluator = ComplexityEval(self._llm)
        self._router = ModelRouter()
        self._economist = TokenEconomist()
        self._quality = QualityGate(self._llm)
        self._executor = SubtaskExecutor(self._llm)
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_tasks)
```

`run(description)` 七步走 [L43-L137](../src/maoe/orchestrator/agent_orchestrator.py#L43-L137):

1. **快照 usage** — 记录 LLM 调用前的 cost,最后差分得到本次任务花了多少。
2. **parser.parse(description)** — 拆子任务。
3. **逐个 evaluate → router.route** — 复杂度打分 + 选模型,填回 subtask 字段。
4. **economist.allocate** — 按复杂度+tier 瓜分 token 预算,填 `token_budget`。
5. **graph.get_execution_order()** — 拓扑分层;循环依赖直接整体 FAILED。
6. **逐层并行 asyncio.gather(`_execute_subtask`)** — `_semaphore` 控并发。
7. **统计 + 返回 EngineResult**。

`_execute_subtask()` [L139-L213](../src/maoe/orchestrator/agent_orchestrator.py#L139-L213) 是真正"循环重试 + 升级"的地方:

```
for attempt in 0..max_attempts-1:
    status = RUNNING
    output = executor.execute(...)
    verdict = quality.check(...)
    if verdict.passed:
        status = COMPLETED → 返回
    else:
        if can_escalate:
            escalation = router.escalate(current)
            if escalation:
                assigned_model/tier = escalation.*
                status = ESCALATED
                escalation_count += 1
# 全部失败
status = FAILED
```

**这里有个微妙细节**:`router.escalate` 调用前用 `ComplexityLevel.MODERATE` + `force_tier=当前 tier` 重新算了一次 `current` decision([L186-L192](../src/maoe/orchestrator/agent_orchestrator.py#L186-L192))。这样写是因为 escalate 需要 RoutingDecision 而不是 tier 字符串 — 一个小代码债。

依赖上下文:`dep_context` 是 `"[依赖id]: 依赖output\n..."` 的拼串,作为本子任务执行的上文 prompt。**只拼直接依赖的 output**,不做递归 — 节省 token。

---

## 6. 编译管线(目前没接 CLI,但有完整契约)

这套子系统的设计目标:**在动 LLM 之前,先用静态校验+成本预测把"不可能完成的任务"挡掉**。

### 6.1 [`registry/skill_registry.py`](../src/maoe/registry/skill_registry.py)

- `discover(root)` [L29-L40](../src/maoe/registry/skill_registry.py#L29-L40) 读 `.maoe/manifest.yaml`,逐个加载 `capsule.yaml` 到 `_capsules: dict[(id, version), SkillCapsule]`。
- `get(skill_id, version=None)` 默认拿最高 semver 版本。
- `search(capability, ...)` [L86-L139](../src/maoe/registry/skill_registry.py#L86-L139) 是**核心匹配算法**。打分公式 [L168-L184](../src/maoe/registry/skill_registry.py#L168-L184):

```
score = 0.30 × contract_match            # 是否真的 provide 这个 capability
      + 0.20 × coverage                   # 1/len(provides) — 越专一加分越多
      + 0.15 × historical_success         # 历史成功率
      + 0.15 × quality.minimum_score      # 质量门下限
      + 0.10 × environment_fit            # requires 中已满足的比例
      − 0.05 × normalized_cost            # cost/0.1 截到 1
      − 0.05 × normalized_risk            # risk/4
```

- `revoke()` — 把一个版本拉黑,但不删,保留审计。
- `write_snapshot()` 把当前 registry 序列化到 `.maoe/skill-registry.json`(就是 IDE 里你打开的那个文件)。

### 6.2 [`compiler/goal_ir.py`](../src/maoe/compiler/goal_ir.py)

`GoalLowerer.lower(goal, **opts)` — **确定性**地把自然语言 goal 变成 `GoalIR`。

- 默认 deliverables = `["source.modified", "test.report"]`。
- 关键词触发:含 "security/auth/jwt/安全/鉴权/权限/登录" → 加 `"security.report"` deliverable + acceptance criterion。
- 含 "document/readme/文档" → 加 `"docs.updated"`。
- `task_type` 根据关键词决定 `bugfix / refactor / feature`。

**这个 lowerer 没用 LLM** — 完全规则驱动,可重现。

### 6.3 [`compiler/capability_graph.py`](../src/maoe/compiler/capability_graph.py)

`CapabilityPlanner.plan(goal)`:从 deliverables 反推依赖图。

- 对每个 deliverable 调 `visit(capability, required_by)` 递归。
- `visit` 在 registry 里找最佳 skill,把它的 `requires` 加入待访问栈。
- 输出 `CapabilityGraph(nodes, edges, required_outputs)`。

环检测:**通过 `stack` 参数,如果当前 capability 已经在路径上,就直接 return**(不抛错,只跳过)。注意这跟 `workflow_compiler.bind()` 的环检测策略不同 — bind 会抛 `StaticValidationError`。

### 6.4 [`compiler/workflow_compiler.py`](../src/maoe/compiler/workflow_compiler.py)

**编译管线的总指挥**。

`compile(goal)` [L43-L72](../src/maoe/compiler/workflow_compiler.py#L43-L72):
1. lower 成 GoalIR(如果传的是字符串)。
2. plan 出 CapabilityGraph。
3. 对每个 variant ∈ {ECONOMY, BALANCED, QUALITY} 调 `_build_candidate(...)`。
4. 算 `_shared_nodes`(三档共用的 skill_id 集合)。
5. `_recommend` 出推荐档(参考 goal.constraints/quality)。
6. 把上面打包成 `CompileResult`,算 `lock_digest = sha256(canonical_json)`。
7. `write_lockfile()` 可选写 `workflow.lock.json`,**用于决策可复现**。

`_build_candidate(goal, variant)` [L82-L200](../src/maoe/compiler/workflow_compiler.py#L82-L200):
- 三档的差别:
  - 模型档:[`VARIANT_MODEL_TIERS`](../src/maoe/compiler/workflow_compiler.py#L22-L26) `{ECONOMY:fast, BALANCED:balanced, QUALITY:powerful}`。
  - 额外交付物:[`VARIANT_EXTRA_OUTPUTS`](../src/maoe/compiler/workflow_compiler.py#L28-L32) `{ECONOMY:[], BALANCED:[quality.report], QUALITY:[quality.report, review.report]}`。
- `bind(capability, stack)` 递归把每个 deliverable 拆成具体 skill。`stack` 检测环 → `StaticValidationError`。找不到 skill → `capability_gap`。
- 拼 `WorkflowNode[]` → `WorkflowDAG` → 走 `WorkflowTypeChecker.validate()` 静态检查。
- 算成本/时间/质量预测(`min(qualities)` `min(reliability)` `max(risks)` `sum(costs)`,layer 内取 max seconds 再 sum)。
- 给 workflow 一个稳定 id:`wf-<variant>-<sha256前12位>`。

### 6.5 [`compiler/type_checker.py`](../src/maoe/compiler/type_checker.py)

`WorkflowTypeChecker.validate(goal, dag)` 跑五个静态检查:

| 错误码 | 含义 |
|---|---|
| `unknown_dependency` | 节点依赖了不存在的节点 id |
| `cycle` | 拓扑分层失败 |
| `capability_gap` | 节点 requires 的能力,在它运行那一层之前没人 provide |
| `schema_mismatch` | 上下游对同一 capability 声明了不同 schema id |
| `missing_deliverable` | 最终所有节点 provide 完仍缺 goal.deliverables 里的某项 |
| (隐含)`_resource_conflicts` | 同一层多个节点写同一个路径前缀(`writes`) |

任意一个错误都丢给 `StaticValidationError`,**编译期就报,不需要花一分钱跑 LLM**。

---

## 7. 实验室(候选评估)

### 7.1 [`experiments/evaluator.py`](../src/maoe/experiments/evaluator.py)

`CandidateEvaluation` 模型 + `from_prediction(candidate)` 工厂:**目前的"评估"就是把编译器的静态预测当作评估结果**,evidence=`["static_validation_passed", "prediction_only"]`。

> 这是工程缺口:真正的评估应该是"小样本跑一下 / 影子运行",但 MVP 阶段先用预测兜底。

### 7.2 [`experiments/early_stopper.py`](../src/maoe/experiments/early_stopper.py)

`EarlyStopper.decide(goal, completed, remaining)`:

```
if len(completed) >= maximum_candidates:           STOP "candidate limit reached"
if Σcost_completed >= goal.constraints.budget:     STOP "cost budget exhausted"
if not remaining:                                  STOP "no candidates remain"
if no completed.passed and quality≥min:            CONTINUE "quality not reached"
spent  = Σcost_completed
best_q = max(quality of passing completed)
affordable = remaining where spent + est_cost ≤ budget
if not affordable:                                 STOP "remaining exceed budget"
gain/cost = max((cand.predicted_quality - best_q)/cand.estimated_cost) for cand in affordable
if gain/cost < minimum_gain_per_cost:              STOP "expected gain too low"
else:                                              CONTINUE
```

这个文件**完整体现了 SOUL.md"够用即停"的工程哲学**。

### 7.3 [`experiments/pareto_selector.py`](../src/maoe/experiments/pareto_selector.py)

`ParetoSelector.select(evaluations, constraints, quality, preferred)`:

1. **硬约束过滤**(`_constraint_failures`):任何一个不满足 → 拒绝。
2. **Pareto 前沿**(`_dominates`):A 支配 B = "A 在所有维度都不差 + 至少一个严格更好"。维度是 `(quality↑, reliability↑, cost↓, latency↓, risk↓)`。
3. **挑推荐**:前沿里有 `preferred_variant` 就选它,否则字典序最大的 `(quality, reliability, -cost, -latency, -risk)`。

### 7.4 [`experiments/candidate_lab.py`](../src/maoe/experiments/candidate_lab.py)

把 evaluator + early_stopper + selector 编排起来:**按成本升序遍历候选,边跑边决定要不要早停**。返回 `ExperimentResult(evaluations, selection, stopped_early, stop_reason, reused_node_ids)`。

`shared_node_ids` 会被加入 `artifact_cache`,模拟"前一个 candidate 跑过的节点可以被下一个 candidate 复用"。

---

## 8. 运行态持久化 `src/maoe/runtime/`

### 8.1 [`runtime/state.py`](../src/maoe/runtime/state.py) — 状态枚举与记录

- `RunPhase`:CREATED → CONTEXT_LOADED → PLANNED → READY → RUNNING → VERIFYING → (RETRYING|ESCALATING|BLOCKED|COMPLETED|FAILED|STOPPED)
- `NodePhase`:PENDING / RUNNING / COMPLETED / FAILED / SKIPPED
- `NodeRunState`:phase + attempts + error + error_fingerprint(用于去重重试) + artifact_hashes + tokens + cost + latency + quality + reused
- `RunState`:run_id + goal + workflow_id + variant + phase + nodes{} + 总 tokens/cost + active_agents + errors + 时间戳
- `EventRecord` / `DecisionRecord`:append-only 审计日志

### 8.2 [`runtime/redaction.py`](../src/maoe/runtime/redaction.py)

写盘前自动脱敏:
- `key` 里出现 `api[_-]?key|authorization|secret|access[_-]?token` → `[REDACTED]`
- 值里出现 `sk-[a-z0-9_-]{12,}` 或 `Bearer xxx` → `[REDACTED]`
- 递归处理 dict/list/tuple/str

**这就是为什么把真实 key 放进 context,落盘后是 `[REDACTED]`**(我加的 `tests/test_runtime.py::test_run_store_redacts_secrets` 锁住了这条契约)。

### 8.3 [`runtime/run_store.py`](../src/maoe/runtime/run_store.py)

**事实数据库**。一个 run 一个目录:`.maoe/runs/run-YYYYMMDD-HHMMSS-<8hex>/`,里面 8 个文件:

```
state.json        # 当前 RunState 的最新快照
checkpoint.json   # 给 resume 用的"已确认安全"快照
events.jsonl      # 顺序事件流 (EventRecord)
decisions.jsonl   # 顺序决策流 (DecisionRecord)
context.json      # 初始上下文（自动 redact）
artifacts.json    # 产出列表
costs.json        # 总成本统计
report.json       # 结束报告
```

关键方法:
- `create(compiled, candidate, context)` → 新建目录 + 落初始文件。
- `save_state(state)` → 原子写 state.json。
- `load_state(run_id)` / `checkpoint(state)` / `resume(run_id)` — resume 会把 COMPLETED/STOPPED 之外的 phase 重置为 READY。
- `append_event` / `append_decision` — JSONL 追加。
- `_run_dir(run_id)` 通过 `_validate_run_id` 防路径穿越(我加的 `test_run_store_rejects_path_traversal` 锁住)。

### 8.4 [`runtime/__init__.py`](../src/maoe/runtime/__init__.py)

包导出。**这里我刚修过一次:原来引用了不存在的 `scheduler.py`,导致 `from maoe.runtime import ...` 会 ImportError**。现在只导出真实存在的类,不再引用 scheduler。

---

## 9. Bootstrap [`src/maoe/bootstrap/loader.py`](../src/maoe/bootstrap/loader.py)

启动期合规检查:

- 找最近的 `.maoe/manifest.yaml` 作为项目根。
- 校验 manifest 里的五大 group(`core_files / agents / skills / commands / hooks`)都是非空 list,每条记录的 `path` 都真实存在、不逃逸根目录。
- 对每个 `core_files` 项算 sha256,塞进 `loaded_context: list[LoadedContextItem]`。
- 给一个 `run_id = "run-YYYYMMDD-HHMMSS"`。

**这跟 RunStore 的 run_id 是两套独立 id 系统**(bootstrap 时间戳精度到秒,RunStore 精度到秒+8 位随机)。可以理解为 bootstrap 是"session 级",RunStore 是"task 级"。

---

## 10. Benchmarks

### 10.1 [`benchmarks/metrics.py`](../benchmarks/metrics.py)

- `TaskCategory` / `ConfigProfile` 枚举。
- `BenchmarkConfig` dataclass:profile + force_tier + max_attempts + enable_escalation/quality_gate(消融实验用)。
- `CONFIG_PROFILES` 字典预置 5 档:DEFAULT / FAST_ONLY / BALANCED_ONLY / AGGRESSIVE_ESCALATION / CONSERVATIVE。
- `BenchmarkRun` / `SubtaskMetric` / `BenchmarkReport` 是结果模型。

### 10.2 [`benchmarks/suite.py`](../benchmarks/suite.py)

预置基准任务清单 `BENCHMARK_TASKS: list[BenchmarkTask]`。每个 task 有 id / description / category / expected_subtasks / max_seconds / human_baseline_score 等。`get_task_by_id(tid)` 是个查找函数。

### 10.3 [`benchmarks/runner.py`](../benchmarks/runner.py)

- `BenchmarkRunner.run_task(task)`:为每个 task 起一个 `MAOEEngine`,跑完抓 `EngineResult` 转 `BenchmarkRun`。
- `run_suite(tasks)`:遍历 + 聚合 + 排序。
- 这是**唯一同时使用 maoe + benchmarks 两个包的胶水层**。

### 10.4 [`benchmarks/report.py`](../benchmarks/report.py)

`ReportGenerator(report, output_dir)`:
- `.save()` → 同时写 JSON + Markdown 两份。
- `.to_markdown()` → 表格化展示成本/时间/通过率/逐 subtask 详情。

---

## 11. 测试 `tests/`

| 文件 | 覆盖 |
|---|---|
| [test_models.py](../tests/test_models.py) | pydantic 校验、SkillCapsule 不变量(risk≥MEDIUM 必须有 rollback) |
| [test_compiler.py](../tests/test_compiler.py) | GoalLowerer / CapabilityPlanner / WorkflowCompiler / TypeChecker |
| [test_registry.py](../tests/test_registry.py) | SkillRegistry discover / search / get / revoke / snapshot |
| [test_router.py](../tests/test_router.py) | route / escalate / 跨复杂度映射 |
| [test_economist.py](../tests/test_economist.py) | budget 分配、clamp、warning |
| [test_orchestrator.py](../tests/test_orchestrator.py) | MAOEEngine 端到端(mock LLM) |
| [test_quality.py](../tests/test_quality.py) | QualityGate 短输出、JSON 解析失败 |
| [test_experiments.py](../tests/test_experiments.py) | CandidateLab / EarlyStopper / ParetoSelector |
| [test_bootstrap.py](../tests/test_bootstrap.py) | manifest 校验、context 加载、sha256 |
| [test_runtime.py](../tests/test_runtime.py) | (**我新加的**)包导出 / RunStore CRUD / redaction / 路径穿越拒绝 |

跑全量:`.venv/bin/pytest -q` → 当前 **48 passed in 0.4s**。

---

## 12. 工程纸面契约 vs. 工程现状

| 名字 | 在哪 | 状态 |
|---|---|---|
| [MAOE.md](../MAOE.md) | 项目根 | "项目身份"。说自己是 Skill 原生工作流编译器 |
| [AGENTS.md](../AGENTS.md) | 项目根 | 8 个角色定义,每个对应 `agents/<name>.md` |
| [RULES.md](../RULES.md) | 项目根 | 写代码必须遵守的硬规则 |
| [SOUL.md](../SOUL.md) | 项目根 | 工程哲学(诚实、够用即停、风险必须有回滚...) |
| [WORKING-CONTEXT.md](../WORKING-CONTEXT.md) | 项目根 | 当前 session 的状态卡 |
| [COMMANDS-QUICK-REF.md](../COMMANDS-QUICK-REF.md) | 项目根 | 命令速查 |
| [.maoe/manifest.yaml](../.maoe/manifest.yaml) | 工程注册表 | bootstrap loader 校验这里 |
| `commands/*.md` | **不存在!** | manifest 里列了 build/plan/route/run/resume/report,但根本没有 `commands/` 目录 |

**`commands/*.md` 是已声明但未交付的契约缺口** — 跑 `BootstrapLoader().load()` 会因 `invalid commands path` 报错。这是后续要补的功课。

---

## 13. 一次 `maoe run` 完整时序(把所有讲过的串起来)

```
sequenceDiagram (ASCII)

User       CLI       Engine      Parser    Eval    Router    Econ.    Exec.    Quality    LLM
 │          │          │          │         │        │         │        │         │         │
 │ maoe run │          │          │         │        │         │        │         │         │
 │─────────▶│ click    │          │         │        │         │        │         │         │
 │          │ run()    │          │         │        │         │        │         │         │
 │          │ → Eng.   │          │         │        │         │        │         │         │
 │          │─────────▶│ run(desc)│         │        │         │        │         │         │
 │          │          │ snap usage          │        │         │        │         │         │
 │          │          │─────────▶│ parse()  │        │         │        │         │ chat_json
 │          │          │          │─────────────────────────────────────────────────────────▶│
 │          │          │          │◀─────── subtasks[] (JSON)                                │
 │          │          │ for s:                                                              │
 │          │          │─────────────────────▶│ evaluate(s.desc) → ComplexityScore           │
 │          │          │─────────────────────────────▶│ route(id,level) → assigned_model    │
 │          │          │ economist.allocate → budget per subtask                            │
 │          │          │ graph.get_execution_order() → layers                               │
 │          │          │ for layer:  (asyncio.gather + Semaphore)                           │
 │          │          │   for s in layer:                                                  │
 │          │          │     for attempt in max_attempts:                                   │
 │          │          │─────────────────────────────────────────▶│ executor.execute       │
 │          │          │                                          │── chat → output ──▶ LLM │
 │          │          │─────────────────────────────────────────────────▶│ quality.check  │
 │          │          │                                                   │── chat_json ─▶ LLM
 │          │          │     if passed:  store output, break                                │
 │          │          │     else:  router.escalate → assigned_model bump up tier           │
 │          │          │ usage diff → total_cost / total_tokens                             │
 │          │          │◀── EngineResult                                                    │
 │          │ print/JSON                                                                    │
 │ stdout   │                                                                                │
```

> 你能解释这张图的每一步,就算把"运行管线"吃透了。

---

## 14. 自我学习建议路线

1. **跑通最小回路**:`maoe run "写一个反转字符串的 Python 函数"` 先看真实输出。
2. **加断点 / 打印** 在 `orchestrator.run()` 的每一步,看 subtask 字段是怎么被一步步填满的。
3. **改 `COMPLEXITY_TO_TIER`** 看路由行为变化(比如把 MODERATE→FAST,看质量门会不会大量重试)。
4. **看测试**:`tests/test_orchestrator.py` 用了 mock LLM,是你学"如何在不烧钱的前提下读懂一段执行流"的最好教材。
5. **挑战题**:把 `commands/*.md` 补上(参考 `.maoe/manifest.yaml`),让 `BootstrapLoader().load()` 不再报错 — 这会逼你读懂"工程契约"那一层。
6. **进阶**:把编译管线 + 运行管线打通 — 让 `maoe run` 先调 `WorkflowCompiler`,从 `CandidateWorkflow.dag` 转成 `TaskGraph`,再走 orchestrator。这是这个项目下一个里程碑。

---

## 附录 A:能跳读的源码索引

运行管线:
- [main.py](../src/maoe/main.py) → [orchestrator/agent_orchestrator.py](../src/maoe/orchestrator/agent_orchestrator.py) → [parser/task_parser.py](../src/maoe/parser/task_parser.py) / [evaluator/complexity_eval.py](../src/maoe/evaluator/complexity_eval.py) / [router/model_router.py](../src/maoe/router/model_router.py) / [economist/token_economist.py](../src/maoe/economist/token_economist.py) / [quality/quality_gate.py](../src/maoe/quality/quality_gate.py) → [llm/client.py](../src/maoe/llm/client.py)

编译管线:
- [compiler/goal_ir.py](../src/maoe/compiler/goal_ir.py) → [compiler/capability_graph.py](../src/maoe/compiler/capability_graph.py) → [compiler/workflow_compiler.py](../src/maoe/compiler/workflow_compiler.py) → [compiler/type_checker.py](../src/maoe/compiler/type_checker.py)

实验室:
- [experiments/evaluator.py](../src/maoe/experiments/evaluator.py) / [experiments/early_stopper.py](../src/maoe/experiments/early_stopper.py) / [experiments/pareto_selector.py](../src/maoe/experiments/pareto_selector.py) / [experiments/candidate_lab.py](../src/maoe/experiments/candidate_lab.py)

数据契约:
- [models/task.py](../src/maoe/models/task.py) / [models/complexity.py](../src/maoe/models/complexity.py) / [models/routing.py](../src/maoe/models/routing.py) / [models/capsule.py](../src/maoe/models/capsule.py) / [models/workflow.py](../src/maoe/models/workflow.py)

运行态:
- [runtime/state.py](../src/maoe/runtime/state.py) / [runtime/run_store.py](../src/maoe/runtime/run_store.py) / [runtime/redaction.py](../src/maoe/runtime/redaction.py)

注册表与引导:
- [registry/skill_registry.py](../src/maoe/registry/skill_registry.py) / [bootstrap/loader.py](../src/maoe/bootstrap/loader.py)

Benchmarks:
- [benchmarks/metrics.py](../benchmarks/metrics.py) / [benchmarks/suite.py](../benchmarks/suite.py) / [benchmarks/runner.py](../benchmarks/runner.py) / [benchmarks/report.py](../benchmarks/report.py)
