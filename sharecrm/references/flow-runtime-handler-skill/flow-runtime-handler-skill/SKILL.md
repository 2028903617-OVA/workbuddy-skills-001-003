---
name: "flow-runtime-handler-skill"
description: "Operate ShareCRM approval flow, business flow, and stage accelerator runtime tasks. Use when users need to approve, reject, complete, reassign, remind, send back, retrieve, cancel, suspend, edit task data, advance stage, check progress, or process pending workflow tasks. Always require human confirmation before write or irreversible operations and append a Run Ledger record after each attempted write."
apiName: "flow-runtime-handler-skill"
---
# Flow Runtime Handler

## Purpose

Safely operate workflow runtime tasks through ShareCRM CLI:

- Approval flow: approve, reject, reassign, remind, add approver, send back, retrieve, cancel, reply, carbon copy, check detail/progress.
- BPM/business flow: complete, update and complete, reassign, remind, cancel, suspend, edit, trigger, check detail/log.
- Stage accelerator: fetch stage instance and advance stage.

This is a high-risk writer skill. Treat every runtime operation as a state-changing action unless it is an explicit query/detail command.

## Contract

| Item | Rule |
| --- | --- |
| Role | writer |
| Risk | high |
| Preconditions | Target identifier and operation are known, or query first to select a target. |
| Human confirmation | Mandatory before every write, reassignment, cancellation, rollback, or stage transition. |
| Retry | Retry only after correcting parameters; stop on permission errors or status conflicts. |

Do not hardcode tenant, environment, user, URL, token, credential, or project-specific IDs. Read credentials from the approved local credential mechanism when a command requires authentication.

## Minimal Input

```yaml
taskType: approval | bpm | stage
target:
  taskId: string
  instanceId: string
  entityId: string
  objectId: string
action: approve | reject | complete | change_handler | remind | add_approver | send_back | retrieve | cancel | suspend | edit | update_and_complete | move_stage | reply | carbon_copy | query_detail | query_progress
payload:
  opinion: string
  handlerIds: [integer]
  data: object
  stageId: string
  previousTaskId: string
```

## Workflow

1. Classify the flow type: `approval`, `bpm`, or `stage`.
2. If the target is missing or ambiguous, query pending tasks/detail first and let the user select one.
3. Map the user's intent to one action and command using `references/runtime-commands.md`.
4. Validate required parameters with the command reference; run CLI `--help` when uncertain.
5. Before any write, state the exact target, action, side effect, and intended command shape; wait for explicit confirmation.
6. Execute one target at a time. For multiple tasks, ask/confirm per task unless the user explicitly approves a bounded batch.
7. Verify by re-querying pending tasks, runtime detail, instance detail, progress, or audit log.
8. Append a compact Run Ledger JSONL entry after every attempted write, including failed or blocked attempts.

## Safety Rules

- Never infer a destructive action from vague intent; clarify first.
- Stop on insufficient permission, ambiguous target, missing required parameter, or task status conflict.
- Prefer `--help` over guessing command flags.
- Keep sensitive payloads out of chat and ledgers; store only references, summaries, and hashes.
- For edit/update operations, show the field-level change summary before confirmation.

## Runtime State

```text
planned -> ready -> running -> succeeded
                         -> failed
                         -> blocked
                         -> skipped
```

Use `blocked` for missing identifiers/parameters/permissions. Use `skipped` when the user cancels or declines confirmation.

## Run Ledger

After every attempted write, append one JSON object to `{workspace}/tempfile/flow-runtime-ledger.jsonl`.

Use the same `run_id` across retries and fallback operations for the same user goal. Increment `attempts` across repeated attempts. Store large or sensitive input/output payloads as artifacts and reference them from `input_ref` or `output_ref`.

Preferred helper:

```bash
python3 <skill_dir>/scripts/append_ledger.py --workspace <WORKSPACE_DIR> --entry '<JSON_OBJECT>'
```

Required JSON fields:

```yaml
run_id: generated id
goal: original user goal
status: succeeded | failed | blocked | skipped
target: taskId/instanceId/objectId summary
command: sharecrm <module> runtime <operation>
confirmation: approved | declined | not_required
started_at: timestamp
ended_at: timestamp
attempts: number
errors: []
```

Optional fields: `input_ref`, `output_ref`, `output_summary`, `artifact_hash`, and `operator`.

## Command Reference

Read `references/runtime-commands.md` only when a concrete operation or command mapping is needed.
