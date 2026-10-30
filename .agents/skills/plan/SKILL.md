---
name: plan
description: "出方案 / 实施计划。把任务拆成小到每步有明确完成标准的小任务，带勾逐条推进。 / Produce an implementation plan: break the task into small tasks, each with a clear done-when and a checkbox."
---

# Plan / 出方案

## 目标 / Goal

把"要做的事"拆成一张清单，每个条目小到能独立完成、且能判断"做完了没"。方案要先过独立评审，再给用户确认；确认前不写任何代码。

Break "the thing to build" into a checklist where each item is small enough to finish independently and judge "done or not". The plan passes an independent review first, then goes to the user for confirmation; no code before that.

## 拆任务的标准 / How small is small

- 每个任务 = 一件事，能一句话说清"做完会是什么样"。
- **列 todo 要逐条对着需求**：`analyze` 列出来的每一条（它编的 R1、R2…），**每一条都要有任务负责，一条不漏**，对照表里写清是哪个 R 由哪个任务、用哪条 A 标准兜住；**修 bug 就把根因拆成编号的点（B1、B2…），按同一张表逐条对照**。漏了不算合格方案。
- 每个任务带一个**完成标准**（done-when）——**它就是这个任务的验收用例**（给编号，如 A1/A2），并且**标类型**：`单测` / `端到端` / `人工`。
  - `单测`：一条命令 → 看到必须出现的结果
  - `端到端`：同样是一条命令，但验的是真实的端到端路径
  - `人工`：界面上点、肉眼看的，或要人拍板的
- **每条验收用例还要写"落点"——它落在仓库的哪个文件**（写清路径）：
  - `单测` / `端到端` → 落在**测试文件**（第 ④ 步本来就把测试写在那里）
  - `人工` → 落在**一份清单文件**（跟着仓库走）
  - 项目里已有用例目录**就用它**（如 `docs/acceptance/测试用例/`）；没有就用 `docs/acceptance/`
  > 为什么：见 dev-harness 仓库的 `docs/rationale.md`《为什么验收用例要有落点》（**卡不含该文件**）。
- **"看到什么"必须是必须出现的东西**（`3 passed`、`eventId 非空`、页面上出现某字段），**不能是"没报错"**——三种类型都适用。
- **`单测` / `端到端`**：`<命令>` → 看到 `<必须出现的结果>`。命令要**碰到本任务改的行为**；`curl /health → 200` 这种跟任务无关的绿命令不算。**能写成命令的就必须写成命令**——只有确实写不成的才标 `人工`。
- **`人工`**：写明**谁、在哪里、做什么、看到什么**，并留下产物（截图 / 接口返回 / DOM 片段）。**"谁"必须是非实现者**（用户，或另一个独立 agent）——"我点了一下看到了"等于没写，产物也要由 TA 产生。要人拍板的事（选方案、spike 调研）属于这一类：验收人写“用户”，看到写“用户书面选定 X”。
- 反例：“接管功能正常”“页面对了”没法核；`npm test` → `0 failed` 也不算（零测试匹配时照样过）。
- 三种类型都套不上的，**不算一个合格的任务，回去重写**。
  > 纯文案/纯文档类任务也**照样要有带类型的完成标准**：能核的写成命令（如 `grep -c "第 10 条" README.md` → 看到 `1`，或渲染后截图对比），核不了的写 `人工`（**用户** 读 <哪份文件>，确认 <措辞是否符合要求>，留 <书面回复>）。**“这活没法验”不是豁免理由。**
- 任务之间尽量独立，能一个个做、一个个验证。
- （为什么完成标准要这么严：见 dev-harness 仓库的 `docs/rationale.md`，**卡不含该文件**。）
- 拆到你觉得"这个还能再拆吗"时停一下——再小就是噪音了。
- **被退回重做时（先读账本，再出方案）**：如果这一轮是 `review` 判回来的（《第 7 步后的分叉》），**开干前先读账本**——特别是上一轮的 `analyze`/`reproduce`/`plan`/`tdd` 记录和评审写下的失败判词。
  > **这是新方案的第一道输入，不是可选项**：上一版为什么没过，决定了这一版方案该长什么样；不读就出方案，等于把上一轮的错法再拆一遍任务。
  > **你是一个"干净的脑子"**：退回重做时 orchestrator 会**另起一个全新的子 agent** 跑入口那一步 + 本步，只给它账本、原始需求和代码现状，**不给它上一版的方案**。所以**别去翻上一版方案"接着改"**——**先假设上一版的方向是错的**，从账本的事实出发重出方案。（**方向是在这一步定的，所以只换入口卡没用，本步必须一起换**。）
  > **入口那一步（`reproduce`/`analyze`）已经交过一张「教训 → 处置 → 判词」表**（见那两张卡的《退回来的活怎么干》）——**那张表就是你出方案的约束**：
  > - 判**"已规避"**的：方案里必须真有一条任务在兜它，并在逐条对照表里写明是哪条；
  > - 判**"仍然存在"**的：方案里必须写清**为什么这次不构成问题**——**评审员会直接查这条**（见《流程》第 4 步），写不出理由就是没处置；
  > - 判**"已不适用"**的：说清为什么不适用了（需求变了？根因被推翻了？）。
  >
  > 修 bug 时还要对上上一版的根因复核结论：**复核后仍然成立的 B** 必须仍被方案覆盖；**被推翻的 B** 不许再出现在方案里。
  > **入口那一步还没交这张表 → 停下让它补**，不许自己替它编一张。

