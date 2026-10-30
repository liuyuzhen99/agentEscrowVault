---
name: orchestrate
description: "开发迭代总指挥。每次开工先读本卡，判断当前是修 bug 还是做需求，然后按流程推进并汇报进度。 / Orchestration entry. Read this first every session, determine bug-vs-feature, then advance the flow and report progress."
---

# Orchestrate / 总指挥

你的工作不是自己埋头写代码，而是当"总指挥"：搞清楚现在干到哪一步、下一步该干嘛、每步干完怎么算完，并且把进度写进进度账本给人看。

You are the orchestrator, not a lone coder. Your job is to know which step we are on, which step is next, what "done" means for each step, and to log progress into the ledger for humans to read.

## 开工第一件事 / First thing every session

1. 读 `progress/` 目录，找到当前正在进行的任务账本（无则说明本次要新开一个任务）。
2. 判断任务类型：修 bug 还是做需求（判断不出就问用户）。
3. 新建/打开账本，并**向用户一句话汇报**：现在是哪个任务、走到哪一步、下一步要做什么。
4. **在账本建好、且向用户汇报之前，禁止读任何文件的正文内容（含源代码）去定位/分析；禁止改任何业务文件；禁止加载任何干活卡。只允许：看目录和文件名、读 `progress/` 里的账本正文、读账本模板、**把 `progress/` 加进本项目 `.gitignore`**、建账本、向用户汇报。**
5. 做完以上，才开始读代码、干活。

1. Read `progress/` to find the in-progress task ledger (or start a new task if none exists).
2. Determine task type: bug fix or feature (if unclear, ask the user).
3. Create/open the ledger and **report to the user in one line**: which task, which step, what's next.
4. **Until the ledger is created AND the user has been notified, do NOT read the body of any file (including source code) to locate/analyze; do NOT change any business file; do NOT load any execution skill. Only these are allowed: listing directories and file names, reading the ledger file(s) under `progress/`, reading the ledger template, **adding `progress/` to this project's `.gitignore`**, creating the ledger, and reporting to the user.**
5. Only then start reading code and doing the work.

## 流程 / The Flow

### 开端岔路 / Entry fork

- **修 bug / Bug fix**：用 `reproduce`（①复现、②定位原因）
- **做需求 / Feature**：用 `analyze`（①看懂需求、②分析现有代码）

### 汇合后的主干 / Shared trunk

> **每步交接铁律 / The step-handoff rule**：每一步做完后、进入下一步之前，必须先做两件事——①在账本里追加一条本步记录（干了啥 / 结果 / 下一步），②向用户一句话报进度。**报完就立即继续，不许就地停下来等用户。没记账、没报进度，不许进入下一步；报了进度但任务没完，也不许停。**
>
> **After finishing a step and before moving on, you MUST first: (1) append one ledger entry (what you did / result / next), (2) report progress to the user in one line. Then keep going immediately — do not stop and wait for the user. No ledger entry + no report means you may not proceed; a report without a finished task also does not mean you may stop.**

> **汇报不等于收工 / A progress report is not a stopping point**：进度汇报只是让用户看得见，**不是本轮的终点**。任务没做完、也没卡住、也不需要用户拍板时，**汇报完必须紧接着继续干活**，不能把“发了一条进度汇报”当成停下来等的理由。
>
> **停下必须自证 / Stopping must be justified**：任何时候你想停下等用户，**必须在停下来那条消息里写明你属于下面哪一条**（写明**已完成 / 需确认 / 卡住**中的一个词 + 一句原因，不要只写符号）。**归不进这三条的（如“已完成一个阶段/一个批次”“已停在进度点”），一律不许停，继续干**；含糊地说“已停在进度点”而引不出具体一条，就是违规。
> 只有三种情况才可以停下来等：①任务已全部完成（真正收尾，账本可删）；②确实需要用户补充信息或确认/拍板（**基本只发生在第 3 步出方案，以及需求/根因不确定需问用户；其他步骤默认不需要确认——例外：发布等有副作用的步骤仍必须先经用户点头，见本卡《可信度原则》）**；③真的卡住（遇到了自己解不了的阻塞，必须写明卡在哪）。除此之外，一律继续。
>
> **什么时候算“卡住”（第③条）/ When does it count as blocked (case ③)**：**环境/工具链级阻塞**（如测试容器起不来、依赖版本不兼容、密钥/网络缺失）不是靠“再试一次”能解决的。判定门槛：**同一个阻塞连续重试 2–3 次仍不通过**，就停下判定为“卡住”，**不要再继续重试**（子 agent 派发失败按 `review` 卡“重派一次”的口径走）。重试前**先看上一次的日志/退出状态**：若上次已经报错/已退出（如 `[ERROR]`、进程已结束），**不要用 `sleep` 干等一个已经结束的过程**——`sleep` 只能用于等待“确实还在跑”的任务（本地：进程存活 / 日志在增长；**等远端流水线这类本地看不到进程的活，则用状态查询轮询，每次看状态是否还在推进**）。
> **判定为卡住而停下时**，除按上文《停下必须自证》写明“卡住”一词外，还必须一次说清（也记进账本）：①卡在哪（什么环境/工具链问题）；②试过哪几种解法、为何都不通；③需要用户做什么（修环境 / 授权换验证方式 / 决定跳过）。**不得自行改变方案或降级验收标准来绕过卡住**（例如擅自跳过 e2e、拿 mock 冒充真实验证）——绕不绕、怎么绕，由用户定。
> 反面：**代码/方案类问题自己解决，不算卡住、不停**（确需用户拍板时走第②条；反复引入回归时走 `review` 卡的**退回重做**，也不是"卡住"）。

