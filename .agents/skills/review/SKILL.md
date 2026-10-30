---
name: review
description: "独立评审（代码质量闸门）。只判在本地就能查实的代码质量与测试可信度，不判能不能交付。 / Independent review as a code-quality gate: only what can be judged locally — code quality and test trustworthiness; it does not decide whether the thing is deliverable."
---

# Review / 独立评审

## 本步管什么、不管什么 / Scope (read this first)
> **管**：**代码质量 + 测试可信度 + 架构基线**——膨胀 / 重复 / 孤儿 / 测试是不是假绿 / 项目约束 / 逐行可追溯 / **`plan` 架构落位与实际 diff 对不对得上（含 `tdd` 第 8 条 8.1–8.9）**。这些都是**读代码 + 跑测试 + 对着 diff 搜一遍就能查实**的，且**越早查越便宜**（拖到部署后改，要重走一遍发布）。
>
> **不管**：**"这需求到底交没交对"**。那是**真实环境 + 真实数据**才能判的事——要发环境的任务，**这条由第⑨步 `re-verify` 判**，本步的 pass **不代表可交付**。
>
> **所以本步不许拿"我猜这里可能有问题"打回**：提的每条问题都要能指到代码位置、说清**什么条件下会错**；不确定的当场定论（依 `tdd` 刹车自判）或标"待用户裁定"，**不许写成"疑似"挂着一堆**。
>
> **例外（纯仓库内任务）**：这类任务没有 ⑧⑨，"真实环境"就是仓库本身，所以**"按需求逐条判交没交对"仍归本步**（见铁律第 2 条与《流程》）。

