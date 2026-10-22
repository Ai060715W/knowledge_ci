# 项目协作规范

## 项目范围

- 本项目工作区为 `D:\knowledge_ci`，默认使用简体中文沟通和编写说明文档。
- `knowledge_ci.html` 是现有产品与系统设计说明及需求分析依据；未经明确要求，不覆盖、重命名或改写该文件。
- `PROJECT_PLAN.md` 存放项目计划，区分已有设计、已确认约束、建议方案和待确认事项；不得把方案描述视为已实现的业务功能。
- `TASK_PLAN.md` 是逐任务排期与状态的唯一记录，任务按 2～3 个工作日拆分，包含依赖、目标路径、每日步骤、验收与建议分支名；`PROJECT_PLAN.md` 保留范围、架构及验收基线，并引用任务计划。
- 当前按 Recall 单人开发编排任务，系统实现语言为 Python；后续增加开发者时沿用模块边界重新分配任务。分支管理由用户安排。

## 目录与命名

- 当前根目录仅存放项目规范、项目计划、原型及必要的工程配置，不创建临时分析文件。
- 根目录允许长期保留 `TASK_PLAN.md`；只维护这一份细分排期，不复制出相互矛盾的任务清单。任务编号发布后保持稳定，拆分使用子编号并重新计算后续工期。
- 后续新增目录前，先在本文件中定义其用途、内容分类、命名规范和清理策略，再创建目录。
- 文档使用有明确含义的英文文件名；Python 包、模块使用 snake_case，其他业务目录优先使用 kebab-case。
- 临时输出不得混入源码；确需保留的生成产物必须先约定目录与清理方式。
- 测试仅按需临时执行；临时测试代码、样例、测试专用配置、报告和运行产物必须在本次验证结束后删除，不得以 Git 忽略代替清理。测试材料不得入库或打包，测试工具不得加入业务依赖。

### 后续工程目录预案

当前启动 T01 最小工程，按以下用途逐项创建必要目录，不预建未使用的业务模块。任何新增子目录必须先遵循已有约定，未覆盖时先更新规范。

| 路径 | 内容与命名 | 清理策略 |
| --- | --- | --- |
| `src/knowledge_ci/` | Python 应用包；按 `contracts`、`repository`、`analysis`、`evidence`、`knowledge`、`review`、`jobs`、`storage`、`web`、`integrations` 分模块；入口 `cli.py`、`app.py` | 源码长期保留；模块命名 snake_case，不放生成数据 |
| `src/knowledge_ci/web/templates/`、`src/knowledge_ci/web/static/` | 服务端模板及静态资源；模板和资源按所属功能命名 | 保留源文件；不提交缓存与构建产物 |
| `var/tmp/local-checks/`（仅验证期间存在） | 按需临时放置测试代码、合成或脱敏样例、测试专用配置和报告；测试文件使用 `test_*.py` | 本次验证结束后删除整个目录；不得入库、打包或长期保留 |
| `var/tmp/local-checks/` 下的 `tests/fixtures/`、`tests/integration/`、`runs/` | T03 临时历史生成器 `repository_builder.py`、预期清单 `knowledge_cases.json`、`test_fixture_repository.py`；`runs/` 下按运行隔离合成 Git 仓库（含中文与空格路径）及 Git 自管内部目录 | 生成仓库由上下文管理器清理（含异常退出）；本次验证结束删除整个 `local-checks/` |
| `src/knowledge_ci/storage/migrations/`（T04） | Alembic 迁移环境 `env.py`、`script.py.mako` 与 `versions/NNNN_snake_case.py`（`--rev-id` 用四位递增序号）；随 wheel 分发，根目录不建 `migrations/` 或 `alembic.ini` | 已应用迁移不可随意改写或删除；结构变更只新增版本 |
| `docs/decisions/` | 工程启动后记录决策；文件名 `NNNN-kebab-case.md` | 长期保留；替代旧决策须保留关联记录 |
| `tools/parser/`（T06按需创建） | Vue SFC/JS/TS静态解析辅助工具；`index.mjs`、`package.json`、`package-lock.json`；仅接收源码数据并输出JSON | 工具源码/锁文件入库；`node_modules`与缓存忽略，不执行目标仓库代码 |
| `var/` | 本地运行数据，按 `db`、`cache`、`artifacts`、`logs`、`tmp` 分类；须在创建时加入 Git 忽略 | `cache` 可重建，`tmp` 任务结束清理，日志轮转；数据库与证据产物先备份并核对引用再清理 |
| `var/db/`、`var/artifacts/objects/`（T04，根目录由 `KNOWLEDGE_CI_DATA_DIR` 指定，默认 `var`） | `db/knowledge_ci.sqlite3` 及 SQLite 自管的 `-wal`/`-shm`；`artifacts/objects/sha256/<哈希前2位>/<其余62位>` 内容寻址文件，路径由内容哈希推导，数据库不存机器路径 | 不手改、不单独删除；清理或迁移前先备份并核对数据库引用（T22 落实）；`artifacts/packages/` 仍为可重建构建包 |

