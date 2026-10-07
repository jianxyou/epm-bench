# 相关工作与 gap 备忘（2026-09-23）

43 篇过了一遍（全部核对过 arXiv 标题和作者）。按"它测什么 / agent 是不是自己在世界里动 / 有没有测撤回后照做 / 自变量 / 判分"五项筛。

## 一句话结论

**没有人做过**：把 LLM agent 放进 3D 家居模拟器，给一条延迟指令，触发在视野外出现，在配对集里撤回它，让 agent 自己跑，从世界状态读它有没有照做——同时把"意图怎么存"当自变量。

最近的两篇（PM-Bench、TriggerBench）是"同一个问题、不同设定、不同判分"；Shen et al. 是机制层面的同路人。没有直接竞争者。

## 六类工作，各差在哪

### 1. 前瞻记忆基准（同一个问题）
| 篇 | 做了什么 | 差在哪 |
|---|---|---|
| **PM-Bench** (Liu & Gabriel, 2607.12385) | 文字"虚拟一周"，有 cancel/override/reschedule 共 11 个更新事件；**定义了 "update violation"（取消后按旧版本做）但全文没报这个数**；只报了"更新后新版本的命中率 47%" | 只有 2 个 cancel 事件；每步是"问它选哪些任务 ID"，Set-F1 判分；不是自己在世界里动；记忆干预是 agent 变体（ledger / heartbeat），不是控制意图表示 |
| **TriggerBench** (Zhang et al., 2606.23459) | 聊天里先给约束、后给触发；Neg-Clean 变体中途把约束解除，正确行为是闭嘴。GPT-5.2：约束在时 98% 提醒，解除后只 44% 闭嘴。比了 RAG/A-MEM/Mem0/Letta | 回一句话不是动作；GPT-4o 当裁判；"解除"是"风险被预先处理掉了"，不是用户明确说"不用了"；没有取消早/晚的时序 |
| NLSI (NAACL'24)、SAGE、SimuHome (ICLR'26 oral)、SMH-Bench、ProAgentBench、StreamMemBench | 常驻指令 / 智能家居定时任务 / 主动助手 | 都没有撤回；SimuHome 的延迟动作注册在设备自动化层，不在 agent 记忆里 |

### 2. 撤回 / 更新在记忆系统里的处理（同一个机制）
| 篇 | 做了什么 | 差在哪 |
|---|---|---|
| **Shen et al. "Revoked but Still Authoritative"** (2609.08258) | 5 个记忆后端（Graphiti/Zep/mem0/langmem/cognee）× 9 模型：被撤销的策略照样被检索 81/81，不安全动作 43%；加检索守门 → 0% | 单次策略决策，没有环境、没有延迟线索、没有具身；修法是"检索时拦"，我们是"原地改写" |
| **Yao et al. "Forgetting Without Restarting"** (2609.04875) | 字符串删掉了，行为里 80% 还在用（string 0 次 vs 行为 80%） | 是 unlearning 方法；对话/工具 agent；支持我们"判分要看行为不看话"的论点 |
| STALE (2605.06527)、Sun & He (2608.01619) | "检索到了更新、行为没跟上"（IPA gap，最好 55%） | 聊天；失效是隐式的（后来观察到），不是明确取消 |
| Memora/FAMA (ACL'26 Findings)、MemoryAgentBench、LongMemEval、MemConflict、Supersede、Nakayashiki 2608.25553 | 事实/偏好的更新与失效，QA 判分 | 全是事实，不是义务；全是回答，不是动作 |
| GateMem、Control-Plane Placement | 显式删除请求后的泄漏 | 访问控制视角 |

### 3. 任务中途用户改主意（动作层面）
| 篇 | 做了什么 | 差在哪 |
|---|---|---|
| **InterruptBench** (Zou et al., 2604.00892) | WebArena 上 6 个模型，有"撤回要求"这一类打断，功能性判分 | 打断是即时的、在带内的；只测最终意图是否达成，**没有"执行了被撤回要求"的指标**；不变记忆设计 |
| RefuteBench、LLMs Get Lost in Evolving User Intent | 聊天里用户反馈/改意图 | 没有世界、没有延迟线索 |

### 4. 停止指令 / 可纠正性
| 篇 | 做了什么 | 差在哪 |
|---|---|---|
| Munirathinam 2606.06460 | 实时 SSH/K8s 里发 halt：OpenAI 模型 0/40 停下 | "全停"不是"只放弃这一件、其余照做" |
| Palisade shutdown resistance (2509.14260)、Leong 2608.28502 | 关机指令、指令仲裁 | 安全框架，不是意图记账 |

### 5. 具身记忆
KARMA、WorldLines (EMNLP'26)、BeliefMem、MEMORA、Analytic Concept-Centric Memory、RoboGraph、Chameleon（真机操作里的 PM）——**没有一篇撤回过指令**。

### 6. 判分方法批评（支持我们"世界状态判分"）
Gaming the Judge (2601.14691)：动作不变只改 CoT，LLM 裁判假阳性涨 90%。Unreliable Progress Bar (2609.08589)：agent 自报进度不可靠。加上 Yao 的 80% vs 0%——这三篇是我们拒绝 LLM 裁判和自报的依据。

### 7. BDI × LLM
ChatBDI (AAMAS'25) 是接口工作；Cariani 2024 是哲学论述。**没人实证测过 LLM agent 的意图放弃**——Bratman / Cohen–Levesque 的"承诺可以被撤销"这个框架在 AAMAS 还空着。

## 我们为什么要写（motivation 三句）

1. **现象已被发现，但只在"回话"层面。** TriggerBench 44%、PM-Bench 定义了却没量。一个机器人不是被问"你会不会做"，是自己走过去做。这两者差多少，没人量过——我们量了：选择题式判分放过 53% 的违规。
2. **原因被归到模型或系统，没被归到表示。** 大家比的是模型（8 个）或整套系统（Mem0 vs Letta）。我们把信息对齐，只动"意图怎么存"，六个家族同一个模型从 56% 到 7%。他们报的 precision–recall 权衡，在我们这里不存在。
3. **具身场景一篇没有。** 五六篇具身记忆基准，没有一篇撤回过指令。而撤回在具身场景最要紧：动作改变世界，不能撤销。

## 审稿人最可能的三问和回答

- **"PM-Bench 已经定义了 update violation，你们只是补了它没报的数？"** — 它 2 个 cancel 事件、任务 ID 判分、文字周历；我们 480 对配对集、世界状态判分、具身、表示做自变量。不是补一张表，是换了测量。
- **"TriggerBench 已经比过 Mem0/Letta 了。"** — 它比系统，我们比表示；它 GPT-4o 判分，我们从世界状态读；它没有取消时序；它的结论是"有权衡"，我们证明权衡是记账造成的。
- **"Shen et al. 六周前已经说撤销不生效。"** — 同路人，引为 convergent evidence。他们是单次决策 + 检索层原因；我们是延迟线索 + 自主动作 + 行为后果，修法从"检索拦截"推广到"原地改写"。

## 要引进论文的新文献（已核对）
InterruptBench 全作者、Chameleon 全作者（bib 里原来是 Anonymous）、Memora/FAMA、STALE、SimuHome、Munirathinam、Palisade shutdown、Nakayashiki、AgentAbstain、Gaming the Judge、Unreliable Progress Bar、ChatBDI、Cariani 2024（这两条不在 arXiv，作者顺序待核）。
