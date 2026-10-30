---
name: analyze
description: "做需求的前两步：看懂需求要做什么 + 分析现有代码现状。 / Feature steps 1-2: understand the requirement + analyze the existing code."
---

# Analyze / 看懂需求与分析代码

> 本卡用于**做需求**分支的开头两步：①看懂需求要什么、②分析现有代码现状。

## 铁律 / The rules

1. **先讲清"要做什么"**：用你自己的话复述需求，说清做完后用户能得到什么，别急着想代码。**复述是你的理解，不能替代原文**——原文另贴进账本（第 5 条），两份都要有。
2. **把需求拆成一条一条**：需求里每一条"用户能看见的行为"，单独列出来并编号（R1、R2…），每条写清"做完是什么样"。
   > **这份清单就是 `plan` 逐条对照的底稿——这里漏一条，后面就一定漏一条。** 含糊的、讲不通的当场问用户，不要自己补。
3. **先摸清现状**：动手前看清现有代码长什么样、跟这个需求相关的部分在哪，别凭空设计。
4. **被退回重做时（先读账本，再动手）**：如果这一轮是 `review` 判回来的（《第 7 步后的分叉》），**开干前先读账本**——特别是上一轮的 `analyze`/`plan`/`tdd` 记录和评审写下的失败判词。
   > **读账本是这一步的入场券，不是可选项**：没读账本就重做，等于把上一轮的死法再走一遍。
   > **你是一个"干净的脑子"**：退回重做时 orchestrator 会**另起一个全新的子 agent** 跑这一步 + `plan`，只给它账本、原始需求和代码现状，**不给它上一版的方案**。所以**别去找上一版方案"接着改"**——从账本里的**事实**（判词、失败现象、命令输出）出发，**先假设上一版的方向是错的**。（退回是为了**换方向**，而方向是在 `plan` 定的，所以入口卡和 `plan` 一起换。）
   > 读完必须先写清**"上一版错在哪"**（分析错在哪 / 方案错在哪 / 实现错在哪），**并且逐条回答账本里每条教训的归宿**（见《退回来的活怎么干》），再谈新的需求清单。
   > **不许把上一版的需求清单 R1、R2… 当既定事实接着用**——它本身就是上一轮失败的一部分，要重新核一遍。
5. **需求原文来自用户给的截图**：需求包常常是文字截图（聊天记录、PRD 页面、报错截图）。先读图，把原文**逐字**贴进账本第 1 步的一块《需求原文》里，`R1、R2…` 每条都要能对上原文里的一句——**不许猜，也不许用你自己的话把需求改写一遍然后当原文**。看不清、截断、前后矛盾，**攒成一次**问用户（不要一句一问）；本会话读不了图就直说"我看不了图，请把文字贴过来"，**不许凭推测把内容补全**。
6. **代码现状只信代码**：`README`、`docs/`、设计文档、注释**只能当参考**——**连"顺着文档去找代码"都不行**，文档里的路径、类名、流程经常是旧的。定位靠搜：`grep` / `glob` 关键符号、入口函数、调用链、测试。每条结论都要能指到 `文件:行`；**文档和代码打架时以代码为准**，并把那处冲突记进账本（哪份文档、它说了什么、代码实际怎样）。
   > **范围**：这条管的是"拿文档当代码现状、当证据"。项目**明文写下的约定**（`docs/ADR`、`CONTRIBUTING` 里的规则、接口规范）属于 `tdd` 卡第 4 条（先守本项目的规矩）那一档，仍然按它来——但它也只是约束，**不是代码现状**，"现在到底怎么实现"照样要读代码。
   > **证据分两种**：**肯定结论**（"这里就是这么实现的"）必须指到 `文件:行`；**存在性否定**（"代码里没有这个东西"）必须给**搜索命令 + 原始输出 + 用过哪几种搜法**——照 `plan`《影响面》里"搜了没有"的标准，**不许把"我没搜"写成"搜不到"**。
   > **搜索痕迹要留在账本里**：定位时用过的命令（`grep`/`glob` + 关键词）贴进账本第 2 步的结果。**"从 README 里看到路径、打开文件、报了 `文件:行`"不算读了代码**——从文档里看到的名字，必须再用搜索确认它还在代码里，才算数。

