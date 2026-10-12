# Change Free Approval Handler

> **CLI**: `sharecrm approval runtime change-free-approval-task-handler`
>

## Purpose and Scenario

Modify the handler configuration for a free approval node in an approval instance.

## Operation Boundaries and Execution Rules

This operation modifies the handler configuration of a free approval node. `freeApprovalDef` must be converted from the real `freeTasks` configuration of the current free-approval task: retain only `assignee` in each item and generate a zero-based `order` in the real array order. A returned `state` is for identifying state only and must not be sent. `assignee.person` must be an array of real user IDs. Do not add, remove, or merge nodes, and do not construct nodes from personnel names.


## Operation Type

Non-Read

## Primary Target

Handler of a free approval instance

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default. `freeApprovalDef` must come from the current context or CLI query results only; do not fabricate it. When the trusted `freeApprovalDef` required for execution is absent from the current context, before writing you must read the current task details with `CHANGE_HANDLER_BUTTON` and obtain the real array from the corresponding `eventLink.freeTasks`. Convert each item to only `assignee` and an `order` generated from its array order, then remove `state` before sending it. If no non-empty `freeTasks` can be uniquely attributed to the current task, stop. Do not fall back to instance details, names, candidates, or historical parameters to construct it, and do not read details again as default verification after a successful write.

## CLI Example

```bash
sharecrm approval runtime change-free-approval-task-handler --data '{"instanceId":"<instance-id>","modifyOpinion":"<confirmed-reason>","freeApprovalDef":[{"assignee":{"person":["<confirmed-user-id>"]},"order":0},{"assignee":{"person":["<confirmed-user-id>"]},"order":1}]}'
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

After a successful write, when verifying only current candidates, you must query active tasks by instance in "Lightweight State Verification" in `../SKILL.md` and must not call `get-task-detail` or `instance-detail`. Query `get-task-detail` or `instance-detail` only when the user explicitly asks to view or verify the free-approval configuration. Do not promise final business status when evidence is insufficient.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `instanceId` | String | ✅ | The approval flow instance ID. |
| `modifyOpinion` | String | Optional | The explanation or comment filled in when changing the approval handler. |
| `freeApprovalDef` | List<Map> | Optional | The free-approval handler configuration array. Each item must contain only `assignee` and `order`: `assignee.person` is an array of real user IDs, and `order` is the zero-based node order. Pass it in the complete JSON request body through `--data`; its value may only be converted from the current task's real `freeTasks`, with `state` removed. Do not use a flat flag, personnel name, or manually constructed value. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `instanceId` non-empty | Required parameter |
| `freeApprovalDef` non-empty | Required when changing free-approval handlers; it must be the real configuration array for the current task |
| Every item has a valid structure | `assignee.person` is a non-empty user-ID array and `order` is a non-negative integer generated from the current array order |