> **A progress report exists to make progress visible — it is NOT the end of your turn.** If the task is not finished, you are not blocked, and no user decision is required, then **after reporting you must immediately keep working**; never treat “I posted a progress update” as a reason to stop and wait.
>
> **Stopping must be justified.** Whenever you want to stop and wait for the user, you MUST state in that very message which of the three cases you fall under (write one of **completed / needs-confirmation / blocked** plus one line why — words, not just symbols). **If it doesn't fit one of the three (e.g. “finished a phase/batch”, “stopped at a progress point”), you may NOT stop — keep working.** Vague “I've stopped at a progress point” with no specific case is a violation.
> Only three cases justify stopping: (1) the task is fully complete (true closure, ledger may be deleted); (2) a user must supply missing information or give a confirmation/decision (**essentially only at step 3 (plan) or when requirement/root cause is unclear and you must ask**; other steps need no confirmation by default — **exception: side-effecting steps such as deploy still require explicit user approval, see the “Trust principle”**); (3) you are truly blocked (state exactly where). Otherwise, keep going.
>
> **When does it count as blocked (case ③)?** An **environment/toolchain blocker** (e.g. test containers won't start, incompatible dependency versions, missing credentials/network) is not something “one more try” will fix. Threshold: if the **same blocker persists after 2–3 consecutive retries**, stop and mark it blocked — **do not keep retrying** (for subagent spawn failures, follow the `review` card's “re-spawn once” rule). Before retrying, **check the previous run's log/exit status first**: if it already failed/exited (e.g. `[ERROR]`, process gone), **do NOT `sleep`-wait on a process that has already ended** — `sleep` is only for waiting on something genuinely still running (**locally: live process / growing log; for remote pipelines where no local process exists, poll a status query and check whether it's still progressing**).
> **When stopping as blocked**, besides marking “blocked” per the “Stopping must be justified” rule above, say all three in one message (and log them in the ledger): (1) where it's blocked (what environment/toolchain issue); (2) which workarounds you tried and why each failed; (3) what you need from the user (fix the environment / authorize another verification path / decide to skip). **You must NOT change the approach or downgrade the acceptance bar to get around a blocker** (e.g. silently skipping e2e, passing mocks off as real verification) — whether and how to work around it is the user's call.
> Conversely: **code/design problems you solve yourself — those are not “blocked”; don't stop** (if a real user decision is needed, go through case ②; when regressions keep appearing, use the `review` card's **fall back and redo** — that is not “blocked” either).

3. 出方案 / Produce a plan
4. 开发 / Implement
5. 测试 / Test
6. 本地验证 / Local verification
7. 独立评审 / Independent review

### ③ 内部的闸门：方案独立评审 / Gate inside step ③: independent plan review

- 方案写完后、**给用户确认之前**，先派一个**独立 agent**（不带实现记忆）评审这份方案。
- **评审查哪几条、按什么口径，唯一出处是 `plan` 卡《流程》第 4 步**（完整性 / 过度设计 / **影响面可不可信** / **架构落位可不可信** / 退回重做时的"教训有没有真被处置"）——**本卡不复述，避免两处清单各自漂移**（照 `plan` 卡那份发给评审员）。
- 不过 → 回 ③ 改，改完再评。
- **这是 ③ 内部的闸门，不占新步骤编号**（本卡和其它卡里"第⑤/⑥/⑦/⑨步"的引用不受影响）。

- After the plan is written and **before it goes to the user**, spawn an **independent agent** (no implementation memory) to review it.
- **Which axes it checks, and with what wording, has exactly one source: step 4 of the `plan` card's Steps** (completeness / over-design / **whether the impact list is credible** / **whether the 架构落位 is credible** / on a redo, whether the lessons were actually handled) — **not restated here, so the two checklists cannot drift apart** (brief the reviewer from the `plan` card's copy).
- Fail → back to ③, then review again.
- **This is a gate inside ③ — it takes no new step number** (the "step ⑤/⑥/⑦/⑨" references in this and other cards stay valid).

### 第 7 步后的分叉 / Branch after step 7

- **退回重做（先看这条）/ Fall back and redo (check this first)**：⑦ **反复出现"上一轮的修改新引入的回归"** → 说明**方案层面有问题**，再补是救不回来的。**退回任务开头重做**：做需求 → `analyze`，修 bug → `reproduce`。**触发条件只有这一条，不看改了几轮。**
  > **不在这条里的打回不算退回重做**：例如**依据不实 / 只引文档没给代码位置**——那是**补依据**（账本追加修订记录，回缺的那一步补上），照 `review` 铁律第 9 条走，**不要 reset 掉本轮代码**。
  > **退回不是"重新做一遍"，是"带着上一轮的教训重做"**：被打回的那一步**开干前必须先读账本**（含 `review` 每次判 FAIL 写进去的判词），交一张**教训 → 处置 → 判词**表，再出新的清单和方案；**修 bug 还要逐条证伪上一版的根因 B1、B2…**。**`plan` 也吃这张表**：它出方案时不许把判"仍然存在"的教训放着不管，而且要交给方案评审**逐条核**。细节见 `analyze`/`reproduce` 卡的《退回来的活怎么干》与 `plan` 卡《拆任务的标准》最后一条。**没读账本就重做 = 把上一轮的死法再走一遍。**
- **具体五步看 `review` 卡**（那里是唯一出处，本卡不重复）：存 wip 分支 → 确认没误伤 → `git reset --hard HEAD~1` → 核对账本还在 → 对着账本重做。**回退时禁止 `git clean`**（`-fdx` 里的 `-x` 会把被忽略的文件一起删掉，而账本就在 `progress/` 里）。之后照常走 **方案独立评审 → 用户确认 → 实现**。
- **回退目标见 `review` 卡《铁律》第 5/6 条**；**退回不做次数判据**——判据是"在收敛"（"假设变了没有"），触发 `review` 卡《铁律》第 8 条信号时**报告用户、但不停下干等**（信号清单只在 `review` 卡里列，本卡不重复）。

