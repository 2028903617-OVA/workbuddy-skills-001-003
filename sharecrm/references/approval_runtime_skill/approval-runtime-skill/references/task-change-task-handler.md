# Change Approval Task Handler

> **CLI**: `sharecrm approval runtime change-task-handler`
>

## Purpose and Scenario

Change the handler of a specified approval task.

## Operation Boundaries and Execution Rules

Changing the handler changes the pending handler for that task. `persons` must be a confirmed personnel list; do not pass names, department names, or unconfirmed candidates. After execution, directly use the task `current_candidate_ids` query in "Lightweight State Verification" in `../SKILL.md` and verify it against the confirmed personnel-ID list.


## Operation Type

Non-Read

## Primary Target

Handler of a specified approval task

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default.

## CLI Example

```bash
sharecrm approval runtime change-task-handler --data '{"taskId":"<task-id>","persons":["<user-id>"],"modifyOpinion":"<reason>"}'
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

When verifying only current candidates, you must directly run the task query in "Lightweight State Verification" in `../SKILL.md` and must not call `get-task-detail` or `instance-detail`; verify `current_candidate_ids`. Do not promise that the handler changed or final business status when evidence is insufficient.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | The approval task ID, used to locate the current approval task. |
| `persons` | List<String> | ✅ | An array of new handler user IDs for the regular approval task. Pass it in the complete JSON request body through `--data`, e.g. `{"persons":["<user-id>"]}`; do not use a flat flag. |
| `modifyOpinion` | String | Optional | The explanation or comment filled in when changing the approval handler. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |
| `persons` non-empty | Required parameter |
