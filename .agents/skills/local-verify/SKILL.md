---
name: local-verify
description: "本地验证。在本地隔离环境真跑一次，留证据。 / Local verification: really run it in the local isolated environment, leave evidence"
---

# Local Verify / 本地验证

## 目标 / Goal

这是流程第 ⑥步：在本地真实环境跑一遍，确认不是"测试过了就算完"，而是真的能用。

This is step 6: run it for real in a local environment, confirming it actually works, not just "tests passed".

## 做什么 / What to do

1. 在本地隔离环境（Docker 或本地起服务）把功能真实跑通。**开始之前先把环境重建到当前代码（固定动作，不是可选项）**：
   - **本轮改没改代码，以 `git diff HEAD~1 --stat` / `git show --stat HEAD` 为准**——本轮代码在第④步**已经 commit**（本轮返修是 `--amend` 回同一个 commit，所以 `HEAD~1` 恒定是"本轮之前"），而 `git status` 是干净的、**不能拿它当依据**（拿它看会得出"没改"，直接导致不重建就验旧代码）。有实现改动就必须先重建重启，不许自己认定“没改”；重建 + 重建/重启跑服务的那个环境，再开始验证——一个动作做完再往下：`docker compose up -d --build`（重建镜像 + 重建容器）/ 重打 jar 后重启服务进程 / 前端 dev server 重启。
   - **账本只贴这条命令的原始输出**（命令 + 输出）+ **写明验的是哪个服务/端口/容器**（与重建的对象对得上）。**不需要推导时间戳、不需要证明谁先谁后**——把“重建/重启环境”真的做在前面，验的就是新代码。
   - **别只做半套**：只跑构建不重启、或只 `restart` 不重建（`docker restart` / `compose restart` / 不带 `--build` 的 `compose up -d`）都只是重启，镜像/产物没变，不算。
   - **若启动依赖环境变量**（DB/中间件地址、开关、密钥），**把关键变量也一并记下**（缺变量导致验错对象是常见坑）。
2. 走一遍真实的使用路径（不是抠单测）。
3. **按 `plan` 方案里的验收用例（A 编号那套）逐条跑**：`端到端` 类必须逐条跑完、逐条贴上实跑结果——**只要有一个没跑或没过，本步就不算完成**。（`单测` 类在 ⑤ 已经跑过，本步不重复；`人工` 类的归属见第 5 条。）
   > **顺带把影响面清单里"靠 `端到端` 兜"的那几条一起跑了**：清单上"搜到了"、且**只有一个 `端到端` 用例能覆盖**的使用方，它的回归就落在本步（⑤ 跑的是 `单测`，够不着）。跑完在账本里写明**哪几条清单项是在这里验掉的**——⑤ 会把"没有测试覆盖"的标出来，**已经是 `端到端` 用例的那部分别漏**。
4. **带 `端到端` 类用例时，按“先全跑、再统一修”两轮来（不要跑一条修一条）/ With `e2e` cases, use two passes — run them all first, then fix together (do not fix case-by-case as you go)：**
   - **第 1 轮：一次把 `端到端` 类用例跑完，不改代码。** 拿当前代码把每一条都跑一遍（含很可能失败的），逐条记“通过 / 失败（现象）/ 受阻（环境，如实标）”。**不要中途停下来改代码**——先把问题全貌拿到（很多失败可能是同一个根因）。
   - **跑完后统一处理**：把失败项归类（哪些是同一个原因），**一次性改完**；环境受阻项单独列出（不当场折腾环境，最后统一说明）。**若中途整个环境不可用（服务/mirror 崩了）导致后面用例根本跑不下去，把整步如实标“卡住”、把跑不了的用例记成“受阻（环境）”（不要为了凑“全跑完”编造结果）。**
     > 状态词只有**整步**一个粒度：`卡住` 是账本标题上的步骤状态（出口见 `orchestrate`《停下必须自证》第③条），**单条用例不要写“卡住”**，写“受阻（环境）”。
   - **第 2 轮：重跑验证。** 失败项必重跑；改动涉及的、可能受影响的用例也要重跑（改动面大就全量重跑），直到 `端到端` 类全部 pass。
5. **按用例类型分工**（类型在 `plan` 的方案里就标好了）：
   - **`端到端` 类由本步负责**：必须**真端到端跑**（真起前后端、真走浏览器/真调接口到真实链路），不能拿单元测试、mock、接口单测代替。
   - **`单测` 类不归本步**：它在 ⑤ 已经跑过，本步只保证真实路径整体跑通（见第 2 条）。
   - **`人工` 类由非实现者执行**（用户，或另一个独立 agent）：按方案里写的"谁 / 在哪 / 做什么 / 看到什么"去做，**留下产物**（截图 / 接口返回 / DOM 片段）。**本步要先创建方案里写好的那份清单文件，把方案里所有 `人工` 用例列进去**（哪怕有些要到 ⑨ 才跑）——**每条跑完把结果和产物追加进去，不是只记进账本**：账本收尾就删，只记在账本里等于没沉淀。**它不进本步的自动闸门**（第 3 条只管 `端到端` 类），但也**不许悄悄丢掉、不许假装跑过**；做这一条需要用户在场时，按《停下必须自证》第②条如实停下要人。
   - **用例没标类型 → 退回 `plan` 补类型**，不许自己猜一个标准去跑。**缺落点 → 一并退回 `plan` 补落点。**
