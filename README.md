# Knowledge CI

面向代码仓库的知识发现与人工审核系统。当前为 T01 工程基线：提供配置校验、命令行入口和 HTTP 健康检查，尚未提供仓库分析或知识生成。T02 在 `src/knowledge_ci/contracts/` 增加了各入口共用的领域 schema、状态转换规则与错误码，运行行为不变；`KNOWLEDGE_CI_PILOT_LANGUAGE` 只接受契约定义的 `vue-typescript`。

## 环境与安装

- Python 3.12；本次验证使用 3.12.14。
- 使用 uv 管理环境与锁文件。先按 [uv 官方安装说明](https://docs.astral.sh/uv/getting-started/installation/) 安装 uv。
- Git 需在 PATH 中。后续 Vue/TS 解析任务会引入独立 Node 解析辅助工具，T01 不安装目标项目依赖。
- 以下命令均在项目根目录执行。

~~~powershell
uv sync --locked
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv run --locked knowledge-ci --help
uv run --locked knowledge-ci check-config
uv run --locked knowledge-ci serve
~~~

访问 http://127.0.0.1:8000/healthz；按 Ctrl+C 停止。健康检查只返回状态与应用版本。

首次安装尚无 Python 时，uv 可以按 .python-version 准备 Python 3.12。uv.lock 固定直接与间接依赖；安装使用 locked 模式，防止无意改锁文件。依赖升级应作为显式变更验证。

本机已有 .venv 时，也可直接运行：

~~~powershell
.\.venv\Scripts\knowledge-ci.exe check-config --require-pilot
.\.venv\Scripts\knowledge-ci.exe serve
~~~

## 配置

配置前缀为 KNOWLEDGE_CI_，读取根目录 .env，环境变量优先于文件。.env 被 Git 忽略，不能提交凭据；命令行可用 --env-file 指定其他文件。

相对路径的 `PILOT_REPOSITORY` 以配置文件所在目录为基准。默认 `.env` 的基准是当前工作目录；用 `--env-file` 指定其他文件时，相对路径以该文件所在目录为基准。

Git 路径输出按 UTF-8 解码，支持 Windows 中文及带空格的仓库路径；无法解码的仓库元数据返回退出码2，不回显原始输出。

| 变量 | 默认值 | 作用 |
| --- | --- | --- |
| KNOWLEDGE_CI_HOST | 127.0.0.1 | 只接受本机监听地址 |
| KNOWLEDGE_CI_PORT | 8000 | 监听端口，范围1～65535 |
| KNOWLEDGE_CI_LOG_LEVEL | info | 服务日志级别 |
| KNOWLEDGE_CI_PILOT_REPOSITORY | 空 | 本地Git仓库路径，支持相对路径 |
| KNOWLEDGE_CI_PILOT_COMMIT | 空 | 完整40位小写commit SHA，不使用移动分支作为基线 |
| KNOWLEDGE_CI_PILOT_LANGUAGE | 空 | 目标源码语言标识；当前试点为vue-typescript |
| KNOWLEDGE_CI_PILOT_OWNER | 空 | 试点知情者，当前为Recall |
| KNOWLEDGE_CI_MODEL_PROVIDER | mock | T01仅支持假响应 |
| KNOWLEDGE_CI_ALLOW_SOURCE_EGRESS | false | T01禁止源码外发 |
| KNOWLEDGE_CI_MODEL_BUDGET_USD | 0 | T01无外部模型调用 |

未配置试点时，空应用与普通 check-config 可启动；涉及试点的检查必须显式执行：

~~~powershell
uv run --locked knowledge-ci check-config --require-pilot
~~~

缺少试点、commit不在本地仓库、无效端口或不支持的配置均返回退出码2，错误不回显输入值。--help 与 --version 返回0。默认.env可省略；显式--env-file指定的文件不存在时返回2，不静默回退到默认配置。

`check-config` 输出包含 `env_file_loaded` 字段：true 表示读取了配置文件，false 表示配置文件不存在或未使用，全部使用默认值和环境变量。

本地 `.env` 需指向试点仓库的只读克隆。克隆命令示例：

~~~powershell
git clone --no-checkout https://github.com/Ai060715W/Vue3Admin.git var/cache/repositories/vue3-admin
~~~

示例试点值：

~~~dotenv
KNOWLEDGE_CI_PILOT_REPOSITORY=var/cache/repositories/vue3-admin
KNOWLEDGE_CI_PILOT_COMMIT=77e9634e3eb764704b9ff9a5810e1a9747422c0f
KNOWLEDGE_CI_PILOT_LANGUAGE=vue-typescript
KNOWLEDGE_CI_PILOT_OWNER=Recall
~~~

用户允许后续接入外部模型；供应商、内容范围与预算尚未确定。当前配置不能开启真实模型，T12接入前再记录具体约定。

## 本地验收

测试代码、样例、验证工具配置和报告仅在本地临时执行，验证后删除，不进入Git或安装包。

~~~powershell
uv run --locked knowledge-ci --version
uv run --locked knowledge-ci check-config --require-pilot
uv run --locked knowledge-ci serve
~~~

启动后检查 /healthz，并按Ctrl+C确认退出。历史验证结果保留在基线决策 docs/decisions/0001-baseline.md 中。

2026-10-20复审修复：Windows / Python 3.12.14 下12项临时回归检查通过，覆盖中文路径、异常编码和错误脱敏；真实试点校验通过。临时脚本、合成仓库及运行产物验证后删除，具体命令与结果见基线决策。

## 当前试点与范围

- 仓库：[Ai060715W/Vue3Admin](https://github.com/Ai060715W/Vue3Admin)。
- 主基线：77e9634e3eb764704b9ff9a5810e1a9747422c0f；对照提交：24660e19cf665a4e8bb87067913e6d468de0967a。
- 第一轮关注 Vue3Admin/src 内的路由权限、Pinia状态、请求拦截、分片上传和流式聊天。
- 实现语言是 Python；目标源码为 Vue SFC / TypeScript / JavaScript，不能使用 Python ast 解析目标。
- 仓库总计4次提交，主基线可追溯3次；历史证据较少，正式知识的业务原因需要知情者核验。未在此宣称已经发现10条知识。
- 当前不运行试点的构建、脚本或服务；试点中的配置文件与凭据不纳入模型输入。

详见 docs/decisions/0001-baseline.md；任务进度统一记录在 TASK_PLAN.md。
