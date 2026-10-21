# 0009：T03 合成历史复现规格与预期

- 日期：2026-10-21；规格版本：`t03-v1`。
- 编号：0002～0008已在任务计划中预留给后续决策，使用0009避免冲突。
- 目的：为 T04～T18 及 T25～T27 提供共同的场景编号、固定语义和人工预期，不依赖真实仓库、外部模型或业务事故资料。
- 保留策略：Recall 已明确选择沿用现行规范，仅保留本文的复现规格和预期结果；生成器、JSON 样例、测试代码、合成仓库与报告在本次验证后删除。
- 本文描述后续模块的输入/输出约定。解析、依赖图、排名、证据采集和模型生成尚未实现，不能把人工预期当作其实际运行结果。

## 选择与架构影响

测试材料必须用完删除，因此不在源码中建立 fixtures 包，也不增加开发专用 CLI、业务依赖或锁文件条目。后续任务按本文在 `var/tmp/local-checks/` 重建临时材料，沿用场景名及预期语义，完成验证后清理。

“相同生成器的两次运行得到完全相同的 Git 对象”和“将来按规格重建等价场景”是两个验收层次。本轮核对 commit/tree/blob 的逐字节一致性；后续重建以历史关系、源码语义和以下 oracle 为准。本文不保存完整样例源码，不能仅凭记录的 SHA 恢复已删除的 Git 对象；不得声称这是可直接复用的持久夹具包。

不改 T02 领域契约，不提前定义排名或依赖边的业务 schema。表内类型标签是黄金预期的语义标记；T06～T10 落地时需映射到各模块正式输出。

## 合成 Git 历史

采用 Git SHA-1 对象格式、单分支 `main`、6 个线性提交，无 remote、merge、submodule、符号链接或目标项目依赖。文件全部为 UTF-8、LF、末尾换行和普通 `100644` blob。作者及邮箱仅使用合成身份 `fixture-a/b@example.invalid`；提交者统一为 `fixture-bot <fixture-bot@example.invalid>`。

| 场景 | UTC 提交时间 | 作者 | 提交主题 | 变化与必须满足的关系 |
| --- | --- | --- | --- | --- |
| baseline | 2025-01-01 00:00:00 | fixture-a | baseline: synthetic request flow | 初始5文件；策略直接比较 attempts ≤ 3，尚无 MAX_ATTEMPTS；请求模块、入口及两类 Vue SFC |
| constraint | 2025-01-02 00:00:00 | fixture-a | constraint: cap total attempts at two | policy 增加 MAX_ATTEMPTS=2，比较仍为 attempts ≤ MAX_ATTEMPTS；不能宣称已正确实现两次总尝试 |
| fix | 2025-01-03 00:00:00 | fixture-b | fix: stop after the second completed attempt | 比较改为 attempts < MAX_ATTEMPTS；两次已完成尝试后停止重试从本提交起成立 |
| rename | 2025-01-04 00:00:00 | fixture-a | rename: request module becomes network | request.ts → network.ts；保持模块字节不变，main 仅调整导入目标；Git `--find-renames=100%` 必须识别 R100 |
| format | 2025-01-05 00:00:00 | fixture-b | style: indent retry policy | policy 仅 return 行缩进从2空格改成4空格；blob 改变，`git diff --ignore-all-space` 为空 |
| boundaries | 2025-01-06 00:00:00 | fixture-a | boundaries: imports, silent fallback and misleading strings | 增加6文件：空 catch、双模块循环、两类动态 import、未解析依赖、字符串/注释误导内容；共11文件，作为默认固定快照 |

作者时间与提交者时间相同，使用 Unix 时间戳 `1735689600 + 提交序号 × 86400`、时区 `+0000`。时间属于合成历史，与本次实际执行日期区分。

生成器须使用参数数组调用 Git，禁用 hooks、签名及 init 模板，固定换行与 commit cleanup。清除继承的 `GIT_*`，隔离系统/全局 Git 配置、全局 attributes、工作树与 index；用另一份开启 autocrlf、签名、默认 SHA-256 的配置验证显式 SHA-1 和本地约定仍生效。不得运行生成仓库内的 JS/TS、包管理器、插件、构建或脚本。

## 默认快照的符号和原文件位置

源码根为 `src/`，别名 `@/` 映射到 `src/`；路径大小写保留。行号从1开始，结束行包含在内。以下是必须出现的代表性符号；T06 还应提取11个文件模块、两个组件及支持的变量声明，不以本表代替全部符号列表。

| 路径 | 名称 / 类型 | 原文件行号 | export / SFC 块 |
| --- | --- | --- | --- |
| src/policy.ts | canRetry / function | 3～5 | 是 |
| src/network.ts | request / function | 3～5 | 是 |
| src/Panel.vue | retry / function | 7～9 | 否 / script_setup |
| src/LegacyPanel.vue | label / method | 7～9 | 否 / script |
| src/legacy.js | readLegacy / function | 1～7 | 是 |
| src/cycle/a.ts | a / function | 2～4 | 是 |
| src/cycle/b.ts | b / function | 2～4 | 是 |
| src/loader.ts | loadFeature / function | 1～3 | 是 |
| src/loader.ts | loadPlugin / function | 4～6 | 是 |

