---
name: test
description: "测试。跑全量测试和需求用例，贴出原始输出作为证据。 / Test: run all tests and requirement cases, paste raw output as evidence."
---

# Test / 测试

## 目标 / Goal

这是流程第 ⑤步：代码写完先跑测试，绿了才交下一步（⑥本地验证）。代码跑不起来、测试没绿，就不往后走。

This is step 5: run tests after coding, hand to step 6 (local verification) only once green. If it doesn't run / tests aren't green, it doesn't proceed.

## 做什么 / What to do

1. 跑全量测试 + 本需求 **`单测` 类**的测试用例（`端到端` 类归 ⑥、`人工` 类归 ⑥/⑨，本步不跑、也不因此停下）。
2. **把命令和原始输出贴进账本**，别只写"全过了"。
3. 有失败的，逐条修，直到全绿。

1. Run all tests plus this requirement's **`unit`** test cases (`e2e` cases belong to ⑥ and `manual` to ⑥/⑨; this step neither runs them nor stops for them).
2. **Paste the command and raw output into the ledger** — never just "all passed".
3. Fix failures one by one until green.

## 证据要求 / Evidence

完成时账本必须含：
- 跑的命令（如 `npm test`、`mvn test`）
- 原始输出的关键部分（通过/失败数）
- 需求用例跑完的结果——**按 `plan` 标好的类型**：**`单测` 类**逐条贴实跑结果，**照 `plan` 的 A 编号一条不漏**（`端到端` 类归 ⑥；`人工` 类由非实现者在 ⑥/⑨ 做）
- **影响面清单上"搜到了"的那些使用方**，逐个说清属于哪种：**有测试覆盖的**→跑没跑、结果如何；**没有测试覆盖的**→**如实标成"本地验不了"**（并写明"没测试覆盖"），交给 ⑨（清单上"搜不到"的也归 ⑨）

> **"全绿"要带限定**：全量测试绿只证明**被测试覆盖的部分**没坏——清单上标"搜不到"和"本地验不了"的那些，绿色盖不住它们，**不许写成"整体没坏"**。
> 不记账 = 本步不算完成，不能进入下一步。
When done, the ledger must include: the command(s) run, the key raw output (pass/fail counts), and the result of running the requirement's cases — **by the type `plan` assigned**: every **`unit`** case with its raw run result, **by `plan`'s A-id, none missing** (`e2e` belongs to ⑥; `manual` is done by a non-implementer at ⑥/⑨); plus **each "found" dependent from the impact list, classified**: those **with test coverage** → whether they ran and what the result was; those **without coverage** → **mark them "cannot verify locally" honestly** (naming "no test coverage") and hand them to ⑨ (entries marked "cannot search" also go to ⑨).
> **"All green" needs its qualifier**: a green full suite only proves **the covered parts** are unbroken — entries marked "cannot search" or "cannot verify locally" are not covered by that green, **so never write "nothing is broken"**.
> No ledger entry = this step is not done; do not proceed to the next step.

## 完成标准 / Done when

所有测试绿 + 需求用例里的 **`单测` 类**全过（`端到端` 类归 ⑥；`人工` 类由非实现者在 ⑥/⑨ 做、**结果与产物进 ⑥ 建的那份清单文件**（`plan` 标的落点）——**本步不要求人工产物，也不因此停下**），且账本里有上面列出的全部证据。**本轮的代码已在 ④ 开发完成时 commit 过（一轮一个 commit）；本步不另外 commit。**

> **降级红线**：本步只负责「跑测试 + 贴原始输出」。测试绿只代表测试过，**不代表本地验证（⑥）也过了**；不要拿测试绿去充当⑥的“真跑一遍”。

All tests green + every **`unit`**-type requirement case passing (`e2e` belongs to ⑥; `manual` cases are done by a non-implementer at ⑥/⑨, **with the result and artifact going into the checklist file step ⑥ created** (the landing spot `plan` recorded) — **this step neither requires their artifacts nor stops for them**), with every evidence item listed above logged. **This round's code was already committed at the end of step ④ (one commit per round); this step does not commit again.**

> **No-downgrade line**: this step only does “run tests + paste raw output”. Green tests only prove tests pass — they do NOT prove local verification (⑥) passed; don't use green tests to masquerade as ⑥'s “real run”.