- **Fall back and redo (check this first)**: step ⑦ — **a "regression newly introduced by the previous round's fix" keeps coming back** → **the approach itself is at fault** and more patching won't save it. **Go back to the task's entry point**: feature → `analyze`, bug fix → `reproduce`. **This is the only trigger; it does not count rounds.**
  > **A FAIL that is none of these is not a redo**: e.g. **grounds that do not hold up / a document cited with no code location** — that is **supplying the grounds** (append a revision entry to the ledger, go back to the step that is short) per rule 9 of `review`; **do not reset this round's code**.
  > **A fallback is not "do it again" — it is "redo it carrying the previous round's lessons"**: before the sent-back step does anything it **must read the ledger** (including every FAIL verdict `review` wrote into it), produce a **lesson → handling → verdict** table, and only then the new list and plan; **a bug fix must also falsify the previous root causes B1, B2 …** **`plan` consumes that table too**: it may not leave a "still present" lesson unhandled, and it must hand the table to its own plan reviewer for a **row-by-row** check. See "How to redo a sent-back task" in the `analyze`/`reproduce` cards and the last bullet of the `plan` card's "How small is small". **Redoing without reading the ledger just replays the previous round's way of dying.**
  > **The whole redo chain runs on a "clean head"**: a fallback exists to **change direction**, and **direction is set in `plan`** — so **swapping only the entry card is useless: the entry card *and* `plan` must be run by a brand-new subagent**, given only the ledger + the original requirement + the code as it stands, **not the previous plan and not its self-explanation**, and told to **assume the previous direction was wrong**. Rationale and mechanics: rule 6, step 5 of the `review` card.
  > **Fallbacks have no limit and no counter** — **each one must prove it is converging**; the test is **"did the hypothesis change"**, not "how many tries"; re-splitting the same tasks without touching an assumption = spinning in place. When the signals in rule 8 of the `review` card fire, **write it in the ledger and report to the user, then keep doing what you still can — a notification, not a halt.** (The signals themselves are listed only in `review`; do not re-list them here.)
- **The five steps live in the `review` card** (single source; not duplicated here): park a wip branch → check you won't clobber anything → `git reset --hard HEAD~1` → confirm the ledger survived → redo against the ledger. **Never `git clean` when falling back** (the `-x` in `-fdx` deletes ignored files too, and the ledger is one of them in `progress/`). Then continue as usual: **plan review → user confirmation → implementation**.
- **The fallback target is in rules 5–6 of the `review` card**; **fallbacks have no limit and no counter**, but each must prove it is converging (the test is "did the hypothesis change"), and when rule 8's signals fire, **report to the user but do not halt**.

- **要发环境的任务**（功能/改动）：8. 发布测试环境 / Deploy to test environment；9. 测试环境复测 + 交付判断 / Re-verify and judge delivery（**真正的终点**：用例全过 **且** 需求逐条交对 **且** 影响面清单逐条处理完）
- **纯仓库内任务**（文档/内部文件）：**没有⑧⑨**，所以 **⑦ pass → 完成**——但此时 **⑦ 要连"按需求逐条判交没交对"一起判**（它的"真实环境"就是仓库本身）。

- **Tasks needing an environment** (features/changes): steps 8-9 — deploy, then **re-verify AND judge delivery (the real finish line)**: all cases pass **and** every requirement item delivered **and** every impact-list entry dealt with.
- **Repo-only tasks** (docs/internal files): **there is no ⑧⑨**, so **⑦ pass → done** — but in that case **⑦ must also judge delivery against the requirement item by item** (the repo itself is its real environment).

### commit 的时机 / When to commit

- **一轮一个 commit**：第④步（开发）做完**立刻 commit 一次**，⑤测试 / ⑥本地验证 / ⑦独立评审都在这个 commit 之上跑。（为什么提前：见 dev-harness 仓库的 `docs/rationale.md`，**卡不含该文件**。）
- **一轮只有一个 commit，返修一律 amend 进去**：④ 那一次 commit 之后，**到下一轮 ④ 之前不再新增 commit**——⑤/⑥/⑦ 期间任何返修（改代码、补测试、按评审意见改）都 `git commit --amend` 并回 ④ 那个 commit 里。这样 `HEAD` 始终是本轮唯一那个 commit，`HEAD~1` 就一定是"本轮之前"，⑦ 判回退时 `git branch wip/…` + `reset --hard HEAD~1` 才能可靠执行（见 `review` 卡《铁律 / The rules》第 6 条"固定五步"第 1 步）。
  > 证据怎么贴：要看"本轮改了什么"用 `git diff HEAD~1 --stat` / `git show --stat HEAD`（**它会随 amend 一起更新**），**不要用 `git log`**——amend 不产生新条目，`git log` 看不出本轮改了几次。账本里记的是"这一步做了什么 + 命令与原始输出"，不是 commit 列表。
- **先 commit，再贴 diff 证据**：`git show --stat HEAD` / `git diff HEAD~1 --stat` **只有在 ④ 的 commit 已经存在时**才对准本轮改动。顺序是**先把 ④ 做完并 commit，再跑这两条命令、把输出贴进账本**；先贴后 commit 的话，取到的是上一轮的东西。
- **commit message 必须带 `## 影响面` 小节**——把 `plan` 的影响面清单**跟着代码留下来**（账本会删，这份不能跟着消失）。格式：

  ```
  <一行摘要>

  ## 影响面
  - <既有符号>：使用方 <A、B>（搜法：`grep ...`）
  - <既有符号>：搜了 <哪几种搜法>，未发现其他使用方
  - <既有符号>：跨服务/外部依赖，**无法确认**（可能受影响：<谁>）
  - <既有符号>：使用方 <C>，**本地验不了**（<没测试覆盖 / 环境起不来>）
  ```

  确实没动既有符号的，写"未改动既有符号"+**依据**（`git diff` 涉及哪些文件、为什么里面没有既有符号）——**光写结论不算**，⑦会拿 diff 对着核。**为什么写进 commit**：出问题时 `git log` 是唯一还留着"这次碰过什么"的地方——账本删了，影响面清单不能也跟着没。

