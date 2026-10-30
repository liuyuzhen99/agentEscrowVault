---
name: tdd
description: "测试驱动开发。先写一个会失败的测试，再写让它通过的最少代码。 / Test-driven development: write a failing test first, then the minimum code to make it pass."
---

# TDD / 测试驱动开发

## 铁律 / The rule

**没有失败的测试，不许写实现。** 先让测试红，再写代码让它绿。

**No implementation without a failing test first.** Make the test red, then write code to make it green.

## 循环 / The loop

1. 写一个失败的测试（红）——它精确表达你要的行为。
2. 跑一下，确认它确实因为"功能还没做"而失败，不是因为测试写错了。
3. 写**最少的**代码让它通过（绿）。
4. 跑全部测试，确认没弄坏别的。
5. 重复，直到这个任务的所有测试都绿。

> **风险场景要落成测试 / Turn risk scenarios into tests**：逐个过 `plan` 列出的风险场景，想“我的实现遇到它会怎样”；凡是**可能静默出错**的（不报错、但结果不对），就要写一个测试把它钉住。尤其注意“复用/并发/重复触发/异常”这四类——它们最容易“看起来对、实则错”。
>
> **Go through each risk scenario from `plan` and ask "what does my implementation do when it happens?" For any that could fail silently — wrong result without an error — write a test that pins it. Watch reuse / concurrency / repeat-trigger / failure paths especially: these most often look right but aren't.**

> **改完要回归“邻域”——照着 `plan` 的影响面清单打勾，不是凭感觉 / Re-verify the neighborhood — work down `plan`'s impact list, do not improvise it**：**"邻域"是哪些，`plan` 已经逐个搜过并写在影响面清单里了，不要临场另想一套。** 改完逐条对着清单验：
> - **清单上"搜到了"的**：逐个验它的使用方没被撞坏（能写成命令的就写成命令）。
> - **清单上"搜不到"的**：本地验不了就**如实标出来**，交给 ⑨ 在测试环境验——**不许跳过，也不许写成"应该没事"**。
> - **清单外你真的又想到了别的受影响处**：验它，并**补进影响面清单**（④重写 commit message，见 `orchestrate`）。
> 把逐条结果写进账本。（为什么：见 dev-harness 仓库的 `docs/rationale.md`，**卡不含该文件**。）
>
> **The "neighborhood" is not yours to improvise: `plan` already searched for it and wrote it into the impact list — verify against that list, item by item.** For each entry marked **found**, verify its dependents were not broken (a command where a command is possible). For each entry marked **cannot search**, say so honestly if it cannot be checked locally and hand it to ⑨ for the test environment. For each entry marked **cannot verify locally**, likewise hand it to ⑨ — **never skip it, never write "should be fine"**. If you do think of something else affected that is not on the list, verify it **and add it to the list** (rewrite the commit message at ④ — see `orchestrate`). Log the per-item results in the ledger. (Why: see `docs/rationale.md` in the dev-harness repo — **cards do not ship this file**.)

> **批量改动要谨慎 / Be careful with bulk edits**：用正则/批量替换改代码时，**先用最窄的模式定位，确认命中的正好是你打算改的那些位置**（改前先把命中清单过一遍）——尤其避免连带命中长得像的邻近调用；然后**逐点改写**（多点机械改动也可，但要逐点核过命中清单）；**不要用宽泛正则**一口气改一片。把命中清单与逐点改动记入账本。
>
> **When changing code with regex/bulk replacement: first narrow the pattern so its hits are exactly the sites you intend to change (review the hit list before editing)** — especially avoid also hitting lookalike nearby calls; then **edit point by point** (multi-site mechanical edits are fine, but check each against the hit list); do NOT use a broad regex to change a whole region at once. Log the hit list and the point-by-point edits in the ledger.

1. Write one failing test (red) — it states exactly the behavior you want.
2. Run it; confirm it fails *because the feature is missing*, not because the test is buggy.
3. Write the *minimum* code to make it pass (green).
4. Run all tests to confirm nothing else broke.
5. Repeat until every test for this task is green.

## 写代码时就要守的 / Write it right the first time

> **这一节是在你写代码那一刻生效的。绿了不算完——写出来的东西不能比必要的更复杂。**
>
> **This section applies the moment you write code. Green is not enough — what you wrote must not be more complex than the job needs.**

**1. 只写需求要的，不写“以后可能需要”的 / Build only what the requirement needs.**
**先说清“需求”是什么 / First, what counts as “the requirement”**：= 用户的需求 + `plan` 里已确认的风险场景 + **实现中新发现的、真实会发生的失败路径** + 项目约束（第 4 条）+ 本次改动直接产生的必要清理（第 2 条）。**这五类都算；不在里面的才算多余。**
The requirement = what the user asked for + the **confirmed risk scenarios from `plan`** + **failure paths discovered during implementation that will really happen** + project constraints (item 4) + cleanup your own change necessarily produces (item 2). **All five count; only what's outside them is extra.**