1. **Clarify "what to build" first**: restate the requirement in your own words — what does the user get when done — before thinking about code. **Your restatement is your understanding and never replaces the original** — paste the original into the ledger too (rule 5); you need both.
2. **Break the requirement into items, one by one**: every "behaviour the user can see" gets its own numbered line (R1, R2 …), each saying what "done" looks like.
   > **This list is the basis `plan` checks against item by item — miss one here and you will miss one there.** Anything vague or incoherent: ask the user; don't fill it in yourself.
3. **Understand the current state first**: look at the existing code and where it relates, before designing anything in a vacuum.
4. **When this is a redo after a fallback — read the ledger first**: if `review` sent this back (see "Branch after step 7"), **read the ledger before doing anything** — above all the previous round's `analyze`/`plan`/`tdd` entries and the reviewer's failure verdicts.
   > **Reading the ledger is the entry ticket for this step, not an option**: redoing without reading it just replays the previous round's way of dying.
   > **You are a "clean head"**: on a redo the orchestrator **spawns a brand-new subagent** to run this step + `plan`, given only the ledger, the original requirement and the code as it stands — **not the previous plan**. So **do not go find the previous plan and "continue" it**; start from the **facts** in the ledger (verdicts, failure symptoms, command output) and **assume the previous direction was wrong**. (A fallback exists to **change direction**, and direction is set in `plan` — so the entry card and `plan` are swapped together.)
   > After reading, first write down **"what the previous version got wrong"** (analysis / plan / implementation) **and answer, item by item, where each lesson in the ledger ended up** (see "How to redo a sent-back task"), then produce the new requirement list.
   > **Never carry the previous version's requirement list (R1, R2 …) over as fact** — it is part of what failed; re-check it.