6. 把运行结果、看到的现象留成证据。

1. Really run the feature in the local isolated environment (Docker or local service). **Before you start, first bring the environment up to the current code — a fixed action, not an option**:
   - **Whether code changed this round is settled by `git diff HEAD~1 --stat` / `git show --stat HEAD`** — this round's code was **already committed at step ④** (and this round's fixes are `--amend`-ed back into that same commit, so `HEAD~1` is always "before this round"), while `git status` is clean and **must not be used as the test** (it would say "nothing changed" and you would verify the old code without rebuilding). If code changed, rebuild and rebuild/restart the serving environment BEFORE verifying — not by your own claim — one action, then move on: `docker compose up -d --build` (rebuild image + recreate container) / repackage the jar then restart the service process / restart the frontend dev server.
   - **The ledger only needs this command's raw output** (command + output) **plus which service/port/container you verified** (it must match what you rebuilt). **No timestamp derivation, no proving which time is later** — if the rebuild/restart really happens first, you are verifying the new code.
   - **Don't do half of it**: building without restarting, or `restart` without rebuilding (`docker restart` / `compose restart` / `compose up -d` without `--build`) are restarts only — the image/artifact is unchanged, so it does not count.
   - **If startup depends on env vars**, **record the key ones too**.
2. Walk the real usage path (not just unit tests).
3. **Run the acceptance cases from `plan`'s output (the A-numbered set) one by one**: every `e2e` case must be run and its real result pasted — **one un-run or failing case means this step is not done**. (`unit` cases already ran at step ⑤ and are not repeated here; `manual` cases are covered by item 5.)
   > **While you are at it, cover the impact-list entries that only an `e2e` case can reach**: where a "found" dependent's only coverage is an `e2e` case, its regression lands here (⑤ runs `unit` and cannot reach it). Record in the ledger **which list entries were verified here** — ⑤ marks the ones with no coverage at all, but **do not drop the ones that are already `e2e` cases**.
4. **With `e2e` cases, use two passes — run them all first, then fix together (do not fix case-by-case as you go):**
   - **Pass 1: run every `e2e` case once, without changing code.** Run all of them against the current code (including ones likely to fail), recording each as "pass / fail(with symptom) / blocked(environment — mark honestly)". **Do not stop mid-way to fix code** — first get the full picture (many failures may share one root cause).
   - **After the run, fix as a batch:** group the failures (which share a cause) and fix them **in one go**; list the environment-blocked cases separately (don't fight the environment on the spot — explain them at the end). **If the whole environment becomes unusable mid-run (service/mirror down) so later cases cannot be run at all, mark the whole step “blocked” and record the un-runnable cases as “blocked (environment)” (never fabricate results just to claim "all run").**
     > The state word has **exactly one granularity — the whole step**: `blocked` is the step's status in the ledger heading (its exits are in `orchestrate`'s “Stopping must be justified”, case ③); **do not write “blocked” on an individual case** — write “blocked (environment)”.
   - **Pass 2: re-run to verify.** Failing cases must be re-run; cases touched by or potentially affected by the change must also be re-run (if the change is broad, re-run everything), until all `e2e` cases pass.
