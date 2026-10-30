---
name: re-verify
description: "测试环境复测 + 交付判断（真正终点）。在测试环境复测用例、按产品需求逐条判交没交对、并把影响面清单上够不着的逐条处理掉；三样都过才算完成。 / Re-verify on the test env and judge delivery (the real finish line): re-run the cases, judge the requirement item by item, AND deal with every unreachable impact-list entry; only when all three pass is the task done."
---

# Re-verify / 测试环境复测

## 铁律 / The rule

**任务的真正终点在这里，不是"发布上去"。** 复测通过才算完成；没通过就回去改，别再往下走。

**"这需求到底交没交对"也在这里判。** 第⑦步 `review` 是**代码质量闸门**——它只判"代码写得好不好、测试可不可信"，**它 pass 不代表可交付**（要发环境的任务，"需求交没交对"不在那一步下结论）。**那条判断是第⑨步的职责。** 所以本步不是"把用例再跑一遍"，而是**真正确认这件东西能不能交**。

The real finish line is here, not "deployed". Only a passing re-verify means done; otherwise go back and fix — do not proceed.

**And "does this actually deliver the requirement" is judged here too.** Step ⑦ `review` is the **code-quality gate** — it judges whether the code is good and the tests are trustworthy, and **its pass does not mean deliverable** (for env tasks it draws no conclusion about requirement delivery). **That judgment is step ⑨'s job.** So this step is not "re-run the cases" — it is the **real confirmation that this can be handed over**.

## 做什么 / What to do

1. 在测试环境上把功能复测一遍，走真实路径。
2. **按 `plan` 标好的用例类型复测**（验收用例就是方案里那些，编号也是那套，不用另找）：
   - `单测` / `端到端` 两类：在测试环境上逐条复测并贴实跑结果——**全通过才算复测通过**。
   - `人工` 类：由**非实现者**（用户，或另一个独立 agent）在测试环境上按方案写的"谁 / 在哪 / 做什么 / 看到什么"去做，留产物。**结果和产物追加进 ⑥ 建好的那份清单文件**（`plan` 标的落点），**不是只记进账本**——账本收尾就删；⑥ 没轮到的 `人工` 用例在本步跑，只记账本的话一样等于没沉淀。
3. **按产品需求逐条判"交没交对"（本步的核心，不只是跑用例）**——拿**用户的原始需求**（不是 `plan` 的用例）逐条问：
   - 这条需求，**在真实环境上真的做到了吗**？
   - 有没有**只有上真环境才暴露**的问题（真实数据、真实依赖、真实并发、权限/配置、上下游不一致）？
   - **用例全过 ≠ 需求交付**：拿需求重新念一遍，别只对着用例打勾。
   - **最常见的一类失败**：**用例全绿，但需求没满足**——那说明 `plan` 的完成标准写歪了（用例没覆盖需求）。**发现了就必须如实写出来并打回**，打回时说清是"完成标准漏了哪条需求"，不要装作是通过。
   > 判据落地：每条需求写一行"**需求原文 → 真实环境上看到了什么 → 交没交对（对 / 不对 / 部分）**"。
4. **把 `plan` 影响面清单上**"搜到了"里**本地没验掉的**、以及**"搜不到"和"本地验不了"两类，在这里逐条验掉**——这是老功能唯一的兜底，也是你（能部署，但不会每次都把老功能走一遍）真正要点的清单：
   - **"搜到了"里本地没验掉的，本步必须验**：清单标了"搜到了"、但它的回归被推给本地却没真跑（④没验、⑤没有覆盖它的 `单测`、⑥没有覆盖它的 `端到端`）——**这类最容易被漏**，它既不在 ⑤ 也不在 ⑥ 的用例里，只能在这里点。**别让"搜到了"变成"没人验过"。**
   - **能验的必须验**：只要测试环境够得着这一条（能点、能调、能看），就**必须真的走一遍**，不许标"验不了"。**"验不了"只留给测试环境确实够不着的**。
   - **标"验不了"的要自证**：写清**试了什么**——**给出一条用户能重跑的具体入口**（页面 URL / 接口 + 参数 / 用的哪个账号），**再写卡在哪**（缺什么数据、缺什么权限、依赖哪个下游没起）。**没写这两样的"验不了"不算数**，按没验处理。写不出可重跑入口的，说明你根本没试到那一步。
   - 逐条记：**验了什么 → 看到了什么 → 老功能还正常吗**。
   - **回归范围就是这张清单，不是"全量测试再跑一遍"**——清单上没有的不用管。
   > **不许用"如实标出"把整张表糊过去**：如果**每一条**都标了"验不了"，这本身就是异常——要么这个测试环境根本不该用来复测（按第③条标"卡住"并找用户），要么是在走过场。**全表"验不了"= 本步不算完成。**