`Panel.vue` 依次为 template（1～3行）、script setup（开始标签第4行、导入第5行、attempts 第6行、retry 第7～9行、结束标签第10行）、style（11～13行）。`LegacyPanel.vue` 为 template 第1行、script 开始标签第2行、vue 导入第3行、defineComponent 第4～11行、结束标签第12行。script 块内容以开始标签后的换行起算：setup 的块内第4行、普通 script 的块内第6行均映射到原文件第7行。T06 必须使用实际解析器位置验证，不能把源码字符串定位检查算作 AST 验收。

## import 边与排除项

每行代表一个来源明确的 import；重复关系去重规则留给 T07 正式契约。此样例无重复 import，因此入度按唯一来源模块计数。

| 来源及行号 | specifier | 目标 / 语义 |
| --- | --- | --- |
| src/network.ts:1 | @/policy | src/policy.ts / static |
| src/Panel.vue:5 | @/policy | src/policy.ts / static |
| src/main.ts:1 | @/network | src/network.ts / static |
| src/main.ts:2 | ./Panel.vue | src/Panel.vue / static |
| src/LegacyPanel.vue:3 | vue | external，不能当作仓库内文件 |
| src/cycle/a.ts:1 | ./b | src/cycle/b.ts / static |
| src/cycle/b.ts:1 | ./a | src/cycle/a.ts / static |
| src/loader.ts:2 | ./feature | src/feature.ts / dynamic_literal |
| src/loader.ts:5 | 含 name 插值的 ./plugins/${name}.ts | unknown_dynamic，不虚构具体目标 |
| src/loader.ts:7 | ./missing | unknown_missing，目标不在快照中 |

唯一强连通循环为 `{src/cycle/a.ts, src/cycle/b.ts}`。`strings.ts` 含带 `https://`、`//`、`/* */` 的普通/模板字符串，字符串中的伪 import('./ghost')、空 catch 文本及注释中的 import './comment-only'；它们均不能产生边或空 catch 候选。

这里只是 import 图，不是完整调用图。动态关系及缺失模块应保留 unknown；静态无法证明的行为不能自动判定安全。

## Git 信号和示例 Top-K

观察窗口覆盖这6次提交，包含首次添加、纯改名与格式提交；改名链采用 `--follow --find-renames=100%`。每文件每提交只计一次，不按增删行数重复计数；贡献者按固定作者身份去重。

| 默认快照路径 | 变更提交数 | 作者数 | 仓库内入度 |
| --- | --- | --- | --- |
| src/policy.ts | 4 | 2 | 2 |
| src/network.ts（含 request.ts 历史） | 2 | 1 | 1 |
| src/main.ts | 2 | 1 | 0 |
| src/Panel.vue | 1 | 1 | 1 |
| src/LegacyPanel.vue | 1 | 1 | 0 |
| src/cycle/a.ts | 1 | 1 | 1 |
| src/cycle/b.ts | 1 | 1 | 1 |
| src/feature.ts | 1 | 1 | 1 |
| src/legacy.js | 1 | 1 | 0 |
| src/loader.ts | 1 | 1 | 0 |
| src/strings.ts | 1 | 1 | 0 |

示例分析配置：frequency / contributors / indegree 权重分别为 0.5 / 0.25 / 0.25，分别除以本样例的最大值 4 / 2 / 2 后加权；K=3。分数相同按保留大小写的仓库相对 POSIX 路径字典序升序。

预期前三名为 policy（1.0）、network（0.5）、Panel（0.375）；main 同为0.375，因 `src/Panel.vue` 排在 `src/main.ts` 之前而居第4。policy 作者为 fixture-a/b，其余文件只有 fixture-a。历史只有6次提交，事故/工单/业务损失信号均缺失；不得把缺失事故信息当作零风险。这是 T08 可消费的一套示例配置，尚未冻结生产权重或实现排名器。

## 证据、知识与追问预期

所有 ID 使用 T02 的不透明字符串约束；源码路径、scope 与 locator 不含机器绝对路径。code 的 content_hash 为整个文件原始字节的 SHA-256，excerpt 仅展示原文件指定行；commit 哈希所指产物为 `git cat-file commit` 的完整原始提交内容；human_answer 为完整回答的 UTF-8 字节。哈希统一使用 `sha256:` 前缀。

