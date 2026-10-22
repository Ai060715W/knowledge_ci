# 0010：T04 基础存储与迁移

- 日期：2026-10-22；分支 `feat/hyw/T04`（基于 main 895b97a）；状态：实现与自动验证完成，待 Recall 验收。
- 范围：Repository、Snapshot、AnalysisRun、Job、Evidence 与阶段产物的持久化；知识/追问/审核/审计表由 T14/T15 增量迁移。

## 选择与架构影响

| 选择 | 原因 | 对架构的影响 |
| --- | --- | --- |
| SQLite（WAL）+ SQLAlchemy 2.1.6 + Alembic 1.20.1 | 本机单用户、单 worker，免维护数据库服务；ORM 与迁移为切换数据库保留路径 | 新增运行依赖 sqlalchemy、alembic（传递 Mako、MarkupSafe），uv.lock 锁定 |
| 写事务一律 `BEGIN IMMEDIATE` | SQLite 只有一个写者；在 BEGIN 就取写锁，忙时尚未执行任何业务语句，可安全重试 | `Database.transaction()` 遇写锁按 busy_timeout 等待并有界退避重试，耗尽抛 `StorageBusyError`；事务体内的错误只回滚、不自动重放 |
| 读用 `Database.read()`：普通 BEGIN + `query_only` | WAL 下读不阻塞写；误写立即失败，不会悄悄占写锁 | 查询入口用 read，命令入口用 transaction |
| synchronous 保持默认 FULL | NORMAL 在断电时可能丢最近提交，审核与证据数据不能接受 | 写入稍慢；当前单用户量级可忽略 |
| 迁移放 `src/knowledge_ci/storage/migrations/` | wheel 只打包 `src/knowledge_ci`；根目录迁移不随包分发，安装后无法初始化 | 规范目录表已改；无根目录 `alembic.ini`，pyproject 仅为开发者生成修订提供 `[tool.alembic]` |
| 迁移在单一事务内，期间关外键，提交前 `PRAGMA foreign_key_check` | SQLite 的 batch 模式重建表时需关外键；检查失败整体回滚 | 迁移要么完整生效要么不改库 |
| 约束命名规范（`pk_`/`uq_`/`fk_`/`ck_`） | 后续 batch 迁移按名称修改约束 | 0001 与模型 `create_all` 的 DDL 逐行一致 |
| 时间只接受带时区值，按 naive UTC 存储 | SQLite 无时区类型 | naive 时间写入即失败；读出恢复 tzinfo=UTC |
| ID 为 `<前缀>_<32位hex>`（repo/snap/run/job/ev/art） | 满足 T02 Id 约束，可读且不可猜；不承诺按时间排序 | 由 `models.new_id()` 统一生成；分页不依赖 ID 顺序 |

## 数据位置与产物

- `KNOWLEDGE_CI_DATA_DIR`（默认 `var`，相对路径锚定规则同 PILOT_REPOSITORY）下：`db/knowledge_ci.sqlite3` 及 `-wal`/`-shm`；`artifacts/objects/sha256/<前2位>/<其余62位>`。
- 产物以内容哈希寻址，数据库只存哈希，文件位置由哈希推导；仓库根目录 `repositories.allowed_root` 是库中唯一的机器路径。
- `ArtifactStore.put()` 在事务外写入：临时文件 + fsync + 原子替换，幂等，损坏文件会被替换；Windows 并发替换的短暂拒绝有界重试。`read()` 每次校验哈希。
- 事务内 `record()` 登记内容目录（先核对文件存在且大小一致），`attach()` 把内容命名为 `(analysis_run_id, stage, name)` 的逻辑产物 `artifact_id`。失败事务只可能留下无引用、可复用的文件；孤儿文件清理归 T22。

## 身份与去重

| 记录 | 唯一身份 | 重复写入 |
| --- | --- | --- |
| Repository | allowed_root（规范化由 T05 负责） | 返回已有记录 |
| Snapshot | (repository_id, commit_sha) | 返回已有记录；同 commit 不同 tree 为 `idempotency_conflict` |
| AnalysisRun | T02 `identity_key()`（快照 + 全部版本 + config_hash） | 返回已有记录；不同配置得到不同 run，产物互不覆盖 |
| Job | (repository_id, idempotency_key) | 指纹相同返回同一 Job，不同为 `idempotency_conflict` |
| 逻辑产物 | (analysis_run_id, stage, name) | 内容相同返回已有产物；不同为 `idempotency_conflict`，迟到或重复执行不能覆盖已提交产物 |
| Evidence | (snapshot_id, stable_hash(locator), content_hash) | 返回已有记录；同一位置内容变化（如重新回答）是新证据 |

数据库层另行保证：Job 的快照与 run 属于同一仓库链（复合外键）；租约三字段仅 running 时全部存在；attempt ≤ max_attempts；状态、阶段、类型取值 CHECK；model/prompt 版本同空同有；证据与产物引用的内容必须已登记。

## 后续任务使用约定

- 一次业务操作 = 一个 `with db.transaction() as session:`，各 store 函数共用该 session，多条写入同时提交或回滚。
- 阶段产物：事务外 `store.put(bytes)`；事务内 `store.attach(...)` 与 `job_store.update_job(..., advance_stage)` 一起提交，租约失效则产物引用一并回滚（T11）。
- 证据：`put` → `record` → `evidence_store.add_evidence`；`get_evidence()` 的结果直接交给 `contracts.knowledge.reference_errors`（T10/T13）。
- `update_job` 只接受 contracts.jobs 的纯函数转换，禁止改身份字段。
- `Database()` 遇未初始化的库报错，不静默建空库；先执行 `knowledge-ci migrate`。`serve` 不自动迁移。
- `StorageBusyError`/`StorageError` 到 API 错误码的映射留给 T11/T20（现有 ErrorCode 无对应的 503 类代码，需先改契约）。

## 新增迁移

1. 修改 `storage/models.py`。
2. 以临时 `KNOWLEDGE_CI_DATA_DIR` 执行 `knowledge-ci migrate` 得到 head 库。
3. `alembic -x db=<该库文件> revision --autogenerate --rev-id 0002 -m "add knowledge"`（`-x` 须写在子命令前），人工审阅：不得 import 业务模块；超长 SQL 提为常量。
4. `alembic -x db=<该库文件> upgrade head` 后 `alembic -x db=<该库文件> check` 无差异；已应用版本不改写。

## 切换 PostgreSQL 前需复核

- 事务：`BEGIN IMMEDIATE` 与 query_only 只适用于 SQLite；`update_job` 已带 `FOR UPDATE`，但各 add_* 的"先查后插"在并发写者下需处理唯一约束冲突。
- 类型与约束：`length()/substr()` 检查、JSON 列、naive UTC 时间列（宜改 timestamptz）需迁移演练；字符串长度上限 SQLite 不强制，PostgreSQL 会强制。
- 产物目录不随数据库迁移，备份与恢复须一起验证（T22）。

验证命令与结果见 [TASK_PLAN.md 第6节](../../TASK_PLAN.md)。