## 影响面 / Impact on what already works

**出方案时必须回答："这次要改的既有东西，还有谁在用？"** **这是本步的必交内容，和"每个任务要有完成标准"同级。**

> **文档不是影响面**：`README`/`docs`/设计文档里的调用关系、模块图**不许用文档里的描述充当影响面**——文档只当背景参考；清单里每一条使用方都必须是**你搜到的、能指到 `文件:行` 的代码**。

1. **列出本次要改/要用的每一个既有符号**——既有函数、接口（含返回结构）、字段、数据表/缓存键、配置项。**清单从 `git diff` 来，不是从记忆来**：先跑 `git diff HEAD~1 --name-only`（第一轮还没有 `HEAD~1` 就跑 `git status`）看这次动了哪些文件，逐个判断里面有没有既有符号——**别凭印象说"我没动老的"**。
2. **逐个搜它的使用方，搜法要多样**：直接搜名字只是第一步，还要想到**间接引用**——配置/脚本里写的、字符串拼出来的、被继承或实现的、被反射/注解/路由表登记的。**能想到的搜法都要用**。
3. **结果按四类写，不许合并**：
   - **搜到了**：列出使用方（附搜索命令 + 结果）。这些使用方就是本次要回归的对象。
   - **搜了没有**：写明**用了哪些搜法**、没搜到什么。光写"没有其他调用方"不算——那看不出你搜到什么程度。
   - **搜不到**：跨仓库、外部服务、依赖运行时的行为（并发 / 时序 / 真实数据）——**写明"无法确认"**、**写明你试过哪些搜法（附搜索命令 + 结果，和"搜了没有"一样要给证据）**、**写清为什么搜不了**（哪个系统/哪个仓库不在本仓库范围内）、并写清**谁可能受影响**。这类**不许写成"应该没问题"**。
   - **本地验不了**：能搜到使用方、但**本地没有测试覆盖、或本地环境起不来**（需要真实数据/权限/上下游）——写清是哪个使用方、为什么要到测试环境才能验。**这类最后会变成⑨要点的清单**。
     > **不许把"我没搜"写成"搜不到"**：`搜不到` 指**客观上搜不了**（信息不在本仓库），不是"懒得搜"。分不清时按搜过的算——**先搜，搜不动再归这类**。
4. **"没动既有符号"要拿证据说话，不能自己声明**：只有**这次改动的文件里确实没有既有符号**时才算免。要交的是**清单，不是一句话**——`git diff` 涉及的**每个文件**都列出来，写成三列：

   | 文件 | 这个文件里有哪些既有符号 | 为什么它们没被改 |
   |---|---|---|
   | `<路径>` | `<函数/接口/字段/常量>` | <只新增、未改动 / 新增代码没有接管它 / …> |

   **只新增文件也要列**：新代码有没有挂到某个既有入口上（新路由接管了某个路径、新分支改了某个既有判断、新注册项顶替了原实现）——**这类"没改文件但改了行为"最容易漏**。**评审会拿 `git show HEAD` / `git diff HEAD~1` 逐行对着这张表核**：改动里出现了既有符号（**含既有的入口被新代码接管**）而清单说"未改动" → **按诚信问题打回**。
   > **这一条是豁免，不是默认值**：拿不准某个东西算不算"既有符号"（加可选参数？改返回结构？改配置默认值？）→ **按"是"处理**，列进去。豁免的举证责任在写的人。
5. **尽力搜 + 如实报**：漏了使用方是能力问题，写得比实际搜到的更满（"没搜"写成"搜不到"、"搜不到"写成"无影响"）是诚信问题——**后者在⑦/⑨验收时直接打回**。

> 这份清单往下传：**④照着它回归**（改动方自己验）、**⑤跑 `单测` 能覆盖的那些**、**⑥跑 `端到端` 才能覆盖的那些**、**⑦照着它独立核对**、**⑨把本地够不着的逐条验掉**——所以它要**跟着代码走**，写进 commit message 的 `## 影响面` 小节（见 `orchestrate` 卡《commit 的时机》）。（为什么：见 dev-harness 仓库的 `docs/rationale.md`，**卡不含该文件**。）