5. **The requirement's source text is whatever the user handed over as a screenshot**: requirement packages often arrive as images of text (chat logs, a PRD page, a bug-report screenshot). Read the image first and paste the original **verbatim** into a 《需求原文》 block in ledger step 1; every `R1, R2 …` must map to one sentence of that original — **never guess, and never restate the requirement in your own words and pass that off as the original**. If it is unreadable, truncated or self-contradictory, **collect the questions and ask once** (not one per turn); if this session cannot read images, say so — "I cannot see images, please paste the text" — and **never fill the gaps by guessing**.
6. **The current code counts only as code**: `README`, `docs/`, design notes and comments are **background only** — **they are not even a way to find the code**; paths, class names and flows in a document are regularly stale. Locate by searching: `grep` / `glob` the key symbols, entry functions, call chains and tests. Every conclusion must point at a `file:line`; **when a document and the code disagree the code wins**, and record that conflict in the ledger (which document, what it said, what the code actually does).
   > **Scope**: this rule governs "a document as the current state or as evidence". A convention the project **states in writing** (`docs/ADR`, rules in `CONTRIBUTING`, interface specs) is the tier of rule 4 in the `tdd` card (follow this project's own rules first) and is still followed — but it is a constraint, **not the current state**; "how is this implemented today" still requires reading the code.
   > **Two kinds of evidence**: a **positive claim** ("this is how it is implemented") must point at a `file:line`; an **existence-negative** ("this thing is not in the code") must come with the **search command, its raw output, and which search methods were used** — the same bar as `plan`'s "searched, found nothing", and **never write "I did not search" as "it cannot be found"**.
   > **Leave the search trail in the ledger**: paste the commands you used to locate things (`grep`/`glob` plus the keywords) into ledger step 2's result. **"I saw a path in the README, opened the file and reported a `file:line`" is not reading the code** — a name you saw in a document must be confirmed by a search that it still exists in the code before it counts.

## 流程 / Steps

1. 复述需求：目标是什么、边界在哪、有什么不确定的。
2. **把需求拆成一条一条并编号**：每条 = 一个"用户能看见的行为"，写清做完是什么样。含糊的当场问用户。
3. 定位现有代码里相关的部分（文件、模块、入口）——**靠搜代码，不靠文档指路**（见铁律第 6 条）。
4. 把"现状"和"要变成什么样"的差距列清楚。
5. 带着这份理解回到 `plan`（出方案）——`plan` 会逐条对着这份清单列 todo。
   > **被退回重做时**：第 2 步之前先走一遍《退回来的活怎么干》（读账本 → 写"上一版错在哪" → 逐条闭合教训）。

1. Restate the requirement: the goal, its boundaries, and anything unclear.
2. **Break it into numbered items**: each = one "behaviour the user can see", with what "done" looks like. Ask the user about anything vague.
3. Locate the relevant parts of the existing code (files, modules, entry points) — **by searching the code, not by following a document** (rule 6).
4. Spell out the gap between "current state" and "desired state".
5. Take this back to `plan` — it lists todos against this list item by item.
   > **On a redo after a fallback**: before step 2, work through "How to redo a sent-back task" (read the ledger → write "what the previous version got wrong" → close every lesson).

## 退回来的活怎么干 / How to redo a sent-back task

> 这段只在**被 `review` 退回重做**时才走（**仅缺依据的打回不算退回重做**——照 `review` 铁律第 9 条补依据即可，不用换干净脑子）。第一次开工没有上一轮，但**铁律第 4 条那条"退回时要先读账本"的规则照旧成立**——只是这一轮不适用。

退回后**先做这三件事，再谈新方案**：

1. **读账本**：上一轮的 `analyze`/`plan`/`tdd` 记录 + 评审每次判 FAIL 时写下的失败判词（`review` 卡要求写进账本）。**读不到判词就先问用户/评审要**——只知道"被打回来了"、不知道"为什么"，等于没读。
2. **写"上一版错在哪"**：逐条列出——分析错在哪 / 方案错在哪 / 实现错在哪。这是**结论性判断**，不是复述账本。
3. **逐条闭合教训**：账本里每条教训都要有归宿，做成对照表：

   | 账本里的教训 | 这版怎么处置 | 判词 |
   |---|---|---|
   | <上一轮为什么没过 / 哪条是错判> | <新清单里哪一条 / 哪个动作负责它> | <已规避 / 仍然存在（写明为什么这次不构成问题） / 已不适用> |

   > **每条教训都必须有判决**，不许留空、不许只写一段"这次会注意"的总结。**判"仍然存在"的必须在方案里说明为什么这次不构成问题**，否则就是没处理。

**证据要求**：账本里必须有上面这张**教训 → 处置 → 判词**的表，外加"上一版错在哪"的逐条判断。**没有这张表 = 本步不算完成，不许进 `plan`。**

## How to redo a sent-back task

> This section is used **only when `review` has sent the task back** (a fallback for **missing grounds** is not a redo — supply the grounds per rule 9 of `review`; no clean-head reset). A first run has no previous round, but **rule 4 of 铁律 still stands** — it simply does not apply yet.

Do these three things **before** proposing anything new:

1. **Read the ledger**: the previous round's `analyze`/`plan`/`tdd` entries **plus the failure verdict the reviewer wrote each time it failed** (the `review` card requires it in the ledger). **If the verdict is missing, ask the user/reviewer for it** — knowing "we were sent back" without knowing "why" is not reading it.
2. **Write "what the previous version got wrong"**: item by item — analysis / plan / implementation. This is a **judgement**, not a retelling of the ledger.
3. **Close every lesson**: each lesson in the ledger must land somewhere, as a table:

   | Lesson in the ledger | How this version handles it | Verdict |
   |---|---|---|
   | <why the last round failed / which call was wrong> | <which item of the new list / which action owns it> | <avoided / still present (say why it is not a problem this time) / no longer applies> |

   > **Every lesson needs a verdict.** No blanks, and no vague "we'll be careful this time" paragraph. **"Still present" is only acceptable if the plan explains why it is not a problem now** — otherwise it was not handled.

**Evidence**: the ledger must contain that **lesson → handling → verdict** table plus the item-by-item "what the previous version got wrong". **No table = this step is not done; do not proceed to `plan`.**

## 证据要求 / Evidence

完成时账本必须含：
- 对需求的一句话复述（目标 + 边界）
- **需求逐条清单**（编号 + 每条"做完是什么样"）
- 找出的相关代码位置 + 现状与目标的差距
- **被退回重做时**：还要有《退回来的活怎么干》里那张**教训 → 处置 → 判词**表 + "上一版错在哪"的逐条判断

> 不记账 = 本步不算完成，不能进入下一步。

When done, the ledger must include: a one-line restatement of the requirement (goal + boundary); **the numbered requirement list** (id + what "done" looks like for each); and the located code spots plus the current-vs-desired gap. **On a redo after a fallback**, it must also include the **lesson → handling → verdict** table from "How to redo a sent-back task" plus the item-by-item "what the previous version got wrong".
> No ledger entry = this step is not done; do not proceed to the next step.

## 注意 / Notes

有不确定的地方要问用户，不要自行揣测需求。看不懂的现状记成"信息缺口"，不要装懂。

Ask the user about anything unclear — don't guess the requirement. Record what you can't understand as an "information gap", not as a confident assumption.
