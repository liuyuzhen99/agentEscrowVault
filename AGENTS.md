<!-- dev-harness:antigravity:start -->
> 本节供 Google Antigravity 使用 / This section is for Google Antigravity.
>
> This project uses dev-harness: a skill-based development flow plus a progress ledger.
>
> Before doing any work, read `.agents/skills/orchestrate/SKILL.md`. It tells you how the
> flow works, which step you are on, and how to log progress.
>
> The other cards (`analyze`, `reproduce`, `plan`, `tdd`, `test`, `local-verify`,
> `review`, `deploy`, `re-verify`) are loaded on demand as the flow reaches each step;
> they live under `.agents/skills/<name>/SKILL.md`. Do not assume a card body is already
> in context.
>
> Progress lives in one ledger per task under `progress/`, using the template at
> `.agents/skills/orchestrate/assets/ledger-template.md`. Append one entry per finished
> step; never rewrite history. When the task is done, land the acceptance cases in the
> repo at the spots `plan` recorded before deleting the ledger — a case that lives only
> in the ledger was never deposited. (An abandoned task lands nothing: just delete it.)
<!-- dev-harness:antigravity:end -->
