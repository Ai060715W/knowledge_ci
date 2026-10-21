# Knowledge CI 项目计划

- 编制日期：2026-10-19
- 状态：实施计划草案；技术建议与待确认事项见第 3、11 节。
- 需求依据：[knowledge_ci.html](D:/knowledge_ci/knowledge_ci.html)，当前为静态产品与系统设计说明。
- 协作规范：[AGENTS.md](D:/knowledge_ci/AGENTS.md)、[CLAUDE.md](D:/knowledge_ci/CLAUDE.md)。
- 逐步执行与排期：[TASK_PLAN.md](D:/knowledge_ci/TASK_PLAN.md)，每项2～3个工作日。
- 已确认：当前由 Recall 一人开发；系统实现语言使用 Python；分支管理由 Recall 安排。
- 当前阶段：T01工程与自动验证完成、待验收；T02共享契约完成、待验收。已具备可安装Python包、配置、CLI、健康检查及共享schema/状态规则。扫描、数据库和审核业务尚未实现。
- 更新原则：范围、契约或排期变化时先更新本计划，再调整实现；已完成项必须附验证证据。

## 1. 项目目标与现状

### 1.1 要解决的问题-

从代码结构和 Git 演进中发现“为什么这样设计、哪些约束不能破坏、哪些历史例外仍然有效”，经证据核验与人工审核形成结构化知识，并在后续代码变化和开发操作中持续使用。

第一阶段先回答一个问题：对一个真实仓库，能否发现并经人工认可 10～30 条有开发价值、可追溯的隐藏知识。

“有价值”至少满足以下一项：解释设计原因、指出不可破坏的业务约束、说明历史兼容或事故保护逻辑；同时能够改变阅读、修改或验证代码的决策。仅复述函数功能的摘要不计入成果。

### 1.2 已有内容与缺失内容

| 项目 | 当前状态 | 对开发计划的影响 |
| --- | --- | --- |
| 产品目标与三阶段路线 | HTML 已描述 | 可以作为需求基线，仍需补齐验收口径 |
| 知识发现、新鲜度、注入、增量演进 | 设计描述 | 没有可运行的业务实现 |
| 知识单元 | 字段表和 JSON 示例 | 示例字段不完全一致，需统一契约 |
| 页面交互 | 锚点跳转、导航高亮、折叠说明 | 不是知识审核工作台 |
| Python工程与基础验证 | T01已验证，待验收 | 18项测试、Ruff及独立wheel安装复验通过；数据库、业务API和CI后续建立 |
| 试点仓库与模型政策 | 已选Vue3Admin、GitHub，允许后续外部模型 | 固定77e9634为主基线；供应商与预算仍待确定，当前mock |

### 1.3 当前执行原则

1. 一人按依赖顺序开发，每完成一个可验证切片再进入下一项。
2. 按领域划分模块，后续人员加入时按模块接手，避免因加人重写系统。
3. 分支策略由 Recall 管理；本计划只定义每项工作的输入、输出和合入条件。
4. 首期采用模块化单体，保留接口边界；图数据库、向量服务、A2A 留到有证据需要时再引入。
5. 第一阶段所有正式知识均由人审核；模型评分不能代替审核结论。

## 2. 范围、优先级与需求追踪

本文用 P0 表示发现与审核 MVP，P1 表示新鲜度与增量演进，P2 表示注入与平台扩展。它们是实施优先级，不代表线上故障级别。

| 编号 | HTML 来源章节 id | 能力 | P0 交付边界 | 后续阶段 |
| --- | --- | --- | --- | --- |
| R01 | discovery | 仓库接入与版本定位 | 读取一个本地 Git 仓库的指定 commit，不修改被分析仓库 | P1 接入一种远程托管平台 |
| R02 | discovery | AST 与依赖分析 | 首批分析Vue/JS/TS，提取组件、模块、类、函数及静态import边 | P1补充可解析调用；更多语言后置 |
| R03 | discovery | Top-K 与异常信号 | 修改频率、模块入度、贡献者信号；循环import、硬编码阈值、空catch/静默降级等候选线索 | 有数据后接入事故、回滚、MR 讨论信号 |
| R04 | discovery | 历史证据与追问 | 代码片段、Git commit、人工回答；追问分配与回答闭环 | P1 接入选定平台的 PR/MR、Issue 证据 |
| R05 | knowledge-unit | 结构化知识 | 结论、原因、范围、证据、评分、负责人、来源快照和不可变修订 | P1 增加影响评估与版本恢复操作 |
| R06 | overview / roadmap | 基础审核平台 | 候选列表、详情与证据、修改、追问、批准、驳回、发布、审计 | 后续扩充图谱、风险视图、通知 |
| R07 | freshness | 新鲜度判断 | 先记录可验证的快照与范围，不宣称实时新鲜 | P1 实施 commit 对比、保守 AST Diff、影响判断 |
| R08 | evolution | 增量演进 | 保存足够的版本与审计基础，不自动改写已发布知识 | P1 单平台事件、风险分级、建议更新、恢复 |
| R09 | injection | 开发前注入 | 不纳入 P0 | P2 实现 get_context，再验证一个客户端集成 |
| R10 | agents | 六类 Agent 与 A2A | 对应为应用内模块职责，不建设 Agent 网络 | P2 依据实测瓶颈决定是否引入 A2A |
| R11 | architecture / metrics | 存储、任务、可观测性 | 本地持久化、可恢复任务、日志、成本与发现质量统计 | 随协同运行规模升级基础设施 |