> **Covers**: **code quality + test trustworthiness + the architecture baseline** — bloat / duplication / orphans / whether the tests are false-green / project constraints / line-by-line traceability / **whether `plan`'s 架构落位 matches the actual diff (including `tdd` item 8's 8.1–8.9)**. These are provable by **reading code, running tests and searching against the diff**, and **the earlier they are caught the cheaper they are** (fixing after deploy means going through release again).
>
> **Does NOT cover**: **"does this actually deliver the requirement"**. That needs the **real environment and real data** — for env tasks it is judged at **step ⑨ `re-verify`**, and a pass here **does not mean it is deliverable**.
>
> **So this step may not send work back on a hunch**: every issue raised must point at a code location and say **under what condition it goes wrong**; anything uncertain is decided on the spot (per `tdd`'s brakes) or marked "awaiting user adjudication" — **never left dangling as "suspected"**.
>
> **Exception (repo-only tasks)**: they have no ⑧⑨ — the repo itself is the real environment, so **"judge delivery against the requirement item by item" stays with this step** (see rule 2 and Steps).

1. **独立视角**：评审的人（或视角）不能是那个写代码的实现者本身。实现者不能给自己判 pass。
2. **只管代码质量**（见卡首《本步管什么、不管什么》）：查的是**代码写得好不好、测试可不可信**。要发环境的任务，"需求交没交对"归第⑨步，**本步不为它下结论**；纯仓库内任务没有⑧⑨，**那条仍归本步**。
3. **怎么判**：拿原始需求/`plan` 的完成标准当尺子，逐条判"过/没过 + 证据"；再主动挑战"清单上压根没想到"的坏法（见《流程》）——但**挑战的落点仍然是"代码里确有其事"**，不是"上真实环境可能出问题"（后者归⑨）。
   **判 FAIL 的必须写进账本**（为什么没过 + 具体问题清单 + 指到代码位置），**判 pass 的也写**（逐条依据）。
4. **判 FAIL 回哪里（按问题性质分流）**：
   - **代码质量问题**（膨胀 / 重复 / 孤儿 / 假绿 / 项目约束 / 逐行追溯 / 架构基线里**代码侧**的违例，如 8.1 循环依赖、8.4 契约删改、8.2 调了未声明的入口）→ **回 `tdd` 改代码**，改完重走 ⑤⑥⑦。这是本步**绝大多数** FAIL 的去向。
   - **架构落位本身不实**（路径不对、入口符号不存在、9 条里"不涉及"给不出仓库级证据）→ **回 `plan` ③ 修订落位**（账本追加一条修订记录，**不重写历史**），改完再走 ④⑤⑥⑦。**不许打回给实现者**——落位是 ③ 的产物，他无权改。（发环境的任务与纯仓库内任务都走这条，不依赖下一条那个只管"需求理解错"的分支。）
   - **纯仓库内任务的"需求没交对"**（这类任务没有⑧⑨，交付判断在本步做，见《流程》第 1 条）→ 看是哪一类：**实现没做对** → 回 `tdd`；**需求理解错 / 完成标准写歪** → 回 `plan`。
   - **依据不实 / 只引文档没给代码位置**（铁律第 9 条）→ **不是换方向，是补依据**：账本追加一条修订记录，回缺的那一步（`analyze` / `reproduce` / `plan` ③）补上，再走 ③④⑤⑥⑦。**不走第 6 条那套重做**——它只为第 5 条的"同一类回归反复出现"服务，会 reset 掉本轮代码。
   - **反复引入回归** → 走下面第 5 条（退回任务开头重做）。
   > **要发环境的任务**：需求是否交付**不在本步判**（归⑨），所以这里不会因"需求没交对"而 FAIL。
5. **什么时候必须换方向（退回重做）**：**同一类问题反复出现——"上一轮的修改新引入的回归"反复发生（不必连续）**。这说明**问题在方案/方向层，再一轮轮补是救不回来的**，必须退回任务开头重做。
   > 触发条件只有这一条，**不看改了几轮**：两轮里发现"方向错了"比十轮里改错别字严重得多。**"改了很多轮还没过"不构成触发条件**——那只是慢，不是方向错。
6. **退回怎么做——固定五步**（**执行者是 orchestrator，不是评审员**：评审员只读，这五步是写操作）：

   1. **存证据**：`git branch wip/失败-<日期或简述>`——把失败的尝试留在 git 里。
      > **先 amend 再 park**：这条命令抓的是**当前 HEAD**，所以本轮返修必须已经 `git commit --amend` 进那一个 commit（见 `orchestrate` 卡《commit 的时机》）；还有未提交的返修就先 amend，否则下一步会连它们一起丢掉。
   2. **确认没误伤**：先 `git status`。**工作区里有不属于本轮的未提交改动 → 先处理掉（提交或另存）**，别一起 reset 掉。
   3. **回退代码**：`git reset --hard HEAD~1`（退到本轮那个 commit 之前）。
      > **禁止 `git clean`**——`git clean -fdx` 的 `-x` 会连被忽略的文件一起删，**账本就在 `progress/` 里**。
   4. **核对账本还在**：`ls progress/`。**账本是这次失败的经验，回退了就白退**；它不进 git，删了只能从备份恢复——所以**回退前就确认它不在被删范围内**，而不是指望"发现不在再恢复"。
   5. **重做任务入口那一步 + `plan`**：做需求 → `analyze`；修 bug → `reproduce`（**要重新落到根因**）。
      - **先读账本**（含每次判 FAIL 的判词），对着它逐条回答"上一版错在哪"，交一张**教训 → 处置 → 判词**表（做需求见 `analyze` 卡《退回来的活怎么干》，修 bug 见 `reproduce` 卡；**修 bug 还要逐条证伪上一版的根因 B1、B2…**）。
      - **整条重做链换"干净的脑子"**：**另起一个全新的子 agent** 跑"入口卡 + `plan`"这一段，**只给它三样东西**：① 账本（含历次失败判词）② 原始需求 ③ 代码/仓库现状。**不给它上一版方案、也不给它上一版的自我解释**。**并交代它的默认立场：先假设上一版的方向是错的，别默认继承。**
      - 之后照常走：方案独立评审 → 用户确认 → 实现。
      > 为什么必须换脑子、为什么只换入口卡不够：见 dev-harness 仓库的 `docs/rationale.md`（**卡不含该文件**）。**执行不需要读它**——上面这几步照做就对。

7. **每次退回都要自证"在收敛"**：退回可能一次就成，也可能要好几次——**次数不是判据**。判据是**"假设变了没有"**：这一版推翻了上一版的哪个假设？为什么上一版那条路走不通？**如果答案是"没动假设、只是把任务重新拆了一遍" → 就是原地打转**，按第 8 条报告用户。这条判断**写进账本**（接在《退回来的活怎么干》那张表后面）。

8. **该找用户时主动报告——是"通知"，不是"停下"**：出现下面任一种，**写进账本并报告用户**，然后**继续做你还能做的部分**（不要干等）：
   - **退回重做之后，又是因为同一类问题被打回**（说明入口卡/方案的诊断能力到头了——这跟第 5 条的触发条件不是一回事：第 5 条管的是"同一轮里反复引入回归"，这里管的是"换了一版方向之后还是同一类病"）
   - 根因是**需求本身有歧义或自相矛盾**（AI 修不好，只能用户拍板）
   - 根因是**环境 / 权限 / 外部依赖**（再退多少次都没用）
   - **某一轮退回没产生任何新的失败信息**（空转）
   > **报告是给用户知情权，不是把活推回去**（为什么不"停下"：见 dev-harness 仓库的 `docs/rationale.md`，**卡不含该文件**）。

9. **分析和方案的结论必须落在代码上**：账本第 2 步（定位原因 / 分析代码）和第 3 步（出方案，含影响面与架构落位）里的结论，**只引了文档、没给代码位置**，判 **FAIL**——文档会过期、写的是理想状态，"文档里这么说"不算证据。
   > **判据分两种，缺一即 FAIL**：**肯定结论**（"这里就是这么实现的"）要有 `文件:行`；**存在性否定**（"代码里没有这个东西"）要有**搜索命令 + 原始输出 + 用过哪几种搜法**（照 `plan`《影响面》的标准，**不许把"我没搜"写成"搜不到"**）。另外，**定位用过的搜索命令要贴在账本第 2 步的结果里**——贴不出命令的结论，按"没读过代码"判。
   > **打回哪一步、怎么回**：缺依据是**补依据**，不是换方向——**在账本追加一条修订记录**，回缺的那一步（`analyze` / `reproduce` / `plan` ③）补上，然后重走 ③④⑤⑥⑦。**不走铁律第 6 条那套"换干净脑子重做"**（那是给铁律第 5 条"同一类回归反复出现"用的，它会 `git reset --hard HEAD~1` 丢掉本轮代码）。
   > **两种情形不算违规**：引**需求原文**（用户给的截图 / 原话）——那是需求的出处，不是"拿文档当代码"；结论是**"代码里不存在"**、但按上面的判据给了**搜索命令 + 原始输出 + 搜过哪几种**——这也算落到了代码上。
   > **需求清单也归本条**：每条 `R1、R2…` 要能对上账本《需求原文》里的原句；发现某一轮的需求清单是**转述**而不是原文，同样判 FAIL，回 `analyze`。

> **退回重做之后同样要独立复评**：换"干净的脑子"重做出来的东西**不是自己人**，照样必须**另派独立子 agent** 复评（见《流程》第 6 条）。

1. **Independent**: the reviewer must not be the implementer. The implementer never passes their own work.
2. **Code quality only** (see "Scope" at the top): what this step checks is **whether the code is good and the tests are trustworthy**. For env tasks, "does it deliver the requirement" belongs to step ⑨ — **this step draws no conclusion about it**; repo-only tasks have no ⑧⑨, so **that judgment stays here**.
3. **How to judge**: use the original requirement / the `plan`'s done-when as the measuring stick; give "pass / fail + evidence" for each; then actively attack the failures nobody thought to list (see Steps) — but **the landing point is still "this is really in the code"**, not "this might break on the real environment" (that is ⑨'s).
   **Every FAIL verdict must go into the ledger** (why it did not pass + the concrete problem list + the code location), **and so must every pass** (the per-item grounds).