- **commit message 还要带 `## 架构落位` 小节**——**只放结论，不放命令与输出**（命令与原始输出留在账本里）。格式：

  ```
  ## 架构落位
  - 落位：<模块/层>（<路径或 glob>）
  - 入口：<跨模块调用走的既有入口符号；无则写"无">
  - 契约：<碰没碰公开签名/端点/schema；碰了写破坏面+迁移路径+迁移期>
  - 基线：涉及 <8.x、8.y>；不涉及 <其余>（<一句总理由>）
  ```

  9 条全不涉及也是一行合法的写法（如纯文案改动）。**为什么写进 commit**：与 `## 影响面` 同理——账本删了，"这段代码为什么放这儿、当时按哪几条基线判的"不能跟着消失。**落位中途改过**（④ 发现了真会发生的失败路径、或本次自造孤儿的清理牵动了别的文件）→ 账本追加一条修订记录（**不重写历史**），这里的结论同步成修订后的。
- 要发环境的任务：⑦ pass（**只代表代码可以发了，不代表可交付**）后继续 ⑧发布 ⑨复测+交付判断。

- **One commit per round**: commit **immediately after step ④ (implement)**; ⑤ test / ⑥ local verification / ⑦ independent review all run on top of it. (Why earlier: see `docs/rationale.md` in the dev-harness repo — **cards do not ship this file**.)
- **Exactly one commit per round; every fix is amended into it**: after ④'s single commit, **no new commit until the next round's ④** — any rework during ⑤/⑥/⑦ (code, tests, review feedback) is folded back into that one commit with `git commit --amend`. So `HEAD` is always this round's only commit and `HEAD~1` is always "before this round", which is what makes the `git branch wip/…` + `reset --hard HEAD~1` fallback in the `review` card reliable.
  > How to show evidence: to see "what this round changed" use `git diff HEAD~1 --stat` / `git show --stat HEAD` (**it follows the amend**), **not `git log`** — amending adds no entry, so `git log` cannot show how many times the round changed. The ledger records "what this step did + command and raw output", not a commit list.
- **Commit first, paste diff evidence second**: `git show --stat HEAD` / `git diff HEAD~1 --stat` only point at this round's change **once step ④'s commit exists**. So **finish step ④ and commit, then run those two commands and paste their output into the ledger**; pasting before committing picks up the previous round.
- **The commit message must carry an `## 影响面` (impact) section** — it makes `plan`'s impact list **travel with the code** (the ledger is deleted; this must not vanish with it). Shape:

  ```
  <one-line summary>

  ## 影响面
  - <existing symbol>: dependents <A, B> (search: `grep ...`)
  - <existing symbol>: ran <which searches>, found no other dependents
  - <existing symbol>: cross-service / external dependency, **cannot confirm** (may affect: <who>)
  - <existing symbol>: dependent <C>, **cannot verify locally** (<no test coverage / environment cannot run it>)
  ```

  If the change genuinely touches no existing symbol, write "no existing symbols changed" **plus its grounds** (which files the diff touches, and why none holds an existing symbol) — **the bare conclusion does not count**; ⑦ checks it against the diff. **Why in the commit**: when something breaks, `git log` is the only place still holding "what did this change touch" — the ledger is gone, and the impact list must not go with it.

- **The commit message must also carry an `## 架构落位` section** — **conclusions only, no commands or output** (those stay in the ledger). Shape:

  ```
  ## 架构落位
  - Sits in: <module/layer> (<path or glob>)
  - Entries: <the existing entry symbols cross-module calls go through; "none" if none>
  - Contracts: <whether public signatures/endpoints/schema changed; if so, breakage surface + migration path + migration window>
  - Baseline: engaged <8.x, 8.y>; not engaged <the rest> (<one-line reason>)
  ```

  "None engaged" is a valid one-liner (e.g. a copy-only change). **Why in the commit**: same as `## 影响面` — the ledger is deleted, and "why this code sits here, and which baselines were applied" must not vanish with it. **If the 落位 changed mid-round** (④ hit a failure path that will really happen, or orphan cleanup this change created touched another file) → append an amendment record to the ledger (**never rewrite history**) and sync the conclusions here to the amended version.
- Env tasks: after ⑦ passes (**that only means the code is fit to ship, not that it is deliverable**), continue to ⑧ deploy, then ⑨ re-verify + delivery judgment.

### 收尾 / Closure

- 要发环境的任务：⑨**复测通过 + 需求逐条交对** → 完成；**按《清理规则》把验收用例落进仓库，再删账本**；**发现问题** → 按性质回 `tdd`（实现问题）或 `plan`/任务入口（方向问题），改完重发再复测。
- 仓库内任务：**⑦ 独立评审 pass** → 完成；**按《清理规则》把验收用例落进仓库，再删账本**（**这类任务没有⑧⑨，"按需求判交没交对"已在⑦里判过**；commit 早在 ④ 就做了，不是终点）。
- 任务**放弃**：直接删账本（不设“已放弃”状态词）。

- Env tasks: ⑨ **re-verify passes AND every requirement item is delivered** → done; **land the acceptance cases per 《清理规则》, then delete the ledger**; issues → back to `tdd` (implementation) or `plan`/entry point (direction), fix, redeploy, re-verify.
- Repo-only tasks: **step ⑦ review passes** → done; **land the acceptance cases per 《清理规则》, then delete the ledger** (**these have no ⑧⑨, so the delivery judgment was made inside ⑦**; the commit happened back at ④ and is not the finish line).
- Abandoned tasks: delete the ledger outright (no "abandoned" status word).

## 每步的标准 / What "done" means per step

> **证据不可降级铁律 / The no-downgrade rule**：每步的“完成”只以该步要求的客观证据为准。**不许降级、不许拿近似证据冒充、不许把本步该做的事推到后面的步骤**——“测试绿了”不等于本地验证完成；“build 通过”不等于真机跑通；拿不出本步该有的证据，就老实标记“卡住”。
>
> **Every step is "done" only by its required objective evidence. Never downgrade, never substitute lookalike evidence, and never defer this step's job to a later step** — “tests green” is not local verification; “build passes” is not a real run; if you lack the step's evidence, mark it blocked honestly.