| 场景 | 可观察事实与证据位置 | 缺口 / 默认阻断追问 | 最早适用版本 |
| --- | --- | --- | --- |
| threshold | policy:1～5，MAX_ATTEMPTS=2 且比较为 <；constraint/fix 的原始 Git 记录 | 为什么总尝试次数为2，是否有上游配额或兼容约束？代码不能自行证明业务原因 | fix |
| silent_catch | legacy.js:4～5，为空 catch；函数在解析失败后返回 null | 是否允许静默降级、适用范围和可观测性要求是什么？不能仅凭空 catch 断言业务缺陷 | boundaries |
| cycle | cycle/a.ts:1～4 与 cycle/b.ts:1～4 的相互 import | 循环是否是认可的初始化约束，还是需要拆分？不能推断已经发生运行故障 | boundaries |

每类均保留 observed 事实和 inferred 原因的区别；业务动机不明时设 claim.gap、evidence_sufficiency=partial、risk=unknown、失效条件 unknown 并解释缺口。模型分数不能把 inferred 改成 observed。

三类追问均应演示 open → answered → resolved：使用明确标注“合成人工回答”的记录，回答先进入 answered，此时仍阻断；采纳为 HumanAnswerLocator 指向当前 question 的证据后才 resolved。resolved 不会清除旧修订的 claim.gap，不会补齐充分度、创建新内容或通过审核；须显式生成引用人工证据的新修订，设 human_confirmed、充分度、负责人，重新批准当前 content_hash 后才能发布。

同时验证回答不足 → 重开（保留回答）、取消（保留原因）、旧修订的 blocking 问题继续阻断新修订；取消问题不消除结论的证据缺口。合成回答只能证明这套流程，不能算作真实试点知识或 A04 的有效知识数量。

负面预期：缺失 evidence_id、跨 snapshot 引用、human_confirmed 仅引用代码、旧 content_hash 批准必须被拒绝；fix 不可成为 baseline 的历史证据；默认快照中 request.ts 已不存在，不得沿用旧路径定位。commit 祖先关系和 blob/行内容须由采集器校验，T02 schema 本身不访问 Git。

## 本轮对象指纹

以下是本轮同一生成器双运行所得的固定值，用于核对本轮确定性；对象本体按约定删除，未来语义等价重建不强求复原这些 SHA。

| 场景 | commit SHA | tree SHA |
| --- | --- | --- |
| baseline | 8d048abd6319f30957dfe903e2415972ffb57d5d | dddba73e00b7ba3c5e9d2900c71b50ea79633989 |
| constraint | 4052301148d268903d41470ce3a203ec744d5ba4 | de538e5c3324ff5542de61e3eab8db35ce948b64 |
| fix | 605538012b2960cfa75051cf85552226aa5510df | 711df72287faee79b9e7162caf3742a0a6902d0b |
| rename | ca43463334dd6548728c15f978448c479c27bf07 | 83aa83fca279b32a00e4ede1cb67c10dd537d814 |
| format | 3a6b7351ccc6224f9434378513b2541696d829ec | a0f505fa6eb240d50503d3f9b6bfa42faa93ec6a |
| boundaries | 4961b1060b74d3e308043a99fd96f8eb1a18d8d3 | 2f2cae2c6f571940883aa072ad66c3e66b2ed3d8 |

临时预期清单按 T02 canonical JSON 规则的哈希为 `sha256:a71fe6e800204c768c4d7846b01fbc5732253a7e6a3d6f6fc098baf2f11a194e`；它用于标识本轮输入，不是文件下载位置或已保存产物的承诺。

## 重建、验证和清理约定

1. 在已约定的 `var/tmp/local-checks/tests/fixtures/` 临时编写生成器与 JSON oracle，集成检查放 `tests/integration/`；所有运行仓库仅放 `var/tmp/local-checks/runs/` 的独立子目录。
2. 按上述历史规格生成两套仓库，一套路径含中文和空格，另一套带冲突的 Git 环境/全局配置；比较全部 commit/tree/blob、作者/时间/提交说明与逐文件历史，不从待测实现反推 oracle。
3. 用 T02 schema 实例化快照、两套分析配置、源码符号、证据和知识/追问；验证发布成功路径及负面边界。T06/T07/T08 尚未实现时仅检查 oracle 的源码行位置、引用和算术一致性。
4. 正常退出、使用方异常和历史生成中途异常均清理本次生成目录；拒绝覆盖既有目录。删除前核对绝对路径为 runs 的直接子目录，拒绝符号链接/junction/reparse point；不得清理调用者提供的其他目录或真实试点。
5. Windows 使用普通 mkdir 继承项目 ACL 创建唯一目录；本机 Python tempfile 的 mode=700 曾导致沙箱无法读写。该环境限制不能误报为业务失败，也不能遗留失败目录。
6. 验证结束删除整个 `var/tmp/local-checks/`，检查 Git 不追踪测试材料、打包范围不包含 var、业务源码及锁文件未发生无关改动；执行环境、命令和结论统一写入 TASK_PLAN。

本次执行结果以 [TASK_PLAN.md 第6节](../../TASK_PLAN.md) 为准。本文保留复现协议，后续重建不得声称已删除的脚本仍可直接运行。