**The plan must answer: "who else uses the existing things this change touches?"** **This is required output of this step, on the same footing as "every task needs a done-when".**

> **A document is not an impact list**: call graphs and module diagrams taken from `README`/`docs`/design notes do not count — **never let a document's description stand in for the impact list**. Documents are background only; every usage you list must be code you searched for and can point at with `file:line`.

1. **List every existing symbol this change touches or relies on** — existing functions, interfaces (including response shapes), fields, tables/cache keys, config items. **Derive the list from `git diff`, not from memory**: run `git diff HEAD~1 --name-only` first (on the very first round there is no `HEAD~1` — use `git status`) to see which files this change touches, then decide file by file whether an existing symbol is in there — **never assert "I touched nothing old" from recollection**.
2. **Search each one's callers, using several kinds of search**: searching the name is only step one — also think about **indirect references**: written in config/scripts, built from strings, inherited or implemented, registered via reflection/annotations/route tables. **Use every search you can think of.**
3. **Report the result in four categories; never merge them**:
   - **Found**: list the dependents (with the search command + its result). These are what this round must regress.
   - **Searched, found nothing**: say **which searches you ran** and what came back empty. "There are no other callers" alone is not enough — it does not show how hard you looked.
   - **Cannot search**: cross-repo, external services, runtime-dependent behavior (concurrency / ordering / real data) — **write "cannot confirm"**, **write which searches you tried (with the search command and its result — same evidence bar as "searched, nothing")**, **say why it cannot be searched** (which system / which repo is outside this one), and who may be affected. **Never write "should be fine" here.**
   - **Cannot verify locally**: the dependents *were* found, but **there is no local test coverage, or the local environment cannot run it** (needs real data / permissions / upstream+downstream) — say which dependent and why it takes the test environment. **These become the list ⑨ must click through.**
     > **Never write "cannot search" for "I did not search"**: `cannot search` means it is **objectively unsearchable** (the information is not in this repo), not that searching was skipped. When unsure, treat it as searchable — **search first, and only file it here once searching genuinely fails**.
4. **"I changed no existing symbol" needs evidence, not a declaration**: the exemption applies only when **the files this change touches really contain no existing symbol**. What you hand over is an **inventory, not a sentence** — list **every file** `git diff` touches, in three columns:

   | File | Which existing symbols it holds | Why none was changed |
   |---|---|---|
   | `<path>` | `<function / interface / field / constant>` | <only added, not modified / the new code does not take it over / …> |

   **A new-files-only diff still needs the table**: does the new code hang off an existing entry point (a new route taking over a path, a new branch changing an existing condition, a new registration displacing the original implementation)? **This "no file changed but the behaviour did" case is the easiest to miss.** **The reviewer checks this table line by line against `git show HEAD` / `git diff HEAD~1`**: an existing symbol appears in the diff (**including an existing entry point taken over by new code**) while the list says "none changed" → **sent back as an integrity problem**.
   > **This is an exemption, not a default**: if you are unsure whether something counts as an "existing symbol" (adding an optional parameter? changing a response shape? changing a config default?) → **treat it as one and list it**. The burden of proof sits with whoever claims the exemption.
5. **Search hard + report honestly**: missing a caller is a capability gap; claiming more than you searched (writing "cannot search" for "did not search", or "no impact" for "cannot search") is an integrity gap — **and the latter is sent back at ⑦/⑨**.