| 步 Step | 完成标准 Done when |
|---|---|
| 1 复现/看懂 | 能用自己的话讲清楚"问题是什么"或"需求要什么" |
| 2 定位/分析 | 找到了明确的根因 / 看清了现有代码现状 |
| 3 出方案 | 需求**逐条**都有任务负责、任务能**直接照着做**；**影响面清单已交**（既有符号 → 使用方 → 怎么回归；四类都要：搜到了 / 搜了没有 / 搜不到 / 本地验不了；确实没改既有符号的写"本次未改动既有符号"+**依据**）；**架构落位已交**（五件事 + 8.1–8.9 逐条结论；每条"不涉及"附**仓库级搜索命令**——**缺落位或"不涉及"没给命令 = 本步不算完成**）；**每条验收用例的落点已交**（落在仓库哪个文件——**缺落点 = 本步不算完成**，收尾时没有它对不了账）；**先过独立 agent 的方案评审**（完整 + 不过度设计 + **影响面可不可信** + **架构落位可不可信**），再**等用户确认**（写代码前唯一需要停下等确认的一步；发布等有副作用步骤除外，见《可信度原则》） |
| 4 开发 | 代码写完，先测试后写码（TDD） |
| 5 测试 | 测试全绿；需求用例里的 **`单测` 类**全过（`端到端` 类归 ⑥；`人工` 类由非实现者在 ⑥/⑨ 做） |
| 6 本地验证 | 本地隔离环境真实验证通过；带用例时 **`端到端` 类全部跑通（每条都 pass）**（须本地真端到端）。**`人工` 类由非实现者做、结果与产物进 ⑥ 建的清单文件，不进本条闸门**（但也不许跳过） |
| 7 独立评审 | **代码质量闸门**——只判**代码质量 + 测试可信度 + 架构基线**（膨胀/重复/孤儿/假绿/项目约束/逐行可追溯/**架构落位与实际 diff 对不对得上，含 8.1–8.9**）；**不判"能不能交付"**（要发环境的任务归 ⑨；纯仓库内任务没有⑧⑨，交付判断仍归本步）。派内置 reviewer 子 agent 复查（不给实现者自述）；开不了才停下告诉用户（属“停下必须自证”第③条 卡住）。**准入：第⑥步的 `端到端` 用例已全部 pass**。**判 FAIL 默认回 `tdd`**；**落位本身不实 → 回 ③ 修订落位（不许打回给实现者）**；**依据不实 / 只引文档没给代码位置 → 补依据，不算退回重做（见 `review` 铁律第 9 条）**；**只有"反复引入回归"才退回任务开头重做**（做需求→`analyze`，修 bug→`reproduce`），不停下（见《第 7 步后的分叉》） |
| commit（每轮一次） | **④开发做完立刻 commit**（一轮一个 commit，回退点固定是 `HEAD~1`）；⑤/⑥/⑦ 的返修一律 `--amend` 回这一个 commit；**commit message 必须带 `## 影响面` 小节**（把 `plan` 的清单跟着代码留下来）**和 `## 架构落位` 小节**（只放结论：落位路径 / 入口符号 / 契约 / 涉及哪几条基线——命令与输出留在账本里）；**账本贴 `git diff HEAD~1 --stat` / `git show --stat HEAD` 为证，不要贴 `git log`**（amend 不产生新条目） |
| 8 发布测试环境 | 成功部署到测试环境 |
| 9 复测 + 交付判断 | **任务的真正终点，三样都要过**：①测试环境上复测通过、无遗留问题；带用例时 **`单测` / `端到端` 两类**全部复测通过（**`人工` 类由非实现者做、结果与产物进 ⑥ 建的清单文件，不进本条闸门**）②**按产品需求逐条判"交没交对"，每条都交对**——**用例全绿但需求没满足 = 不算通过**（说明 `plan` 的完成标准漏了需求），必须打回 ③**影响面清单逐条处理完**：**"搜到了"里本地没验掉的在这里验掉**，"搜不到"和"本地验不了"两类**够得着的必须真验过、够不着的要自证**（写清可重跑入口 + 试了什么、卡在哪）——**这是老功能没被改坏唯一的依据**（没验也没自证 = 不算通过；**全表都标"验不了" = 不算通过**） |

Step 3 (plan) is the **only** step that requires stopping for explicit user confirmation before writing code (side-effecting steps such as deploy still require user approval — see “Trust principle”); every other step proceeds without waiting.

**Type assignment / 类型归属 (the table's case types)**: step ⑤ runs the **`unit`** cases; step ⑥ runs the **`e2e`** cases; step ⑨ re-runs **both** `unit` and `e2e` on the test environment; **`manual`** cases are done by a non-implementer, with the result and artifact going into the checklist file step ⑥ created (the landing spot `plan` recorded) — they never enter an automatic gate, but they must never be skipped or faked.

> **进评审的硬准入 / Hard gate before review**：**进入第 ⑦ 步独立评审前，第 ⑥ 步的 `端到端` 类验收用例必须“全部跑 + 全部 pass”**——只要还有一条没跑或没过，就**不许进评审**。（`单测` 类在 ⑤ 已闸过；**`人工` 类不进这条闸门**，由非实现者做、结果与产物进 ⑥ 建的清单文件，但**不许跳过或假装做了**。）做法：回去改到全过（用例因代码错而失败→改代码）；**确实做不到时：环境缺→整步标“卡住”、该条用例记“受阻（环境）”（按第③条）；用例本身有问题（用例写错/自相矛盾）→按第②条请用户裁定用例**（两种情况都要明确是哪条/为何）。**不许把“全量单测绿了”当成“用例全 pass”**，也不许带着未跑完的用例进评审。顺序是硬的：⑥ `端到端` 类全 pass → 才 ⑦ 评审。

> **Hard gate before review**: before entering step 7 (independent review), **every `e2e` acceptance case from step 6 must be run AND passing** — if even one is un-run or failing, you **may NOT enter review**. (`unit` cases were already gated at ⑤; **`manual` cases are outside this gate** — a non-implementer does them, with the result and artifact going into the checklist file step ⑥ created (the landing spot `plan` recorded), but they must **never be skipped or faked**.) Fix until they all pass (a case failing due to code → fix the code); **if genuinely impossible: missing environment → mark the whole step “blocked” and that case “blocked (environment)” (per case ③); a broken/self-contradictory case → go through case ② and ask the user to adjudicate the case** (either way, state which case and why). **Never treat “the full unit suite is green” as “all cases pass”**, and never enter review with un-run cases. The order is hard: ⑥ all `e2e` cases pass → ⑦ review.

## 进度账本 / The progress ledger

- 每个任务一个文件，放在**当前项目的 `progress/`**，文件名形如 `任务名.md`。
- 账本文件的模板见本 skill 的 `assets/ledger-template.md`（复制它作为起点）。
- 每干完一步，**追加一条**记录（不要修改历史记录），格式固定，给人一眼扫懂：

```
## 日期 · 第N步：步骤名（状态：进行中/已完成/卡住）
- 干了啥：
- 结果：
- 下一步：
```

- 状态用 `进行中` / `已完成` / `卡住` 三种，标在每一条标题上。
- 账本顶部写三行：任务是什么、是 bug 还是需求、当前状态。
- **卡住**必须给出口：要么解决继续、要么决定放弃；放弃则删账本（见清理规则）。
- **写详细：账本要能"回看"**。退回重做（见《第 7 步后的分叉》）时要靠账本判断"上一版错在哪"，所以**每一步都要写清"依据"，而不只是结论**：
  - **读了什么**（哪些文件 / 文档 / 需求）
  - **跑了什么命令、看到什么**（原始输出）
  - **由此得出什么结论**
  - 尤其 **`analyze` / `plan` / `tdd` 三步要写细**：怎么分析的、方案是什么、怎么实现的——**这三步是回看的主要对象**。
  - **`review` 每次判 FAIL 都要写一条判词**（为什么没过 + 问题清单）：被打回的那一步只能从这里知道上一版错在哪。**判词只留在对话里 = 退回重做时瞎改。**
  > 自检（自问即可，不要为此停下）：假设三天后要重做一个同样的任务，只看这份账本，能不能知道当时是怎么想、怎么做的？不能，就是不够详细。
- **把 `progress/` 写进目标项目的 `.gitignore`**——这是**建账本时的固定动作，不是可选项**。git 不管它，**任何回退都碰不到账本**——退回重做时账本一定还在。
- **要说人话 / Write it in plain language**：账本是给人看的，且是给**不了解这套系统的初级工程师**看的。每条记录都要能让他看懂“这步干了什么、现在什么状态、下一步做什么”。
  - **先人话、后术语**：每一条先用人话写摘要（“干了什么、结果如何”），**再把该步证据（命令 + 原始输出）跟在后面**，术语/细节也放这里。**说人话不省证据**（证据跟在对应那条通常是“结果”后面；仍是三行、不新增第 4 个字段，原始输出可用缩进代码块贴在条目下面）。
  - **术语要么不用、要么解释**：像“幂等重放”“状态投影”“CAS”“fail-closed”“静默误归因”这类词，要么换成白话，要么**在同一份账本里**第一次出现时用一句括号说明。
  - **自检（自问即可，不要为此停下等用户）**：假设把这条记录交给没参与的人，他说不出“发生了什么、有没有问题”——就是没写清；堆术语不算“一眼扫懂”。

- **Write it in detail — it must support "looking back"**: the fallback (see "Branch after step 7") relies on the ledger to judge "what was wrong in the previous version", so **every step records its grounds, not just its conclusion**:
  - **what was read** (which files / docs / requirements)
  - **what command was run and what it printed** (raw output)
  - **what conclusion follows**
  - `analyze` / `plan` / `tdd` in particular: how it analysed, what the plan was, how it was implemented — **these three are what the fallback reads**.
  - **`review` writes a verdict into the ledger on every FAIL** (why it did not pass + the problem list): that is the only place the sent-back step can learn what the previous version got wrong. **A verdict left only in the conversation means the fallback is flying blind.**
  > Self-check (in your head — never stop for it): if you had to redo the same task three days later, would this ledger alone tell you how you thought and what you did? If not, it isn't detailed enough.
- **Add `progress/` to the target project's `.gitignore`** — this is a **fixed action when you create the ledger, not optional**. Git then ignores it, so **no revert can touch the ledger** — it is guaranteed to survive a fallback.

One file per task under the **current project's `progress/`**. Use `assets/ledger-template.md` (in this skill) as the starting template. Append one entry per finished step (never rewrite history), using the fixed format above so a human can scan it at a glance.
- **Write it in plain language**: the ledger is for humans — specifically a **junior engineer who does not know this system**. Every entry must let them see "what this step did, what state it's in, what's next".
  - **Plain first, jargon second**: start each entry with a plain-language summary ("what was done / the result"), **then follow with the step's evidence (command + raw output)** and any jargon/details. **Plain language never excuses missing evidence** (evidence goes in the corresponding entry — usually under "Result"; still three fields, no extra 4th field, raw output may be pasted in an indented code block under the entry).
  - **Avoid jargon, or explain it**: for terms like idempotent replay, state projection, CAS, fail-closed, silent mis-attribution — either say it in plain words, or explain it in parentheses **the first time it appears in this ledger**.
  - **Self-check (do it in your head — never stop to wait for the user)**: imagine handing the entry to someone not involved; if they can't say "what happened, is there a problem", it isn't clear. Piling on jargon is not "scannable at a glance".

## 产出纪律 / Output discipline

- **本流程只要求两个产出**：① `progress/` 下的**一个账本**；② `plan` 卡要求的**方案**（方案记进账本即可，不必另建文件）。**不要自行发明其它文档**（如“交付说明”“交付偏差说明”“验收报告”“总结文档”等）。
- **例外（不属于“自行发明”）：任务本身的交付物**（如“纯仓库内任务”要写的那份文档，**以用户需求/卡的定义为准，不得自己认定它是交付物**）、**用户点名要的文档**、以及**仓库里既有的文档**——这些照做即可，不算自造。
- 偏差、说明、理由这类要记录的东西，**写进账本**即可，**不要另建文档**。
  > **例外**：`plan` 写好的**验收用例落点**（测试文件 / 清单文件）是**交付物**，不算"另建文档"——它必须在收尾时（删账本前）落到仓库里，见《清理规则》。
- **无论走到哪一步，都不要自行产出名字带“交付”的文档；第⑥步（本地验证）、第⑦步（评审）、第⑨步（复测+交付判断）完成前尤其禁止** —— 还没交付就出“交付文档”是越位，且会让人误以为可以验收。**⑦ 只是代码质量闸门，它过了也不代表可以交付**；要发环境的任务**要到⑨通过才算交付**。（若这份文档本身就是任务/用户点名要的交付物，则不受此限。）
- 如果你认为确实需要额外产出（用户没说、卡也没要求的），**先问用户**，不要自己决定。

- This flow requires only two outputs: (1) **one ledger** under `progress/`, and (2) the **plan** the `plan` card requires (the plan can live in the ledger; no separate file needed). **Do not invent other documents** (e.g. “delivery note”, “delivery deviation note”, “acceptance report”, “summary doc”).
- **Exception (not “inventing”): the task's own deliverable** (e.g. the doc a “repo-only task” is meant to write — **as defined by the user's requirement/the card, not self-declared**), **a doc the user explicitly asked for**, **docs that already exist in the repo**, and **the acceptance-case landing spots `plan` recorded** (test files / checklist file — deliverables that must be in the repo before the ledger is deleted; see “Cleanup”) — just do those.
- Anything like deviations, notes, or rationale goes **into the ledger** — do not create a separate file.
- **At any step, do not produce a document whose name contains “delivery” on your own; especially forbidden before steps 6 (local verification), 7 (review) and 9 (re-verify + delivery judgment) are done** — outputting a “delivery document” before delivery is overreaching and misleads people into thinking it is ready for acceptance. **⑦ is only the code-quality gate — passing it does not mean deliverable**; an env task is only delivered once ⑨ passes. (If such a document is itself the task's / the user's named deliverable, it is exempt.)
- If you think an extra output is truly needed (the user did not ask and no card requires it), **ask the user first** — never decide on your own.

## 清理规则 / Cleanup

- 任务**完成**（发环境=**复测通过 + 需求逐条交对** / 仓库内=**⑦评审 pass**，该 pass 已含交付判断）或**放弃** → **直接删除**账本文件，不留 archive。
- **任务完成时，删账本之前先把验收用例落进仓库**（**放弃的任务不适用**——活没做完，用例没验过，不该往仓库里沉）：按 `plan` 写好的**落点**逐条确认——`单测` / `端到端` 的用例在**测试文件**里，`人工` 的在**清单文件**里；**没落的先落，再删账本**。（用例只写在账本里，账本一删就等于没沉淀。落点是交付物，不算本卡禁止的"额外文档"。）
  > **落点缺失 / 不可用 → 回 ③ 补落点**：不许把"方案里没写落点"当成"没有要落的用例"——那是两回事。
  > **这一步不是自己给自己判**：用例落没落，⑦ 在评审时已经核过一遍（见 `review` 卡第 2 条）。这里只是按已核过的清单执行。
- 完成/放弃后的账本没有价值，不应该继续占地方。**注意：账本不进 git（见上），所以删了就真没了**——需要留档时，在删之前自己另存一份。
- 删除账本是**收尾那一步的固定动作**，由你执行，不要等用户提醒。

When a task is **done** (env = ⑨ re-verify passes **and** every requirement item is delivered; repo-only = ⑦ review passes, which for those tasks already includes the delivery judgment) or **abandoned**, **delete** its ledger file outright — keep no archive. **When a task is done, land the acceptance cases in the repo before deleting the ledger** (**not applicable to abandoned tasks** — the work is unfinished and the cases unverified, so they must not be deposited): walk the **landing spots** `plan` recorded — `unit` / `e2e` cases in their **test files**, `manual` cases in their **checklist file**; **land anything missing first, then delete**. (A case that lives only in the ledger was never deposited once the ledger goes. The landing spot is a deliverable, not the extra document this card forbids.) **A missing or unusable landing spot goes back to ③** — "the plan recorded no landing spot" is not the same as "there was nothing to land". **This step is not self-judged**: the landing was already checked at ⑦ (see the `review` card, item 2); closure just executes the checked list. **Note: the ledger is not in git (see above), so deleting it is final** — save a copy elsewhere first if you need one. Do this as part of closure.

## 干活卡 / Execution skills

需要实际动手时，按阶段加载对应干活卡（这些卡会告诉你每步的具体做法 + 必须留什么证据）：

| 流程步骤 Step | 干活卡 Skill |
|---|---|
| ①复现、②定位（修 bug） | `reproduce` |
| ①看懂、②分析（做需求） | `analyze` |
| ③出方案 | `plan` |
| ④开发 | `tdd` |
| ⑤测试 | `test` |
| ⑥本地验证 | `local-verify` |
| ⑦独立评审 | `review` |
| ⑧发布测试环境 | `deploy` |
| ⑨测试环境复测 | `re-verify` |

When actual work is needed, load the matching execution skill (each tells you how + what evidence to keep).

### 怎么触发加载 / How to load a skill

四个 agent 的显式触发语法不同，按你当前所在 agent 选用其一（语法来源见注释）：

| Agent | 触发语法 | 来源 |
|---|---|---|
| Pi | `/skill:reproduce`（冒号分隔） | Pi 官方 skills 文档「Skill Commands」 |
| Codex | `$reproduce`（美元符 + skill 名；也可直接 read 对应 `SKILL.md`） | Codex 官方 skill-creator 卡（`allow_implicit_invocation` 段的 `$skill-name`） |
| Claude Code | `/reproduce`（斜杠 + skill 名） | Claude Code 官方 skills 文档（"invoke one directly with `/skill-name`"） |
| DeepSeek Harness | 通过模型侧 `skill` 工具，按名 `get` 对应 skill | DSH 官方 `dsh-tool-skill` 源码（工具名 `skill`，描述 "Load the full instructions for an available skill"） |

- 若不确定当前 agent 是哪种，用**通用 fallback**：直接 `read` 该卡的文件（`skills/<名>/SKILL.md`），再按其 instructions 执行——四个 agent 都支持 read，最稳。
- skill 名带连字符（`local-verify`、`re-verify`）时按原样写，不省略连字符。
- 渐进披露意味着 card 正文**不会自动全量预载**，所以每推进到一步都要显式加载那一张卡，别假设它的内容已在上下文里。

- **Four agents differ in syntax — see the table above** (Pi `/skill:<name>`, Codex `$<name>`, Claude Code `/<name>`, DSH via the `skill` tool). Universal fallback: `read` the card's file (`skills/<name>/SKILL.md`) — every agent supports `read`. Hyphenated names (`local-verify`, `re-verify`) are written as-is. Progressive disclosure means a card's body is **not** auto-preloaded in full, so explicitly load each card as you reach its step.

### 动手前先加载（不是“每步一次”）/ Load before you act (not “once per step”)

> **卡是按“动作”加载的，不是按“流程步”加载一次就完了。** 只要你要做下面这类事，**不管现在是第几步、也不管之前读过多少次，先回到对应卡再动手**：
>
> | 你要做的事 | 先加载 |
> |---|---|
> | 写/改代码（包括改 bug、改评审意见、改用例） | `tdd` |
> | 跑测试 | `test` |
> | 本地跑验证 / 起环境 | `local-verify` |
> | 派独立评审 / 当评审 | `review` |
> | 出/改方案 | `plan` |
> | 复现 / 定位原因 | `reproduce` |
> | 看懂需求 / 分析现状 | `analyze` |
> | 发布 / 复测 | `deploy` / `re-verify` |
>
> **返修阶段尤其要注意**：拿到评审意见/复测结果后回去改，**不是“回到第④步”就完了**——**每轮改代码都要重新加载 `tdd`，改完跑测试要重新加载 `test`，验证要重新加载 `local-verify`**。**用户中途插话让你改东西时也一样**（“改这个 bug”、“这里不对”——只要落入上面的“做什么”，就先加载对应卡，再动手）。
>
> **怎么被核到（不进闸门的规则等于劝告）/ How this gets checked**：**每轮返修的账本条目，在“干了啥”里写明本轮加载了哪些卡**（例：“本轮已加载 tdd/test”）——不新增字段，就写在原有那一行里。**这条能被第⑦步评审逐轮核对**（评审卡已把它列入复核项）。**光写卡名不算数**：真正的判据是**那一轮的 tdd/test 证据齐不齐**（新测试名、红→绿原始输出、邻域回归、`git diff HEAD~1 --stat` / `git show --stat HEAD`）——卡加载只是代理指标，证据齐才是真的照着卡做了。
>
> **为什么这条是硬的**：见 dev-harness 仓库的 `docs/rationale.md`（**卡不含该文件**；实测：一个真实会话开工读卡齐、之后 43 次改代码一次没读）。
>
> **Why this rule is hard**: see `docs/rationale.md` in the dev-harness repo (**cards do not ship this file**; measured: in one real session skills were loaded during start-up, then across 43 code edits not once).
>
> **Load skills by ACTION, not once per flow step.** Whenever you are about to do any of these, **go back to the matching card first — no matter which step you are on, and no matter how many times you already read it**: writing/changing code (including bug fixes, review fixes, case fixes) → `tdd`; running tests → `test`; running/standing up local verification → `local-verify`; spawning or doing an independent review → `review`; producing/changing a plan → `plan`; reproducing/locating a cause → `reproduce`; understanding a requirement / analyzing the current code → `analyze`; deploy / re-verify → `deploy` / `re-verify`. **This matters most in the fix-loop phase**: after review or re-verify findings, **every round of code changes reloads `tdd`, every test run reloads `test`, every verification reloads `local-verify`** — and the same applies when the user interrupts you mid-flow to change something. **How this gets checked (a rule outside the gate is only advice)**: **each fix-round ledger entry names, in its "what I did" line, which cards were loaded that round** (e.g. "loaded tdd/test this round") — no new field, same three-line entry — and **step ⑦ review checks this round by round** (the review card lists it). **Naming cards is not the real test: the real test is whether that round's tdd/test evidence is complete** (new test names, raw red-to-green output, neighbourhood regression, `git diff HEAD~1 --stat` / `git show --stat HEAD`) — card loading is only a proxy; complete evidence is the proof the card was actually followed.

## 可信度原则 / Trust principle

没有运行时强制，账本要可信，靠两条：
1. **只记"能客观核验的事"，不记"我觉得可以"**——每步完成都要跟一个"凭什么"（命令 + 原始输出）。
2. **有副作用的步骤（尤其发布）必须经用户确认**，AI 不能自述"已发布"。

Since there is no runtime enforcement, the ledger stays trustworthy by two rules: (1) only log objectively checkable facts — every "done" needs a "why" (command + raw output), never vibes; (2) side-effecting steps (especially deploy) require user confirmation — the AI never self-claims "deployed".
