# 0001：T01 工程与试点基线

- 日期：2026-10-19。
- 状态：T01工程实现与自动验证完成，待Recall验收合入。
- 工作分支：feat/hyw/T01（用户已创建，当前继续使用）。
- 用户已确认：Recall单人开发；Python实现；试点为Ai060715W/Vue3Admin；允许后续接入外部模型，供应商和预算待定。

## 问题与最直接路径

先获得一套可以重复安装、启动、校验配置和退出的工程，再做领域契约与分析流水线。空应用不能依赖真实仓库或模型账号才能启动，但声称具备真实试点配置时必须验证本地Git与固定commit。

## 已落地的选择

| 选择 | 原因 | 对架构的影响 |
| --- | --- | --- |
| Python 3.12，当前验证3.12.14 | 已有可用解释器；与所选依赖一起锁定验证，减少初始环境变量 | pyproject限定3.12小版本系列；后续语法/运行时升级显式验证 |
| uv + uv.lock + src布局 | 安装和执行走同一锁定依赖，避免全局环境漂移 | 工程只依赖项目环境；机器绝对路径不进入包元数据 |
| FastAPI + Uvicorn | 满足后续API边界，当前仅健康路由 | create_app工厂复用配置，不创建数据库或扫描任务 |
| Pydantic Settings | 对.env和环境变量做类型/边界校验 | 基础配置独立于T02领域契约；错误不输出原始值 |
| 标准库argparse | 当前只有少量命令，无需额外CLI框架 | HTTP与CLI共享配置，未来命令复用应用服务 |
| 本地pytest + 标准库HTTP客户端 + Ruff（不入库） | 验证实际HTTP服务 | 验证代码、工具配置和依赖仅本地使用，不写入业务清单 |
| 模型mock、外发false、预算0 | 用户允许后续接入，但尚无供应商和预算决定 | T01不会执行外部模型调用；T12前更新政策与适配器 |
| 数据库/模板依赖后置 | T01不创建存储或审核页面 | SQLAlchemy/Alembic在T04、模板在需要时引入，不提前维护空模块 |

## 试点选择与固定版本