### T01 结构与运行约定

- `src/` 只放应用源包；`src/knowledge_ci/` 入口为 `__init__.py`、`__main__.py`、`app.py`、`cli.py`、`config.py`。T02起创建 `contracts/`，仅含 `__init__`、`common`、`repository`、`evidence`、`knowledge`、`jobs`、`errors` 模块；其余业务目录由对应任务创建，不预建。
- `contracts/` 只依赖标准库与 pydantic，不 import 其他业务模块或配置；字段、状态机、错误语义变更先改契约再改调用方。
- T04 创建 `storage/`：`__init__`、`database`（引擎、事务、写锁重试、迁移入口）、`models`（表与约束）、`artifacts`（内容寻址产物）、`repository_store`、`job_store`、`evidence_store` 及 `migrations/`；后续表按 `*_store.py` 由对应任务新增。storage 只依赖 contracts、SQLAlchemy/Alembic 与标准库，不 import config/cli/app/web；数据库与产物根目录由入口组装后传入。
- 业务源码目录不放测试。测试临时放`var/tmp/local-checks/tests/`（可按`unit`、`integration`分子目录），验证后删除；测试专用工具通过临时环境按需提供，不纳入业务依赖或uv.lock。
- `docs/decisions/` 保留 `0001-baseline.md`、T03 的 `0009-golden-fixtures.md` 与 T04 的 `0010-storage-foundation.md`（0002～0008已由后续任务预留）；0009 记录合成历史的复现规格、预期行为与后续模块使用约定，不保存测试脚本、样例源码或运行报告；0010 记录存储选型、事务与产物约定。
- `.venv/` 为项目隔离环境；`var/cache/uv/` 为可重建依赖缓存，`var/cache/uv-bootstrap/` 为可重建的本地依赖工具；均不入 Git。任务临时验证环境放在 `var/tmp/`，验证后清理。
- 工具自动生成的Python `__pycache__/` 可在所属模块内出现，忽略并按需清理；Ruff/pytest缓存分别放 `var/cache/ruff/`、`var/cache/pytest/`。构建包放 `var/artifacts/packages/`，文件名由构建工具生成，可重新构建；`.venv/`和缓存内部由相应工具管理，不手改依赖文件。
- `var/cache/repositories/vue3-admin/` 存放用户指定试点的只读克隆；保持 Git 历史，不运行项目脚本、不安装其依赖、不改写原项目。目录可重建，清理前核对是否仍被本地试点配置引用。
- 根目录允许 `README.md`、`.python-version`、`uv.lock`、`pyproject.toml`、`.gitignore`、`.env.example`；依赖由 uv 锁定并使用 locked 模式安装，Python 基线为 3.12。
- 配置统一使用 `KNOWLEDGE_CI_` 前缀；缺少真实试点或模型权限时允许本机空应用启动，涉及试点的检查必须明确失败，不能虚构已配置仓库。
- 用户允许后续接入外部模型，供应商和预算待确定；当前 T01 仍为假响应、源码外发关闭、模型预算为 0，真实接入前记录明确约定。

根目录后续仅按需新增 `pyproject.toml`、依赖锁文件、`.gitignore`、脱敏的 `.env.example` 与工程说明；不得提前生成空目录或未使用的配置。

## 开发与多人协作

- 非琐碎任务先说明计划、影响范围与验证方法，再实施；发现偏差时先调整计划。
- 开发前阅读本文件及目标目录下更具体的 `AGENTS.md`，规则调整先于实践变更。
- 多人按模块分工，变更前确认文件归属、接口契约和上下游依赖；共享配置、公共类型与数据模型由明确负责人统一维护。
- 模糊需求先标记假设与待确认事项；未批准的技术建议不得写成已定决策。
- 技术决策必须说明问题、选择理由及对架构的影响；改动保持最小范围，解决根因。
- 密钥、token、密码不得写入代码或文档；生产环境访问凭据通过环境配置管理。
- 不自动执行 `git push`；仅在用户明确要求时执行。部署遵循后续确认并记录的项目命令。
- 任务计划中的分支名是可采用的建议，不代表分支已创建；分支创建与合并由 Recall 安排。任务完成须更新任务状态、实际用时和验收证据。

- 任务计划中的分支名是可采用的建议；分支创建与合并由 Recall 安排。任务完成须更新状态、实际用时和验收证据。

## 本阶段验证

- 当前实施 T04：按 T02 契约建立 SQLite 存储、Alembic 迁移与内容寻址产物，覆盖 Repository/Snapshot/AnalysisRun/Job/Evidence；不实现 Git 读取、worker、知识表、HTTP 路由或模型调用。
- 验证空库升级与迁移往返、唯一/外键/检查约束、事务回滚、写锁重试、按逻辑ID回读产物及 wheel 安装后迁移；测试材料验证后删除。样例沿用 0009 场景语义，不重建 Git 历史。
- 运行命令、环境与结果写入 TASK_PLAN；T04 由 Recall 验收，不虚报完成。
- 不修改原 HTML，不自动创建/切换分支、提交、推送或部署。
