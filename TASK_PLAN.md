# Knowledge CI 逐步任务计划书

- 更新日期：2026-10-20。
- 当前负责人：Recall；系统实现语言：Python；分支创建和合并由 Recall 管理。
- 本文件负责逐任务排期、状态、实际用时与验收记录；[主计划](D:/knowledge_ci/PROJECT_PLAN.md)负责需求范围、架构、数据契约和阶段验收基线。
- 共 40 项任务，每项 2～3 个工作日，平均 2.65 天。优先执行 P0 的 24 项任务；P1/P2 是后续预备队列。
- T01工程与自动验证完成，待验收；本轮复审修复位于用户指定的fix/hyw/1020分支，其余状态以总表为准。卡片末尾分支名仍是建议，目标文件按实施进度创建。

## 1. 排期怎么使用

1. 从 T01 顺序执行；任务开工前确认表内依赖已经验收并纳入你选定的开发基线。
2. 一项任务对应一个可以独立审核、合入的工作范围，建议一个任务一个分支。前置依赖是技术依赖，单人排期还遵守表中顺序。
3. 每项工期已经包含实现、针对性测试、必要文档、自查和合入准备，不再额外叠加“每周一天测试”。
4. 1 天按一个人的完整可投入工作日计；每周按 5 个工作日换算。兼职、会议和请假按实际容量折算，周末/节假日不算开发日。
5. 尚未指定开工日期，使用 D001 起算的相对工作日。把 D001 对应到实际开工日，再按你的工作日历顺延即可。
6. 各阶段后单列约 10% 的机动容量，允许在阶段中使用；机动容量不提前建功能分支，不当作已完成任务。外部授权、知情者回复、模型开通和部署审批等待另记。
7. 新任务如果预计超过 3 天，先拆出能独立验收的子任务，再开始或继续；不能把超出范围的工作藏在“联调/修复”里。

### 1.1 工期汇总

| 阶段 | 任务 | 任务工期 | 机动容量 | 阶段合计 | 按每周5天 | 启动条件 |
| --- | --- | --- | --- | --- | --- | --- |
| P0 发现与审核 MVP | T01～T24，共24项 | 62天 | 7天 | 69天 | 约14周 | T01落定试点与实现假设 |
| P1 新鲜度与增量演进 | T25～T34，共10项 | 28天 | 3天 | 31天 | 约6.2周 | P0价值与质量验收通过，再确认投入 |
| P2 开发前注入 | T35～T40，共6项 | 16天 | 2天 | 18天 | 约3.6周 | P1验收通过，选定一个客户端 |
| 全部基线 | 40项 | 106天 | 12天 | 118天 | 约24周 | 假设各阶段连续启动；不含外部等待 |

原“P0约8～10周”是工作包级粗估，现由逐项累加的“62天任务 + 7天机动”替代。此处按完整原定P0范围估算，没有为了维持旧周数缩减审核、恢复或试点验收。每完成一个里程碑，用实际耗时校准剩余任务；不得悄悄修改验收标准来维持工期。

### 1.2 里程碑及相对工作日

| 门槛 | 任务范围 | 计划工作日 | 可以看到的成果 |
| --- | --- | --- | --- |
| M0 范围与契约 | T01～T03 | D001～D007 | 环境、契约、可重复黄金样例 |
| M1 可复现分析 | T04～T11 | D008～D027 | 固定快照、AST、图、Top-K、证据和扫描CLI |
| M2 端到端薄切片 | T12～T17 | D028～D044 | 一条知识从模型草稿到页面审核发布；T13已做早期价值核验 |
| M3 追问与可靠性 | T18～T22 | D045～D056 | 追问、恢复、冲突、成本报告、备份恢复 |
| M4 MVP验收 | T23～T24 | D057～D062 | 真实仓库试点及A01～A12证据 |
| P0机动 | 按实际缺陷分配 | D063～D069 | 用于范围内返工；未用可前移下一阶段 |
| M5 增量与新鲜度 | T25～T34 | D070～D097 | 增量复核、人工更新、恢复、单平台事件 |
| P1机动 | 按实际缺陷分配 | D098～D100 | 未用可前移下一阶段 |
| M6 注入与反馈 | T35～T40 | D101～D116 | 上下文查询、一个MCP/客户端闭环、反馈 |
| P2机动 | 按实际缺陷分配 | D117～D118 | 完成当前范围收尾 |

P1/P2的序号与相对工作日用于容量预留，不构成现在必须投入全部118天的承诺。A2A、更多语言、多仓库、多租户、完整IDE插件和多平台适配均未纳入这40项承诺。

## 2. 任务排期总表

状态只在下表维护，可使用“待开始 / 进行中 / 待验收 / 已完成 / 阻塞”。同一时间默认只有一项主任务进行中；真实等待可转去处理依赖已满足的后续项，并记录偏离原顺序的原因。

### 发现与审核 MVP：T01～T24