4. **Where a FAIL goes (route by the nature of the problem)**:
   - **Code-quality problems** (bloat / duplication / orphans / false-green tests / project constraints / line-by-line traceability / **code-side** architecture-baseline violations such as 8.1 a cycle, 8.4 a contract removed or changed, 8.2 calling an undeclared entry) → **back to `tdd`**, then re-run ⑤⑥⑦. This is where **most** FAILs from this step go.
   - **The 架构落位 itself is unsound** (wrong paths, a non-existent entry symbol, nine verdicts without repo-level evidence) → **back to `plan` step ③ to amend the 落位** (append an amendment record to the ledger — **never rewrite history**), then re-run ④⑤⑥⑦. **Never send this to the implementer** — the 落位 is ③'s artifact and they may not rewrite it. (Both env tasks and repo-only tasks take this route; it does not depend on the next bullet's "requirement misread" branch.)
   - **A repo-only task's "requirement not delivered"** (those tasks have no ⑧⑨, so the delivery judgment happens here — see item 1 above) → depends which kind: **the implementation is wrong** → back to `tdd`; **the requirement was misread / the done-when was written wrong** → back to `plan`.
   - **Grounds that do not hold up / a document cited with no code location** (rule 9) → **supply the grounds, do not change direction**: append a revision entry to the ledger, go back to the step that is short (`analyze` / `reproduce` / `plan` ③), then re-run ③④⑤⑥⑦. **Do not use rule 6's redo** — that serves rule 5's "the same regression keeps returning" and resets this round's code.
   - **Regressions keep being introduced** → use rule 5 below (fall back to the task's entry point and redo).
   > **For env tasks**: whether the requirement is delivered **is not judged here** (that is ⑨'s), so this step never fails on "requirement not delivered".
5. **When the direction must change (fall back and redo)**: **the same class of problem keeps coming back — a "regression newly introduced by the previous round's fix" keeps happening (not necessarily consecutively).** That means **the approach/direction itself is at fault and more patching will not save it**; go back to the task's entry point and redo.
   > This is the only trigger, and **it does not count rounds**: finding "the direction is wrong" in round two matters far more than a typo fixed in round ten. **"It has taken many rounds and still fails" is NOT a trigger** — that is slow, not wrong-headed.
6. **How to fall back — the fixed five steps** (**the executor is the orchestrator, not the reviewer**: the reviewer is read-only, these five steps are write operations):

   1. **Preserve the evidence**: `git branch wip/failed-<date or short note>` — keep the failed attempt in git.
      > **Amend first, then park**: this captures **the current HEAD**, so this round's fixes must already be `git commit --amend`-ed into that single commit (see the `orchestrate` card's "When to commit"); if any fix is still uncommitted, amend it first, or the next step throws it away too.
   2. **Check you won't clobber anything**: run `git status` first. **If the working tree holds uncommitted changes that are not part of this round, deal with them first** (commit or park them).
   3. **Revert the code**: `git reset --hard HEAD~1` (back to before this round's commit).
      > **Never `git clean`** — the `-x` in `git clean -fdx` deletes ignored files too, **and the ledger is one of them in `progress/`**.
   4. **Confirm the ledger survived**: `ls progress/`. **The ledger is the lesson from this failure — reverting it away wastes the whole exercise.** It is not in git, so if it is deleted the only recovery is your own backup — so **make sure it is out of harm's way before reverting**, rather than hoping to "restore it once you notice".
   5. **Redo the task's entry step + `plan`**: feature → `analyze`; bug fix → `reproduce` (**re-land the root cause**).
      - **Read the ledger first** (including every FAIL verdict), answer "what was wrong in the previous version" item by item against it, and produce a **lesson → handling → verdict** table (features: the `analyze` card's "How to redo a sent-back task"; bug fixes: the `reproduce` card — **a bug fix must also falsify the previous root causes B1, B2 … item by item**).
      - **Run the whole redo chain on a "clean head"**: **spawn a brand-new subagent** for the "entry card + `plan`" stretch, and **give it only three things**: (1) the ledger (with every failure verdict), (2) the original requirement, (3) the code/repo as it stands. **Do not give it the previous plan, and not the previous version's self-explanation.** **And tell it its default stance: assume the previous direction was wrong — do not inherit it.**
      - Then continue as usual: plan review → user confirmation → implementation.
      > Why a clean head is required, and why swapping only the entry card is not enough: see `docs/rationale.md` in the dev-harness repo (**cards do not ship this file**). **You do not need it to execute** — the steps above are enough.

7. **Every fallback must prove it is converging**: a fallback may succeed on the first try or take several — **the count is not the test**. The test is **"did the hypothesis change"**: which assumption of the previous version does this one overturn? Why was the previous road a dead end? **If the answer is "no assumption changed, the tasks were just re-split" → it is spinning in place**, so report per rule 8. Record that judgement **in the ledger** (right after the "How to redo a sent-back task" table).

8. **Tell the user when the signals are there — as a notification, not a halt**: on any of these, **write it in the ledger and report it to the user**, then **keep doing whatever part you still can** (do not sit and wait):
   - **after a fallback, the same class of problem came back again** (the entry card/plan has hit its diagnostic limit — this is NOT the same condition as rule 5: rule 5 is "regressions keep appearing within one attempt", this one is "a new direction was tried and it is still the same disease")
   - the cause is **the requirement itself being ambiguous or self-contradictory** (no AI can fix that; only the user can decide)
   - the cause is **environment / permissions / an external dependency** (no number of fallbacks will help)
   - **a fallback produced no new failure information at all** (spinning)
   > **Reporting gives the user visibility; it does not hand the work back** (why not "halt": see `docs/rationale.md` in the dev-harness repo, which **cards do not ship**).

9. **Analysis and plan conclusions must land on code**: when the entries in ledger step 2 (root cause / code analysis) and step 3 (the plan, including the impact list and architecture placement) **cite only a document and no code location**, judge **FAIL** — documents go stale and describe intentions, so "the doc says so" is not evidence.
   > **Two kinds of evidence, either one missing is a FAIL**: a **positive claim** ("this is how it is implemented") needs a `file:line`; an **existence-negative** ("this thing is not in the code") needs the **search command, its raw output, and which search methods were used** — the same bar as `plan`'s impact list, and **never write "I did not search" as "it cannot be found"**. The **search commands used to locate things must be pasted into ledger step 2**; a conclusion whose commands are missing counts as "the code was never read".
   > **Where it goes back — and how**: missing grounds means **supply the grounds**, not change direction: **append a revision entry to the ledger**, go back to the step that is short (`analyze` / `reproduce` / `plan` ③) to supply it, then re-run ③④⑤⑥⑦. **Do not use rule 6's "clean head" fallback** — that one exists for rule 5's "the same class of regression keeps returning", and it runs `git reset --hard HEAD~1`, discarding this round's code.
   > **Two cases are not violations**: quoting the **requirement text** (the user's screenshot or words) — that is the requirement's source, not "a document standing in for code"; and a conclusion of **"this does not exist in the code"** that meets the criterion above — **search command, raw output, and which methods were tried** — which has landed on the code too.
   > **The requirement list is covered too**: every `R1, R2 …` must map to a line of the ledger's requirement original; if a round's list is a **paraphrase** rather than the original text, that is also a FAIL back to `analyze`.

> **A fallback's output is re-reviewed too**: work produced by a "clean head" subagent **is not automatically trustworthy** — it still MUST go to a **fresh independent agent** (see step 6 under 《流程 / Steps》).

## 怎么派独立 agent / How to spawn the independent reviewer

- 优先派内置 `reviewer` 子 agent（只读，高思考；给它原始需求 + plan 的完成标准**与风险场景**，不要给实现者的自述结论）。
- 没有 reviewer agent 时，可以用任意独立的只读/审查型 agent 代替。
- **给它明确指出仓库路径和操作范围（如“在 <仓库目录> 内执行 `git show HEAD` / `git diff HEAD~1` / 读文件，不要在家目录或全盘 grep”）；它已启动但因环境/路径问题跑偏或失败时，重派一次，而不是干等。**
- 若实在连一个独立 agent 都开不了 → **停下，直接告诉用户**：“这个环境开不了独立子 agent，评审这一步做不了”，不要假装切换视角自己评自己。

- Prefer spawning the built-in `reviewer` subagent (read-only, high-thinking; give it the original requirement + the plan's done-when **and risk scenarios**, NOT the implementer's self-assessment).
- If no reviewer agent exists, use any independent read-only/audit agent.
- **Give it the exact repo path and scope (e.g. "run `git show HEAD` / `git diff HEAD~1` / read files inside <repo dir>; do not grep the home dir or the whole disk"); once it has started, if it goes off-track or fails due to an environment/path problem, re-spawn once instead of waiting.**
- If you truly can't spawn even one independent agent → **stop and tell the user**: "this environment can't spawn an independent subagent, so the review step can't be done." Never fake an "independent view" by reviewing yourself.

## 流程 / Steps

这是流程第 ⑦步：前两步（⑤测试、⑥本地验证）已经绿，**本轮的代码已经 commit（一轮一个 commit）**。你只读评审，不改。
**本步是"代码质量闸门"，不是交付验收**——要发环境的任务，**"需求交没交对"归第⑨步**（见卡首《本步管什么、不管什么》）；纯仓库内任务没有⑧⑨，**那条归本步**（见第 1 条末）。

This is step 7: the prior two steps (5 test, 6 local verification) are green and **this round's code is already committed (one commit per round)**. You review read-only, don't change.
**This step is the "code-quality gate", not delivery acceptance** — for env tasks, **"does it deliver the requirement" belongs to step ⑨** (see "Scope" at the top); repo-only tasks have no ⑧⑨, so **that judgment belongs here** (see the end of item 1).

1. 拿原始的需求/任务（回到 `plan` 的完成标准）当尺子。
   > **要发环境的任务**：这里只核到"**代码层面实现了完成标准要求的行为**、且证据齐"为止——**真实环境下需求到底有没有交对，不在本步下结论**（那是⑨的事），**更不许因为"我想不出它在真实环境会怎样"就打回**。
   > **纯仓库内任务**：没有⑧⑨，所以**"按需求逐条判交没交对"就在本步做完**——逐条问"需求要的这件事，现在真的做到了吗"，做到才算过。
2. 逐条对照：每条完成标准，做没做到、有没有证据。
   - **顺带核一遍"用例落点"**：拿 `plan` 里每条 A 用例的落点，**自己 `ls` / `grep` 一遍**（附命令与原始输出）——`单测` / `端到端` 的**测试文件在不在**、`人工` 的**清单文件在不在**。**缺落点、或落点指向的文件不存在 → 回 ③ 补落点 / 回 ⑥ 把清单落下来**，不许记成"通过"。
     > 为什么本步要核：**账本收尾就删**，用例只有落进仓库才留得下。收尾那一步是删账本的人自己执行，**自己不核自己**——所以核验放在本步（⑦）。
3. **对抗式挑战（不只核对清单）**：核对只能发现“清单上写了但没做到”的；发现不了“清单上压根没想到”的。所以还要主动去找这份实现坏的方式：
   - 这个改动碰到**复用/共享、并发/重复触发、异常/失败路径、空值/边界、超时对齐**时，会不会静默出错（不报错、但结果错）？——**判据是"代码里读得出这条路径确有缺陷"**（哪个条件、走到哪一行、结果怎么错）。**只是"上真实环境可能会出问题"的猜测不算**：那种事由⑨在真实环境上验，本步不据此打回。
   - 将找到的问题与 `plan` 的风险场景对照：`plan` 漏了哪些？
   - **独立核对影响面清单（治“不知道还有谁在用”）**：拿 `plan` 的影响面清单和 commit message 的 `## 影响面` 小节，**自己去搜一遍**——本次改动的每个既有符号，清单列的使用方对不对？有没有明显该搜到却没搜到的？**把"搜了没有"写成"无影响"、或把"搜不到"并进"搜了没有"、或把"本地验不了"当"没搜"用的，打回。** 这是核对事实：**每个你核过的符号都要附你自己的搜索命令与结果**（包括"搜了没搜到"的那些——**不是只在你指控漏了谁的时候才给证据**）。
     > 与上一条的分界：**"代码里读得出会被影响" = 打回**；**"我搜了一圈，发现清单漏了某个使用方" = 打回**；**"我猜上真实环境可能会坏" = 不算**（归⑨）。
   - **"未改动既有符号"这句豁免要逐行核**：拿 `git show HEAD --name-only` / `git diff HEAD~1 --name-only` 看这次动了哪些文件，**再对着方案里那张三列表（文件 / 里面有哪些既有符号 / 为什么没被改）逐行核 diff 内容**——**只新增文件也要核**：新代码有没有挂到某个既有入口上（新路由接管了路径 / 新分支改了既有判断 / 新注册项顶替了原实现）。**表里漏了文件、或改动里出现了既有符号（含既有入口被接管）而表说"没改" → 按诚信问题打回。**
   - **清单上"搜不到"的项**：本步**不要求**验证它们（那是⑨在真实环境做的），但要核**有没有被如实标出来**——把"无法确认"写成"无影响"就是诚信问题，打回。
4. 看代码质量：可读、可维护、有没有明显坑。**并对照 `tdd` 卡《写代码时就要守的》逐条独立复核（不要只看实现者的自述）**：
   - **项目约束**：项目自己有没有编码/架构约定（`CONTRIBUTING.md`/ADR/架构测试/lint）？本次改动**新增的代码**有没有踩？（尤其跨模块直连内部、绕过 facade 这类）
   - **架构基线（拿 `plan` 的《架构落位》对着 diff 核）**：
     - **路径**：`git diff HEAD~1 --name-only` ⊆ 落位声明的路径；越界 → 打回。**例外（不算越界）**：按 `tdd` 第 1 条**实现中新发现且真会发生的失败路径**、按第 2 条**本次自造孤儿的清理（含其它文件里因此失效的）**——这两类是 `tdd` **要求**的，不许因此打回；但它们**必须已记账本并追加修订进落位**（账本追加修订记录，不重写历史），**你比对的是修订后的声明**。
     - **入口符号**：diff 里新增的跨模块调用点，用的是不是落位第 2 项声明的那几个符号？**调了别的（尤其对方内部方法/字段）→ 打回。**
     - **公共契约（8.4）**：按**落位声明的边界**判（不是看 `public` 关键字）。落位声明为对外/跨模块的契约，diff 里有没有删/改，或**新增必填项**？有而落位没给"破坏面 + 迁移路径 + 迁移期"三项 → **打回**。（**同一次提交内改完全部调用点、且没有本次改动之外的消费者**的单元内签名变更**不算**契约变更。）
     - **循环依赖（8.1）**：按落位声明的**粒度**，**从新增边的终点在整仓库范围**走回起点（只在 diff 里看不出环）；有环 → **打回**。
     - **"不涉及"的条目**：对 ③ 的每条"不涉及"命令**自己重跑一遍并附自己的输出**（照上面影响面那套的完整形态，含"**该搜到却没搜到 → 打回**"）。**8.1/8.3/8.5/8.7 不许只拿 diff 反查**——这四条的违例可能整个在 diff 之外。给不出自己的输出 → 打回。
     - **落位本身不实**（路径不对、入口符号不存在、9 条里"不涉及"给不出仓库级证据）→ **不是打回给实现者**，按**《铁律》第 4 条**的失败路由**回 `plan` 修订落位**。
   - **膨胀**：有没有多余的抽象/开关参数/预留扩展？（没有第二个调用方就抽接口/策略/工厂/基类）
   - **重复**：同一段逻辑在本次改动里出现两遍以上？**仓库里是否已有现成实现、却又新写了一个？**
   - **空壳转发**：有没有只转发、不干事的类/方法（对外 facade / 既有边界层不算）？
   - **逐行可追溯**：拿 `git show HEAD` / `git diff HEAD~1` 逐行看（**本轮代码在第④步已经 commit，裸 `git diff` 是空的**），每行真的能追到 **`tdd` 第 1 条定义的某一类需求（含实现中新发现的失败路径）**吗？**改动面是否明显大于任务所需？**
   - **孤儿**：本次改动造出的没人用的代码（包括其它文件里因此失效的）删了没有？
   - **测试质量（治“假绿”）**：本次新增/修改的测试**能不能抓住 bug**？按 `tdd` 第 7 条逐条查：①期望值是不是**独立推导**的（有没有拿被测代码自己的 builder/helper 去算期望值 → 自证断言，两边一起错、永远绿）；②断言是不是打在**真实结果/副作用/退出码**上（**只断言“没报错/没抛异常/返回非空” = 不算断言**）；③有没有**断言 mock 本身**（`toHaveBeenCalled`、断言 `*-mock` 元素存在——把真实现删掉它照样绿）；④有没有**grep 源码文本**当测试（应改成跑它、断言效果；反向守卫除外）；⑤有没有**变动探测器**（只有刻意的决定能让它失败：常量值、提示原话、私有结构）；⑥**断言真的会被执行到吗**（断言写在永不进入的分支里、循环零次、遍历空集合、断言自己刚造的数据——**把被测逻辑整个掏空后测试还绿 = 它根本没碰到被测行为**）；⑦有没有**用删除/跳过/削弱断言换来的绿**（删测试、`skip`/`xfail`/`.only`、注释掉、`toBe` 改成 `toBeTruthy`、精确值改成“非空”——**没有写明理由的移除/放宽都算**）。
     > **“红”也要核**：看账本里那一轮的**红色原始输出**——**红是不是真由“缺功能”引起的**？如果红其实是测试自身写错、编译不过、选择器写错、环境没起，那这个测试**没有证明过它能失败**，红→绿不成立，**打回**。
     > **评审要自己动手验一次，不许只看实现者的自述**：**挑一处实现，心里把它改坏**（改常量 / 分支走反 / 删掉一个副作用 / 返回空 / 去掉一处校验 / **整个掏空**），问“**现有测试会不会红**”。**不会红 = 那个行为没被保护 → 打回**。这一步是 `tdd` 变异自检的外部复核，**账本里的变异自检记录要对着核**（记录里说“由测试 X 抓住”，就去看测试 X 是不是真能抓住）。
   > **违例 → 打回（不是“建议”）。定级 / Severity**：**硬违例 → 打回**（无第二调用方就新增抽象/策略/工厂/基类；**仓库已有实现却又新写一个**；本次自造孤儿（含其它文件里因此失效的）未清（跨仓库/公开 API 只标不删，见 `tdd` 第 2 条）；**本次新增/修改的代码或测试里用了 Mockito（见 `tdd` 第 6 条）**；**测试是自证断言 / 只断言“没报错” / 断言 mock / grep 源码文本 / 掏空实现后仍绿 / 靠删测试·跳过·削弱断言换绿（见 `tdd` 第 7 条）**；踩了机器可执行的约束，如架构测试/lint/CI；**踩了架构基线的硬违例：8.1 新增循环依赖、8.4 公共契约被删/改或新增必填项而没给"破坏面+迁移路径+迁移期"（见 `tdd` 第 8 条）**）。**三个坏味道的其余情形及需求不符/项目约束不符按 `tdd` 各条口径判**——**本清单只是索引，判据一律以 `tdd` 卡各条全文（含刹车与豁免）为准，此处不重列。**
   > **“疑似”不算 pass**：拿不准的必须当场定论（依 `tdd` 各条的刹车自判），或写“待用户裁定”并在账本挂起；**不得写成“pass，另附 N 条疑似”**——带未决项不能 pass。“疑似”只能用于**需求本身有歧义**，不得用于代码质量复核。
   > 另：`tdd` 第 1 条（不为将来加东西、没要求的错误处理、先搜仓库现成实现）、第 2 条（勿顺手改相邻、匹配既有风格、无关死代码只说、本次自造孤儿已清）、第 4 条（规矩冲突按机器约束>多数写法>文档 取用并记账）、**第 6 条（本次新增/修改的代码或测试里不许用 Mockito——注意"已有用法不强制清理"，只有本次碰到的才算违例）**、**第 7 条（测试本身要合格：期望值独立推导、断言真实结果、不断言 mock、不 grep 源码文本、不是变动探测器、掏空实现后不会仍绿、不是靠删/跳过/削弱换来的绿）** **同样逐条给结论**。**另：`tdd` 第 8 条（架构基线 8.1–8.9，除上面那两条硬违例外的其余各条按各自口径判；8.6 是评审信号不是 grep 判死；每条要么给查法的命令与原始输出，要么给"不涉及"的仓库级命令）同样逐条给结论。**
   > **还查一件事（返修轮的卡与证据）/ Also check the fix rounds**: 逐轮看账本——**这一轮改代码/跑测试，是不是真的按 `tdd`/`test` 做了**？判据不是“它说读了卡”，而是**那一轮的 tdd/test 证据齐不齐**（新测试名、红→绿原始输出、邻域回归、`git show --stat HEAD` / `git diff HEAD~1 --stat`；`test` 则是命令 + 原始输出）。**缺了就是没照卡做→写明哪一轮缺什么**。
   > **还查退回重做那几轮（收敛自证）/ Also check the fallback rounds**: 如果账本里有退回重做的记录，逐轮核两件事——①**"这次推翻了上一版的哪个假设"写没写**、以及**它是不是真的换了假设**（把两版方案对起来看：**只重新拆了一遍任务、没动假设 = 原地打转，写明**）；②若那一轮触发了铁律第 8 条的任一信号，**账本里有没有"已报告用户"的记录**。**缺哪条写哪条**（依据在铁律第 7、8 条）。
   > **验证环境是不是当前代码 / Is the verified environment the current code**: 看 `local-verify` 那一轮的证据——**验证前有没有先跑“重建 + 重建/重启环境”并把命令与原始输出贴进账本**？**只跑构建不重启、或只 `restart` 不重建（`docker restart` / `compose restart` / 不带 `--build` 的 `compose up -d`）都不算**；改动后没重建/重启就直接开始验证的，写明。（不需要核时间戳先后——这条靠“动作发生过”，不靠自证数字。）
5. 有问题就列出来，返回实现者改。
   > **每次判 FAIL，都要把判词写进账本**（不是只在对话里说一遍）——**判几次写几条**：**这一轮为什么没过 + 具体问题清单**（每条写清是哪个完成标准/哪段代码、现象、以及属于"旧方案问题"还是"上一轮修改新引入的回归"）。
   > **这是退回重做的前提**：被打回的那一步（`reproduce`/`analyze`）要靠这份判词才知道上一版错在哪（见那两张卡的《退回来的活怎么干》）。**判词只在对话里、账本里没有 = 退回重做时等于瞎改。**
   > 判 pass 时也追加一条：本轮 pass + 逐条完成标准的依据。
6. **返修后必须再派独立 agent 复评**——每轮都必须是独立子 agent 评审，直到明确 pass。实现者自己（包括 grep 自查、自己读代码）不能充当复评。
7. 代码质量这一维度过了（独立 agent 明确说 pass），才算 pass。**通过后：仓库内任务到此完成（它的"交付"判断也在本步做完了）；要发环境的任务进下一步 `deploy`——注意本步 pass 只表示"代码可以发了"，不表示"需求已经交付"，后者由⑨判**；reviewer 本身不 commit、不改任何东西。

1. Use the original requirement/task (the `plan` done-when) as the measuring stick.
   > **Env tasks**: verify only as far as "**the code implements the behaviour the done-when requires**, with evidence" — **whether the requirement is truly delivered on the real environment is NOT concluded here** (that is ⑨'s job), and **you must not send work back just because you cannot picture how it behaves on the real environment**.
   > **Repo-only tasks**: there is no ⑧⑨, so **"judge delivery against the requirement item by item" is done here** — ask of each item "is the thing the requirement asked for actually done now?"; only then does it pass.
2. Go item by item: for each done-when, is it met, and is there evidence?
   - **Also check the "case landing spots"**: take each A-case's landing spot from `plan` and **`ls` / `grep` it yourself** (attach the command and raw output) — does the **test file** exist for `unit` / `e2e`, and the **checklist file** for `manual`? **A missing landing spot, or a spot pointing at a file that does not exist → back to ③ to record it / back to ⑥ to land the checklist** — never record it as "pass".
     > Why this step: **the ledger is deleted at closure**, so a case survives only if it landed in the repo. Closure is executed by the same person who deletes the ledger — **nobody checks their own work** — so the check lives here (⑦).
3. **Adversarial challenge (not just checklist matching)**: matching only finds "on the list but not done"; it can't find "never on the list". So actively hunt for how this implementation breaks:
   - Does it fail silently (wrong result, no error) under **reuse/sharing, concurrency/repeat-trigger, failure paths, empty/boundary, timeout alignment**? — **the test is "the defect is readable in the code"** (which condition, which line, how the result goes wrong). **A mere guess that "it might break on the real environment" does not count**: the real environment is ⑨'s job, and this step does not send work back on that basis.
   - Compare what you find against the `plan` risk scenarios: what did `plan` miss?
   - **Cross-check the impact list independently (this is what catches "didn't know who else depended on it")**: take `plan`'s impact list and the commit message's `## 影响面` section and **search again yourself** — for each existing symbol this change touches, are the listed dependents right? Is anything obviously missing that should have been found? **Send it back if "searched, nothing" stands for something never searched, if "cannot search" was folded into "searched, nothing", or if "cannot verify locally" is being used to mean "did not search".** This is fact-checking: **attach your own search command and its result for every symbol you checked** — including the ones where you found nothing, **not only when you are claiming a miss**.
     > Where this differs from the item above: **"the code shows it will be affected" = send back**; **"I searched and the list missed a dependent" = send back**; **"I guess it might break on the real environment" = does not count** (that is ⑨'s).
   - **Check the "no existing symbol changed" exemption line by line**: look at `git show HEAD --name-only` / `git diff HEAD~1 --name-only` for the files this change touches, **then work through the plan's three-column table (file / which existing symbols it holds / why none was changed) against the diff content** — **check a new-files-only diff too**: does the new code hang off an existing entry point (a new route taking over a path, a new branch changing an existing condition, a new registration displacing the original implementation)? **A file missing from the table, or an existing symbol in the diff (including an existing entry point taken over) while the table says "not changed" → sent back as an integrity problem.**
   - **Entries marked "cannot search"**: this step does **not** verify them (⑨ does, on the real environment) — but do check **whether they were marked honestly**: writing "no impact" where the truth is "cannot confirm" is an integrity problem, and it goes back.
4. Check code quality: readable, maintainable, obvious pitfalls. **And independently re-check every item of `tdd`'s 《写代码时就要守的》 — do not just read the implementer's own account**:
   - **Project constraints**: does the project document coding/architecture conventions (`CONTRIBUTING.md` / ADRs / architecture tests / lint)? Does the **newly added code** break any (especially reaching into another module's internals instead of the project's facade)?
   - **Architecture baseline (check `plan`'s 《架构落位》 against the diff)**:
     - **Paths**: `git diff HEAD~1 --name-only` ⊆ the paths the 落位 declares; anything outside → send back. **Exception (not out-of-bounds)**: a **failure path discovered during implementation that will really happen** (per `tdd` item 1) and **cleanup of orphans this change created, including in other files** (item 2) — `tdd` **requires** both, so never send those back for being off-plan; but they **must already be logged and appended to the 落位** (append an amendment record to the ledger, never rewrite history) — **you compare against the amended declaration**.
     - **Entry symbols**: do the newly added cross-module call sites in the diff target the symbols declared in 落位 item 2? **Anything else (especially another module's internal methods/fields) → send back.**
     - **Public contracts (8.4)**: judge by **the boundary the 落位 declares**, not by the `public` keyword. For contracts the 落位 declares external/cross-module, does the diff remove or change one, or **add a required field**? If so and the 落位 gives no **breakage surface + migration path + migration window** → **send back**. (An intra-module signature change where **every call site is updated in the same commit and nothing outside this change consumes it** is **not** a contract change.)
     - **Cycles (8.1)**: at the **granularity the 落位 declares**, **walk from the new edge's target back to its source across the whole repo** (a diff alone cannot show a cycle); a cycle → **send back**.
     - **"Not engaged" entries**: **re-run each of ③'s commands yourself and attach your own output** (the full form of the impact-list cross-check above, including "**something that should have been found was not → send back**"). **8.1/8.3/8.5/8.7 may not be cleared by diff reverse-lookup** — their violations can live entirely outside the diff. No output of your own → send back.
     - **The 落位 itself is unsound** (wrong paths, a non-existent entry symbol, nine verdicts without repo-level evidence) → **do not send it to the implementer**; route it back to `plan` per the failure routing in **《铁律》 item 4**.
   - **Bloat**: extra abstractions / flags / extension points (interface / strategy / factory / base class before a second caller exists)?
   - **Duplication**: the same logic shape twice or more in this change? **Did the repo already have an implementation that was re-written instead?**
   - **Middle man**: any class/method that does nothing but delegate (a public facade or an existing boundary layer does not count)?
   - **Line-by-line traceability**: walk `git show HEAD` / `git diff HEAD~1` (**this round's code was committed at step ④, so a bare `git diff` is empty**) — does each line really trace to **one of the requirement kinds defined in `tdd` item 1 (including failure paths discovered during implementation)**? **Is the change surface clearly larger than the task needs?**
   - **Orphans**: was code made unused by this change (including in other files) removed?
   - **Test quality (catching “false green”)**: can the tests this change added or modified **actually catch a bug**? Check item by item against `tdd` item 7: (1) is the expected value **derived independently** (or computed with the code under test's own builder/helper → mirror assertion: both sides move together, always green); (2) does the assertion land on a **real result / side effect / exit code** (**asserting only “no error / no exception / returned non-empty” is not an assertion**); (3) does it **assert on the mock itself** (`toHaveBeenCalled`, a `*-mock` element — delete the real implementation and it still passes); (4) does it **grep source text** as a test (should run the thing and assert its effects; reverse guards excepted); (5) is it a **change detector** (only an intentional decision can fail it: a constant's value, exact message wording, private structure); (6) **is the assertion actually reached** (inside a branch never entered, a zero-iteration loop, an iteration over an empty collection, or asserting on data the test just built — **still green after the implementation is hollowed out means it never touched the behavior**); (7) was green **bought by deleting / skipping / weakening tests** (a deleted test, `skip`/`xfail`/`.only`, commented out, `toBe` → `toBeTruthy`, an exact value → "non-empty" — **any removal or relaxation without a stated reason counts**).
     > **Check the “red” too**: look at that round's **raw red output** in the ledger — **did it fail because the feature was missing?** If the red actually came from a broken test, a compile error, a wrong selector, or an environment that would not start, then the test **never proved it can fail**, the red→green cycle does not hold, and it goes **back**.
     > **The reviewer verifies this by hand, not from the implementer's account**: **pick one piece of the implementation and break it in your head** (wrong constant / flipped branch / a side effect removed / empty return / a validation dropped / **hollow it out entirely**) and ask **"would any existing test go red?"** **If none would, that behavior is unprotected → send it back.** This is the external re-check of `tdd`'s mutation check, and the ledger's mutation-check record must be audited against it (if the record says "test X catches it", go look at whether test X really does).
   > A violation → **send it back** (not a “suggestion”). **Severity**: **hard violations → send back** (adding an abstraction/strategy/factory/base class with no second caller; **rewriting something the repo already has**; orphans this change created, including in other files, not cleaned (cross-repo / public API: flag only, see `tdd` item 2); **Mockito used in code or tests this change added or modified (see `tdd` item 6)**; **a mirror assertion / a “no error” assertion / an assertion on a mock / a source-text grep / still green after the implementation is hollowed out / green bought by deleting, skipping or weakening a test (see `tdd` item 7)**; breaking a machine-enforced constraint such as architecture tests / lint / CI; **breaking an architecture-baseline hard violation: 8.1 a new cyclic dependency, or 8.4 a public contract removed/changed, or a newly required field with no "breakage surface + migration path + migration window" (see `tdd` item 8)**). **Other instances of the three smells and requirement/project-constraint mismatches follow the full text of the corresponding `tdd` item** — **this list is only an index; the verdict always follows the full text of each `tdd` item (including its brakes and exemptions), not re-listed here.**
   > **“Suspected” is not a pass**: anything uncertain must be decided on the spot (judge by `tdd`'s brakes) or recorded as "awaiting user adjudication" and left open in the ledger; **never report "pass, with N suspected items"** — unresolved items cannot pass. “Suspected” applies only to **ambiguity in the requirement itself**, never to the code-quality checks.
   > Also give a verdict for `tdd` item 1 (nothing built for the future, no unrequested error handling, searched the repo for an existing implementation), item 2 (no incidental edits to neighbours, matched existing style, unrelated dead code only mentioned, orphans this change created cleaned up), item 4 (rule conflicts resolved as machine constraint > majority pattern > docs, and logged), **item 6 (no Mockito in code or tests this change added or modified — note that "existing usage is not cleaned up by this change", so only what this change touched counts as a violation)**, **item 7 (the test itself must qualify: expectation derived independently, asserts real results, no assertion on a mock, no source-text grep, not a change detector, not still-green after the implementation is hollowed out, and not green bought by deleting/skipping/weakening)**, **and item 8 (the architecture baseline 8.1–8.9 — apart from the two hard violations above, each follows its own wording; 8.6 is a review signal, not a grep death sentence; each entry gives either the check's command and raw output or, for "not engaged", a repo-level command)**.
   > **Also check the fix rounds**: go through the ledger round by round — **did that round's coding/testing actually follow `tdd`/`test`?** The test is **not** "it said it loaded the card" but **whether that round's tdd/test evidence is complete** (new test names, raw red-to-green output, neighbourhood regression, `git show --stat HEAD` / `git diff HEAD~1 --stat`; for `test`: the command + raw output). **If it is missing, that round did not follow the card — state which round is missing what.**
   > **Also check the fallback rounds**: if the ledger records fallbacks, verify two things per round — (1) **is "which assumption of the previous version this overturned" written down**, and **was an assumption genuinely changed** (put the two plans side by side: **re-splitting the same tasks without touching an assumption = spinning in place — say so**); (2) if that round fired any signal from rule 8, **is there a "user was told" record in the ledger**. **Name whichever is missing** (per rules 7 and 8).
   > **Is the verified environment the current code**: look at the `local-verify` round's evidence — **was "rebuild + recreate/restart the environment" run before verifying, with the command and its raw output in the ledger?** **Building without restarting, or `restart` without rebuilding (`docker restart` / `compose restart` / `compose up -d` without `--build`), does not count**; if code changed and verification started without a rebuild/restart, say so. (No timestamp comparison needed — this rests on the action having happened, not on self-reported numbers.)
5. List issues, return to the implementer to fix.
   > **Every FAIL verdict goes into the ledger** (not just said once in the conversation) — **one entry per FAIL**: **why this round did not pass + the concrete problem list** (for each problem: which done-when / which code, the symptom, and whether it is an "original-plan problem" or "a regression newly introduced by the previous round's fix").
   > **This is what a fallback runs on**: the step sent back (`reproduce`/`analyze`) learns what the previous version got wrong from this verdict (see those two cards' "How to redo a sent-back task"). **A verdict that lives only in the conversation, with nothing in the ledger, means the fallback is flying blind.**
   > On a pass, append one too: this round passed + the per-done-when grounds.
6. **After any fix, you MUST spawn an independent agent to re-review** — every round is an independent-subagent review, until it clearly passes. The implementer's own check (including grep / self-reading) is NOT a re-review.
7. Pass only when an independent agent explicitly says pass on the code-quality axis. **After pass: a repo-only task is finished (its delivery judgment was made here too); an env task moves to `deploy` — note that a pass here only means "the code is fit to ship", NOT "the requirement is delivered"; that is judged at ⑨**; the reviewer itself never commits and never changes anything.

## 证据要求 / Evidence

完成时账本必须含：逐条对照结果（每条完成标准：过/没过 + 证据）+ 对抗式挑战的结论（没找到就写“无”）+ **影响面清单的独立核对结论（你核了哪些既有符号、每个都附搜索命令与结果——包括没搜到的；豁免"未改动既有符号"的有没有对着 diff 核过）** + **`tdd`《写代码时就要守的》逐条复核结论（项目约束/膨胀/重复/空壳转发/逐行可追溯/孤儿/**测试质量**/**架构基线 8.1–8.9**，每条给结论）** + **架构基线的核对依据（落位逐项：路径是否越界、入口符号、公共契约、循环依赖、每条"不涉及"**你自己重跑的命令与输出**；以及 8.1–8.9 逐条结论）** + **测试质量复核的具体依据（自证断言/只断言没报错/断言 mock/grep 源码文本/变动探测器，逐项结论；以及"我把哪一处实现改坏、哪个测试会红"的实测结论）** + 评审是谁（独立视角）+ **每一轮的判词（判 FAIL 的：为什么没过 + 问题清单；判 pass 的：逐条依据）** + **需求清单与账本《需求原文》的对账结论（每条 R 对得上哪句原文；对不上就是转述，判 FAIL）**。
> **每次退回重做还要多记两条**：① 这次重做**推翻了上一版的哪个假设**（即第 7 条的"在收敛"自证）；② 如果触发了第 8 条的任一信号，**已报告用户**的记录。**缺这两条 = 那次退回不算做对。**
> 不记账 = 本步不算完成，不能进入下一步。

When done, the ledger must include: the item-by-item result (each done-when: pass/fail + evidence), the outcome of the adversarial challenge (write "none" if nothing found), **the independent cross-check verdict on the impact list (which existing symbols you checked, each with its search command and result — including the ones that came back empty; and whether any "no existing symbol changed" exemption was checked against the diff)**, **the verdict for every item of `tdd`'s 《写代码时就要守的》 (project constraints / bloat / duplication / middle man / line-by-line traceability / orphans / **test quality** / **architecture baseline 8.1–8.9**, each with a verdict)**, **the grounds for the architecture-baseline check (per 落位 item: whether any path was out of bounds, the entry symbols, the public contracts, the cycle walk, and for every "not engaged" entry **your own re-run command and output**; plus a verdict for each of 8.1–8.9)**, **the concrete grounds for the test-quality check (a per-item verdict on mirror assertions / "no error" assertions / assertions on mocks / source-text greps / change detectors, plus the result of "I broke this one thing — does any test go red?")**, who did the review (independent view), **the verdict of every round (on FAIL: why it did not pass + the problem list; on pass: the per-item grounds)**, **and the reconciliation of the requirement list against the ledger's requirement original (which sentence each `R…` maps to; an unmapped item is a paraphrase — FAIL)**.
> **Every fallback must additionally record two things**: (1) **which assumption of the previous version it overturned** (the "is it converging" proof required by rule 7); (2) if any signal in rule 8 fired, **the record that the user was told**. **Missing either one means that fallback was not done properly.**
> No ledger entry = this step is not done; do not proceed to the next step.