P0 暂不承诺：全语言/全仓精准调用图、运行时数据流、多平台集成、事故自动归因、全自动正式知识发布、实时 Agent 拦截、多租户权限体系，以及证明因果关系的模型结论。

## 3. 关键技术建议与架构影响

### 3.1 已确认与建议的区别

| 决策 | 状态 | 原因与影响 |
| --- | --- | --- |
| 系统使用 Python 开发 | 用户已确认 | 工程、分析、任务与知识服务均以 Python 为主 |
| 当前按一人分配工作 | 用户已确认 | 按最短依赖链推进，不预设多人同时维护基础设施 |
| 分支管理 | 由 Recall 安排 | 任务计划提供可采用的分支建议，创建、合并与推送仍由用户安排 |
| 首批被分析仓库使用Vue/JS/TS | 用户已选定仓库，T01核对源码 | Python仍是系统实现语言；目标解析器与SFC位置映射须独立适配 |
| 模块化单体 | 建议 | 一个代码库、一套契约；HTTP、CLI、worker 共享应用服务，后续可独立接手模块 |
| FastAPI + Pydantic Settings | T01已落地并验证 | 复用校验模型生成 API 契约，减少调用方与服务端模型漂移 |
| Jinja2 服务端页面，按需补少量浏览器脚本 | 建议 | 单人先完成审核流程；未来复杂交互可复用 API 更换前端 |
| SQLAlchemy + Alembic | 建议 | 持久化与迁移有明确边界，为后续数据库迁移保留路径 |
| SQLite 用于本机单用户 MVP | 建议，有适用边界 | 降低启动成本；单 worker、短事务、失败重试必须验证 |
| 共享服务或多 worker 前评估 PostgreSQL | 条件性决策 | 数据库变更需要迁移演练，不把 ORM 当作自动兼容保证 |
| 本地证据文件 + 存储接口 | 建议 | 首期无需对象存储服务；证据引用使用逻辑 ID，避免数据库写死绝对路径 |
| 模型提供方适配器 + 固定假响应 | 建议 | 在未选定供应商前可完成联调；真实输出需独立评估质量与成本 |