**新发现的风险场景要记账，不许拿来当“加东西”的借口 / Log newly found risk scenarios — don't use them as a licence to build more**：实现中途发现的新失败路径，**先写进账本（触发条件 + 原 plan 没有）再动手**；**用户确认后新增/改写的风险场景，账本记“旧→新”**。评审会按这条记录复核：**真的会出现、且当前实现真会错 → 算这一类（不得因“计划外”打回）；只是“万一呢”的担心 → 不算需求。**
A failure path found mid-implementation: **log it first (its trigger + that the original `plan` missed it), then fix it**; **if a risk scenario is added/rewritten after user confirmation, log old→new**. Review checks this record: **a path that will really happen and that the current implementation really gets wrong counts as this category (never send it back just for being “off-plan”); a bare “what if” worry does not count.**

**动手前先搜一遍仓库里有没有现成的实现/工具函数**——有就复用或扩展现有的，**别另写一个**（“仓库里已经有、我又写了一个”是最常见的膨胀）。
**Before writing, search the repo for an existing implementation / utility** — reuse or extend it, **don't write another one** ("it already exists and I wrote a second one" is the most common bloat).

不要为“将来可能要”加抽象层、开关参数、预留扩展点、没人用的接口实现。没有第二个调用方之前，不要抽接口/策略/工厂/基类。**没要求的错误处理不要写——但风险场景里真实会发生的失败路径不算“没要求的错误处理”，该写测试的照写。** **写了 200 行、本来 50 行能写完的，重写**（绿了之后再改写，必须重跑测试 + 邻域回归并重新记账）。写完问自己：“资深工程师会说这写复杂了吗？”

No abstractions, flags, extension points, or interface implementations added for a future that isn't here. No splitting into interface / strategy / factory / base class before a second caller exists. **No error handling for cases the requirement doesn't have — but a failure path that the risk scenarios say will really happen is NOT "an error case the requirement doesn't have"; write the test for it.** **If you wrote 200 lines and 50 would do, rewrite it** (if you rewrite after green, re-run tests + neighborhood regression and log again). Ask: “would a senior engineer call this overcomplicated?”

**2. 只碰必须碰的 / Touch only what you must.**
不要“顺手”改进相邻代码、注释、格式；不要重构没坏的东西；**匹配既有风格**（哪怕你更喜欢别的写法）。发现与本次无关的死代码——**只说，不删**（写进账本结果行，不另开文档）。但本次改动**自己造成的孤儿（没人用的 import/变量/方法）要自己删掉**——**包括其它文件里因本次改动才变得没人用的（哪怕它以前是活代码）；删前先搜调用方确认没人用再删（跨仓库/公开 API 不删，标出来）。**

Don't “improve” adjacent code, comments or formatting; don't refactor what isn't broken; **match the existing style** even if you'd do it differently. Notice unrelated dead code — **mention it, don't delete it** (write it in the ledger's result line; don't open a separate document). But orphans **your own change** created must be removed by you — **including things in OTHER files that only became unused because of this change** (even if they were live code before); **search for other callers first, then delete** (cross-repo / public API: don't delete, flag it).

**不碰 ≠ 不验证 / Not touching ≠ not verifying**：只碰必须碰的指的是“改不改”，**邻域验证照做**（见上文《改完要回归“邻域”》）——不要拿这一条当“相邻不用管”的依据。
**“Touch only what you must” governs what you EDIT — neighborhood verification still applies** (see《改完要回归“邻域”》above). Do not cite this item as a reason to skip it.

**3. 每一行改动都要能追溯到需求 / Every changed line traces to the request.**
把改动逐行过一遍（**逐行核的是实现代码**；测试代码只需追溯到它钉住的风险场景/用例——**不许因为“需求里没写”就删掉风险场景的测试**）：**这行是为了满足上面哪一类需求？** 答不上来就是多余的，删掉。收尾时把“本次改了哪些文件/函数、为什么”写进账本（贴 `git diff HEAD~1 --stat` 或 `git show --stat HEAD`，测试代码单列）。

Walk your diff line by line (**line-by-line applies to implementation code**; test code only needs to trace to the risk scenario / case it pins — **never delete a risk-scenario test because "the requirement doesn't mention it"**): **which of the requirement kinds defined above does this line serve?** If you can't answer, it's extra — remove it. Log “which files/functions changed and why” in the ledger (paste `git diff HEAD~1 --stat` or `git show --stat HEAD`, test code listed separately).

**4. 先守本项目的规矩 / Follow this project's own rules first.**
动手前先查项目自己有没有编码/架构约定（`CONTRIBUTING.md`、`CODING_STANDARDS.md`、`docs/`、ADR、架构测试如 ArchUnit、lint 配置）。**有就按它来——项目规矩优先于本节的通用基线。** 特别是：**跨模块/跨层访问走项目既有的通道（如 facade）**，不要图省事直连内部；**发现自己的改动踩了项目约束，当场按正道修掉**，不许“记一笔待评审”就往下走（真修不了→按 orchestrate《停下必须自证》第②条问用户）。
**规矩之间、或规矩与实际代码冲突、或文档明显过期时**，按这个优先级取用：**机器可执行的约束（架构测试 / lint / CI）> 当前代码里占多数的实际写法 > 文档**；把“哪条规矩、怎么冲突、按哪条做”写进账本。**不许在没给出佐证时就以“文档可能过期”绕开项目规矩——要么按上面的优先级拿出机器约束/多数写法的依据并记账，要么按第②条问用户。涉及架构/边界决策的文档冲突，一律走第②条交用户，不用“多数写法”覆盖。**