5. 留证据：看到了什么结果、是否符合预期。
6. 判定：
   - **通过**（用例全过 **且** 需求逐条交对 **且** 影响面清单逐条处理完：**"搜到了"里本地没验掉的在测试环境验掉**、"搜不到"和"本地验不了"两类够得着的都真验过、够不着的都按上面自证过）→ 任务完成，删除账本（见 orchestrate 的清理规则）。
   - **发现问题** → **按问题性质回不同的地方，别一律回 `plan`**：
     - **代码/实现问题**（需求清楚，就是没做对）→ 回 `tdd`（开发），改完重新发布、再复测。
     - **方案/方向问题**（需求理解错了、完成标准写歪了、同一类问题反复出现）→ 回 `plan`（出方案），严重的**退回任务入口**（做需求 → `analyze`；修 bug → `reproduce`）——见 `review` 卡《铁律》第 5/6 条。
     - **老功能被改坏**（影响面清单上某条没兜住）→ 回 `tdd` 修；**并把这个使用方补进影响面清单**（④重写 commit message，见 `orchestrate`），说明上一版为什么没搜到。

1. Re-verify the feature on the test environment, walking the real path.
2. **Re-run by the case type `plan` assigned** (the acceptance cases are the plan's, same ids — don't hunt for another list):
   - `unit` / `e2e`: re-run each one on the test environment and paste the real result — **all passing is required**.
   - `manual`: a **non-implementer** (the user, or a separate independent agent) does what the plan says — who / where / what they do / what they see — on the test environment, leaving an artifact. **The result and artifact are appended to the checklist file step ⑥ created** (the landing spot `plan` recorded) — **not only to the ledger**: the ledger is deleted at closure, and `manual` cases that ⑥ did not reach run here, so ledger-only means never deposited.
3. **Judge delivery against the product requirement, item by item — the core of this step, not just running cases** — take the **user's original requirement** (not the `plan`'s cases) and ask of each item:
   - On the real environment, **was this actually delivered?**
   - Are there problems **only the real environment exposes** (real data, real dependencies, real concurrency, permissions/config, upstream/downstream mismatch)?
   - **All cases green ≠ requirement delivered**: re-read the requirement; do not just tick the cases.
   - **The most common failure**: **every case is green but the requirement is unmet** — that means the `plan`'s done-when was written wrong (the cases do not cover the requirement). **If you find it, you must say so and send it back**, stating which requirement the done-when missed — never pretend it passed.
   > Make it concrete: one line per requirement — "**requirement text → what was observed on the real environment → delivered (yes / no / partial)**".
4. **Work through the impact list: the "found" entries that were never verified locally, plus everything in the "cannot search" and "cannot verify locally" categories** — this is the only safety net for the existing features, and it is the list you (who can deploy but do not walk the old features every time) actually have to click through:
   - **"Found" entries not verified locally must be verified here**: the list marks them "found", but their regression was pushed to local and never actually ran (④ did not verify, ⑤ has no `unit` case covering them, ⑥ has no `e2e` case covering them) — **these are the easiest to lose**: they sit in no case at ⑤ or ⑥, so this is the only place they get clicked. **Never let "found" turn into "nobody verified it".**
   - **What can be verified must be verified**: if the test environment can reach the entry (click it, call it, look at it), you **must walk it** — do not mark it unverifiable. **"Cannot verify" is reserved for what the test environment genuinely cannot reach.**
   - **Anything marked "cannot verify" must justify itself**: say **what you tried** — **give a concrete entry point the user can re-run** (page URL / endpoint + parameters / which account) — and then **where it blocked** (which data, which permission, which downstream is down). **An entry without both does not count** — treat it as un-verified. If you cannot produce a re-runnable entry point, you never actually got to that step.
   - Record per entry: **what was verified → what was observed → is the old feature still fine**.
   - **The regression scope is this list, not "run the whole suite again"** — what is not on the list does not need checking.
   > **Do not paper over the whole table with "marked honestly"**: if **every** entry is marked unverifiable, that itself is abnormal — either this environment should not be used for re-verify at all (mark the step blocked per case ③ and ask the user), or the step is being performed as theatre. **An all-unverifiable table means this step is not done.**