> The list is handed down the chain: **④ regresses against it** (the implementer's own check), **⑤ runs what `unit` cases cover**, **⑥ runs what only an `e2e` case can reach**, **⑦ cross-checks it independently**, **⑨ verifies on test whatever was unreachable locally** — so it must **travel with the code**, in the commit message's `## 影响面` section (see the `orchestrate` card, "When to commit"). (Why: see the repo's `docs/rationale.md` — installed cards **do not ship** that file.)

## 架构落位 / Where this change sits

**出方案时必须回答："这次改动放在哪、跨不跨边界、动没动契约？"** **这也是本步的必交内容**——架构要在**这里**定，不能等写代码时再想（那时位置已经定了）。

要写五件事：

1. **进哪些具体路径/glob**，以及**预期不改**的路径清单。（这两张清单是⑦比对 diff 的依据。）
2. **跨模块调用的入口符号全名**——本次会跨模块调的那些入口，逐个写全名（**含本次新增的入口**；本次不许调这些之外的东西，见 `tdd` 第 8.2 条）。
3. **依赖粒度**声明（按文件 / 包 / 构建模块），以及**本次新增的依赖边**（谁 → 谁）。
4. **持久化数据的 owner 符号**——本次会写的每份数据，它是谁管的（唯一写入口是谁）。不碰持久化就写"不涉及"＋为什么。
5. **8.1–8.9 逐条结论**：涉及的写"打算怎么守"，**并写出该条查法要引用的那个具体声明**（8.3 的唯一入口 / 8.8 的对外公开面 / 8.9 的写入入口）；**8.4 涉及的还要写出"破坏面 + 迁移路径 + 迁移期"三项**（缺一即违例，⑦按落位核）；不涉及的写"不涉及"＋**为什么**。

> **"不涉及"要拿证据说话**：每条"不涉及"必须附**仓库级搜索命令 + 原始输出**（与《影响面》的"搜了没有"同一条标准）。
> **8.1 / 8.3 / 8.5 / 8.7 的"不涉及"不许只用"在 diff 里没看到"来证明**——这四条的违例可能**整个在 diff 之外**（本来就存在的反向依赖边、仓库里已有的封装、别处的第二个写入口）。
> **裁定规则：9 条里凡标"不涉及"却没给命令的 → 本步不算完成。**

> **动态装配**：项目如果有 **DI 容器 / 注册表 / 路由表 / 配置开关 / 消息订阅**，**静态读依赖不够**——真实调用关系可能只写在那处装配里。
> 这时要在第 2、3 项里**指名那个具体的装配文件/清单**（如 Spring `@Configuration`、`AndroidManifest`、路由表文件），核那一处是不是同一条边；
> **核不了的按《影响面》"搜不到"的标准写证据行**（读不了什么、为什么），并按 `orchestrate`《停下必须自证》第②条**交用户裁定**——不许默认静态结论成立。

> 这节往下传：**④照着它写**、**⑦拿它对着 diff 核**——所以它也要**跟着代码走**，写进 commit message 的 `## 架构落位` 小节。**落位中途要改**（比如 ④ 实现时发现了真会发生的失败路径、或本次自造孤儿的清理牵动了别的文件）→ **账本追加一条修订记录（不重写历史），commit message 同步**，⑦ 比对**修订后**的声明。（为什么：见 dev-harness 仓库的 `docs/rationale.md`，**卡不含该文件**。）

**The plan must answer: "where does this change sit, which boundary does it cross, does it touch a contract?"** **This is also required output of this step** — architecture is settled **here**, not while writing code (by then the placement is already chosen).

Write five things:

1. **Which concrete paths/globs it lands in**, plus the list of paths it is **expected not to touch**. (These two lists are what ⑦ compares the diff against.)
2. **The entry symbols it will call across modules**, by full name (**including entries this change adds**; nothing else may be called — see `tdd` 8.2).
3. The **dependency granularity** (file / package / build module) and **the dependency edges this change adds** (who → whom).
4. The **owner symbol** of each piece of persisted data it writes (who is the single write entry). If it writes none, say "not engaged" and why.
5. **A verdict for each of 8.1–8.9**: engaged → how you will honour it, **naming the specific declaration that rule's check cites** (8.3's sole entry / 8.8's public face / 8.9's write entry); **8.4 engaged also states breakage surface + migration path + migration window** (missing any is a violation; ⑦ checks it against the 落位); not engaged → why.

> **"Not engaged" needs evidence**: every "not engaged" carries a **repo-level search command + raw output** (the same bar as 《影响面》's "searched, nothing").
> **8.1 / 8.3 / 8.5 / 8.7 may not be cleared by "I did not see it in the diff" alone** — their violations can live **entirely outside the diff** (a pre-existing reverse edge, an existing wrapper, a second write site elsewhere).
> **Verdict rule: any of the nine marked "not engaged" without a command means this step is not done.**

> **Dynamic assembly**: if the project has a **DI container / registry / route table / config switch / message subscription**, **reading dependencies statically is not enough** — the real wiring may exist only in that assembly.
> Then items 2 and 3 must **name that specific assembly file/list** (Spring `@Configuration`, `AndroidManifest`, a router table file) and check whether it is the same edge;
> **what cannot be checked gets an evidence line to 《影响面》's "cannot search" standard** (what could not be read, and why) and goes to the user per `orchestrate`'s《停下必须自证》case ② — **never assume the static conclusion holds**.

> This section is handed down too: **④ writes against it**, **⑦ checks it against the diff** — so it also **travels with the code**, in the commit message's `## 架构落位` section. **If the 落位 has to change mid-round** (④ hit a failure path that will really happen, or cleaning up an orphan this change created touched another file) → **append an amendment record to the ledger (never rewrite history) and sync the commit message**; ⑦ compares against the **amended** declaration. (Why: see the repo's `docs/rationale.md` — installed cards **do not ship** that file.)

Each task = one thing with a one-line "done looks like".
- **The todo list must follow the requirement item by item**: every item `analyze` listed (its R1, R2, … ids) must have a task owning it, **none left out**, and the mapping table must say which R is covered by which task with which A-id done-when; **for a bug fix, number the root-cause points (B1, B2, …) and map them in that same table**. A plan with a gap is not a valid plan.
- Each task carries a **done-when** — **that done-when *is* the task's acceptance case** (give it an id, e.g. A1/A2) — **and it is typed**: `unit` / `e2e` / `manual`.
  - `unit`: one command → see a result that must appear
  - `e2e`: also one command, but exercising the real end-to-end path
  - `manual`: something you click or eyeball, or something a human must decide
- **Every acceptance case also states its "landing spot" — which file in the repo it lands in** (give the path):
  - `unit` / `e2e` → the **test file** (step ④ already writes the tests there)
  - `manual` → a **checklist file** that travels with the repo
  - If the project already has a case directory, **use it** (e.g. `docs/acceptance/测试用例/`); otherwise use `docs/acceptance/`
  > Why: see 《为什么验收用例要有落点》 in the dev-harness repo's `docs/rationale.md` (**cards do not ship this file**).
- **What you "see" must be something that must appear** (`3 passed`, a non-empty `eventId`, a field present on the page) — **"no error" does not count**. This binds all three types.
- **`unit` / `e2e`**: `<command>` → see `<a result that must appear>`. The command must **exercise the behaviour this task changed**; an unrelated green command like `curl /health → 200` does not count. **If it can be a command it must be one** — only what genuinely can't is marked `manual`.
- **`manual`**: write **who, where, what they do, what they see**, and leave an artifact (screenshot / API response / DOM snippet). **"Who" must be a non-implementer** (the user, or a separate independent agent) — "I clicked it and it looked right" is not a done-when, and the artifact must come from that person too. Something a human must decide (choosing an option, a spike) belongs here: acceptance is “the user”, and "see" is “the user picks X in writing”.
- Bad: “takeover works”, “the page is right”; `npm test` → `0 failed` also fails (it passes with zero tests matched).
- If none of the three types fits, it is **not a valid task — rewrite it**.
  > Pure copy / pure documentation tasks **still need a typed done-when**: if it is checkable, make it a command (e.g. `grep -c "第 10 条" README.md` → see `1`, or a rendered screenshot diff); if it is not, write `manual` (**the user** reads <which file>, confirms <whether the wording is right>, leaves <a written reply>). **“This can't be verified” is not an exemption.**
- Tasks should be as independent as possible. Stop splitting when further splitting becomes noise.
- (Why the done-when must be this strict: see `docs/rationale.md` in the dev-harness repo — **cards do not ship this file**.)
- **When this is a redo after a fallback — read the ledger before planning**: if `review` sent this back (see "Branch after step 7"), **read the ledger before doing anything** — above all the previous round's `analyze`/`reproduce`/`plan`/`tdd` entries and the reviewer's failure verdicts.
  > **This is the new plan's first input, not an option**: why the previous version failed determines what this version's plan must look like; planning without reading it just re-splits the previous round's mistake into tasks.
  > **You are a "clean head"**: on a redo the orchestrator **spawns a brand-new subagent** to run the entry step + this step, given only the ledger, the original requirement and the code as it stands — **not the previous plan**. So **do not go dig up the previous plan and "continue" it** — **assume the previous direction was wrong** and re-plan from the ledger's facts. (**Direction is set at this step, so swapping only the entry card is useless — this step must be swapped too.**)
  > **The entry step (`reproduce`/`analyze`) has already produced a 「lesson → handling → verdict」 table** (see "How to redo a sent-back task" in those two cards) — **that table is a constraint on your plan**:
  > - verdict **"avoided"**: the plan must contain a task that actually covers it, and the mapping table must say which one;
  > - verdict **"still present"**: the plan must say **why it is not a problem this time** — **the reviewer checks this directly** (see step 4 under Steps); no justification means it was not handled;
  > - verdict **"no longer applies"**: say why (requirement changed? root cause overturned?).
  >
  > For a bug fix, also line up with the previous root-cause re-check: a **B that still holds** must still be covered by the plan; an **overturned B** must not reappear in it.
  > **If the entry step has not produced that table → stop and have it produced**, never invent one on its behalf.

## 流程 / Steps

1. 想清楚目标：这个任务做完，用户能看到/得到什么？
2. 拆任务，逐个写清"完成标准"（含类型）。
3. **做影响面分析**——按《影响面》那一节做（四类都要写全）；**同时做《架构落位》**（五件事都要写，9 条逐条给结论）。
4. **派一个独立 agent 评审这份方案**（不给它你的实现记忆）：
   - **完整性**：需求（或根因）里每一条，方案里有没有任务负责？任务写得够不够细、**能不能直接照着做**？
   - **过度设计**：有没有加没必要的校验、哈希、抽象层、预留扩展点？
   - **落点写没写**：每条 A 用例有没有写清**落在仓库哪个文件**（`单测`/`端到端` → 测试文件，`人工` → 清单文件）？**缺落点就不算过**——收尾时没有它对不了账。
   - **影响面可不可信**：抽它列的使用方**自己去搜一遍**——有没有明显该搜到的没搜到？四类划分是不是在回避（把"没搜"写成"搜不到"，把"搜不到"写成"无影响"）？**"未改动既有符号"这句豁免，对着 diff 核过了吗？** **这是核对事实，不是猜。**
   - **架构落位可不可信**：**逐项自己去搜、附命令与结果**（照上一条的做法）——①**进哪些路径**：这些路径真实存在吗？和要改的东西是同一个模块/层吗？"预期不改"清单可执行吗？②**入口符号**：grep 它们**真实存在**、且是公开的吗？③**依赖粒度**：和仓库结构一致吗（有构建模块就必须按模块判）？④**owner**：grep 它**存在且唯一**吗？⑤**9 条结论**：对着文件清单**自己重判一遍**，专抓"标了不涉及、其实涉及"；每条"不涉及"**有没有仓库级命令**，以及 8.1/8.3/8.5/8.7 是不是**只拿 diff 在搪塞**。**这是核对事实，不是猜。**
   - **退回重做时再加一条——教训有没有真被处置**：把入口那步的「教训 → 处置 → 判词」表一并交给它，**逐条核**：判"已规避"的在方案里有没有对应任务？判"仍然存在"的，方案给的"为什么不构成问题"**站不站得住**？判"已不适用"的理由成不成立？**对不上就打回。**
   - 要求它**逐条对照**（要求 → 对应任务 → 判词），并指到具体行。**只回一句"完整、无过度设计"不算评审。**
   - 不过 → **回第 2 步（任务拆得不对）、第 3 步（影响面不对 / 用例没写落点）、或第 3 步的《架构落位》（落位本身不实：路径不对、入口符号不存在、9 条结论没证据）改**，按失败的是哪一条；改完再评。
   > 这是第③步**内部**的闸门，**不占新编号**（全仓"第⑤/⑥/⑦/⑨步"的引用不受影响）。评审要在**给用户确认之前**跑完。
5. 把清单写成 markdown 勾选框，交给用户确认。
6. 用户点头后才进入 `tdd`（写代码）。

1. Clarify the goal: what does the user see/get when this is done?
2. Split into tasks, each with a typed done-when.
3. **Do the impact analysis** — follow the "Impact on what already works" section (all four categories); **and do 《架构落位》** (all five items, with a verdict for each of the nine).
4. **Spawn an independent agent to review the plan** (it gets no implementation memory):
   - **Completeness**: does every requirement item (or root-cause point) have a task? Is each task detailed enough to **be executed directly from the plan**?
   - **Over-design**: unnecessary validation, hashing, abstraction layers, extension points?
   - **Are the landing spots recorded** (every A case: which file it lands in; `unit`/`e2e` → test file, `manual` → checklist file) — **a missing landing spot fails this gate**, because closure has nothing to reconcile against.
   - **Is the impact list credible**: pick the dependents it lists and **go search again yourself** — is anything obviously missing? Are the four categories being used to dodge (writing "cannot search" for "did not search"; writing "no impact" for something that cannot be searched)? **Was the "no existing symbol changed" exemption checked against the diff?** **This is fact-checking, not guessing.**
   - **Is the 架构落位 credible**: **search each item yourself and attach your commands and results** (same method as the row above) — ①**paths**: do they exist, and are they the same module/layer as what changes? Is the "expected not to touch" list actionable? ②**entry symbols**: do they **really exist** and are they public? ③**granularity**: does it match the repo's structure (if build modules exist it must be module-level)? ④**owner**: is it **unique**? ⑤**the nine verdicts**: **re-judge them yourself against the file list**, hunting for "marked not-engaged but actually engaged"; does every "not engaged" carry a **repo-level command**, and are 8.1/8.3/8.5/8.7 being waved through **with diff-only evidence**? **This is fact-checking, not guessing.**
   - **On a redo, one more axis — were the lessons actually handled**: hand it the entry step's 「lesson → handling → verdict」 table and have it **check every row**: does an "avoided" lesson have a task covering it? Is the "still present" justification **sound**? Does the "no longer applies" reason hold up? **Any mismatch → send the plan back.**
   - Require a **line-by-line mapping** (requirement → owning task → verdict) citing specific lines. **A one-line "complete, no over-design" is not a review.**
   - Fail → **go back to step 2 (the tasks are wrong), step 3 (the impact list is wrong, or a case has no landing spot), or step 3's 《架构落位》 (the 落位 itself is unsound: wrong paths, a non-existent entry symbol, nine verdicts without evidence)**, whichever failed; then review again.
   > This is a gate **inside** step ③ — it does **not** take a new step number (the hardcoded "step ⑤/⑥/⑦/⑨" references elsewhere stay valid). It must finish **before** the plan goes to the user.
5. Write the list as markdown checkboxes and show it to the user.
6. Only after the user agrees, move to `tdd`.

## 输出格式 / Format

```markdown
# 方案：<任务名>

## 目标
<一句话说清做完后是什么样>

## 逐条对照
<做需求：照 `analyze` 的 R 编号；修 bug：把根因拆成编号的点（B1、B2…），同样逐条对照。>
| 编号 | 内容 | 由哪个任务负责 | 这条方案的完成标准（A 编号） |
|---|---|---|---|
| R1 | <照抄 `analyze` 里的第一条> | <任务 2> | <A2> |

## 任务清单
- [ ] 1. <任务一>（A1，单测）— 完成标准：`<命令>` → 看到 `<必须出现的结果>`
      落点：`<测试文件路径>`
- [ ] 2. <任务二>（A2，人工）— 完成标准：<谁，非实现者> 在 <哪里> 做 <什么>，看到 <什么>（留 <产物>）
      落点：`<清单文件路径>`
- [ ] 3. ...

## 影响面 / Impact on what already works
| 既有符号 | 搜到的使用方（附搜索命令） | 本次怎么回归它 |
|---|---|---|
| <函数/接口/字段/表/配置> | <A、B（`grep ...`）> | <A 对应的完成标准编号 / 到测试环境点某处> |

搜了没有：<用了哪些搜法，没找到什么>
搜不到：<试过哪些搜法 + 为什么搜不了（哪个系统/仓库不在范围内）+ "无法确认" + 谁可能受影响>
本地验不了：<哪个使用方、为什么本地验不了（没测试覆盖 / 环境起不来）>

## 架构落位 / Where this change sits
进哪些路径：<具体路径 / glob>
预期不改：<路径清单>
跨模块调用的入口符号：<全名，逗号分隔；没有就写"无">
依赖粒度：<文件 / 包 / 构建模块>；本次新增的依赖边：<A → B；没有就写"无">
持久化数据 owner：<每份数据 + 它的唯一写入口符号；不碰就写"不涉及" + 为什么>

| 基线 | 结论 | 涉及的：打算怎么守 + 引用的那个具体声明；不涉及的：为什么（附仓库级搜索命令） |
|---|---|---|
| 8.1 循环依赖 | 涉及 / 不涉及 | <...> |
| 8.2 绕过入口 | 涉及 / 不涉及 | <...> |
| 8.3 横切件单入口 | 涉及 / 不涉及 | <唯一入口 / 为什么不涉及（`grep ...`）> |
| 8.4 公共契约 | 涉及 / 不涉及 | <...> |
| 8.5 数据单写入口 | 涉及 / 不涉及 | <owner 符号 / 为什么不涉及（`grep ...`）> |
| 8.6 失败当成功 | 涉及 / 不涉及 | <...> |
| 8.7 加载期配置 | 涉及 / 不涉及 | <为什么不涉及（`grep ...`）> |
| 8.8 可见性 | 涉及 / 不涉及 | <对外公开面 / 为什么不涉及> |
| 8.9 共享状态写入 | 涉及 / 不涉及 | <写入入口 / 为什么不涉及> |

动态装配：<项目有没有 DI/注册表/路由表/配置开关/消息订阅？有就指名那个文件并核；核不了的写"搜不到"+证据行>

<!-- 确实没动任何既有符号时，整段换成：本次未改动既有符号 + 那张三列表（文件 / 里面有哪些既有符号 / 为什么没被改）。 -->

<!-- 被退回重做时才写这一段：照抄入口那步的表，补上"这一版哪条任务兜它"，交给方案评审逐条核。

## 上一轮教训的处置
| 账本里的教训 | 入口那步的判词 | 这一版由谁兜 / 为什么不构成问题 |
|---|---|---|
| <照抄> | 已规避 | <任务 N> |
| <照抄> | 仍然存在 | <为什么这次不构成问题> |
| <照抄> | 已不适用 | <为什么不适用了> |
-->

## 风险场景 / Risk scenarios
<这个改动会碰到哪些容易坏、且可能静默出错的情况？逐条列出，并写清“遇到它会怎样”。>
- 复用/共享：同一资源被重复取用、多处共享时，会不会拿到过时/错配的结果？
- 并发/重复触发：同一操作被并发或重复触发时，会不会错乱？
- 异常/失败路径：外部调用失败、中途报错时，状态会不会回不去/hang 住？
- 空值/边界：空链、越界、非法值、首次/末次时行为对不对？
- 超时对齐：前后端/上下游的等待时间、超时是否一致？
```

- 风险场景不是抽象地写“要考虑边界”——**要具体到“这个改动里，哪个地方会被复用/并发/异常”，并说明遇到时会怎样（尤其会不会静默出错）。**
- 若某个改动确实不涉及这些（如纯文案），写一句“不涉及”即可，不用硬凑。
  > **“不涉及”只作用在风险场景这一栏**，跟上面每个任务的完成标准无关——文案类任务的完成标准照样要写（见前文）。

- Risk scenarios are not an abstract "consider edge cases" — be concrete about **where in this change reuse/concurrency/failure can happen, and how it fails silently when it does**.
- If none apply (e.g. pure copy change), just say so; don't pad.
  > **“None apply” is scoped to the risk-scenario section only** — it says nothing about each task's done-when, which is still required (see above).

## 证据要求 / Evidence

完成时账本必须含：拆出的任务清单 + 每个任务的完成标准（含类型）**和落点** + **逐条对照（R / B 编号 → 任务 → A 编号）** + **影响面清单（既有符号 → 使用方 → 怎么回归它；四类都要：搜到了 / 搜了没有 / 搜不到 / 本地验不了）** + **架构落位（五件事 + 8.1–8.9 逐条结论；每条"不涉及"附仓库级搜索命令）** + **独立评审的逐条判词（含对影响面与架构落位的核对结论，附评审自己的命令与结果）** + 用户确认的痕迹 + 风险场景清单。**被退回重做时还要有**：新方案里的「上一轮教训的处置」表 + 评审对这张表**逐条**的核验结论。
> **缺影响面清单 = 本步不算完成**（确实没改既有符号的，写"本次未改动既有符号"+**依据**：`git diff` 涉及哪些文件、为什么里面没有既有符号——**光写结论不算**）。**影响面清单还要写进 commit message 的 `## 影响面` 小节**——账本会删，它不能跟着消失。
> **缺架构落位、或 9 条里有标"不涉及"却没给仓库级命令的 = 本步不算完成。**（8.1/8.3/8.5/8.7 的"不涉及"**不许只用"在 diff 里没看到"来证明**。）**架构落位也要写进 commit message 的 `## 架构落位` 小节。**
> **被退回重做时，缺这张表、或缺评审对它的逐条核验结论 = 本步不算完成，不许给用户确认、不许进 ④。**（与入口那步"没有这张表就不许进 `plan`"对称——不能这头堵住、那头漏掉。）
> 不记账 = 本步不算完成，不能进入下一步。

When done, the ledger must include: the task list, each task's typed done-when **and its landing spot**, **the item-by-item mapping (R / B id → task → A id)**, **the impact list (existing symbol → dependents → how each will be regressed; all four categories: found / searched-nothing / cannot-search / cannot-verify-locally)**, **the 架构落位 (all five items plus a verdict for each of 8.1–8.9; every "not engaged" carrying a repo-level search command)**, **the independent review's item-by-item verdicts (including its cross-check of the impact list and of the 架构落位, with the reviewer's own commands and results)**, the user's confirmation, and the risk-scenario list. **On a redo after a fallback**, it must also include the new plan's 「how the previous round's lessons are handled」 table, plus the reviewer's **row-by-row** verdict on that table.
> **A missing impact list means this step is not done.** If the change genuinely touches no existing symbol, the exemption must carry its **grounds** (which files the diff touches, and why none holds an existing symbol) — **not the bare sentence** "no existing symbols changed"; the reviewer verifies it against the diff. **The impact list also goes into the commit message's `## 影响面` section** — the ledger gets deleted; this list must not vanish with it.
> **A missing 架构落位 — or any of the nine marked "not engaged" without a repo-level command — means this step is not done.** (For 8.1/8.3/8.5/8.7, "not engaged" **may not** be proved by "I did not see it in the diff" alone.) **The 架构落位 also goes into the commit message's `## 架构落位` section.**
> **On a redo, a missing table — or a missing row-by-row verdict on it — means this step is not done: do not show the plan to the user and do not proceed to ④.** (Symmetric with the entry step's "no table, no entry to `plan`" — one end must not be sealed while the other leaks.)
> No ledger entry = this step is not done; do not proceed to the next step.

## 记进度 / Log progress

- 方案写好后，先去账本记一条（状态：进行中）——写清楚拆了哪几个任务、各自完成标准，标注**待用户确认**。
- 用户点头后，再补一条：方案已确认，进开发。

- After writing the plan, log one ledger entry (status: 进行中) — list the tasks and their done-when, marked **awaiting user confirmation**.
- After the user agrees, log another entry: plan confirmed, moving to implementation.
