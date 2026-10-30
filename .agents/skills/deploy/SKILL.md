---
name: deploy
description: "发布到测试环境。发布是有副作用的动作，必须先经用户确认，发布成功后留外部事实为证。 / Deploy to test env: a side-effecting action that requires user confirmation; keep external facts as evidence."
---

# Deploy / 发布测试环境

## 铁律 / The rule

发布是**有副作用、不可轻易撤回**的动作。AI 不能自己说"已发布"——必须**先经用户确认**，发布成功后要留"部署系统返回"之类的外部事实，而不是自述。

Deploying is a side-effecting, hard-to-undo action. The AI must not claim "deployed" on its own — it must get **user confirmation first**, then keep an external fact (e.g. the deploy system's response) as evidence, not self-description.

## 做什么 / What to do

1. 准备好要发布的东西，向用户说明"我要发布什么、到哪"，**等用户点头**。
2. 用户确认后，执行发布。
3. 把部署系统的返回结果贴进账本。

1. Prepare what to deploy, tell the user "what, where", and **wait for approval**.
2. After approval, execute the deploy.
3. Paste the deploy system's response into the ledger.

## 证据要求 / Evidence

完成时账本必须含：用户确认的痕迹 + 部署系统返回（构建号/发布成功提示等发布系统返回）。
> 不记账 = 本步不算完成，不能进入下一步。

When done, the ledger must include: the user's confirmation + the deploy system's response (build number / deploy success message).
> No ledger entry = this step is not done; do not proceed to the next step.

## 完成标准 / Done when

用户确认过、部署系统明确返回成功，且证据已留。

> **降级红线**：“部署成功”必须以**外部部署系统的返回**（构建号/发布回执等）为准，不许 AI 自述“已发布”；没有外部返回就不算完成。

User confirmed, deploy system clearly returned success, evidence logged.

> **No-downgrade line**: “deployed” must be backed by the external deploy system's response (build number / release receipt). The AI must never self-claim “deployed” — no external response means not done.