5. Keep evidence: what was observed, whether it matches expectation.
6. Decide:
   - **Pass** (all cases pass **and** every requirement item delivered **and** every impact-list entry dealt with: **"found" entries not verified locally are verified on the test environment**, and in the other two categories everything reachable was genuinely walked while everything unreachable justified itself as above) → task done; delete the ledger (see orchestrate's cleanup rule).
   - **Issues found** → **go back to different places depending on the nature of the issue — do not send everything back to `plan`**:
     - **Code/implementation issue** (the requirement is clear; it just is not done right) → back to `tdd`, then redeploy and re-verify.
     - **Approach/direction issue** (the requirement was misunderstood, the done-when was written wrong, the same class of problem keeps returning) → back to `plan`, and for the serious cases **to the task's entry point** (feature → `analyze`; bug fix → `reproduce`) — see the `review` card's rules 5/6.
     - **An existing feature was broken** (an impact-list entry did not hold) → back to `tdd` to fix it; **and add that dependent to the impact list** (rewrite the commit message at ④ — see `orchestrate`), saying why the previous version missed it.

## 证据要求 / Evidence

完成时账本必须含：
- 测试环境上的复测结果（看到了什么、合不合预期）
- 带用例时：**`单测` / `端到端` 两类**用例的复测结果（逐条）
- **按产品需求逐条判"交没交对"的记录**（每条一行："需求原文 → 真实环境上看到什么 → 对 / 不对 / 部分"）——**这一条是"可交付"的依据，不许省**。若发现"用例全绿但需求没满足"，写明是哪条需求、并说清 `plan` 的完成标准漏了什么。
- **影响面清单的逐条处理结果**——每条一行："验了什么（或为什么够不着）→ 看到什么 → 老功能还正常吗"；**"搜到了"里本地没验掉的要单独标出来**（说明它为什么没落在 ⑤/⑥ 的用例里）；标"验不了"的必须带**可重跑的入口 + 试了什么 + 卡在哪**。**这一条是"老功能没被改坏"唯一的依据**。
> **全表都标"验不了" = 本步不算完成**（说明这个环境不该用来复测，按第③条标"卡住"找用户）。
> 不记账 = 本步不算完成，不能进入下一步。

When done, the ledger must include:
- the re-verify result on the test env (what was observed, whether it matches);
- if the requirement carries cases, each **`unit` / `e2e`** case's re-verify result (per case);
- **the item-by-item delivery judgment against the product requirement** (one line each: "requirement text → what was observed on the real environment → yes / no / partial") — **this is the basis for calling it deliverable and must not be skipped**. If "all cases green but requirement unmet" is found, name the requirement and say what the `plan`'s done-when missed;
- **the per-entry result for the impact list** — one line each: "what was verified (or why it is unreachable) → what was observed → is the old feature still fine"; **"found" entries not verified locally must be called out separately** (saying why they fell into no case at ⑤/⑥); anything marked unverifiable must carry **a re-runnable entry point + what was tried + where it blocked**. **This is the only basis for saying the existing features were not broken.**
> **An all-unverifiable table means this step is not done** (it means this environment should not be used for re-verify — mark the step blocked per case ③ and ask the user).
> No ledger entry = this step is not done; do not proceed to the next step.

## 完成标准 / Done when

**三样都过才算完成**：①测试环境复测通过、无遗留问题——**带用例时 `单测` / `端到端` 两类在测试环境逐条复测通过，缺一条就不算完成**（`人工` 类由非实现者做完并留下产物，**结果追加进 ⑥ 建好的清单文件**；不进本条闸门，但也不许跳过）；②**按产品需求逐条判过，每条都交对了**——有任一条没交对（哪怕用例全绿），本步就不算完成；③**影响面清单逐条处理完**——**"搜到了"里本地没验掉的在这里验掉**，"搜不到"和"本地验不了"两类够得着的**真验过**、够不着的按上面**自证过**（写清试了什么、卡在哪）；**全表"验不了"不算完成**。

All three must hold: (1) re-verify passes on test with no leftover issues — **with cases, every `unit`/`e2e` case re-run and passing on the test environment; one missing means not done** (`manual` cases are done by a non-implementer with an artifact, **appended to the checklist file step ⑥ created** — outside this gate, but never skipped); (2) **every product-requirement item has been judged and delivered** — if any item is undelivered, this step is not done, **even if every case is green**; and (3) **every impact-list entry has been dealt with** — **"found" entries not verified locally are verified here**, and in the other two categories everything reachable was **genuinely walked** while everything unreachable **justified itself** (what was tried, where it blocked); **an all-unverifiable table means not done**.
