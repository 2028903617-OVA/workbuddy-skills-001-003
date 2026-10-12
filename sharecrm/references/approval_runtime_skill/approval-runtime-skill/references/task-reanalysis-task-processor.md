# Re-analyze Approval Task Handler

> **CLI**: `sharecrm approval runtime regenerate-task-handler`
>

## Purpose and Scenario

Recalculate the handler of a specified approval task, used to refresh after handler configuration changes.

## Operation Boundaries and Execution Rules

This operation recalculates the task handler based on current rules. First confirm this is "recalculate" rather than a manual handler change, and confirm `taskId`; do not auto-execute because the handler is empty or unknown.


## Operation Type

Non-Read

## Primary Target

Handler analysis result for a specified approval task

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default.

## CLI Example

```bash
sharecrm approval runtime regenerate-task-handler --taskId <task-id>
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

When verifying only current candidates, you must directly run the task query in "Lightweight State Verification" in `../SKILL.md` and must not call `get-task-detail` or `instance-detail`; verify `current_candidate_ids`. Do not promise that handlers were re-analyzed or final business status when evidence is insufficient.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | The approval task ID, used to locate the current approval task. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |
