---
name: reproduce
description: "修 bug 的前两步：稳定复现问题 + 定位根因。先复现，单假设，最小验证。 / Bug-fix steps 1-2: reliably reproduce + locate root cause. Reproduce first, one hypothesis at a time, minimal verification."
---

# Reproduce / 复现与定位

> 本卡用于**修 bug** 分支的开头两步：①复现问题、②定位原因。

**每一步动手前，先停一秒问自己：我建账本了吗？我向用户汇报了吗？没做到就停下补。**

**Before every action, pause and ask: did I create the ledger? did I report to the user? If not, stop and do it first.**

## 铁律 / The rules

1. **先复现**：没能稳定复现之前，不要猜原因。
2. **必须找出根因**：本步的"完成" = **稳定复现 + 明确根因**，两个都要。
   > **只复现出问题、说不出根因，本步就不算完成**，不许进 `plan`。拿着"现象"去出修复方案，一定修错地方——这是最常见的返工来源。
   > 根因要**具体到代码位置**（哪一行 / 哪个条件 / 哪个缺失），不能是"可能是并发问题"这种方向性猜测。
   > **根因不止一个时，逐条编号（B1、B2…）**，每条写明"哪个位置、什么问题"——`plan` 要拿这份编号逐条对照着出方案。
   > **不许拿文档里的描述当根因**：也不是"设计文档说这里应该走 A 分支，所以是 bug"——文档只能当背景；根因只能是你读到的代码位置（`文件:行` + 什么条件下出错）。
3. **同一时刻只验证一个假设**：列出可能原因，一次只测一个，别一股脑乱试。
4. **最小验证**：用最小的改动/输入来证实或否定当前假设，别顺带改别的东西。
5. **被退回重做时（先读账本，再动手）**：如果这一轮是 `review` 判回来的（《第 7 步后的分叉》），**开干前先读账本**——特别是上一轮的 `reproduce`/`plan`/`tdd` 记录和评审写下的失败判词。
   > **读账本是这一步的入场券，不是可选项**：没读账本就重做，等于把上一轮的死法再走一遍。
   > **你是一个"干净的脑子"**：退回重做时 orchestrator 会**另起一个全新的子 agent** 跑这一步 + `plan`，只给它账本、原始需求和代码现状，**不给它上一版的方案**。所以**别去找上一版方案"接着改"**——从账本里的**事实**（判词、失败现象、命令输出）出发，**先假设上一版的方向是错的**。（退回是为了**换方向**，而方向是在 `plan` 定的，所以入口卡和 `plan` 一起换。）
   > **上一版的根因清单（B1、B2…）本身就是重点怀疑对象**：退回重做**最常见的原因就是根因找错了**（修了错的地方，怎么修都过不了）。所以退回后**先逐条证伪上一版的 B 清单**——它到底是不是根因？证据还在不在？**不许把它当既定事实接着用**，也不许在它上面直接改。
   > **旧编号怎么处置**：复核后**仍然成立**的，**保留原编号**并写清证据；**被推翻的作废**，新根因**重新编号 B1、B2…**（从头编，不要接着旧号往下排），并注明它由哪条旧 B 演化而来（或"旧 B 全被推翻"）。这样 `plan` 的对照表和评审的判词都能指回确定的那一条。
   > 读完必须先写清**"上一版错在哪"**，并逐条回答账本里每条教训的归宿（见《退回来的活怎么干》）。

1. **Reproduce first**: don't guess the cause until you can reproduce it reliably.
2. **You must find the root cause**: this step is "done" only when **reliable reproduction + a definite root cause** are both in hand.
   > **Reproducing the symptom without naming the cause means this step is NOT done** — do not move to `plan`. Building a fix on a symptom is how you fix the wrong place; it is the most common source of rework.
   > The root cause must **name the code location** (which line / which condition / what is missing), not a direction like "probably a concurrency issue".
   > **If there is more than one, number them (B1, B2, …)**, each saying "which location, what problem" — `plan` maps its tasks against that numbered list.
   > **Never let a document's prose stand in as the root cause** — "the design doc says it should take branch A, so this is a bug" is not a root cause either. Documents are background only; a root cause is a code location you read (`file:line` plus the condition under which it breaks).
3. **One hypothesis at a time**: list possible causes; test one at a time, never a pile at once.
4. **Minimal verification**: use the smallest change/input to prove or kill the current hypothesis — don't fiddle with other things on the side.
5. **When this is a redo after a fallback — read the ledger first**: if `review` sent this back (see "Branch after step 7"), **read the ledger before doing anything** — above all the previous round's `reproduce`/`plan`/`tdd` entries and the reviewer's failure verdicts.
   > **Reading the ledger is the entry ticket for this step, not an option**: redoing without reading it just replays the previous round's way of dying.
   > **You are a "clean head"**: on a redo the orchestrator **spawns a brand-new subagent** to run this step + `plan`, given only the ledger, the original requirement and the code as it stands — **not the previous plan**. So **do not go find the previous plan and "continue" it**; start from the **facts** in the ledger (verdicts, failure symptoms, command output) and **assume the previous direction was wrong**. (A fallback exists to **change direction**, and direction is set in `plan` — so the entry card and `plan` are swapped together.)
   > **The previous version's root-cause list (B1, B2 …) is itself a prime suspect**: the most common reason to be sent back is that **the root cause was wrong** (the wrong place was fixed, so no amount of fixing passes). So on a redo, **first falsify the previous B list item by item** — is each one really a root cause? Does its evidence still hold? **Never carry it over as fact**, and never patch on top of it.
   > **What happens to the old ids**: one that **still holds** after re-checking **keeps its id** (write down the evidence); an **overturned one is retired**, and the new root causes are **renumbered from B1** (start over — do not continue the old sequence), noting which old B each evolved from (or "all previous B's were overturned"). Then `plan`'s mapping table and the reviewer's verdicts can always point at a definite item.
   > After reading, first write down **"what the previous version got wrong"** and answer, item by item, where each lesson in the ledger ended up (see "How to redo a sent-back task").

## 流程 / Steps

1. 复现问题，记下能稳定触发的步骤。
2. 列出所有可能的原因假设。
3. 从最可能的一个开始，设计最小验证去证实或排除它。
4. 排除一个，划掉一个，换下一个，直到找到根因。
5. 找到根因后，停下——带着明确的根因回到 `plan`（出修复方案），不要顺手直接大改。**根因没得到用户确认之前，禁止写修复代码、禁止改任何业务文件。**
   > **被退回重做时**：第 2 步之前先走一遍《退回来的活怎么干》（读账本 → 逐条证伪上一版 B → 写"上一版错在哪" → 逐条闭合教训）。

1. Reproduce the bug; record reliable trigger steps.
2. List every possible cause.
3. Starting from the most likely, design a minimal verification to prove or eliminate it.
4. Eliminate one, cross it off, move to the next, until the root cause is found.
5. Once the root cause is found, stop — go back to `plan` with that cause; don't jump into a big fix. **Until the user confirms the root cause, do NOT write fix code or change any business file.**
   > **On a redo after a fallback**: before step 2, work through "How to redo a sent-back task" (read the ledger → falsify the previous B list → write "what the previous version got wrong" → close every lesson).

## 退回来的活怎么干 / How to redo a sent-back task

> 这段只在**被 `review` 退回重做**时才走（**仅缺依据的打回不算退回重做**——照 `review` 铁律第 9 条补依据即可，不用换干净脑子）。第一次开工没有上一轮，但**铁律第 5 条那条"退回时要先读账本"的规则照旧成立**——只是这一轮不适用。

退回后**先做这四件事，再谈新根因**：

1. **读账本**：上一轮的 `reproduce`/`plan`/`tdd` 记录 + 评审每次判 FAIL 时写下的失败判词（`review` 卡要求写进账本）。**读不到判词就先问用户/评审要**——只知道"被打回来了"、不知道"为什么"，等于没读。
2. **逐条证伪上一版的根因（本卡特有）**：上一版的 B1、B2… 每条都要重新问一遍"它到底是不是根因"，**允许推翻**。退回重做最常见的原因就是根因找错了。
   > 不许跳过这一步直接找新根因——那样很可能又找一个错的。
   > **编号规则**：复核后仍然成立的**保留原编号**（写证据）；被推翻的**作废**，新根因**重新编号 B1、B2…**（从头编，不接旧号），并注明由哪条旧 B 演化而来。
3. **写"上一版错在哪"**：逐条列出——根因错在哪 / 方案错在哪 / 实现错在哪。这是**结论性判断**，不是复述账本。
4. **逐条闭合教训**：账本里每条教训都要有归宿，做成对照表：

   | 账本里的教训 | 这版怎么处置 | 判词 |
   |---|---|---|
   | <上一轮为什么没过 / 哪条是错判> | <新根因清单里哪一条 / 哪个动作负责它> | <已规避 / 仍然存在（写明为什么这次不构成问题） / 已不适用> |

   > **每条教训都必须有判决**，不许留空、不许只写一段"这次会注意"的总结。**判"仍然存在"的必须在方案里说明为什么这次不构成问题**，否则就是没处理。

**证据要求**：账本里必须有上面这张**教训 → 处置 → 判词**的表 + "上一版错在哪"的逐条判断 + **上一版每条 B 的复核结论**（推翻的写推翻理由，保留的写证据）。**缺任何一项 = 本步不算完成，不许进 `plan`。**

## How to redo a sent-back task

> This section is used **only when `review` has sent the task back** (a fallback for **missing grounds** is not a redo — supply the grounds per rule 9 of `review`; no clean-head reset). A first run has no previous round, but **rule 5 of 铁律 still stands** — it simply does not apply yet.

Do these four things **before** proposing a new root cause:

1. **Read the ledger**: the previous round's `reproduce`/`plan`/`tdd` entries **plus the failure verdict the reviewer wrote each time it failed** (the `review` card requires it in the ledger). **If the verdict is missing, ask the user/reviewer for it** — knowing "we were sent back" without knowing "why" is not reading it.
2. **Falsify the previous root causes, one by one (specific to this card)**: ask again of each B1, B2 … — is it really a root cause? **Overturning it is allowed and expected.** The most common reason to be sent back is that the root cause was wrong.
   > Do not skip this and jump to a new root cause — you will likely pick another wrong one.
   > **Numbering**: one that **still holds** keeps its id (with the evidence); an **overturned one is retired** and the new root causes are **renumbered from B1** (start over, do not continue the old sequence), noting which old B each evolved from.
3. **Write "what the previous version got wrong"**: item by item — root cause / plan / implementation. This is a **judgement**, not a retelling of the ledger.
4. **Close every lesson**: each lesson in the ledger must land somewhere, as a table:

   | Lesson in the ledger | How this version handles it | Verdict |
   |---|---|---|
   | <why the last round failed / which call was wrong> | <which item of the new root-cause list / which action owns it> | <avoided / still present (say why it is not a problem this time) / no longer applies> |

   > **Every lesson needs a verdict.** No blanks, and no vague "we'll be careful this time" paragraph. **"Still present" is only acceptable if the plan explains why it is not a problem now** — otherwise it was not handled.

**Evidence**: the ledger must contain that **lesson → handling → verdict** table, the item-by-item "what the previous version got wrong", **and the re-check verdict for every previous B** (overturned → why; kept → the evidence). **Missing any of them = this step is not done; do not proceed to `plan`.**

## 证据要求 / Evidence

完成时账本必须含：
- 稳定的复现步骤
- **明确到代码位置的根因**（哪一行 / 哪个条件 / 哪个缺失；不止一个时逐条编号 B1、B2…）+ 支撑它的证据（命令 + 原始输出）
- 排除过的假设清单（试了什么、结果如何、排除了谁）
- **被退回重做时**：还要有《退回来的活怎么干》里那张**教训 → 处置 → 判词**表 + "上一版错在哪"的逐条判断 + **上一版每条 B 的复核结论**

> **只复现、没找出根因 = 本步未完成**，不许进 `plan`。
> 不记账 = 本步不算完成，不能进入下一步。
When done, the ledger must include: the reliable reproduction steps; the **root cause named down to the code location** (which line / which condition / what is missing; numbered B1, B2, … when there is more than one) with the evidence that supports it (command + raw output); and the list of hypotheses eliminated (what you tried, the result, which one it killed). **On a redo after a fallback**, it must also include the **lesson → handling → verdict** table from "How to redo a sent-back task", the item-by-item "what the previous version got wrong", and **the re-check verdict for every previous B**.
> **Reproduced but no root cause = this step is NOT done** — do not move to `plan`.
> No ledger entry = this step is not done; do not proceed to the next step.

## 注意 / Notes

每次试完，把"试了什么、结果如何、排除了哪个假设"写进账本，别让推理只留在脑子里。

After each attempt, log "what you tried, the result, which hypothesis was eliminated" into the ledger.