Before coding, check whether the project documents its own coding/architecture conventions (`CONTRIBUTING.md`, `CODING_STANDARDS.md`, `docs/`, ADRs, architecture tests such as ArchUnit, lint config). **Follow them — the repo overrides the generic baseline below.** Especially: **cross-module / cross-layer access goes through the channel the project already uses (e.g. facade)** — don't shortcut into the internals; **if your own change breaks a project constraint, fix it properly on the spot**, never log “pending review” and move on (truly impossible → ask the user via case ② of orchestrate's《停下必须自证》). **When rules conflict with each other, or with what the code actually does, or the docs are clearly stale**, use this order: **machine-enforced constraints (architecture tests / lint / CI) > the majority pattern in the current code > the docs**; log “which rule, how it conflicts, what you followed” in the ledger. **Never bypass a project rule by merely claiming "the docs may be stale" — either follow the order above with evidence (machine constraint / majority pattern) and log it, or ask the user via case ②. A conflict about an architecture/boundary decision always goes to the user via case ②; never override it with "the majority pattern".**

**5. 项目没写规矩时，对照三个坏味道自查 / When the project documents nothing, check these three smells.**
写完对照自查（**是提醒，不是硬判**——项目已有的写法优先；只是轻微可疑的先记下来，别为改而改）：
- **重复代码 / Duplicated Code**：同一段逻辑在本次改动里出现了两遍以上 → **抽成一个，两边都调它**。（不是“长得像就抽”，是同一段逻辑。）**但若为了抽它要给抽出来的东西加参数/开关去迁就两边差异，说明它们不是同一段逻辑——保持重复，别硬抽。**
- **多余抽象 / Speculative Generality**：为“以后可能需要”加的抽象/参数/钩子 → **删掉**，等真需要时再加。
- **空壳转发 / Middle Man**：一个类/方法自己什么都不干、只把调用转给别人 → **去掉，直接调**。（**对外 facade、项目既有的边界/适配/转换层、为解耦或测试而存在的薄转发都不算**；**删之前确认没有第二个调用方、测试不依赖它、且不是跨仓库/公开 API**。）

