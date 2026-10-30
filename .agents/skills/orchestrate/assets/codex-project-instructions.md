## dev-harness 开发流程

本项目使用 dev-harness。开始开发任务时，必须读取本项目根目录下 `.agents/skills/orchestrate/SKILL.md` 并执行其流程。

- 所有路径以本指令文件所在的项目根目录为起点。方法卡中的 `skills/<name>/SKILL.md` 对应本项目 `.agents/skills/<name>/SKILL.md`。按当前操作读取对应卡片全文：`analyze`、`reproduce`、`plan`、`tdd`、`test`、`local-verify`、`review`、`deploy`、`re-verify`。
- 账本放在本项目 `progress/`，模板为 `.agents/skills/orchestrate/assets/ledger-template.md`。开工建立或恢复账本，每步完成追加实际命令和原始输出并向用户报告；任务全部完成后**先按方案里写好的落点把验收用例落到仓库里，再删除账本**——用例只写在账本里，账本一删就等于没沉淀。
- 方案评审与代码评审使用独立子 agent，提供项目路径、原始需求、验收标准与需要评审的文件。评审员必须读取本项目的 `plan`、`review` 及相应方法卡。遵守方法卡规定的独立评审与用户确认步骤。当前 Codex 缺少独立子 agent 能力时，按照 `review` 卡报告受阻。
- 发生错误后修改代码、补充测试、重新验证时，按照 `orchestrate` 卡重新读取对应方法卡，并记录本轮证据。