FastAPI 的自动 API 描述与模板支持可参考 [功能说明](https://fastapi.tiangolo.com/features/) 和 [模板文档](https://fastapi.tiangolo.com/advanced/templates/)；运行时数据模型参考 [Pydantic Models](https://pydantic.dev/docs/validation/latest/concepts/models/)。上述组合是本计划建议，不代表已搭建或已锁定依赖版本。

持久化与迁移的实现基线分别参考 [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/quickstart.html) 与 [Alembic 文档](https://alembic.sqlalchemy.org/en/latest/)，版本在 S01 验证兼容后锁定。

### 3.2 分析能力边界

- 已选试点为Vue SFC / TypeScript / JavaScript，不能使用Python ast。计划通过隔离的[Vue官方SFC解析器](https://github.com/vuejs/core/tree/main/packages/compiler-sfc)及JS/TS解析辅助工具产生受控JSON，Python负责编排；T06再锁定版本和验证能力边界，不执行目标项目代码。
- 静态 import 图是首期可交付项；计算表达式动态导入、反射、运行时注入和无法解析的调用边标记 unknown，不伪装成完整依赖图。
- 规则只提供线索：“宽泛异常捕获”不等于错误，“硬编码阈值”不等于业务规则；是否形成知识依赖证据和人工判断。
- Top-K 首版仅用能稳定采集的信号。默认观察窗口建议为目标 commit 之前 90 天、K=10，作为可配置初值，并由试点调整。
- 信号归一化方式、权重、缺失项和确定性排序规则写入配置版本；事故信息缺失不能当作零风险。
- 建议初始权重：修改频率 0.5、模块入度 0.3、贡献者多样性 0.2；单独展示原始值、归一化值与缺失项。它不是已验证的最优公式。

### 3.3 持久化与长任务

建议用数据库保存任务与阶段结果，由一个专用 worker 逐项处理。HTTP 请求只提交任务，不承担长时间扫描和模型调用。

SQLite 同一时刻仅允许一个写事务，WAL 也不会变成多写者数据库，见 [SQLite 隔离说明](https://www.sqlite.org/isolation.html)。本地 MVP 采用短事务、写锁重试和单 worker；模型网络请求必须在数据库事务外执行。若需要多人共享服务、多 worker 或持续出现写锁等待，评估切换 PostgreSQL。

不在首期引入 Redis、Celery、消息集群、图数据库或向量数据库。任务持久化、重试和故障恢复仍是 P0 必须实现的能力。

## 4. 系统结构与模块边界

### 4.1 运行链路

~~~mermaid
flowchart LR
  User[Recall：CLI / 审核页面] --> Service[应用服务与权限边界]
  Service --> DB[(任务与知识数据库)]
  Worker[单 worker] --> DB
  Worker --> Repo[只读 Git 快照]
  Repo --> Analysis[静态分析与 Top-K]
  Analysis --> Evidence[证据聚合]
  Evidence --> Draft[知识草稿与追问]
  Draft --> DB
  Service --> Review[人工审核与发布]
  Review --> DB
  Draft --> Model[可替换模型适配器]
~~~

源码不是直接交给模型自由操作的工作目录。分析器读取固定快照，模型接收受预算约束的证据材料；模型无法自行执行仓库脚本、扩大读取范围或发布知识。

### 4.2 计划目录

以下是工程结构预案，目录规范以根目录AGENTS.md为准。用户要求测试代码、样例、专用依赖/配置与报告不入库，统一放Git忽略的var/local-checks/；源码和运行配置不依赖该目录。后续业务模块按需创建。

~~~text
knowledge_ci/
├── AGENTS.md
├── PROJECT_PLAN.md
├── TASK_PLAN.md
├── knowledge_ci.html
├── pyproject.toml                 # S01 创建，锁定环境与工具
├── src/knowledge_ci/
│   ├── app.py                     # HTTP 应用组装
│   ├── cli.py                     # 命令入口；复用应用服务
│   ├── contracts/                 # Pydantic schema、枚举、错误码
│   ├── repository/                # Git 访问、快照、路径校验
│   ├── analysis/                  # AST、import 图、规则、评分
│   ├── evidence/                  # 代码与历史证据聚合
│   ├── knowledge/                 # 生成、追问、知识修订
│   ├── review/                    # 审核、发布与审计规则
│   ├── jobs/                      # 持久化任务、阶段、重试
│   ├── storage/                   # 数据访问与产物存储适配器
│   └── web/
│       ├── templates/
│       └── static/
├── migrations/
├── docs/decisions/
└── var/                           # Git忽略；运行数据、产物及local-checks本地验证
~~~

### 4.3 模块输入、输出与禁区

当前全部由 Recall 负责。下表的模块边界用于单人控制改动范围，也用于未来交接。

| 模块 | 输入 → 输出 | 责任边界 |
| --- | --- | --- |
| contracts | 需求定义 → 统一 schema、错误码、样例 | 所有模块复用；禁止各自复制枚举或请求类型 |
| repository | 已授权仓库 + ref → 不可变 Snapshot、文件、Git 历史 | 不执行源码、不写被分析仓库、不调用模型 |
| analysis | Snapshot + 配置 → 符号、import 边、信号、排名、诊断 | 不推断未经证据支持的历史原因 |
| evidence | 候选位置 + Snapshot → 可追溯 Evidence 集合 | 不把代码注释或 commit 消息自动认定为事实 |
| knowledge | 证据 + 模型配置 → Draft、Claim、Question | 不绕过 review 直接发布 |
| review | 指定修订 + 人工决策 → 审核记录、发布指针、审计 | 审核须绑定修订；不能覆盖已有历史 |
| jobs | 命令 + 幂等键 → 可恢复任务及阶段结果 | 编排流程，不复制分析或知识规则 |
| storage | 领域对象 → 持久化记录、逻辑产物引用 | SQL/文件布局封装在此；不决定审核策略 |
| web / cli | 用户输入 → 调用应用服务、展示结果 | 不直接改表、不复制业务状态机 |
| integrations（P1/P2） | 平台事件/上下文请求 → 领域命令/查询 | 不绕过相同的版本、权限和审核规则 |

依赖规则：contracts 不依赖业务模块；业务逻辑依赖契约和存储接口；app/cli/worker 负责组装具体适配器。跨模块读取与写入经过公开服务接口，避免循环 import 和直接跨模块改表。

## 5. 开发前冻结的数据契约

本节是字段级基线。T02已在 `src/knowledge_ci/contracts/` 落地为可执行 schema、状态转换纯函数与错误码（待验收）；字段、状态机或错误语义的后续变更先改契约再改调用方。契约只校验规则并返回新的不可变对象，事务内的CAS比对、ID生成与审计写入由 T04/T14/T15 落实。

T02 相对下表草案的已落地差异：

- Job 增加 `partial` 终态，以及 repository_id、request_hash、requested_ref（仅展示）、max_attempts、lease_expires_at、progress、updated_at；对外读取用不含 lease_token 的 JobView。
- Evidence 去掉 source_ref：locator 按 code/commit/human_answer 判别并定位来源，content_hash 作为产物内容寻址键。
- Knowledge 增加 repository_id、当前修订的 review_status 与时间戳；KnowledgeRevision 增加 based_on_revision、content_hash、evidence_sufficiency、model_score、created_by，invalidation_conditions 改为显式 known/unknown 结构；Claim 增加 gap；Review 绑定 content_hash；Question 增加 adopted_evidence_id、resolution_note；Verification 增加 verification_id。
- AuditEvent、模块排名和知识详情读视图分别在 T15、T08、T14 定义，T02 不预建。

### 5.1 基础对象

| 对象 | 最小字段 | 必须保持的语义 |
| --- | --- | --- |
| Repository | repository_id、name、source、allowed_root | 第一阶段仅接入已授权的本地 Git 仓库；路径规范化并限制根目录 |
| Snapshot | snapshot_id、repository_id、commit_sha、tree_sha、created_at | 只标识代码内容；ref 先解析成完整 commit SHA；分支名仅作展示 |
| AnalysisRun | analysis_run_id、snapshot_id、language、parser_version、rule_set_version、config_hash、pipeline_version、model_version、prompt_version、created_at | 记录一次逻辑分析配置；未调用模型时相应版本可空；同快照不同配置分别保存 |
| Symbol | symbol_id、snapshot_id、analysis_run_id、path、qualified_name、kind、start_line、end_line | 路径使用仓库相对路径及 / 分隔；行号从 1 开始，结束行包含在范围内 |
| Evidence | evidence_id、snapshot_id、type、source_ref、locator、content_hash、excerpt、captured_at | type 首期为 code/commit/human_answer；定位到快照、文件/符号或人工回答记录 |
| Claim | claim_id、kind、text、evidence_ids | kind 为 observed/inferred/human_confirmed；不能用置信度把推断升级成事实 |
| Knowledge | knowledge_id、current_revision、published_revision、lifecycle、state_version | 保存当前/发布指针；任何影响发布的内容或状态变更均递增 state_version |
| KnowledgeRevision | knowledge_id、revision、snapshot_id、analysis_run_id、title、summary、rationale、scope、invalidation_conditions、claims、evidence_ids、risk_level、owner_id、created_at | knowledge_id 稳定，revision 单调递增；已保存修订不原地覆盖 |
| Question | question_id、knowledge_id、revision、assignee_id、text、blocking、status、answer、answered_by、answered_at | 证据不足问题默认阻断发布；回答只触发重新评估，不直接发布 |
| Review | review_id、knowledge_id、revision、decision、reviewer_id、reason、created_at | 审核批准的内容必须与待发布修订一致 |
| Verification | knowledge_id、revision、verified_snapshot_id、scope_hash、result、method、verified_at | 验证针对一个快照与范围；result 为 fresh/stale/unknown |
| Job | job_id、idempotency_key、analysis_run_id、snapshot_id、status、stage、attempt、lease_token、heartbeat_at、error、created_at | 记录执行阶段和可重试性；超时恢复、重试及取消使旧执行凭据失效 |
| AuditEvent | event_id、actor_id、action、object_id、revision、before、after、job_id、occurred_at | 审计追加写入；不存凭据或完整敏感 prompt |

补充规则：

- 统一 ID 为不透明字符串；时间使用 UTC ISO 8601，页面按用户时区展示。
- 快照身份、逻辑分析与执行尝试分开：Snapshot 固定代码，AnalysisRun 固定分析配置，Job 的 attempt 表示重试；同快照不同配置的排名和产物可分别查询。
- code 证据保存文件内容哈希与可回看的片段；外部链接仅作辅助，不能依赖链接永远在线。
- 每条 Claim 引用证据。证据不足的推断可以保留在草稿中，但必须标明缺口并进入追问；发布时所有结论须具备可核验来源或可追溯的人工确认。
- confidence 建议改为 model_score（可空、范围 0～1），另设 evidence_sufficiency=insufficient/partial/sufficient；人工决定独立存 Review。
- last_verified_at 是验证记录的展示投影，不能单独决定是否有效；valid_from_version 必须区分 commit 与可空 release_tag。
- invalidation_conditions 记录规则变化、依赖替换或历史兼容结束等失效条件；未知时显式标记 unknown 并说明缺口，不将空缺解释为永久有效。
- owner_id 在草稿时可空，发布前必填；reviewer_id 来自审核记录。单人阶段允许二者为同一个真实操作者。
- 风险级别 low/medium/high/unknown；证据缺失、冲突或无法判断时不得默认 low。
- 全新候选不强制具备模型评分；格式校验通过也不代表事实正确。

### 5.2 状态维度与转换

| 维度 | 状态 | 转换约束 |
| --- | --- | --- |
| 生命周期 | draft / published / archived | 发布要求当前修订 approved、负责人明确、无阻断追问；归档保留记录 |
| 修订审核 | unreviewed / in_review / changes_requested / approved / rejected | 任意内容修改创建新修订并回到 unreviewed；批准不能自动继承 |
| 新鲜度 | unknown / fresh / stale | 针对指定快照与范围记录；fresh 不代表在任意分支或未来 commit 都有效 |
| 追问 | open / answered / resolved / cancelled | answered 后重新评估；只有证据被采纳或明确结案才 resolved |
| 执行任务 | queued / running / succeeded / partial / failed / cancelled | 失败保留阶段产物；可重试失败在上限内回 queued，重试增加 attempt；partial 表示部分输入失败且诊断可见；取消后不再提交后续结果 |

编辑已发布知识时新建草稿修订，published_revision 仍指向旧的已批准修订，直到新修订被批准并发布。任务失败、模型重跑或后续草稿被驳回均不能破坏原已发布内容。

所有编辑、审核和发布命令同时携带 expected_revision 与 expected_state_version；数据库在同一事务内检查内容修订与状态版本，不匹配返回 409。修改内容或审核/发布状态，以及影响发布的阻断问题变化，都递增 state_version；内容修改另增 revision。单人阶段也保留此契约，以防多页面、重试及未来多人操作覆盖数据。

P0 只声明“该知识在来源快照上已被人工核验”，不宣称持续有效；新目标快照默认 unknown。P1 才扩展跨快照复核。

### 5.3 最小 API 草案

接口统一置于 /api/v1。CLI 和模板页面复用同一应用服务，不通过直接写数据库实现快捷路径。

| 方法与路径 | 输入 / 输出要点 | 阶段 |
| --- | --- | --- |
| POST /repositories | 已授权本地路径 → repository_id | P0 |
| POST /repositories/{id}/analyses | ref、配置、Idempotency-Key → 202 + job_id + snapshot_id + analysis_run_id | P0 |
| GET /jobs/{job_id} | 状态、阶段、进度分母、错误、可重试性 | P0 |
| POST /jobs/{job_id}/retry | 复用逻辑任务、增加 attempt；不重复创建候选 | P0 |
| GET /repositories/{id}/modules | 明确指定 analysis_run_id → 排名、信号解释与来源快照 | P0 |
| GET /knowledge | repository_id、发布/审核状态、分页与筛选 | P0 |
| GET /knowledge/{id} | 指定修订、当前/发布指针、state_version、证据、追问、审核及验证记录 | P0 |
| POST /knowledge/{id}/revisions | expected_revision、expected_state_version、修改内容 → 新修订 | P0 |
| POST /knowledge/{id}/questions | 修订、问题、assignee_id → 追问 | P0 |
| POST /questions/{id}/answers | 回答、操作者 → 回答记录与重新评估任务 | P0 |
| POST /knowledge/{id}/reviews | expected_revision、expected_state_version、approve/request_changes/reject、理由 | P0 |
| POST /knowledge/{id}/publish | expected_revision、expected_state_version → 发布修订及审计记录 | P0 |
| POST /repositories/{id}/change-checks | base_commit、head_commit → 异步影响检测 | P1 |
| POST /context/query | repository_id、target_commit、intent、paths、operation、budget → 最小上下文 | P2 |

统一约定：

- 列表返回 items、next_cursor；错误返回 code、message、details、request_id，敏感数据必须脱敏。
- 校验失败使用 422，资源不存在使用 404，修订冲突使用 409；启用认证的运行模式中区分 401 与 403。
- 分析启动先解析快照再持久化 Job；长任务返回 202，页面轮询任务状态，进度无法量化时只显示阶段。
- Idempotency-Key 重放同一请求返回同一逻辑 Job；同键不同参数返回冲突。
- 逻辑任务内部唯一键包含 repository_id、commit_sha、阶段、pipeline_version、config_hash、模型/提示词版本；候选产物另有稳定去重键。
- 首期本地页面的 actor_id 由服务端配置为 Recall 的操作者身份；不把浏览器提交的任意 reviewer_id 当可信身份。多人共享运行前接入认证与仓库级授权。
- 更改状态的页面表单增加 CSRF 防护或等效同源校验；服务默认只监听本机。

### 5.4 异步结果与恢复约定

P0 用持久化任务和阶段产物即可，不要求独立事件总线。一次逻辑任务允许多次执行，结果提交按幂等键去重。

- worker 定期更新 heartbeat；进程重启后扫描租约超时的 running 任务，标记 interrupted 原因，再按阶段检查点恢复或显式重试。
- 每次执行持有新的 lease_token；结果提交须原子确认任务仍为 running 且 attempt/lease_token 仍有效。超时恢复、重试或取消均使旧 token 失效，迟到响应不得写入或覆盖新产物。
- AST、Git 采集、模型调用和产物保存分别记录结果；部分文件解析失败时保留诊断，并在任务结果中明确 partial，不能静默声称全仓成功。
- 默认最多 3 次可重试尝试，退避参数可配置；语法不支持、权限拒绝等永久失败直接返回可操作原因。
- 未发布的模型结果、未完成追问和临时产物有明确状态；失败重试不产生重复知识或重复审核项。
- 模型外部调用不承诺恰好执行一次；网络超时可能导致再次计费。记录每次调用与预算占用，供应商支持幂等请求时复用其能力；本地最终产物提交必须去重。
- P1 若引入跨进程事件，统一信封至少包含 event_id、schema_version、event_type、aggregate_id、aggregate_revision、snapshot_id、correlation_id、occurred_at、payload；消费方去重且不依赖全局有序。需要可靠投递时再落地事务 outbox。

## 6. 核心流程与产品页面

### 6.1 发现—审核最小闭环

1. 指定一个已授权仓库及 commit，固定快照，列出过滤项与不支持的文件。
2. 解析源码、建立 import 图，结合 Git 历史生成可解释的 Top-K。
3. 对 Top-K 运行有限规则，选出候选位置，收集对应代码与历史证据。
4. 调用固定假响应或真实模型，生成区分事实/推断的知识草稿，并校验引用。
5. 证据不足时创建追问；Recall 回答后重新评估并形成新修订。
6. 在详情页核对原始证据、修改内容、批准或驳回；批准与发布是可审计的明确操作。
7. 发布后能从知识反查修订、来源 commit、代码位置、证据及审核者。

### 6.2 P0 最少页面

| 页面 | 核心操作 | 必须显示的异常 |
| --- | --- | --- |
| 仓库与任务 | 注册本地仓库、启动分析、查看阶段、重试 | 非 Git 路径、未授权路径、无效 commit、任务失败/中断 |
| 模块与候选 | Top-K、信号解释、候选筛选 | 解析缺失、动态关系 unknown、历史不足 |
| 知识详情 | 查看结论/原因、固定快照证据、编辑修订 | 证据缺口、修订冲突、来源不再可访问 |
| 追问与审核 | 分配/回答、差异查看、批准/驳回、发布 | 未解决的阻断问题、未批准修订、失败理由 |
| 正式知识列表 | 查看已发布修订与来源快照 | 新鲜度未知、已归档、存在待审新修订 |

页面验收必须包含空状态、加载状态和失败状态。复杂图谱与仪表盘不阻塞首期闭环。

### 6.3 P1 新鲜度与演进

采用“commit/范围对比 → 保守语法过滤 → 依赖影响 → 必要时模型判断 → 人工/规则决策”的顺序。

- 时间只用于排队，版本与验证范围才是有效性依据。分支前进、rebase、文件重命名与依赖变化均须有处理策略。
- 不能笼统忽略 import 排序、日志修改或任意注释：副作用 import、日志表达式、类型指令、配置指令等可能有行为影响。
- 只有能证明属于约定等价范围的变化才自动跳过；不支持或无法判断的变化进入 unknown/待复核。
- 低风险自动更新先以“只生成建议”的方式观察；达到预先约定的误判与回滚指标后，再决定是否启用自动发布。
- 恢复操作创建一个引用历史内容的新修订，保留当前历史、审核与审计，不删除记录。

### 6.4 P2 注入与集成

先实现普通上下文查询，再适配 MCP 工具；自动在修改前执行依赖具体客户端的 Hook 或工作流能力，须针对选定客户端验证。

MCP 定义服务端可暴露、客户端可调用的工具，本身不保证拦截每次修改，见 [MCP Tools 规范](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)。

get_context 输入至少包含仓库、目标 commit、操作意图、相对路径、操作类型和预算；返回知识 ID/修订、约束、风险、证据、建议验证项、freshness、截断与降级说明。默认只将已发布且对目标版本有效的知识作为约束；unknown/stale 仅能以明确标记的待核验提示返回。

## 7. 单人实施顺序与里程碑

逐任务排期与状态统一维护在 [TASK_PLAN.md](D:/knowledge_ci/TASK_PLAN.md)。它将17个工作包拆成40项任务，每项2～3个工作日，附每日步骤、目标路径、依赖、验收与建议分支名。原S编号用于范围追踪，实际开工与建分支使用T编号。

### 7.1 时间口径与阶段门槛

以一个人完整可投入的工作日估算，每项已含编码、针对性测试、必要文档与合入准备，每周按5天换算；不再另外重复增加每周一天联调。外部授权、模型开通和知情者回复等待单独记录。未指定开工日，使用相对工作日。

| 里程碑 | 任务范围 | 相对工作日 | 可验收成果 |
| --- | --- | --- | --- |
| M0 范围与契约 | T01～T03 | D001～D007 | 试点、环境决定、统一schema与黄金样例 |
| M1 可复现分析 | T04～T11 | D008～D027 | 只读快照、AST/import图、Top-K、证据及扫描CLI |
| M2 端到端薄切片 | T12～T17 | D028～D044 | 草稿生成、修订、审核发布API与最少页面 |
| M3 追问与可靠性 | T18～T22 | D045～D056 | 追问、任务恢复、异常处理、成本与备份恢复 |
| M4 真实试点验收 | T23～T24 | D057～D062 | 真实试点满足第9节A01～A12；不足则调整并重排 |
| P0机动容量 | 7天 | D063～D069 | 范围内返工；可在阶段中使用，未用可释放 |
| M5 增量与新鲜度 | T25～T34 | D070～D097 | 增量复核、建议审核、恢复及单平台事件 |
| P1机动容量 | 3天 | D098～D100 | 使用后记录实际消耗 |
| M6 注入与反馈 | T35～T40 | D101～D116 | 上下文服务、一个MCP/客户端集成及反馈 |
| P2机动容量 | 2天 | D117～D118 | 当前范围收尾 |

P0共24项、62天任务量，加7天机动为69工作日，按每周5天约14周；P1为28+3天，P2为16+2天。全计划40项共106天任务量，加12天机动为118工作日，约24周。P1/P2为预备排期，分别在前一阶段验收后决定是否启动并重新校准。

原先“P0约8～10周”的粗估被逐项累计替代。完整范围的恢复、审核和真实核验需要实际投入，不能为保持旧周数删掉验收。任务细节、状态、实际工时以TASK_PLAN.md为唯一来源。

### 7.2 原工作包与细分任务对应

| 原ID | 工作包 | 执行任务 |
| --- | --- | --- |
| S01 | 确定试点、Python 版本、依赖与最小工程 | T01 |
| S02 | 冻结共享模型与黄金样例 | T02、T03 |
| S03 | 建立持久化、修订与迁移基础 | T04、T14 |
| S04 | 仓库只读访问与快照 | T05 |
| S05 | Python AST 与 import 图 | T06、T07 |
| S06 | Git 信号、Top-K 与规则 | T08、T09 |
| S07 | 代码与历史证据聚合 | T10 |
| S08 | 持久化任务与 CLI 主链路 | T11 |
| S09 | 模型适配与草稿生成 | T12、T13 |
| S10 | 修订、审核、发布应用服务及 API | T14、T15 |
| S11 | 最少审核页面与一条知识薄切片 | T16、T17 |
| S12 | 追问、回答与重新评估 | T18 |
| S13 | 恢复、幂等、冲突与异常页面 | T19、T20 |
| S14 | 指标、预算报告与备份恢复 | T21、T22 |
| S15 | 真实仓库试点与缺陷修复 | T23、T24 |
| S16 | 增量触发、影响判断与安全恢复 | T25、T26、T27、T28、T29、T30、T31、T32、T33、T34 |
| S17 | 上下文服务及一个客户端集成 | T35、T36、T37、T38、T39、T40 |

从T01 → T02 → T03开始，再按任务总表推进。共享契约、幂等与审核原子性随首次实现一起验证，后续可靠性任务补齐故障覆盖。建议分支由Recall按准备开工的任务创建。

## 8. 后续多人接手规则

多人开发是组织变化，不自动意味着多租户产品或微服务。新增人员先接手稳定模块，运行环境是否需要升级另行判断。

### 8.1 交接时需要提供的上下文

每个任务必须写清以下内容，不使用“处理相关文件”一类模糊描述：

~~~text
目标：一个可验收的行为
文件：允许修改的具体路径、禁止触碰的共享文件
输入：schema 名称/版本、固定快照、黄金样例
输出：接口/产物/错误语义，以及调用方
依赖：前置任务和待交付内容
边界：语言、权限、预算、性能、禁止引入的设施
验收：可执行命令或可重复的操作步骤及预期结果
~~~

### 8.2 将来可拆分的模块

| 工作包 | 可交接范围 | 接手前要求 | 必须协调的变更 |
| --- | --- | --- | --- |
| 仓库与分析 | repository、analysis、evidence | Snapshot/Evidence 契约及固定样例稳定 | 符号 ID、定位规则、快照与规则版本 |
| 知识与评估 | knowledge、模型适配、质量评测 | Claim/KnowledgeRevision/Question 契约稳定 | 提示词输出、证据充分度、风险和预算 |
| 应用与可靠性 | storage、jobs、review、迁移 | 状态机、幂等与修订规则稳定 | 表结构、公开接口、权限与审计 |
| 工作台与集成 | web；后续 integrations | API、错误码、mock 样例稳定 | 交互改变的领域命令、上下文返回结构 |

人数与角色届时再确定，不在当前排期中预留虚构负责人。

### 8.3 共享文件与合入门禁

- 新人员加入前指定唯一的集成负责人；当前为 Recall。
- contracts、数据库迁移、pyproject、锁文件、应用入口、根目录规范与计划由集成负责人协调。
- 共享契约先改 schema 与样例，再改生产方和消费方；兼容期与迁移顺序写入变更说明。
- 每项变更只围绕一个验收目标，记录为什么、架构影响、验证结果、迁移与恢复方式。
- 合入前运行该变更影响的验证；不用无关的全量重复测试代替针对性检查。
- 不自动推送、发布或部署；实际工程启动时再记录可验证的部署命令。
- 后续代码负责人规则或 CI 平台配置在选定托管平台后落地，不能把尚不存在的检查当成已启用门禁。

## 9. 验证计划与阶段验收

### 9.1 验证分层

| 层级 | 重点 | 样例/方法 |
| --- | --- | --- |
| 契约与单元 | 字段约束、状态转换、规则、评分、版本冲突 | 仅本地验证工具；固定输入与正反例，不依赖外部模型，验证代码/依赖不入库 |
| 仓库与存储集成 | Git 快照、解析诊断、迁移、任务幂等、证据引用 | 小型合成 Git 历史、临时数据库、内容哈希核验 |
| 页面/API 闭环 | 仓库→候选→追问→审核→发布→回溯 | 固定假响应贯通；覆盖加载、失败、冲突状态 |
| 真实模型评测 | 推断与事实、引用正确性、价值、成本 | 固定证据集、多次运行记录模型/提示词版本 |
| 真实仓库试点 | 隐藏知识价值与可用性 | 仓库知情者逐条核验；Recall 不知情时请知情者确认，不能自行猜测业务历史 |
| 故障与恢复 | worker 中断、模型超时、写锁、产物丢失、备份 | 受控故障注入，确认无重复发布与历史丢失 |

T01已验证CLI、配置和HTTP启动退出；运行命令见README。测试代码、专用工具配置与依赖保存在Git忽略的本地目录，不进入业务仓库，后续按相同规则验证。

### 9.2 P0 发布门槛

| 编号 | 必须满足的验收标准 |
| --- | --- |
| A01 | 一个真实获授权仓库完成至少一次端到端分析；运行期间分支变化不改变本次固定快照 |
| A02 | 同快照、同分析器/配置的静态排名可复现；同 commit 两套配置的产物可分别查询且不覆盖；模型生成记录版本与输入哈希，不承诺字面输出确定性 |
| A03 | 静态分析支持边界、过滤文件、失败文件和 unknown 关系可见；不执行或修改被分析仓库 |
| A04 | 经人工确认至少 10 条、目标 10～30 条去重的有价值知识；公开全部候选数、驳回数与原因 |
| A05 | 正式知识的结论引用、来源 commit、范围、失效条件（允许显式 unknown）、负责人、批准修订和审核记录完整率为 100% |
| A06 | 至少演示 3 条证据不足场景的追问闭环；回答不足时能保持待处理，不能强行发布 |
| A07 | 未批准、证据引用无效、阻断追问未解决的修订无法发布；已批准内容改动后必须重新审核 |
| A08 | 重放分析请求、重试模型阶段及中断恢复均不产生重复知识、重复审核或重复发布；重试/取消后的迟到模型响应不得提交 |
| A09 | 两次基于同一旧修订或状态版本的写入/冲突审核，后提交者收到 409；批准后改动内容不能沿用旧批准发布；不覆盖历史 |
| A10 | 记录扫描耗时、模型调用数、token/费用或可解释估算、失败率；达预算上限时暂停模型阶段并给出原因 |
| A11 | 从备份恢复后可查看发布知识、修订、审计和关联证据；数据库与证据产物一起验证 |
| A12 | 本机运行边界生效；密钥不进入源码/日志/证据；模型无法越过只读采集与审核边界 |

若真实仓库在当前范围内不足以支持 10 条有效知识，M4 记录原因并评估更换试点或调整规则；不通过扩大摘要数量完成指标。

### 9.3 指标口径

| 指标 | 口径 | 用途 |
| --- | --- | --- |
| 候选确认率 | 被确认有价值的去重候选 / 已完成审核的去重候选 | 暴露误报，不隐藏尚未审核的分母 |
| 证据完整率 | 满足 A05 的发布知识 / 全部发布知识 | P0 要求 100% |
| 追问解决率 | resolved 追问 / 非 cancelled 追问 | 与回答率分开，答案不等于解决 |
| 单条有效知识成本 | 试点总模型成本 / 人工认可的有效知识数 | 分母为 0 时记未达标，不记 0 成本 |
| 高价值模块覆盖率 | 有已认可知识的 Top-K 模块 / 可分析的 Top-K 模块 | 排名与分母绑定快照，不代替知识质量 |
| 演进误报/漏报 | 对人工标注的变更样例分别统计 | P1 验收前确定阈值和标注集 |
| 注入采用率 | 用户显式反馈采用的提示 / 实际展示的相关提示 | P2 建立反馈机制后再统计，不把返回结果当采纳 |

M0 确定暂定性能门槛、质量底线和硬预算；M1 根据实测记录校准理由与结果，M4 按明确记录的门槛验收。预算上限与 A04/A05 等质量底线不得因试点未达标而静默放宽。当前不承诺未经测量的实时性、准确率或扫描吞吐。

## 10. 风险与处理策略

| 风险 | 影响 | 处理与触发条件 |
| --- | --- | --- |
| Python实现与Vue目标语言混淆 | 误用Python AST导致目标不可分析 | 已确认Vue/JS/TS试点；T02定义语言/位置契约，T06落实辅助解析器 |
| 静态分析无法覆盖动态JS/TS/Vue行为 | 依赖遗漏、新鲜度误判 | 标记 unknown；先做 import 图，使用反例，不能声称完整调用图 |
| Git 记录不足以证明设计原因 | 模型把猜测包装成事实 | 区分 Claim 类型；转追问；知情者缺席则不发布推断为确定结论 |
| 单人同时扮演作者和审核者 | 缺少独立校验 | 保留显式审核；按证据检查表核验，陌生业务请知情者确认 |
| 模型数据外发与提示注入 | 泄露仓库内容或越权 | 明确可发送内容；过滤密钥/个人信息；源码和讨论视为不可信数据；模型无执行/发布权限 |
| 扫描恶意或超大输入 | 资源耗尽、越界读取 | 限制仓库根、符号链接逃逸、单文件/总大小、解析时限；不加载项目插件或运行脚本 |
| 本地库锁竞争与断电中断 | 页面卡顿、任务状态悬挂 | 单 worker、短事务、重试、检查点、租约恢复；持续竞争则迁移评估 |
| 自动更新删除有效约束 | 使用错误知识进行开发 | P0 禁用自动发布；P1 先建议模式，高风险和冲突强制人工处理 |
| 首期集成范围过大 | 单人交付周期失控 | 先本地仓库和单语言；每个新平台、新语言独立决策和验收 |
| 后续加人同时改共享模型 | 重复接口、迁移冲突 | 模块归属明确，共享契约单点协调，先 schema 后实现 |

## 11. 待确认事项与开始条件

### 11.1 已确认

- 当前开发者：Recall 一人。
- 系统实现语言：Python。
- 分支管理：Recall 负责。
- 未来可能加入其他开发者：模块与契约需支持交接。

### 11.2 M0 需要落定

| 事项 | 建议初值 | 为什么影响实施 |
| --- | --- | --- |
| 首个目标仓库、路径、固定commit、知情者 | Vue3Admin，主基线77e9634，Recall | 已在T01选定；本地路径见基线决策；仅3次基线历史，知识动机仍需人工核验 |
| 目标源码语言与结构 | Vue SFC/TS/JS，Vue3Admin/src，@/*别名 | 已确定；T03/T06/T07/T09/T27按该目标适配 |
| 应用Python版本、依赖管理、锁文件 | Python3.12、uv、uv.lock | T01已完成锁定安装及独立环境复验，结果见基线决策 |
| Web/存储建议是否采用 | FastAPI、Pydantic、Jinja2、SQLAlchemy、Alembic；本地 SQLite | 影响 S01/S03，须在写业务实现前落定 |
| 模型供应商、内容范围、单次/每月预算 | 用户允许后续外部模型；供应商/预算待定；当前mock、外发false、预算0 | T12真实接入前落定，当前不发起模型请求 |
| 试点耗时、容量与质量阈值 | M0 定暂定门槛/硬预算，M1 实测留档校准，M4 验证 | 避免空写性能承诺或验收时临时改变标准 |
| 运行环境 | 默认本机单用户；操作系统兼容范围明确 | 决定 Git 调用、路径处理、数据库和后续部署 |
| P1 托管平台与事件源 | GitHub/GitLab/Gitea 中选一个，或先手动触发 | P0 可暂缓；不同时实现全部平台 |

### 11.3 下一次开发从哪里开始

从TASK_PLAN.md的T01 → T02 → T03开始，对应S01/S02：完成目标仓库、环境决策、契约和黄金样例，再建立数据库与只读快照链路。尚未决定的内容保持为假设，不隐式变成架构承诺。

## 12. 计划维护记录

| 日期 | 变更 | 状态 |
| --- | --- | --- |
| 2026-10-19 | 根据静态设计说明建立计划；按用户补充改为单人推进、Python 实现；保留未来多人交接边界 | 计划完成，工程未启动 |
| 2026-10-19 | 拆为40项2～3天任务，新增TASK_PLAN.md；按逐项工期替换粗估，提供建议分支与验收对应 | 细分计划完成，工程未启动 |
| 2026-10-19 | 启动T01；试点改为用户指定Vue3Admin，选77e9634基线，调整后续目标解析任务 | T01工程与验证完成，待验收 |
| 2026-10-20 | T02落地共享契约；第5节记录与草案的差异，执行任务状态增加partial | T02完成，待验收 |

测试材料按用户要求不入库；验证结论可记入任务文档。逐任务状态、实际用时和验证证据写入TASK_PLAN.md；里程碑或范围变化时同步更新本文件摘要与决策。本文不替代代码接口或数据库迁移的真实实现。