- 远程：https://github.com/Ai060715W/Vue3Admin.git；默认分支main。
- 本地只读克隆：var/cache/repositories/vue3-admin；使用git对象读取，不检出或运行项目代码。
- 主基线：[77e9634](https://github.com/Ai060715W/Vue3Admin/commit/77e9634e3eb764704b9ff9a5810e1a9747422c0f)，完整SHA为77e9634e3eb764704b9ff9a5810e1a9747422c0f。
- 对照提交：[24660e1](https://github.com/Ai060715W/Vue3Admin/commit/24660e19cf665a4e8bb87067913e6d468de0967a)。
- 知情者：Recall，仍需逐条核验业务动机，不能因仓库属于本人就自动认可模型推断。
- 实测HEAD历史共4次提交；主基线历史3次。历史较短，MVP有效知识数量不能预先保证。
- 读取的package.json声明Vue ^3.4.21、TypeScript ~5.4.0、Vite ^5.2.8；仓库也含Node/Express后端，本轮先关注前端源码。

选择前一个提交的原因：对照提交意图是删除注释，但Vue3Admin/src/router/index.ts中的字符串路由 '/*' 被截断，路由定义被移除。此观察来自git show的两侧源码对照，不是运行整套应用后的结论。主基线保留完整路由定义；后续可将这个差异作为“注释变化不一定无语义”的反例。没有修改试点仓库。

## 首轮关注范围

| 路径（相对试点仓库） | 要验证的知识入口 |
| --- | --- |
| Vue3Admin/src/router/index.ts | 白名单、动态路由与权限校验 |
| Vue3Admin/src/stores/modules/permission.ts、users.ts | 权限和用户状态之间的约束 |
| Vue3Admin/src/utils/service.ts、cache/cookies.ts | 请求拦截与令牌处理 |
| Vue3Admin/src/utils/file/fileUpload.ts、CreateChunk.js、worker.js | 分片、并发、校验与恢复线索 |
| Vue3Admin/src/serve/chat/chat.ts | 流式响应处理与状态约束 |

以上是候选分析入口，不是已证实的设计结论。配置、数据库连接、模型密钥与图片等非源码材料默认不进入证据生成输入。

## 目标语言调整及后续任务影响

系统实现语言仍为Python，首批被分析语言正式改为Vue SFC/JS/TS，不采用Python ast作为目标解析器。

计划在T06使用隔离的静态解析辅助工具：由官方Vue SFC解析器提取script/script setup，配合JS/TS语法解析器输出约定的JSON；Python负责仓库、任务、证据和知识流程。辅助工具不得执行import或目标项目插件；具体工具版本及性能在T06锁定。这样避免手写正则拆SFC破坏字符串/行号，又不把Python应用改为Node应用。

- T02：language/parser_version及位置契约包含Vue SFC块到原文件的行号映射。
- T03：黄金样例改用JS/TS/Vue，补字符串含注释标记、副作用import与路径别名。
- T06/T07：改为Vue/JS/TS静态解析，支持相对路径及@/*→Vue3Admin/src/*；计算表达式形式动态import标unknown。
- T09：规则采用静态依赖环、条件中的硬编码阈值、空catch/静默降级候选。
- T27：语义变化过滤覆盖SFC/JS/TS，解析失败或错误去注释不得标fresh。
- 现有任务天数暂作容量预留；T06若辅助工具验证超出3天，按原计划拆子任务并重排，不把语言变化当作零成本。

## 运行环境观察

系统PATH中的python只是Windows Store占位符；py与uv尚未安装为系统命令。本次使用Codex附带Python 3.12.14建立隔离环境，uv 0.13.1仅保留在var/cache/uv-bootstrap，不修改系统Python。新设备按README安装uv，再使用锁文件安装。Node辅助解析尚未实现，本机已检测到Node可执行入口，并有可用的附带Node v24.19.0。

参考：[uv项目管理](https://docs.astral.sh/uv/guides/projects/)、[FastAPI入口](https://fastapi.tiangolo.com/tutorial/first-steps/)、[Pydantic Settings](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/)、[Vue SFC解析包](https://github.com/vuejs/core/tree/main/packages/compiler-sfc)。

## 验证结果

全部在2026-10-19完成。环境：Windows、Python3.12.14、uv0.13.1；初次验证环境曾锁定24个包（含验证工具）；用户随后要求验证材料不入库，现业务uv.lock仅维护运行依赖，FastAPI0.146.0、Pydantic Settings2.16.0、Uvicorn0.54.0、pytest9.1.1、Ruff0.17.1。

| 检查 | 实际结果 |
| --- | --- |
| uv lock及sync --locked | 通过；项目依赖安装到.venv |
| Ruff check与format --check | 通过 |
| pytest（本机测试临时目录） | 18 passed；覆盖真实HTTP启动/退出、配置优先级/错误、缺失试点、Git根目录与固定commit |
| CLI --help / --version | 退出0；版本knowledge-ci 0.1.0 |
| CLI check-config --require-pilot | 退出0；主基线77e9634、vue-typescript、Recall，mock/外发false/预算0 |
| uv build --offline --no-sources | sdist与wheel均成功 |
| 安装包内容核验 | wheel9个文件、sdist10个文件；不含.env、var、Git仓库或字节码缓存 |
| 独立环境安装 | 由锁文件导出带哈希依赖，离线安装到var/tmp/t01-clean-env，再安装wheel；导入来自该环境site-packages而非src |
| 独立环境复验 | 同样18 passed；验证结束清理临时环境 |

本机沙箱默认临时目录权限不足，首次pytest在准备目录时失败，未进入断言；使用项目内隔离目录并以必要本机权限复跑通过。这是验证环境限制，代码没有绕过权限检查。

上述为T01首次完成的历史验证；测试代码现迁入Git忽略的var/local-checks/，测试工具不再写入业务pyproject/uv.lock。本地验证说明留在该目录；独立安装复验步骤为：uv export --locked --all-groups --no-emit-project导出带哈希清单，uv venv建立空环境，uv pip sync --require-hashes安装清单，再uv pip install --no-deps安装构建wheel，最后从该解释器运行测试。临时目录均限定在var/tmp。

T01实际消耗记录为本次AI协作会话，未把2天估算写成已投入2个人日；Recall可在任务记录补充实际人日。未自动提交、推送或切换分支，原HTML和试点源码未修改。

## 用户追加的仓库边界

2026-10-19用户明确要求测试等验证材料不进入仓库。已将原tests迁入var/local-checks/tests/，从业务pyproject移除测试工具依赖及pytest/Ruff配置，并更新Git忽略和后续任务路径。原有18项通过记录保留为历史证据；应用业务逻辑与已选试点保持不变。
