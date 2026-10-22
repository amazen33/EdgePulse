# EdgePulse Copilot instructions

Read [AGENTS.md](../AGENTS.md) and [development-team.md](../docs/development-team.md)
for the current repository contract, team roster and approval boundaries.
Read the specific approved work order and its accepted ADRs before reviewing.

Copilot is a bounded helper: housekeeping or an explicitly assigned read-only
review. Do not edit code, docs, receipts, policy, Git configuration or rulesets.
Do not delegate EdgePulse work to OpenCode. Do not merge, approve an agent's
own work, sign receipts or perform live actions. Report concrete findings with
file/line evidence and distinguish code/CI proof from environment acceptance.
A custom review subagent must explicitly receive the repository instructions;
verify its model separately when the task constrains the provider/model.
