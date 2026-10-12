# Add Approval Sign-off Node

> **CLI**: `sharecrm approval runtime add-extra-node`
>

## Purpose and Scenario

Insert a temporary front sign-off node before the current approval task, specifying the handler and reason for that node.

## Operation Boundaries and Execution Rules

Adding a sign-off node changes the subsequent approval chain. `extraNodeAssignee` must be a confirmed handler identifier, and `addNodeReason` must be provided by the user; do not guess personnel IDs from names, and do not auto-add sign-off nodes.


## Operation Type

Non-Read

## Primary Target

Current approval task and front sign-off node

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default.  You must confirm the sign-off user ID, reason, `sequence`, and routing impact.

## CLI Example

```bash
sharecrm approval runtime add-extra-node --data '{"taskId":"<task-id>","extraNodeAssignee":["<user-id>"],"addNodeReason":"<reason>","sequence":<sequence>}'
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

Before and after writing, when verifying only the added sign-off task, instance state, or current candidates, you must query active tasks by instance in "Lightweight State Verification" in `../SKILL.md` and compare task sets, task summaries, and candidates; do not call `get-task-detail` or `instance-detail`. Query `get-task-detail` or `instance-detail` only when the user explicitly asks to verify sign-off-node order, the actual routing effect of `sequence`, or complete approval routing. Do not promise final business status when evidence is insufficient.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | The approval task ID, used to locate the current approval task. |
| `extraNodeAssignee` | List<String> | ✅ | An array of front sign-off handler user IDs. Pass it in the complete JSON request body through `--data`, e.g. `{"extraNodeAssignee":["<user-id>"]}`; do not use a flat flag. |
| `addNodeReason` | String | ✅ | The reason for adding the sign-off node, explicitly provided by the user. |
| `sequence` | Boolean | Optional | Whether to process the sign-off node sequentially; `true` means sequential processing, `false` means non-sequential processing. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `extraNodeAssignee` non-empty | Required parameter |
| `taskId` non-empty | Required parameter |
| `addNodeReason` non-empty | Required parameter |