| 任务 | 天数 | 相对工作日 | 技术前置 | 状态 | 实际天数 |
| --- | --- | --- | --- | --- | --- |
| [T01 确定试点与最小 Python 工程](#t01) | 2 | D001～D002 | 无 | 待验收 | 本会话完成；人日待录 |
| [T02 冻结共享模型与状态契约](#t02) | 3 | D003～D005 | T01 | 待验收 | 本会话完成；人日待录 |
| [T03 建立可重复的 Git 与知识样例](#t03) | 2 | D006～D007 | T02 | 待开始 | — |
| [T04 建立基础存储与迁移](#t04) | 3 | D008～D010 | T02、T03 | 待开始 | — |
| [T05 实现只读 Git 快照访问](#t05) | 2 | D011～D012 | T03、T04 | 待开始 | — |
| [T06 解析 Vue/JS/TS 并提取符号](#t06) | 3 | D013～D015 | T05 | 待开始 | — |
| [T07 建立 import 依赖图](#t07) | 2 | D016～D017 | T06 | 待开始 | — |
| [T08 计算 Git 信号与 Top-K](#t08) | 3 | D018～D020 | T05、T07 | 待开始 | — |
| [T09 实现首批候选线索规则](#t09) | 2 | D021～D022 | T06、T07、T08 | 待开始 | — |
| [T10 聚合代码与 Git 证据](#t10) | 2 | D023～D024 | T04、T05、T08、T09 | 待开始 | — |
| [T11 贯通持久化扫描任务与 CLI](#t11) | 3 | D025～D027 | T04、T10 | 待开始 | — |
| [T12 实现模型网关与调用预算](#t12) | 3 | D028～D030 | T02、T10、T11 | 待开始 | — |
| [T13 生成可核验草稿与问题建议](#t13) | 3 | D031～D033 | T09、T10、T12 | 待开始 | — |
| [T14 落地知识修订与查询服务](#t14) | 3 | D034～D036 | T04、T13 | 待开始 | — |
| [T15 实现审核发布与基础 HTTP API](#t15) | 3 | D037～D039 | T11、T14 | 待开始 | — |
| [T16 实现仓库、任务和排名页面](#t16) | 2 | D040～D041 | T15 | 待开始 | — |
| [T17 实现知识详情、审核和发布列表](#t17) | 3 | D042～D044 | T16 | 待开始 | — |
| [T18 完成追问回答与重新评估](#t18) | 3 | D045～D047 | T13、T15、T17 | 待开始 | — |
| [T19 完善重启恢复、取消与迟到响应处理](#t19) | 3 | D048～D050 | T11、T12、T18 | 待开始 | — |
| [T20 补齐本机边界与异常交互](#t20) | 2 | D051～D052 | T16、T17、T18、T19 | 待开始 | — |
| [T21 实现质量、耗时和成本报告](#t21) | 2 | D053～D054 | T12、T18、T19、T20 | 待开始 | — |
| [T22 完成备份与恢复演练](#t22) | 2 | D055～D056 | T04、T18、T21 | 待开始 | — |
| [T23 运行真实仓库试点与人工核验](#t23) | 3 | D057～D059 | T17、T18、T19、T20、T21、T22 | 待开始 | — |
| [T24 处理首轮缺陷并完成 MVP 验收](#t24) | 3 | D060～D062 | T23 | 待开始 | — |

### 新鲜度与增量演进：T25～T34（预备排期）

| 任务 | 天数 | 相对工作日 | 技术前置 | 状态 | 实际天数 |
| --- | --- | --- | --- | --- | --- |
| [T25 定义增量输入与变更基准样例](#t25) | 2 | D070～D071 | T24 | 待开始 | — |
| [T26 实现 commit Diff 与路径变更定位](#t26) | 3 | D072～D074 | T05、T25 | 待开始 | — |
| [T27 实现保守的 AST 变化过滤](#t27) | 3 | D075～D077 | T06、T25、T26 | 待开始 | — |
| [T28 计算知识关联与依赖影响范围](#t28) | 3 | D078～D080 | T07、T14、T26、T27 | 待开始 | — |
| [T29 落地新鲜度复核与影响判断](#t29) | 3 | D081～D083 | T12、T25、T28 | 待开始 | — |
| [T30 实现风险分级与更新建议审核](#t30) | 3 | D084～D086 | T15、T18、T29 | 待开始 | — |
| [T31 实现历史内容恢复为新修订](#t31) | 2 | D087～D088 | T14、T15、T30 | 待开始 | — |
| [T32 接入一种托管平台的历史证据](#t32) | 3 | D089～D091 | T10、T25 | 待开始 | — |
| [T33 接收平台事件并触发增量任务](#t33) | 3 | D092～D094 | T19、T29、T30、T32 | 待开始 | — |
| [T34 完成增量闭环与质量验收](#t34) | 3 | D095～D097 | T27、T28、T29、T30、T31、T32、T33 | 待开始 | — |

### 开发前注入：T35～T40（预备排期）

| 任务 | 天数 | 相对工作日 | 技术前置 | 状态 | 实际天数 |
| --- | --- | --- | --- | --- | --- |
| [T35 实现上下文查询与可解释排序](#t35) | 3 | D101～D103 | T14、T29、T34 | 待开始 | — |
| [T36 实现上下文预算与压缩](#t36) | 2 | D104～D105 | T35 | 待开始 | — |
| [T37 提供只读 MCP 上下文工具](#t37) | 3 | D106～D108 | T35、T36 | 待开始 | — |
| [T38 验证一个客户端的开发前调用](#t38) | 3 | D109～D111 | T37 | 待开始 | — |
| [T39 记录注入反馈与采用指标](#t39) | 2 | D112～D113 | T21、T38 | 待开始 | — |
| [T40 完成注入闭环验收与扩展决策](#t40) | 3 | D114～D116 | T35、T36、T37、T38、T39 | 待开始 | — |

## 3. 开工与合入规则

### 3.1 每项任务的共同完成条件

- 卡片中的行为和验收已实现，并运行受影响的验证；不能只有代码提交、没有结果证据。
- 跨模块模型沿用主计划第5节；已有字段、错误语义和状态机变更先更新契约/样例，再改调用方。
- 新目录/子目录先依照 AGENTS.md 与 CLAUDE.md 补齐结构、命名和清理约定，再创建实现文件。
- 任务卡中的路径均相对于D:\knowledge_ci。业务文件入库；var/local-checks/中的测试代码、样例、配置和报告仅保留本地，不入库、不打包，验证工具不写入业务依赖。开工时先校准文件落点。
- 数据迁移只新增有序迁移，不随意改写已应用版本；任务卡中的 migrations/ 指该任务实际生成的版本文件，开工后记录准确名称。
- 安全、幂等、CAS、任务租约等基础规则从首次实现相关入口时生效；后期任务负责补齐故障场景，不把基础正确性延后。
- 在第6节填写实际用时、分支、提交或PR、验证证据与遗留项，再将总表状态改为已完成。

### 3.2 分支对应方式

建议名称为 codex/tXX-short-topic；每张任务卡末尾已给出可直接采用的完整名称。可由你统一替换前缀，任务ID保持不变。

从你选定且已经包含前置任务的基线创建分支。任务验收合入后再推进下一项；确需叠加分支时记录依赖关系，避免遗漏前置提交。不要一次创建40条长期分支，按准备开始的任务创建即可。

如果任务必须拆分，保留原ID作为父项，新增 T14a/T14b 等子项，并使用 codex/t14a-short-topic 形式。父项只有所有子项验收后才能完成；更新剩余天数和后续工作日，不重复计算父项与子项工期。

### 3.3 单项两天或三天的节奏

- 两天任务：第1天完成主要实现与基础验证，第2天完成反例、联调和合入准备。
- 三天任务：第1天明确输入/输出并实现主体，第2天打通边界/消费方，第3天验证异常、整理证据并合入。
- 这些安排是容量上限与顺序参考，按实际推进；某项提前完成后可以前移后续任务。
- 任务卡最后一天的验证包含在天数内；若外部依赖未到，不把“等待”算作功能已验收。

## 4. 逐项任务卡

## 发现与审核 MVP：T01～T24

<a id="t01"></a>

### T01 确定试点与最小 Python 工程

- 工期：2天；计划 D001～D002；里程碑 M0；对应原工作包 S01。
- 前置：无。
- 输入与契约：用户已确认单人/Python、Vue3Admin试点及后续允许外部模型；主基线77e9634，供应商和预算待定。
- 目标路径：`AGENTS.md`、`CLAUDE.md`、`pyproject.toml`、`uv.lock`、`.python-version`、`.gitignore`、`.env.example`、`README.md`、`src/knowledge_ci/{__init__,__main__,app,cli,config}.py`、`var/tmp/local-checks/tests/`（临时验证后删除）、`docs/decisions/0001-baseline.md`。
- 第1天：将规范的当前阶段切换为工程实现并补齐拟创建目录的约定；选定试点commit/目标语言/知情者、依赖组合、预算和运行边界，记录决定。
- 第2天：建立可重复安装的最小工程、空应用/CLI、配置加载及验证命令；验证启动、退出和配置缺失提示。
- 验收/合入：另一套干净环境按记录可安装并启动；真实试点路径/commit、模型数据政策与待处理外部依赖均有记录。
- 范围或等待说明：先以合成样例推进；真实仓库授权或模型开通的等待时间另记。
- 实施记录：2026-10-19，使用用户分支`feat/hyw/T01`（419b71d～6117a83）；已锁定依赖、CLI/真实试点校验、18项测试、Ruff及独立wheel安装复验通过。具体命令与结果见`docs/decisions/0001-baseline.md`。2026-10-20审查复验：干净worktree锁定安装、CLI正反例、18 passed；修复相对路径锚定和空loc错误前缀，已合入`bug/fix/1020`。
- 建议分支：`codex/t01-project-baseline`（仅原建议，实际以用户分支为准）。

<a id="t02"></a>

### T02 冻结共享模型与状态契约

- 工期：3天；计划 D003～D005；里程碑 M0；对应原工作包 S02。
- 前置：T01。
- 输入与契约：主计划第 5 节；Snapshot/AnalysisRun 分离，Knowledge 内容修订与 state_version 分离。
- 目标路径：`src/knowledge_ci/contracts/{__init__,common,repository,evidence,knowledge,jobs,errors}.py`、`var/tmp/local-checks/tests/unit/`（临时验证后删除）。开工校准：新增`common`（基础类型被三个模块共用）与`evidence`（T10产出、T13/T18消费）；`config.py`/`cli.py`改用契约类型与错误格式；pyproject补pydantic直接依赖。
- 第1天：定义仓库、快照、分析执行、符号、证据和任务模型；列必填、可空、ID及时间规范。
- 第2天：定义知识、Claim、追问、审核、验证记录与状态转换；固定请求、响应和错误结构。
- 第3天：补正反例与状态转换用例；核对幂等、租约、阻断追问、失效条件和发布前提。
- 验收/合入：非法字段/状态组合被拒绝；无效引用、旧修订/旧状态版本的错误语义明确；各入口共享同一模型。
- 实施记录：2026-10-20，用户分支`feat/hyw/T02`（基于main 4d5ea0a，未提交）。契约为不可变Pydantic模型加纯函数状态转换，持久化原子性由T04/T14/T15落实；134项临时测试、Ruff、wheel独立环境复验通过，详见第6节。
- 建议分支：`codex/t02-domain-contracts`（仅原建议，实际以用户分支为准）。

<a id="t03"></a>

### T03 建立可重复的 Git 与知识样例

- 工期：2天；计划 D006～D007；里程碑 M0；对应原工作包 S02。
- 前置：T02。
- 输入与契约：T02 schema；目标为JS/TS/Vue SFC，样例不得包含真实私有仓库内容。
- 目标路径：`var/local-checks/tests/fixtures/repository_builder.py`、`var/local-checks/tests/fixtures/knowledge_cases.json`、`var/local-checks/tests/integration/test_fixture_repository.py`。
- 第1天：编写小型 Git 历史生成器：引入约束、修复、改名、格式变化、空catch、循环import和动态import；加入字符串内注释标记、SFC块与@/*别名。
- 第2天：列预期符号/边、Top-K信号、证据、知识与追问输出；保存夹具生成和清理方式。
- 验收/合入：每次生成得到等价历史与预期结果；测试工作目录在运行结束清理；样例可供所有后续模块共用。
- 建议分支：`codex/t03-golden-fixtures`。

<a id="t04"></a>

### T04 建立基础存储与迁移

- 工期：3天；计划 D008～D010；里程碑 M1；对应原工作包 S03。
- 前置：T02、T03。
- 输入与契约：Repository/Snapshot/AnalysisRun/Job/Evidence 契约；知识表按 T14 再增量迁移。
- 目标路径：`src/knowledge_ci/storage/database.py`、`src/knowledge_ci/storage/models.py`、`src/knowledge_ci/storage/artifacts.py`、`migrations/env.py`、`var/local-checks/tests/integration/test_storage.py`。
- 第1天：搭建数据库会话、迁移入口与基础表；固定外键、唯一键和任务/产物去重约束。
- 第2天：实现事务访问与逻辑产物 ID、内容哈希存取；不把机器绝对路径写成业务引用。
- 第3天：验证空库升级、事务回滚、唯一约束、短事务及写锁重试；补基础迁移用例。
- 验收/合入：空库可初始化；重复标识不生成重复记录；失败事务不留下半条任务/产物引用；文件可按逻辑ID回读。
- 建议分支：`codex/t04-storage-foundation`。

<a id="t05"></a>

### T05 实现只读 Git 快照访问

- 工期：2天；计划 D011～D012；里程碑 M1；对应原工作包 S04。
- 前置：T03、T04。
- 输入与契约：本地仓库允许根目录、ref → 完整 commit SHA → Snapshot；Git 通过参数数组调用。
- 目标路径：`src/knowledge_ci/repository/git_reader.py`、`src/knowledge_ci/repository/snapshot.py`、`src/knowledge_ci/repository/path_policy.py`、`var/local-checks/tests/integration/test_git_snapshot.py`。
- 第1天：校验本地 Git 路径与ref，固定SHA/tree；从固定版本枚举/读取文件并保存快照身份。
- 第2天：处理未提交修改、移动分支、路径越界、符号链接、大小限制及无效ref；补反例。
- 验收/合入：分支前进或工作区改动不改变已建立快照；不执行仓库脚本、不写仓库；越界/无效输入有明确错误。
- 建议分支：`codex/t05-git-snapshot`。

<a id="t06"></a>

### T06 解析 Vue/JS/TS 并提取符号

- 工期：3天；计划 D013～D015；里程碑 M1；对应原工作包 S05。
- 前置：T05。
- 输入与契约：已选Vue SFC/TS/JS；Symbol关联snapshot_id/analysis_run_id，SFC脚本位置映射回原文件。
- 目标路径：`src/knowledge_ci/analysis/parser.py`、`src/knowledge_ci/analysis/symbols.py`、`tools/parser/package.json`、`tools/parser/index.mjs`、`tools/parser/package-lock.json`、`var/local-checks/tests/unit/test_symbols.py`。
- 第1天：验证隔离的Vue官方SFC解析及JS/TS辅助解析，冻结JSON输出与工具版本；不执行目标项目插件或脚本。
- 第2天：提取组件、模块、类、函数和导出符号，处理script/script setup及原文件行号映射。
- 第3天：验证语法不支持、解析失败、空文件、大文件和重复名称；保证失败文件可见。
- 验收/合入：黄金样例符号/位置正确；部分失败不会被报为全仓成功；同输入产物稳定。
- 范围或等待说明：系统仍为Python；目标已改Vue/JS/TS。若辅助解析工具验证超出3天，拆T06子任务并重排，不假定语言变更零成本。
- 建议分支：`codex/t06-vue-ts-symbols`。

<a id="t07"></a>

### T07 建立 import 依赖图

- 工期：2天；计划 D016～D017；里程碑 M1；对应原工作包 S05。
- 前置：T06。
- 输入与契约：T06 的模块与符号；T01 固定的包目录/src布局。
- 目标路径：`src/knowledge_ci/analysis/import_graph.py`、`var/local-checks/tests/unit/test_import_graph.py`。
- 第1天：解析静态/字面量动态import、相对路径及@/*别名，区分仓库内/第三方/unknown，输出带来源的边。
- 第2天：计算入度/出度与循环组件，验证重复边、动态import、缺失模块和包重导出。
- 验收/合入：黄金样例静态边与循环结果正确；无法静态确定的关系为 unknown，不宣称完整调用图。
- 建议分支：`codex/t07-import-graph`。

<a id="t08"></a>

### T08 计算 Git 信号与 Top-K

- 工期：3天；计划 D018～D020；里程碑 M1；对应原工作包 S06。
- 前置：T05、T07。
- 输入与契约：目标commit、观察窗口、图入度、版本化权重；缺失信号独立标识。
- 目标路径：`src/knowledge_ci/repository/history.py`、`src/knowledge_ci/analysis/scoring.py`、`var/local-checks/tests/integration/test_module_ranking.py`。
- 第1天：采集截至目标commit的文件变更频率与贡献者信息，处理历史不足与文件改名记录。
- 第2天：实现信号归一化、权重、K、稳定排序及得分解释；保存配置摘要。
- 第3天：验证同快照同配置可复现、同快照不同配置产物分离及并列排序。
- 验收/合入：Top-K可解释并包含原始信号/缺失项；两套配置能按 analysis_run_id 分别查询；不把缺失事故数据当零风险。
- 建议分支：`codex/t08-module-ranking`。

<a id="t09"></a>

### T09 实现首批候选线索规则

- 工期：2天；计划 D021～D022；里程碑 M1；对应原工作包 S06。
- 前置：T06、T07、T08。
- 输入与契约：Top-K模块、AST、循环边；首批仅三类规则。
- 目标路径：`src/knowledge_ci/analysis/rules.py`、`src/knowledge_ci/contracts/candidates.py`、`var/local-checks/tests/unit/test_candidate_rules.py`。
- 第1天：实现循环import、比较/控制条件中的硬编码阈值、空catch/静默降级候选，生成位置与规则版本。
- 第2天：建立误报/排除样例与稳定候选键；输出触发原因和局限。
- 验收/合入：三类规则有正反例，重跑不重复候选；输出是待核验线索，不能直接作为业务事实。
- 范围或等待说明：复杂状态机、跨函数数据流和自动事故归因不加入本任务。
- 建议分支：`codex/t09-candidate-rules`。

<a id="t10"></a>

### T10 聚合代码与 Git 证据

- 工期：2天；计划 D023～D024；里程碑 M1；对应原工作包 S07。
- 前置：T04、T05、T08、T09。
- 输入与契约：候选位置、固定Snapshot、Git历史 → Evidence集合与缺口。
- 目标路径：`src/knowledge_ci/evidence/collector.py`、`src/knowledge_ci/evidence/locator.py`、`var/local-checks/tests/integration/test_evidence_bundle.py`。
- 第1天：获取固定版本代码片段与相关commit，保存定位、内容哈希和原始材料引用。
- 第2天：建立候选—证据关联；核验可回读、缺失历史、重命名与无法定位情况。
- 验收/合入：候选能回查到固定commit及代码位置；证据缺失显式记录；commit说明仅是来源材料，不自动成为事实。
- 建议分支：`codex/t10-evidence-bundle`。

<a id="t11"></a>

### T11 贯通持久化扫描任务与 CLI

- 工期：3天；计划 D025～D027；里程碑 M1；对应原工作包 S08。
- 前置：T04、T10。
- 输入与契约：完整静态流水线；Job幂等键、阶段检查点、attempt/lease_token已在T02/T04定义。
- 目标路径：`src/knowledge_ci/jobs/service.py`、`src/knowledge_ci/jobs/worker.py`、`src/knowledge_ci/cli.py`、`var/local-checks/tests/integration/test_analysis_job.py`。
- 第1天：实现持久化任务提交、领取、阶段状态与单worker执行；按analysis_run保存产物。
- 第2天：串联快照→AST→图→评分→规则→证据，提供CLI启动、查询、结果导出。
- 第3天：实现基本重复请求去重、提交凭据检查和检查点；验证成功/partial/失败及阶段进度。
- 验收/合入：CLI能完成固定仓库分析；重放同一请求返回同一逻辑任务；无效租约不能提交；M1结果可导出。
- 范围或等待说明：重启接管、取消和完整迟到响应故障矩阵在T19扩充，基础提交门禁本任务即生效。
- 建议分支：`codex/t11-analysis-jobs`。

<a id="t12"></a>

### T12 实现模型网关与调用预算

- 工期：3天；计划 D028～D030；里程碑 M2；对应原工作包 S09。
- 前置：T02、T10、T11。
- 输入与契约：EvidenceBundle、固定假响应；一个已获准使用的真实模型提供方。
- 目标路径：`src/knowledge_ci/knowledge/model_gateway.py`、`src/knowledge_ci/knowledge/budget.py`、`var/local-checks/tests/unit/test_model_gateway.py`、`src/knowledge_ci/storage/model_call_store.py`、`var/local-checks/tests/integration/test_model_budget.py`、`migrations/`。
- 第1天：定义供应商无关输入输出与假响应适配器；记录输入哈希、模型/提示词版本。
- 第2天：接入一个真实提供方；实现输入范围校验、脱敏、持久化预算预占/调用账本、超时和调用记录，新增所需迁移。
- 第3天：验证限额、重启、超时和重试后的预算结算：不清零、不重复释放、不遗漏可能计费的调用；用授权样例完成最小真实调用。
- 验收/合入：预算不足时不发起外部请求；重启后账本与预占仍有效；模型无仓库执行权限；假响应可供离线测试。
- 范围或等待说明：模型账号、外发政策未具备时记阻塞/等待，真实调用验收不算通过；不接入多个供应商。
- 建议分支：`codex/t12-model-gateway`。

<a id="t13"></a>

### T13 生成可核验草稿与问题建议

- 工期：3天；计划 D031～D033；里程碑 M2；对应原工作包 S09。
- 前置：T09、T10、T12。
- 输入与契约：Claim/Evidence/KnowledgeRevision schema；正式知识只能经后续人工审核发布。
- 目标路径：`src/knowledge_ci/knowledge/generator.py`、`src/knowledge_ci/knowledge/claim_validator.py`、`var/local-checks/tests/unit/test_draft_generation.py`。
- 第1天：编写版本化生成模板，要求设计原因、范围、失效条件、结论类型和证据ID。
- 第2天：实现结构校验、引用校验、证据充分度与问题建议；保留未知项。
- 第3天：固定样例回放并核验至少两条真实草稿；记录无价值摘要/伪引用并调整一次。
- 验收/合入：伪造证据ID不能通过；猜测不升级为事实；不足证据产生阻断问题建议；有价值判断获得早期反馈。
- 范围或等待说明：只生成待审内容；T14先持久化最小阻断问题，T18再完成分配、回答与重新评估。
- 建议分支：`codex/t13-knowledge-drafts`。

<a id="t14"></a>

### T14 落地知识修订与查询服务

- 工期：3天；计划 D034～D036；里程碑 M2；对应原工作包 S03、S10。
- 前置：T04、T13。
- 输入与契约：Knowledge聚合、不可变Revision、current/published指针及state_version。
- 目标路径：`src/knowledge_ci/storage/knowledge_store.py`、`src/knowledge_ci/knowledge/service.py`、`src/knowledge_ci/knowledge/queries.py`、`var/local-checks/tests/integration/test_knowledge_revisions.py`、`migrations/`、`src/knowledge_ci/storage/question_store.py`、`src/knowledge_ci/jobs/worker.py`、`var/local-checks/tests/integration/test_generation_pipeline.py`。
- 第1天：增加知识/修订及最小Question迁移；草稿与open/blocking问题一并持久化，建立候选去重、修订/状态CAS。
- 第2天：实现历史/分页/证据查询；将worker扩展为证据→模型→草稿/问题落库，保存阶段检查点并校验lease_token。
- 第3天：验证旧版本写入冲突、生成重放、阶段失败恢复以及草稿连同阻断问题原子提交；保留已有发布指针。
- 验收/合入：Job可从证据推进到持久化草稿；重复执行不重复知识/问题；问题不会丢失；CAS冲突正确；历史可回读。
- 建议分支：`codex/t14-knowledge-revisions`。

<a id="t15"></a>

### T15 实现审核发布与基础 HTTP API

- 工期：3天；计划 D037～D039；里程碑 M2；对应原工作包 S10。
- 前置：T11、T14。
- 输入与契约：主计划/api/v1草案；绑定内容修订的Review与状态CAS。
- 目标路径：`src/knowledge_ci/review/service.py`、`src/knowledge_ci/review/publish.py`、`src/knowledge_ci/web/api.py`、`src/knowledge_ci/app.py`、`var/local-checks/tests/integration/test_review_publish.py`、`src/knowledge_ci/storage/models.py`、`src/knowledge_ci/storage/review_store.py`、`migrations/`。
- 第1天：增加Review/AuditEvent迁移与存储，实现审核/发布原子事务；检查负责人、证据及T14已持久化的阻断问题。
- 第2天：接入仓库、任务、排名、知识查询、修订、审核与发布HTTP路由；复用已有服务。
- 第3天：验证409/422/404、双页面冲突审批、未经批准发布及修改后重新审核；本机监听和服务端actor从此启用。
- 验收/合入：从T14数据库升级后，API完成生成→审核→发布→回溯；open/blocking问题拒绝发布；状态与审计同事务；旧批准失效。
- 建议分支：`codex/t15-review-publish-api`。

<a id="t16"></a>

### T16 实现仓库、任务和排名页面

- 工期：2天；计划 D040～D041；里程碑 M2；对应原工作包 S11。
- 前置：T15。
- 输入与契约：T15已有仓库/任务/模块API与读取服务；模板展示，不新增分析规则。
- 目标路径：`src/knowledge_ci/web/pages.py`、`src/knowledge_ci/web/templates/repositories.html`、`src/knowledge_ci/web/templates/jobs.html`、`src/knowledge_ci/web/templates/modules.html`、`var/local-checks/tests/e2e/test_analysis_pages.py`。
- 第1天：增加仓库选择、启动分析、阶段轮询；页面表单采用同源/CSRF防护和服务端actor。
- 第2天：增加Top-K信号与候选入口；处理空、加载、partial/unknown、无效ref和失败状态。
- 验收/合入：能从页面启动并查看分析；失败可理解；模块信号与CLI同源；篡改路径/身份不会扩大授权。
- 建议分支：`codex/t16-analysis-workbench`。

<a id="t17"></a>

### T17 实现知识详情、审核和发布列表

- 工期：3天；计划 D042～D044；里程碑 M2；对应原工作包 S11。
- 前置：T16。
- 输入与契约：T14/T15知识查询、修订、审核、发布服务；同一份schema与错误码。
- 目标路径：`src/knowledge_ci/web/templates/knowledge_list.html`、`src/knowledge_ci/web/templates/knowledge_detail.html`、`src/knowledge_ci/web/templates/review.html`、`var/local-checks/tests/e2e/test_knowledge_pages.py`。
- 第1天：实现候选/正式知识列表与详情、证据、来源快照和失效条件展示。
- 第2天：实现编辑、差异核对、批准、驳回、发布操作；明确当前草稿与已发布修订。
- 第3天：补空/冲突/非法发布状态；通过固定假响应从选仓库到发布贯通一条知识。
- 验收/合入：浏览器中可以完成薄切片；未审候选不混入正式列表；页面始终显示被批准的正确修订。
- 建议分支：`codex/t17-knowledge-workbench`。

<a id="t18"></a>

### T18 完成追问回答与重新评估

- 工期：3天；计划 D045～D047；里程碑 M3；对应原工作包 S12。
- 前置：T13、T15、T17。
- 输入与契约：Question open/answered/resolved/cancelled；blocking变化递增聚合state_version。
- 目标路径：`src/knowledge_ci/knowledge/questions.py`、`src/knowledge_ci/web/templates/questions.html`、`src/knowledge_ci/storage/question_store.py`、`var/local-checks/tests/e2e/test_question_workflow.py`、`migrations/`。
- 第1天：扩展T14已有的最小Question存储，实现分配、列表、回答API与回答者记录；按需新增回答字段/记录迁移。
- 第2天：把人工回答转成可追溯Evidence，触发重新评估及新修订；保留原问题/回答。
- 第3天：贯通页面和至少3类不足证据场景；检验回答不足、重复提交及阻断发布。
- 验收/合入：回答不直接发布；只有问题被解释/采纳才resolved；至少3条闭环可重复演示；旧发布内容保留。
- 建议分支：`codex/t18-question-workflow`。

<a id="t19"></a>

### T19 完善重启恢复、取消与迟到响应处理

- 工期：3天；计划 D048～D050；里程碑 M3；对应原工作包 S13。
- 前置：T11、T12、T18。
- 输入与契约：T11已有基本幂等、检查点和租约提交；本任务扩展恢复路径。
- 目标路径：`src/knowledge_ci/jobs/recovery.py`、`src/knowledge_ci/jobs/service.py`、`src/knowledge_ci/jobs/worker.py`、`var/local-checks/tests/integration/test_job_recovery.py`。
- 第1天：实现心跳过期检测、重启接管、分阶段恢复和人工重试，区分永久/暂时失败。
- 第2天：实现取消与token失效；校验超时旧响应无法覆盖新attempt产物。
- 第3天：执行杀worker、断点恢复、重复请求、重试后旧响应、取消后旧响应的故障矩阵。
- 验收/合入：无重复候选/审核/发布；已完成阶段按约定复用；迟到响应不能提交；用户能看到失败原因与重试入口。
- 建议分支：`codex/t19-job-recovery`。

<a id="t20"></a>

### T20 补齐本机边界与异常交互

- 工期：2天；计划 D051～D052；里程碑 M3；对应原工作包 S13。
- 前置：T16、T17、T18、T19。
- 输入与契约：T05/T12/T15/T16已分别落实路径、模型、本机、表单基础边界。
- 目标路径：`src/knowledge_ci/web/security.py`、`src/knowledge_ci/web/errors.py`、`src/knowledge_ci/web/templates/error.html`、`var/local-checks/tests/integration/test_local_boundaries.py`。
- 第1天：统一页面与API的错误码、request_id、字段错误、冲突刷新与失败恢复说明。
- 第2天：验证越界路径、伪造actor、跨源状态操作、缺失证据和敏感日志；修复局部缺口。
- 验收/合入：关键异常都有可操作反馈；凭据不进代码/日志/证据；入口不能绕过领域服务。
- 范围或等待说明：不新增多租户或账号体系；不是把基础防护推迟到此时才实施。
- 建议分支：`codex/t20-error-boundaries`。

<a id="t21"></a>

### T21 实现质量、耗时和成本报告

- 工期：2天；计划 D053～D054；里程碑 M3；对应原工作包 S14。
- 前置：T12、T18、T19、T20。
- 输入与契约：主计划第9.3节指标口径；T12已记录实际/估算成本与预算占用。
- 目标路径：`src/knowledge_ci/knowledge/metrics.py`、`src/knowledge_ci/web/templates/metrics.html`、`src/knowledge_ci/cli.py`、`var/local-checks/tests/integration/test_metrics_report.py`。
- 第1天：聚合候选分母、确认/驳回/未审数、追问状态、阶段耗时、失败及模型调用成本。
- 第2天：提供简单页面与JSON/表格导出，验证零分母、未知费用、重试调用和快照过滤。
- 验收/合入：报告数字可回查明细；未审候选不隐藏；无有效知识时成本指标不是0；超预算原因可见。
- 建议分支：`codex/t21-quality-metrics`。

<a id="t22"></a>

### T22 完成备份与恢复演练

- 工期：2天；计划 D055～D056；里程碑 M3；对应原工作包 S14。
- 前置：T04、T18、T21。
- 输入与契约：数据库和证据产物共同构成备份；本地运行数据受var清理规则约束。
- 目标路径：`src/knowledge_ci/storage/backup.py`、`src/knowledge_ci/cli.py`、`var/local-checks/tests/integration/test_backup_restore.py`、`docs/decisions/0002-data-lifecycle.md`。
- 第1天：定义一致备份/恢复方法、清单和内容哈希；明确停写或快照策略、缓存与正式数据区别。
- 第2天：在隔离测试目录恢复完整样例，核对知识、修订、审核、审计和证据可访问；记录操作。
- 验收/合入：A11通过；恢复不会写坏现有数据；清理策略保留被正式知识引用的证据。
- 建议分支：`codex/t22-backup-restore`。

<a id="t23"></a>

### T23 运行真实仓库试点与人工核验

- 工期：3天；计划 D057～D059；里程碑 M4；对应原工作包 S15。
- 前置：T17、T18、T19、T20、T21、T22。
- 输入与契约：真实仓库授权、模型可用、知情者可参与；候选和私有原文仅保留本地运行区。
- 目标路径：`var/local-checks/tests/fixtures/pilot_manifest.json`、`docs/decisions/0003-pilot-evaluation.md`、`TASK_PLAN.md`。
- 第1天：记录commit、配置、规模和基线，运行试点，核对解析缺口和预算。
- 第2天：逐条审核候选与追问，记录去重后的有效知识、拒绝理由和证据完整率。
- 第3天：汇总A01–A12检查结果、成本与阻塞项，按影响建立缺陷清单。
- 验收/合入：至少10条、目标10–30条有价值知识并公开候选分母；无法达标如实标阻塞/需调整，不能用摘要充数。
- 范围或等待说明：3天是操作与核验投入估算；授权、知情者答复等待不计入，且不保证3天一定得到10条知识。
- 建议分支：`codex/t23-pilot-evaluation`。

<a id="t24"></a>

### T24 处理首轮缺陷并完成 MVP 验收

- 工期：3天；计划 D060～D062；里程碑 M4；对应原工作包 S15。
- 前置：T23。
- 输入与契约：T23缺陷清单与主计划A01–A12；代码修改路径按缺陷定位后在开工前补入本卡。
- 目标路径：`TASK_PLAN.md`、`PROJECT_PLAN.md`、`var/local-checks/tests/e2e/test_mvp_acceptance.py`、`docs/decisions/0004-mvp-acceptance.md`。
- 第1天：只选累计不超过本卡容量的验收阻断缺陷，写清文件与验证；修复最高优先项。
- 第2天：运行受影响回归及一次完整闭环，复核数据、成本和恢复演练记录。
- 第3天：记录发布/继续修复决定与演示说明，更新实际工时和后续估算。
- 验收/合入：A01–A12全部通过才能完成MVP；超出3天容量新增子任务并重排，不能当作已通过。
- 范围或等待说明：额外部署、性能专项和无限量缺陷修复不隐含在3天内。
- 建议分支：`codex/t24-mvp-acceptance`。

## 新鲜度与增量演进：T25～T34（预备排期）

<a id="t25"></a>

### T25 定义增量输入与变更基准样例

- 工期：2天；计划 D070～D071；里程碑 M5；对应原工作包 S16。
- 前置：T24。
- 输入与契约：MVP验收通过；指定base/head commit；P1目标平台在此选择一种。
- 目标路径：`src/knowledge_ci/contracts/changes.py`、`var/local-checks/tests/fixtures/change_cases.json`、`docs/decisions/0005-incremental-scope.md`。
- 第1天：定义ChangeSet、影响结果、Verification与风险建议模型，确认事件源和范围。
- 第2天：建立格式、类型指令、import副作用、日志表达式、重命名、删除、分叉历史反例；定误报/漏报门槛。
- 验收/合入：每类样例有人工预期；不确定性如何表达明确；平台接入权限和等待事项登记。
- 建议分支：`codex/t25-change-contracts`。

<a id="t26"></a>

### T26 实现 commit Diff 与路径变更定位

- 工期：3天；计划 D072～D074；里程碑 M5；对应原工作包 S16。
- 前置：T05、T25。
- 输入与契约：两个固定commit及T25 ChangeSet；无效祖先关系按已定策略处理。
- 目标路径：`src/knowledge_ci/repository/diff.py`、`var/local-checks/tests/integration/test_commit_diff.py`。
- 第1天：读取base/head差异与新增/删除/修改文件，保留两侧定位。
- 第2天：实现重命名映射、二进制/大文件诊断和不可直接比较历史的处理。
- 第3天：核对黄金变更样例与复现性；不依赖文件时间戳判定新鲜。
- 验收/合入：变更集合可回溯两侧commit；删除/改名不丢失原知识关联；无法比较明确返回unknown/错误。
- 建议分支：`codex/t26-commit-diff`。

<a id="t27"></a>

### T27 实现保守的 AST 变化过滤

- 工期：3天；计划 D075～D077；里程碑 M5；对应原工作包 S16。
- 前置：T06、T25、T26。
- 输入与契约：固定工具版本的Vue/JS/TS两侧AST与SFC映射；T25变化分类与反例，含去注释误伤字符串。
- 目标路径：`src/knowledge_ci/analysis/semantic_diff.py`、`var/local-checks/tests/unit/test_semantic_diff.py`。
- 第1天：制定允许跳过的最小等价规则与版本号，默认不确定则继续检测。
- 第2天：比较符号、签名、控制流、异常处理与import等变化，保存判定原因。
- 第3天：验证纯格式与副作用import、日志表达式、类型/配置指令反例。
- 验收/合入：只能证明的等价变化才跳过；反例不误归无影响；解析失败进入unknown而非fresh。
- 建议分支：`codex/t27-semantic-diff`。

<a id="t28"></a>

### T28 计算知识关联与依赖影响范围

- 工期：3天；计划 D078～D080；里程碑 M5；对应原工作包 S16。
- 前置：T07、T14、T26、T27。
- 输入与契约：知识scope、两侧符号与import图、变更集合。
- 目标路径：`src/knowledge_ci/analysis/impact.py`、`src/knowledge_ci/knowledge/scope_index.py`、`var/local-checks/tests/integration/test_knowledge_impact.py`。
- 第1天：建立路径/符号到知识修订的索引，处理删除和改名。
- 第2天：按有界依赖传播计算受影响候选，标明直接/间接/未知关联。
- 第3天：验证跨模块影响、边变化、未解析依赖与边界外变更。
- 验收/合入：受影响知识可解释；unknown依赖不被静默排除；不把未覆盖范围声明为安全。
- 建议分支：`codex/t28-knowledge-impact`。

<a id="t29"></a>

### T29 落地新鲜度复核与影响判断

- 工期：3天；计划 D081～D083；里程碑 M5；对应原工作包 S16。
- 前置：T12、T25、T28。
- 输入与契约：Verification绑定knowledge revision、目标snapshot与scope_hash。
- 目标路径：`src/knowledge_ci/knowledge/freshness.py`、`src/knowledge_ci/storage/verification_store.py`、`var/local-checks/tests/integration/test_freshness_check.py`、`migrations/`。
- 第1天：串联版本/等价/影响规则，对可确定情况直接记录验证结果。
- 第2天：对剩余项通过受预算约束的模型判断，保留理由、证据及unknown结果。
- 第3天：验证跨分支、旧快照、依赖变化和证据不足；实现change-checks异步服务。
- 验收/合入：fresh只对指定范围与快照成立；不会仅凭时间戳续期；模型不确定时进入人工处理。
- 建议分支：`codex/t29-freshness-check`。

<a id="t30"></a>

### T30 实现风险分级与更新建议审核

- 工期：3天；计划 D084～D086；里程碑 M5；对应原工作包 S16。
- 前置：T15、T18、T29。
- 输入与契约：新鲜度结果、旧修订与新证据；首版只生成变更建议。
- 目标路径：`src/knowledge_ci/knowledge/evolution.py`、`src/knowledge_ci/review/risk_policy.py`、`src/knowledge_ci/web/templates/change_review.html`、`var/local-checks/tests/e2e/test_change_review.py`。
- 第1天：定义low/medium/high/unknown规则和冲突处理；生成新修订或失效建议。
- 第2天：复用审核/追问服务并增加差异页面、证据对照与来源commit展示。
- 第3天：验证高风险、证据冲突、删除警告和旧审批失效；评估成本。
- 验收/合入：旧发布知识不被模型覆盖；所有自动建议可审计；风险不明确不能自动当low。
- 范围或等待说明：自动发布只形成后续启用条件，不在本任务默认打开。
- 建议分支：`codex/t30-knowledge-evolution`。

<a id="t31"></a>

### T31 实现历史内容恢复为新修订

- 工期：2天；计划 D087～D088；里程碑 M5；对应原工作包 S16。
- 前置：T14、T15、T30。
- 输入与契约：历史修订、当前state_version；恢复也须经过审核。
- 目标路径：`src/knowledge_ci/knowledge/restore.py`、`src/knowledge_ci/web/templates/revision_history.html`、`var/local-checks/tests/integration/test_revision_restore.py`。
- 第1天：增加历史内容选择与恢复命令，生成引用原修订的新草稿。
- 第2天：验证权限边界、版本冲突、证据关联及恢复后重新审核。
- 验收/合入：恢复不删历史、不覆盖当前发布指针；重新批准后才可发布；审计能看到恢复来源。
- 建议分支：`codex/t31-revision-restore`。

<a id="t32"></a>

### T32 接入一种托管平台的历史证据

- 工期：3天；计划 D089～D091；里程碑 M5；对应原工作包 S16。
- 前置：T10、T25。
- 输入与契约：T25选定的一个平台；只读凭据及允许仓库；PR/MR、Issue与commit关联契约。
- 目标路径：`src/knowledge_ci/integrations/git_provider.py`、`src/knowledge_ci/evidence/remote_sources.py`、`var/local-checks/tests/integration/test_git_provider.py`。
- 第1天：定义provider接口和脱敏固定响应，确认平台API能力、权限与版本。
- 第2天：实现所选平台的PR/MR与Issue元数据/讨论读取、分页、限流及commit关联。
- 第3天：验证删除/不可访问/限流、缓存和凭据脱敏，将来源转为Evidence。
- 验收/合入：历史材料可以复核且权限被限制到允许仓库；数据缺失显式记录；离线样例可测试。
- 范围或等待说明：仅一个平台；远程克隆、通知Bot和多平台兼容不加入。
- 建议分支：`codex/t32-git-provider`。

<a id="t33"></a>

### T33 接收平台事件并触发增量任务

- 工期：3天；计划 D092～D094；里程碑 M5；对应原工作包 S16。
- 前置：T19、T29、T30、T32。
- 输入与契约：同一选定平台的一个事件入口；先选合并/Push中的明确事件类型。
- 目标路径：`src/knowledge_ci/integrations/events.py`、`src/knowledge_ci/web/webhooks.py`、`var/local-checks/tests/integration/test_incremental_events.py`。
- 第1天：验证平台事件真实性、仓库允许范围与事件schema，固定base/head。
- 第2天：按事件ID去重，持久化再返回接收结果，转换为增量分析Job。
- 第3天：重放重复/乱序/丢失base/失败重试事件；验证历史产物隔离与重试安全。
- 验收/合入：重复事件只对应一个逻辑工作；旧事件不能覆盖较新发布状态；不可处理事件可追踪。
- 范围或等待说明：只部署到已批准的接收环境；外网部署或网络审批时间单列，手动事件回放可先验收内部链路。
- 建议分支：`codex/t33-incremental-events`。

<a id="t34"></a>

### T34 完成增量闭环与质量验收

- 工期：3天；计划 D095～D097；里程碑 M5；对应原工作包 S16。
- 前置：T27、T28、T29、T30、T31、T32、T33。
- 输入与契约：T25预定误报/漏报标准和完整变更样例集。
- 目标路径：`var/local-checks/tests/e2e/test_incremental_workflow.py`、`docs/decisions/0006-incremental-evaluation.md`、`TASK_PLAN.md`。
- 第1天：运行事件→Diff→影响→复核→建议→审核→新发布的闭环。
- 第2天：核对副作用反例、删除/改名、恢复、乱序事件及权限失败，统计耗时/费用。
- 第3天：记录阶段验收和缺陷，重估P2；达标后才进入注入阶段。
- 验收/合入：人工标注集与预定门槛一致；回滚/恢复审计完整；未达标项阻断相应后续能力。
- 建议分支：`codex/t34-incremental-acceptance`。

## 开发前注入：T35～T40（预备排期）

<a id="t35"></a>

### T35 实现上下文查询与可解释排序

- 工期：3天；计划 D101～D103；里程碑 M6；对应原工作包 S17。
- 前置：T14、T29、T34。
- 输入与契约：repository_id、target_commit、intent、paths、operation、budget；发布修订与Verification。
- 目标路径：`src/knowledge_ci/contracts/context.py`、`src/knowledge_ci/knowledge/context_query.py`、`var/local-checks/tests/integration/test_context_query.py`。
- 第1天：冻结上下文输入输出及错误语义，复用路径和仓库边界。
- 第2天：按路径、符号、依赖、风险和发布状态检索排序，返回命中原因。
- 第3天：验证目标版本匹配、未发布排除、跨仓库拒绝及unknown/stale降级。
- 验收/合入：返回项均带知识修订、证据、新鲜度和目标版本；unknown/stale不能伪装成有效约束。
- 建议分支：`codex/t35-context-query`。

<a id="t36"></a>

### T36 实现上下文预算与压缩

- 工期：2天；计划 D104～D105；里程碑 M6；对应原工作包 S17。
- 前置：T35。
- 输入与契约：T35候选上下文和预算；首版优先确定性摘要/去重。
- 目标路径：`src/knowledge_ci/knowledge/context_budget.py`、`var/local-checks/tests/unit/test_context_budget.py`。
- 第1天：定义预算单位、稳定截断和去重方式，优先保留约束/风险/证据引用。
- 第2天：处理无命中、超预算和压缩失败，输出截断/降级原因并测试。
- 验收/合入：返回满足约定预算；压缩不删除关键限定或伪造结论；调用方能判断是否被截断。
- 范围或等待说明：可选LLM重写若引入需另做事实一致性验收，不隐含在2天内。
- 建议分支：`codex/t36-context-budget`。

<a id="t37"></a>

### T37 提供只读 MCP 上下文工具

- 工期：3天；计划 D106～D108；里程碑 M6；对应原工作包 S17。
- 前置：T35、T36。
- 输入与契约：现有context_query服务；使用实施时验证的MCP SDK和一种传输方式。
- 目标路径：`src/knowledge_ci/integrations/mcp_server.py`、`var/local-checks/tests/integration/test_mcp_context.py`。
- 第1天：核实目标客户端/SDK兼容，暴露工具schema和服务入口。
- 第2天：实现get_context调用、错误映射、取消/超时、日志脱敏和本机访问约束。
- 第3天：使用测试客户端校验工具发现、调用、无命中、超预算与拒绝访问。
- 验收/合入：工具输出与普通API同源；无写知识或执行仓库代码能力；不宣称MCP自动拦截编辑。
- 建议分支：`codex/t37-mcp-context`。

<a id="t38"></a>

### T38 验证一个客户端的开发前调用

- 工期：3天；计划 D109～D111；里程碑 M6；对应原工作包 S17。
- 前置：T37。
- 输入与契约：一个选定客户端和明确支持的接入方式；Hook能力需实际验证。
- 目标路径：`docs/decisions/0007-client-integration.md`、`src/knowledge_ci/integrations/client_adapter.py`、`var/local-checks/tests/e2e/test_client_integration.py`。
- 第1天：验证客户端可用接口；若缺少可靠Hook，明确采用显式工作流调用并记录限制。
- 第2天：接入意图/路径/操作信号，显示上下文、来源、失效提示与降级原因。
- 第3天：在受控示例验证修改前能取得上下文、失败时行为明确且无跨仓库泄露。
- 验收/合入：一个客户端有可重复演示步骤；是自动触发还是显式触发写清，不能凭MCP接通宣称已自动拦截。
- 范围或等待说明：仅一个客户端；专用IDE插件、多个Hook和强制策略平台另排任务。
- 建议分支：`codex/t38-client-integration`。

<a id="t39"></a>

### T39 记录注入反馈与采用指标

- 工期：2天；计划 D112～D113；里程碑 M6；对应原工作包 S17。
- 前置：T21、T38。
- 输入与契约：context_request_id、展示的知识修订、显式采用/未采用反馈。
- 目标路径：`src/knowledge_ci/knowledge/feedback.py`、`src/knowledge_ci/web/templates/context_feedback.html`、`var/local-checks/tests/integration/test_context_feedback.py`、`migrations/`。
- 第1天：保存查询与展示记录，提供简短反馈入口及重复反馈处理。
- 第2天：统计采用率、无命中、过期降级、延迟与预算；区分返回/展示/实际采用。
- 验收/合入：分母和样例可回查；工具成功返回不自动计为采用；意图日志按已定隐私规则保存。
- 建议分支：`codex/t39-context-feedback`。

<a id="t40"></a>

### T40 完成注入闭环验收与扩展决策

- 工期：3天；计划 D114～D116；里程碑 M6；对应原工作包 S17。
- 前置：T35、T36、T37、T38、T39。
- 输入与契约：固定版本样例、客户端演示与实际反馈；验证现有范围，不默认扩充A2A。
- 目标路径：`var/local-checks/tests/e2e/test_context_workflow.py`、`docs/decisions/0008-context-evaluation.md`、`TASK_PLAN.md`、`PROJECT_PLAN.md`。
- 第1天：跑查询→压缩→MCP→客户端→反馈，覆盖有效/未知/过期/跨仓库与超时场景。
- 第2天：记录命中价值、延迟、成本与失败行为；确认未绕过审核和版本契约。
- 第3天：记录是否投入多仓库、共享服务、更多语言或A2A的依据及后续独立任务。
- 验收/合入：当前一个客户端闭环可重复验证；未解决问题有任务归属；新增平台化能力必须单独估算与决策。
- 建议分支：`codex/t40-context-acceptance`。

## 5. 原工作包与验收覆盖

### 5.1 S01～S17 对应关系

原S编号保留用于解释主计划；实际排期、状态与建分支以T编号为准。

| 原工作包 | 对应细分任务 |
| --- | --- |
| S01 | T01 |
| S02 | T02、T03 |
| S03 | T04、T14 |
| S04 | T05 |
| S05 | T06、T07 |
| S06 | T08、T09 |
| S07 | T10 |
| S08 | T11 |
| S09 | T12、T13 |
| S10 | T14、T15 |
| S11 | T16、T17 |
| S12 | T18 |
| S13 | T19、T20 |
| S14 | T21、T22 |
| S15 | T23、T24 |
| S16 | T25、T26、T27、T28、T29、T30、T31、T32、T33、T34 |
| S17 | T35、T36、T37、T38、T39、T40 |

### 5.2 P0验收责任落点

| 主计划验收 | 主要实现与验证任务 |
| --- | --- |
| A01 固定快照与真实端到端 | T05、T11、T23 |
| A02 确定性与多配置隔离 | T07、T08、T11、T23 |
| A03 分析边界与只读 | T05、T06、T07、T20 |
| A04 至少10条有效知识 | T13早期反馈，T23统计，T24最终核验 |
| A05 证据/版本/失效条件/审核完整 | T02、T10、T13、T14、T15、T23 |
| A06 至少3类追问闭环 | T18、T23 |
| A07 不得绕过审核发布 | T15、T17、T18、T24 |
| A08 幂等与迟到响应 | T04、T11基础，T19故障验证 |
| A09 修订/状态并发与旧批准 | T14、T15、T17 |
| A10 成本与硬预算 | T12预算控制，T21报告，T23试点 |
| A11 备份与证据恢复 | T22 |
| A12 本机、凭据与执行边界 | T05、T12、T15、T16基础，T20综合验证 |

## 6. 实际执行记录

实际记录只追加结论与证据，不复制任务卡。T01于2026-10-19完成工程和自动验证，2026-10-20修复复审时发现的小问题。实际工作日按投入记录，不将2天估算直接算作实际用时。

| 任务ID | 实际开始/结束 | 实际工作日 | 等待天数与原因 | 实际分支/提交/PR | 验证证据 | 遗留项/新任务 |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | 2026-10-19开始/2026-10-20完成 | 本次会话；人日由Recall补录 | 无业务阻塞；下载及本机临时目录权限已处理 | feat/hyw/T01 (419b71d～6117a83)，bug/fix/1020 (16ad54b后) | 2026-10-19：18项测试、Ruff、真实试点配置检查、独立wheel安装复验通过；见0001-baseline.md。2026-10-20：干净worktree复验、相对路径锚定修复、空loc错误前缀修复、文档更新、新增3项测试后21 passed | 后续Vue/JS/TS解析已重排；模型供应商/预算T12前确定 |
| T01（本轮复审修复） | 2026-10-20开始/结束 | 本次会话；人日待Recall补录 | 无 | fix/hyw/1020；981d376、772bee7（本轮未自动提交） | Git输出显式解码、错误脱敏、CLAUDE.md冲突及目录规则修复；12项临时回归、真实试点校验、Ruff及差异检查通过，详情见0001-baseline.md | 两项审查问题已修复；临时材料已清理，待Recall验收 |
| T02 | 2026-10-20开始/结束 | 本次会话；人日待Recall补录 | 无；T01待验收但已合入main，按用户安排在其上开工 | feat/hyw/T02（基于4d5ea0a，未提交） | Windows、Python 3.12.14、pydantic 2.14.1：`uv run --offline --locked --with pytest==9.1.1`临时测试134 passed（基础类型、模型不变量、知识/追问/Job转换、CAS、伪造/跨快照引用、迟到租约、幂等冲突、错误不回显、contracts依赖边界、CLI回归）；wheel+带哈希锁定依赖的独立环境同样134 passed且导入来自site-packages；Ruff check/format、`git diff --check`、`check-config --require-pilot`通过；wheel 16个文件含contracts、不含测试；临时材料已删除 | 存储层ID生成、事务内CAS与AuditEvent归T04/T14/T15；HTTP异常映射归T15/T20 |

验收记录模板：

~~~text
任务：Txx
结果：完成 / 阻塞 / 拆分
本次实现：可观察行为
验证：命令或操作、输入版本、预期与实际结果
耗时：实际工作日；外部等待单独记录
变更范围：文件、契约与迁移
分支及提交/PR：
遗留项：新任务ID或明确无
下一项：
~~~

## 7. 排期调整与维护

- 工期以本文件为准，主计划只保留本文件导出的阶段摘要；不维护两套独立周数。
- 每个里程碑完成时比较计划/实际、分析偏差，先更新后续任务，再安排新分支。
- 增加范围、变更分析语言、换平台、知情者缺席或单项超过3天时，重新估算受影响任务。
- 若只要求更快的试验版，需要另行明确缩小验收范围；不能把当前完整MVP的62天直接改成短期限。
- 验收未通过的任务保持待验收或阻塞；未使用机动天可以释放，额外工作则新增带验收的小任务。

| 日期 | 修订 | 说明 |
| --- | --- | --- |
| 2026-10-19 | v1 | 将17个工作包拆成40项2～3天任务，建立相对工作日、分支建议、依赖及验收对应；替换原粗估 |
| 2026-10-19 | v2 | T01工程与验证完成待验收；选Vue3Admin/77e9634基线，目标解析调整为Vue/JS/TS；记录实际用户分支与验证证据 |
| 2026-10-19 | v3 | 按用户要求，测试代码/样例/专用依赖配置与报告只保留本地；任务卡验证路径统一迁到Git忽略的var/local-checks/ |
| 2026-10-20 | v4 | T01小问题修复完成：相对路径锚定、空loc错误前缀、测试用完即删规则、文档更新；T06建议分支名改为vue-ts-symbols |
| 2026-10-20 | v5 | 修复Windows中文仓库路径解码和CLAUDE.md合并冲突；记录12项临时回归及真实试点校验结果，T01保持待验收 |
| 2026-10-20 | v6 | T02共享契约完成待验收；校准T02目标路径（新增common、evidence模块，测试改用var/tmp/local-checks临时目录） |