5. **Divide by case type** (the type is set in `plan`'s output):
   - **`e2e` cases are this step's job**: they must be run **truly end-to-end locally** (real front+back end, real browser / real API through the real chain), never substituted with unit tests, mocks, or isolated API tests.
   - **`unit` cases are NOT this step's job**: they already ran at step ⑤; this step only makes sure the real path works as a whole (see item 2).
   - **`manual` cases are done by a non-implementer** (the user, or a separate independent agent): do what the plan says — who / where / what they do / what they see — and **leave an artifact** (screenshot / API response / DOM snippet). **This step creates the checklist file `plan` recorded and lists every `manual` case in it** (even ones deferred to ⑨) — **each result and artifact is appended there, not only to the ledger**: the ledger is deleted at closure, so ledger-only means never deposited. **They are outside this step's automatic gate** (item 3 covers `e2e` only), but they must **never be silently dropped or faked**; if doing one requires the user to be present, stop and ask per 《停下必须自证》case ②.
   - **A case with no type → send it back to `plan` to be typed**; never guess a standard and run it. **A missing landing spot goes back to `plan` too.**
6. Keep the result / observed behavior as evidence.

## 证据要求 / Evidence

完成时账本必须含：
- 用了什么环境（Docker 镜像 / 本地服务）+ **重建/重启环境的命令与原始输出**（证明验证前真的把环境换成了当前代码；只跑构建不重启、或只 `restart` 不重建不算）
- 走了哪条真实路径、看到什么结果
- 带用例时：**`端到端` 类**用例的实跑结果（逐条）+ **第1轮全跑记录与第2轮重跑记录分开贴**（第1轮因环境中途不可用未跑完的，按“受阻（环境）”如实贴并注明从哪一条起受阻；此情况**整步**标“卡住”，只贴真实发生过的记录）
- **影响面清单里在本步验掉的那几条**（哪些清单项、由哪个用例覆盖、结果如何）
- 失败项要写清“现象 + 归类”与最后怎么改的（能看出是“全跑完再统一修”的）
- 若用了 stub/模拟外部依赖、造了测试数据、或改过环境（账号/权限/配置），标注一句“本次本地验证的环境说明（外部依赖 stub／数据准备／环境调整）”

> 不记账 = 本步不算完成，不能进入下一步。

When done, the ledger must include: which environment was used **plus the rebuild/restart command and its raw output** (proof that the environment was brought up to the current code before verifying; building without restarting, or `restart` without rebuilding, does not count) — which real path was walked, and what was observed. If the requirement carries cases, include each **`e2e`** case's real result (per case), **with the pass-1 full-run record and the pass-2 re-run record shown separately** (if pass 1 stopped early because the environment became unusable, paste those results honestly as “blocked (environment)” and note from which case it stopped — in that case the whole **step** is marked “blocked”; record only what actually ran), and for failures the symptom + grouping and how they were finally fixed (so it is clear the run was finished before fixing as a batch); **plus the impact-list entries verified at this step** (which entries, covered by which case, with what result). If you used a stub / mocked external dependency, created test data, or changed the environment (account / permission / config), also note “environment notes for this local verification (external-dep stub / data prep / env adjustment)” in one line.

> No ledger entry = this step is not done; do not proceed to the next step.

## 完成标准 / Done when

真实路径跑通、结果符合预期，且账本里有上面证据。**带用例时：先一次跑完 `端到端` 类（第1轮，不改代码），再统一修，再重跑（第2轮）——最终 `端到端` 类逐条 pass，缺一条或没过一条就不算完成，也不许进第⑦步评审。**（`单测` 类在 ⑤ 已过，本步不重复；`人工` 类由非实现者做完并留下产物，**不进本条闸门**——但也不许跳过。）

**影响面清单也要进本条闸门**：本步的 `端到端` 用例该兜住的那些"搜到了"的使用方，**逐条跑过才算完成**——账本里要写清**哪条清单项由哪条用例兜住、结果如何**；**有清单项该由本步兜住却没跑，本步就不算完成**。本地就是兜不住、只能上测试环境的，在账本里**明确标成"本地验不了"**（写清为什么），交给 ⑨——**不许不声不响地漏掉**。

> **降级红线**：「测试绿了」「编译/build 过了」≠ 本地验证通过。必须真的把服务跑起来、打开页面/调接口看到实际效果，并留下截图或接口返回。**拿改代码之前就启动的老环境去验新代码，也不算本地验证通过**——验的不是你要交的东西，要么先重建重启再验，要么如实标「卡住」。没有本地数据源不是跳过理由——本地起 docker 镜像/自己搭一个可用环境；真搭不起来就老实标「卡住」，不许推给⑧⑨。**需求里的 `端到端` 用例必须全跑且全 pass，不许含糊过——用例因代码错而没过的，回去改到跑通；确实做不到的：环境缺→整步标「卡住」、该条用例记「受阻（环境）」；用例本身有问题（写错/自相矛盾）→按第②条请用户裁定用例。**

Real path works as expected, with the evidence above logged. **With cases: first run all `e2e` cases in one pass (pass 1, no code changes), then fix as a batch, then re-run (pass 2) — finally every `e2e` case must pass; one missing or one failing means not done, and you may not proceed to step 7 review.** (`unit` cases already passed at ⑤ and are not repeated here; `manual` cases are done by a non-implementer with an artifact, and are **outside this gate** — but never skipped.)

**The impact list is inside this gate too**: every "found" dependent that this step's `e2e` cases are meant to cover must actually be run — the ledger must say **which list entry is covered by which case, and with what result**; **if a list entry belongs to this step and was not run, this step is not done**. Anything local genuinely cannot cover is **marked "cannot verify locally"** in the ledger (with the reason) and handed to ⑨ — **never dropped quietly**.

> **No-downgrade line**: “tests green” / “build passes” is NOT local verification. You must actually run the service, open the page / call the endpoint and see the real effect, leaving a screenshot or API response. **Verifying new code against an environment started before your code change does not count either** — you would be verifying something other than what you are shipping: rebuild/restart first, then verify, or mark it blocked honestly. “No local data source” is not a reason to skip — start a docker image / stand up an environment locally; if you truly can't, mark it blocked honestly, never defer it to steps 8–9. **The requirement's `e2e` cases must all be run and pass — no glossing over; a case failing due to code → fix until it passes; if genuinely impossible: missing environment → mark the whole step “blocked” and that case “blocked (environment)”; a broken/self-contradictory case → go through case ② and ask the user to adjudicate the case.**