After writing, self-check (**a reminder, not a hard verdict** — the repo's existing ways win; note mild suspicions instead of churning for their own sake):
- **Duplicated Code**: the same logic shape appears twice or more in this change → **extract one, call it from both.** (Not “looks similar” — the same logic.) **But if extracting forces the extracted thing to grow parameters/flags to accommodate both sides' differences, they aren't the same logic — keep the duplication, don't force it.**
- **Speculative Generality**: abstraction/parameters/hooks added for a future need → **delete**, add when the need is real.
- **Middle Man**: a class/method that does nothing but delegate onward → **remove it, call the real target directly.** (**A public facade, a project's existing boundary/adapter/mapping layer, or a thin layer that exists for decoupling or testability does not count**; **before deleting, confirm there's no second caller, tests don't depend on it, and it isn't a cross-repo / public API.**)

**6. 不许用 Mockito / Never use Mockito.**
**新增的代码和测试一律不许使用 Mockito**——不新增 Mockito 依赖、不用 `mock`/`spy`/`when`/`verify` 这类 API、不用它替换被测对象或其协作方。**要测什么就让它真跑**：真实对象 + 真实依赖；确实需要隔离外部系统时，用项目已有的测试替身（fake / stub / 测试夹具），或者按项目既有做法来。**已有代码里的 Mockito 用法本次不强制清理**（不属本次需求；按第 2 条，看到即可，不要顺手删）——但**只要本次改动碰到的那段测试/代码，就按新规矩写**。
> **做不到怎么办**（比如项目里除 Mockito 之外没有任何可用替身）：**停下，按 orchestrate《停下必须自证》第②条问用户**。**本条不受第 4 条优先级约束**——项目里"多数写法就是 Mockito"**不构成豁免**（否则这条禁令在它最该生效的仓库里正好失效）；也**不许默默用上 Mockito**。
> 判据：本条是**硬违例**——评审看到本次新增/修改的代码里出现 Mockito，直接打回。

**Never use Mockito in any code or test you add.** No new Mockito dependency; no `mock`/`spy`/`when`/`verify`-style APIs; never use it to replace the object under test or its collaborators. **Let the real thing run**: real objects with real dependencies; when an external system genuinely must be isolated, use a test double the project already has (fake / stub / fixture) or follow the project's existing practice. **Existing Mockito usage is NOT cleaned up by this change** (it is not in the requirement; per item 2, notice it and move on) — but **anything this change touches is written to the new rule**.
> **If you cannot** (e.g. the project has no double other than Mockito): **stop and ask the user via case ② of orchestrate's《停下必须自证》**. **This item is not subject to item 4's precedence order** — "the majority pattern in the repo is Mockito" is **not an exemption** (otherwise the ban would lapse exactly in the repos it exists for); and **never quietly reach for Mockito**.
> Verdict: this one is a **hard violation** — a reviewer who sees Mockito in code this change added or modified sends it straight back.

**7. 测试本身要合格——治“假绿” / A test must be able to fail for the right reason.**
**红的测试不等于有用的测试。“跑通了、没报错、覆盖率上去了”都不是测试合格。** 写每个测试前先回答一句：**“我改坏哪个实现，这个测试会红？”** 答不出来 → 这个测试抓不住东西，重设计。六条硬要求：

1. **期望值必须独立推导**——用字面量或手算的固定值（表驱动 + 字面量 `want` 是首选形态）。**绝不许用被测代码自己（或它的 helper/builder）去算期望值**：两边一起错，永远绿。
   > 例：`expect(buildQuery({tag:'urgent'})).toBe(buildQuery({tag:'urgent'}))` ❌（自证）；`expect(buildQuery({tag:'urgent'})).toBe('tag:"urgent"')` ✅（手写）
2. **断言必须打在真实结果上**——结果值、副作用、退出码。**“没抛异常/没报错/返回了非空”不算断言**（这条与 `plan` 对验收用例的要求同源，只是这里管的是单测）。
3. **不许断言 mock/替身本身**——`expect(mockFn).toHaveBeenCalled()`、断言某个 `*-mock` 元素存在，这类断言**只证明 mock 在**，把真实现整个删掉它照样绿。要断言**真组件的行为**；若你正在检查的就是那个 mock，说明该处不该 mock。
4. **不许 grep 源码文本当测试**——“源文件里有这行”只证明源码是源码。**跑它，断言它的输出/副作用/退出码**。（特例：确实要钉住“某个东西**不该**再出现”的反向守卫可以留，但只能是反向的。）
5. **测你自己的契约，不测框架的机制**——测你注册的路由、你发出的查询、你产出的载荷；上游框架自己的行为是上游的测试。**唯一例外**：某个上游行为确实让你意外时，写**一个**窄的“钉住该假设”的测试，并写明为什么。
6. **断言必须真的会被执行到**——被断言的行为**整个不存在时，测试会不会红**？断言写在永远不进的分支里、循环零次迭代、遍历空集合、“先造数据再断言自己造的数据”，都属于**根本没碰到被测行为**：跑起来是绿的，但它证明的是零。**判断法：把被测逻辑整个掏空（或让它直接返回空/恒真），这个测试还绿不绿？还绿 = 它没测到东西，重设计，不是补断言。**

**不许写“变动探测器” / No change detectors**：只有“刻意的决定”能让它失败的测试（某个常量值、某句提示的原话、私有结构的形状）——**它在重构时乱叫，在真出 bug 时睡觉**。要测的是**依赖那个决定的行为**：不是 `expect(MAX_RETRIES).toBe(5)`，而是“失败调用重试 5 次、第 6 次不再发生”。

**不许用“删/跳过/削弱”换绿 / Never buy green by removing or weakening tests**：测试没过时，**不许**删掉它、`skip`/`xfail`/`.only` 掉它、注释掉它，或把断言改弱（`toBe` 改成 `toBeTruthy`、精确值改成“非空/不报错”）来让它变绿。**如果确实要移除或放宽一个测试，必须写明理由并记账**（为什么它不该存在 / 为什么放宽是对的），说不出理由就是拿绿换的。

> **本条（第 7 条）不受第 4 条优先级约束**——第 4 条是"机器约束 > **多数写法** > 文档"，但**"项目里大家就是这么写测试的"不构成豁免**：仓库里多数测试都断言"没报错"、都含自证断言，**不能**因此把本条判无效（否则这条闸门在"假绿成风"的项目里正好失效，而那正是它存在的理由）。确实做不了 → **停下，按 orchestrate《停下必须自证》第②条问用户**。
> 例外只有一处：项目**明文规定**的测试规范（`CONTRIBUTING.md`/ADR/机器可执行的 lint）**与本条冲突**时，按第 4 条以机器约束为准并记账——但**"多数写法"和"历史习惯"不算明文规定**。

> 判据：本条是**硬违例**——评审看到本次新增/修改的测试里出现自证断言、只断言“没报错”、断言 mock、grep 源码文本、**测试在整个被测逻辑被掏空后仍然绿**、或**用删除/跳过/削弱断言换来的绿**，直接打回。

**Before writing a test body, answer: "which production change makes this test fail?" If you cannot name one, the test catches nothing — redesign it.** Six hard requirements:
1. **Derive the expected value independently** — literals or hand-checked fixtures (table-driven tests with literal `want` values are the preferred shape). **Never compute the expectation with the code under test or its helpers/builders** — both sides then move together and the test is always green.
2. **Assert on real results** — values, side effects, exit codes. **"No exception / no error / returned something non-empty" is not an assertion.** (Same rule `plan` already applies to acceptance cases — this is the unit-test side of it.)
3. **Never assert on the mock/double itself** — `expect(mockFn).toHaveBeenCalled()`, or an assertion that a `*-mock` element exists, proves only that the mock is present: delete the real implementation and it still passes. Assert the **real component's** behavior; if the mock is what you are checking, that is where you should not have mocked.
4. **Never grep source text as a test** — "the source contains this line" only proves the source is the source. **Run it and assert its output / side effects / exit code.** (Exception: a reverse guard pinning that something must **not** come back is allowed — reverse only.)
5. **Test your own contract, not the framework's mechanics** — the route you register, the query you emit, the payload you produce; upstream behavior is upstream's test to write. **Only exception**: when upstream genuinely surprised you, write **one** narrow assumption-pinning test and say why.
6. **The assertion must actually be reached** — **would the test go red if the behavior it asserts simply did not exist?** An assertion inside a branch that is never entered, a loop that iterates zero times, an iteration over an empty collection, or "build the data, then assert on the data you built" all mean the test **never touches the behavior under test**: it runs green while proving nothing. **The test: hollow out the implementation (or make it return empty / always-true) — is the test still green? Still green means it tests nothing. Redesign it; do not add assertions.**

**No change detectors**: a test that can only fail on an intentional decision (a constant's value, exact message wording, private structure) **fires on redesign and sleeps through bugs**. Test the behavior that depends on the decision: not `expect(MAX_RETRIES).toBe(5)` but "a failing call is retried 5 times and the 6th attempt never happens".

**Never buy green by removing or weakening tests**: when a test fails, **do not** delete it, `skip`/`xfail`/`.only` it, comment it out, or weaken the assertion (`toBe` → `toBeTruthy`, an exact value → "non-empty / no error") to make it pass. **If a test genuinely must be removed or relaxed, state the reason and log it** (why it should not exist / why relaxing it is right); if you cannot state one, the green was bought.

> **This item (7) is not subject to item 4's precedence order.** Item 4 reads "machine constraint > **majority pattern** > docs", but **"this is how tests are written around here" is not an exemption**: a repo where most tests assert "no error" or contain mirror assertions **cannot** use that to void this item — otherwise the gate would lapse exactly in the repos where false green is the norm, which is the reason it exists. If you genuinely cannot comply → **stop and ask the user via case ② of orchestrate's《停下必须自证》**.
> There is exactly one exception: when the project's **explicitly written** testing convention (`CONTRIBUTING.md` / ADR / machine-enforced lint) **conflicts** with this item, item 4 applies — machine constraint wins, and log it. But **"the majority pattern" and "how it has always been done" are not written conventions**.

> Verdict: a **hard violation** — a reviewer who sees a mirror assertion, a "no error" assertion, an assertion on a mock, a source-text grep, **a test that stays green after the implementation is hollowed out**, or **green bought by deleting / skipping / weakening a test**, in tests this change added or modified, sends it straight back.

**8. 通用架构基线 / Generic architecture baseline.**
> 这一节与项目自己的架构规矩**同一层**：**项目明文规矩优先**（项目规矩更松也按项目；涉及架构/边界的**文档冲突**走第 4 条尾句——交用户，不用"多数写法"覆盖）。
> 冲突解法沿用第 4 条的 **机器约束 > 多数写法 > 文档**；但 **8.1–8.5、8.7–8.9 不受"多数写法"豁免**——理由与第 6、7 条同款：**沉默的多数写法不算"项目明文规矩"**，否则它们在最该生效的仓库里正好失效。
> **每条都对着 `plan` 的《架构落位》判**：落位已声明本次**涉及哪几条**，以及每条查法要引用的**那个具体声明**（8.3 的唯一入口 / 8.8 的对外公开面 / 8.9 的写入入口）。**涉及的要给出查法的命令与原始输出；不涉及的要写明为什么（附仓库级搜索命令）。**
> **硬违例（打回）= 8.1、8.4**；**8.6 是评审信号**（不是 grep 判死）；其余按各条口径判。
> （为什么是这 9 条、为什么放 `plan` 而不只是这里、为什么每条必须带"怎么查"：见 dev-harness 仓库的 `docs/rationale.md`，**卡不含该文件**。）

- **8.1 不许新增循环依赖**：本次新增的依赖边，不许让两个单元形成环。**怎么查**：落位先声明**粒度**（文件/包/构建模块）；列出新增边 A→B；**从 B 出发在整仓库范围**走回 A——环**通常**靠本来就存在的边闭合，**只在 diff 里看会漏**；但**新增的边本身也要纳入走查：同一次改动加的两条边（A→B 与 B→A）就能自己成环**。优选跑栈自带检查（JS `madge`/`dependency-cruiser`、JVM `jdeps`/ArchUnit、Gradle 模块图）并贴原始输出。
- **8.2 不许绕过既有入口直连内部**：跨模块调用**只许走落位里声明的入口符号**。**怎么查**：落位先列出入口符号全名；diff 里每个新增的跨模块调用点，核它调的是不是其中之一；调了别的（尤其对方内部方法/字段）→ 违例。
- **8.3 横切件只准一个入口**：新增的锁 / HTTP 客户端 / 日志 / 时钟 / 随机 / 配置读取，必须复用仓库既有的那一个。**怎么查**：对本次引入的每类横切件，给"搜既有封装的命令 + 原始输出"，并把处置写进落位（复用哪个／为何不复用）。**没给命令 = 违例。只约束新增代码。**
  > **"复用"包括复用既有设施/写法**（如直接用 `slf4j`、`java.time.Clock`、语言/框架自带的标准设施）——**不要求为单一调用方另造 wrapper**；仓库里本来就没有任何既有封装时，本次新建并**写进落位**即可，**不因"没有第二个调用方"打回**（与第 1 条那款硬违例不冲突）。**不要求清理仓库里既有的重复入口**（第 2 条：只说，不顺手改）。
- **8.4 公共契约只加不改不删**：**落位声明为对外/跨模块的**契约（公开签名 / HTTP 端点 / 序列化字段 / schema 列 / 消息格式）**只许新增**；删或改必须给**破坏面 + 迁移路径 + 迁移期**，缺一即违例。**新增必填项也算破坏**（老调用方不传就崩）。**怎么查**：diff 里逐个核这些位置。
  > **不算契约变更**：**同一次提交内改完全部调用点、且没有任何本次改动之外的消费者**的单元内签名变更（模块内部的 `public` 而已）——这类不要求"迁移期"（对内调用没有迁移期可言）。判定看**落位声明的边界**，不看 `public` 这个关键字本身。
- **8.5 同一份持久化数据只有一个写入口**：落位先写出这份数据的 **owner 符号**；新代码必须经过它。**怎么查**：按表名/实体名 grep 全仓库列出写入点；**出现「本次新增的」、绕过 owner 的写入点 → 违例**（历史遗留写入点不算本次违例，按第 2 条只记录；数据迁移/回填脚本可在落位里声明为写入方）。
- **8.6 不许把失败当成成功**：**怎么查**：diff 里找**把错误丢掉**的地方——不重抛、也不作为错误返回、代码里又没写明"为什么可以忽略"。**空 `catch` 体**是其中一种。**不绑语言/关键字**：Go 的 `_ = doThing()`、空的 `if err != nil {}`；Kotlin 的 `runCatching{}.getOrNull()`；shell 的 `cmd || true` / `2>/dev/null`——都是这个形状。**明确不算违例**：`return nil, err` 这类正常错误返回；**有意的领域默认值**（如"查无结果"返回空集合，代码里写明为什么）；遥测/清理这类 best-effort（写明为什么）；框架异常映射（如 `@ExceptionHandler`）。**本条是评审判断，不是 grep 判死。**
- **8.7 加载期不许固化"需要被替换"的值**：**绝对路径**与**当前时间（时钟）**不许在**模块加载 / 静态初始化**期读取——这两类测试最常需要替换，固化后没法注入。要在调用时读，或作参数传入。**怎么查**：diff 里新增的模块顶层 / `static` 初始化块 / `object`·`companion` 初始化里有没有读路径或时钟（**间接读要顺到真正的读取点为止**，不是只看一层）。**不算违例**：进程启动期读一次、之后不变、且不需要被覆写的 boot 配置（如 12-factor 的 `PORT` 这类 env 常量）；**由脚本/模块自身位置推导的路径**（`__file__` / `import.meta.url` / shell 的 `BASH_SOURCE`·`$0` / Gradle·Kotlin 的自身位置）；编译期常量。
- **8.8 新增成员别把可见性开大**：新增的 public / 导出成员，**若其全部调用点都在同一个文件/类/包里，必须收窄可见性**。**怎么查**：grep 该成员调用点。**不算违例**：框架要求的 public（`@Bean`、控制器方法——框架调用它们）；接口/父类要求的方法；**由框架或反射访问的成员**（序列化/ORM 映射/DI 绑定/视图绑定/JS 桥接等）；**落位声明的对外公开面**；语言本身没有可见性机制时**不适用**（落位里写一句）。
  > **仓库内零调用点 ≠ "调用点都在同一处"**：零调用点通常是框架在用（序列化、ORM、DI）。先判它是不是框架访问的——是则不算违例；**不是**框架访问、又确实没人调，那才是"本可以是私有"，按违例。
- **8.9 共享可变状态写入要收敛**：**本次新增的写入点落到共享可变状态上**（全局变量 / 单例 / 缓存——**无论那份状态是不是本次新增的**），写入必须收敛到落位里声明的那个入口。**怎么查**：grep 本次新增的写入点，看它落到的状态是不是**分属不同函数/模块的代码都能写**；是、且落位没声明 → 违例。（`put`/`clear` 这类多个方法本身不算违例，只有**没在落位里声明**才算；**一个函数内顺序执行的累加器**只有一个所有者，**不算共享状态**。）

**8. Generic architecture baseline.**
> This section sits at the **same level** as the project's own architecture rules: **the project's explicitly written rules win** (even when they are laxer; an architecture/boundary **document conflict** goes to the user per item 4's closing sentence — never overridden by "the majority pattern").
> Conflicts resolve by item 4's order — **machine constraint > majority pattern > docs** — but **8.1–8.5 and 8.7–8.9 are NOT exempted by "the majority pattern"**, for the same reason as items 6 and 7: **a silent majority pattern is not a "written project rule"**, otherwise these lapse exactly in the repos they exist for.
> **Judge each one against `plan`'s 《架构落位》**: it declares which ones this change engages and the **specific declaration** each check cites (8.3's sole entry / 8.8's public face / 8.9's write entry). **Engaged → give the check's command and raw output; not engaged → say why, with a repo-level search command.**
> **Hard violations (send back) = 8.1, 8.4**; **8.6 is a review signal** (not a grep death sentence); the rest follow their own wording.
> (Why these nine, why they live in `plan` and not only here, and why every one must state a check: see `docs/rationale.md` in the dev-harness repo — **cards do not ship this file**.)

- **8.1 No new cyclic dependencies**: an edge this change adds must not close a cycle between two units. **Check**: the 落位 first declares the **granularity** (file / package / build module); list the new edge A→B; **walk from B back to A across the whole repo** — a cycle **usually** closes through pre-existing edges, so **a diff-only look will miss it**; but **the new edges themselves must be walked too: two edges added by the same change (A→B and B→A) can close a cycle on their own**. Prefer the stack's own checker (JS `madge`/`dependency-cruiser`, JVM `jdeps`/ArchUnit, Gradle module graph) and paste the raw output.
- **8.2 Never bypass the existing entry point into internals**: a cross-module call **may only use the entry symbols declared in the 落位**. **Check**: the 落位 first lists the entry symbols by full name; for each newly added cross-module call site in the diff, verify it targets one of them; anything else (especially another module's internal methods/fields) → violation.
- **8.3 One entry per cross-cutting concern**: a new lock / HTTP client / logger / clock / RNG / config read must reuse the one the repo already has. **Check**: for each cross-cutting kind this change introduces, give the "search for an existing wrapper" command + raw output, and record the disposition in the 落位 (which one was reused / why none was). **No command = violation. New code only.**
  > **"Reuse" includes reusing an existing facility or idiom** (going straight to `slf4j`, `java.time.Clock`, the language/framework standard) — **you are not required to build a wrapper for a single caller**; where the repo has no existing wrapper at all, what this change creates is fine once it is **declared in the 落位**, and it must **not** be sent back for having "no second caller" (this does not conflict with item 1's hard violation). **Consolidating pre-existing duplicates is out of scope** (item 2: mention it, don't fix it in passing).
- **8.4 Public contracts only gain, never change or lose**: contracts **the 落位 declares as external / cross-module** (public signatures / HTTP endpoints / serialized fields / schema columns / message formats) may only be added; removing or changing one requires **breakage surface + migration path + migration window**, and missing any of the three is a violation. **A newly required field also counts as breakage** (old callers break). **Check**: walk those positions in the diff.
  > **Not a contract change**: an intra-module signature change where **every call site is updated in the same commit and nothing outside this change consumes it** (it merely happens to be `public` inside the module) — no "migration window" is required for an internal call. Decide by the **boundary the 落位 declares**, not by the `public` keyword.
- **8.5 One write entry per piece of persisted data**: the 落位 first names the data's **owner symbol**; new code must go through it. **Check**: grep the table/entity name repo-wide and list every write site; **a write site this change adds that bypasses the owner → violation** (pre-existing legacy writers are not this change's violation — per item 2, record only; data migration/backfill scripts may be declared as writers in the 落位).
- **8.6 Never treat failure as success**: **Check**: in the diff, look for places that **throw the error away** — neither rethrown, nor returned as an error, nor explained in the code as deliberately ignorable. An **empty `catch` body** is one shape of it. **Not tied to a language or keyword**: Go's `_ = doThing()` or an empty `if err != nil {}`; Kotlin's `runCatching{}.getOrNull()`; shell's `cmd || true` / `2>/dev/null` — all are this shape. **Explicitly not violations**: a normal error return such as `return nil, err`; a **deliberate domain default** (e.g. an empty collection for "no results", with the reason in the code); best-effort paths such as telemetry/cleanup (with the reason); framework exception mapping (e.g. `@ExceptionHandler`). **This one is a review judgement, not a grep death sentence.**
- **8.7 Don't freeze values that need substituting**: **absolute paths** and **the clock** must not be read during **module load / static initialization** — those are the two things tests most often need to substitute, and freezing them makes injection impossible. Read them at call time, or pass them in. **Check**: newly added module top level / `static` initializer / `object`·`companion` init that reads a path or the clock (**follow indirect reads to the actual read point**, not just one level). **Not violations**: boot config read once at process start, never changing and never needing to be overridden (12-factor `PORT`-style env constants); **a path derived from the script's or module's own location** (`__file__` / `import.meta.url` / shell's `BASH_SOURCE`·`$0` / Gradle·Kotlin self-location); compile-time constants.
- **8.8 Don't widen visibility for new members**: a newly added public / exported member whose **every call site is in the same file/class/package must be narrowed**. **Check**: grep the member's call sites. **Not violations**: public required by a framework (`@Bean`, controller methods — the framework calls them); interface/parent-imposed methods; **members accessed by a framework or reflection** (serialization / ORM mapping / DI binding / view binding / JS bridge); **the public face declared in the 落位**; and where the language has no visibility mechanism, it **does not apply** (say so in the 落位).
  > **Zero in-repo call sites ≠ "all call sites in one place"**: zero usually means a framework is calling it (serialization, ORM, DI). Decide whether it is framework-accessed — if so, not a violation; if it is **not** framework-accessed and genuinely nothing calls it, that is the "could have been private" case, and a violation.
- **8.9 Converge writes to shared mutable state**: a **write site this change adds that lands on shared mutable state** (a global / singleton / cache — **whether or not that state is new**) must converge on the entry declared in the 落位. **Check**: grep the newly added write sites and see whether the state they touch is one that **code in different functions or modules can write**; if so and the 落位 declares no entry → violation. (Several methods such as `put`/`clear` are not themselves a violation — only being **undeclared** is; a **straight-line accumulator inside a single function** has one owner and is **not shared state**.)

**变异自检（绿了以后必做）/ Mutation check (mandatory after green)**
光有“红→绿”不够：绿只证明测试跑过了，不证明它**抓得住 bug**。所以**每个任务绿了以后**，把这次的实现**在脑子里逐个改坏**，每改一处问一句“**哪个测试会红？**”：

- 常量/参数改错；分支走错（if/else、switch、边界条件反过来）；**少了状态变更/副作用**；返回空值或默认值；去掉校验（零值/空/越界/未授权/畸形输入）；**把被测逻辑整个掏空（或短路成恒真/直接返回空）**。

**没有测试会红的那一处 = 那个行为没被保护**：要么补测试，要么把这个测试改成真能抓住它。**最后那一类（整个掏空）要特别注意**：掏空之后**还绿**，说明这个测试**根本没碰到被测行为**——这时**不是补断言，是重设计这个测试**（见第 7 条第 6 条）。**把“试了哪几个变异、分别由哪个测试抓住”写进账本**——这是本步的必交证据。

> A red→green cycle is not enough: green only proves the test ran, not that it **catches bugs**. So after each task goes green, **mutate your implementation one thing at a time in your head** and ask **"which test goes red?"** — wrong constant/argument; wrong branch (if/else, switch, boundary flipped); **missing state change or side effect**; empty/default return; validation removed (zero, empty, out-of-range, unauthorized, malformed input); **hollow out the implementation entirely (or short-circuit it to always-true / return empty)**.
>
> **Any mutation nothing catches means that behavior is unprotected** — add a test, or fix the test so it really catches it. **The last kind (hollowing it out) deserves special attention**: if the suite is still green after that, the test **never touched the behavior under test** — that is **not a case for adding assertions, it is a case for redesigning the test** (see item 7, requirement 6). **Log which mutations you tried and which test caught each one** — that log is required evidence for this step.

## 证据要求 / Evidence

完成时账本必须含：新增/修改的测试名 + 测试原始输出（红到绿的过程可见，**红的原始输出要能看出它是因“缺功能”而红**）+ **变异自检记录（试了哪几个变异、分别由哪个测试抓住；有没有哪个变异没有任何测试会红）** + **影响面逐条回归结果（照 `plan` 的清单：每条"搜到了"的验没验、结果如何；每条"搜不到"的如实标出来）+ commit message 里的 `## 影响面` 小节（清单有变动时已同步）** + **架构基线逐条结果（照 `plan` 的《架构落位》：8.1–8.9 逐条给"涉及/不涉及"；**涉及的给查法命令与原始输出，不涉及的给仓库级搜索命令**）+ commit message 里的 `## 架构落位` 小节（落位有变动时已同步）** + **本次改了哪些文件/函数、为什么（对应上面第 3 条，贴 `git diff HEAD~1 --stat` 或 `git show --stat HEAD`，测试代码单列）** + **坏味道的处理结果（改了，或记录未改及原因）** + **项目约束的处理结果（已按第 4 条改正，或已按第②条请用户裁定）** + **无关死代码只说要写进这里（否则等于没说）**。
> 不记账 = 本步不算完成，不能进入下一步。

When done, the ledger must include: the added/changed test names, the raw test output (the red-to-green progression visible, **with the raw red output showing it failed because the feature was missing**), **the mutation-check record (which mutations you tried, which test caught each, and whether any mutation nothing caught)**, **the per-item impact regression result (against `plan`'s list: each "found" entry verified or not and with what result; each "cannot search" entry marked honestly) plus the commit message's `## 影响面` section (synced if the list changed)**, **the per-item architecture-baseline result (against `plan`'s 《架构落位》: 8.1–8.9 each marked engaged / not engaged; **engaged entries give the check's command and raw output, unengaged ones a repo-level search command**) plus the commit message's `## 架构落位` section (synced if the 落位 changed)**, **which files/functions changed and why (item 3 above; paste `git diff HEAD~1 --stat` or `git show --stat HEAD`, test code listed separately)**, **smells: fixed, or recorded with a reason**, **project constraints: fixed per item 4, or adjudicated by the user under case ②**, and **any unrelated dead code you only mentioned (otherwise mentioning it amounts to nothing)**.
> No ledger entry = this step is not done; do not proceed to the next step.

## 注意 / Notes

- 一次只做一个小任务（来自 `plan` 的清单），别一次性写一大堆。
- 测试要能客观失败/通过，不能靠人工肉眼看。
- 每完成一个任务，勾掉 `plan` 里对应的框，并往账本追加一条进度。

Work on one small task at a time (from the `plan` checklist). Tests must pass/fail objectively, not by eyeballing. After each task, tick its checkbox and append one ledger entry.
