# Retry Approval Subsequent Tasks

> **CLI**: `sharecrm approval runtime retrytask`
>

## Purpose and Scenario

Retry tasks that failed to execute or need reprocessing in a specified approval instance.

## Operation Boundaries and Execution Rules

Retry reprocesses failed tasks in the instance. First confirm the current instance, failure reason, and allowed retry scope; do not auto-retry simply because an anomaly was detected. After execution, re-query the instance status or related task results.


## Operation Type

Non-Read

## Primary Target

Approval instance subsequent tasks

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default.

## CLI Example

```bash
sharecrm approval runtime retrytask --instanceId <instance-id>
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

When verifying only instance state, you must directly run the instance query in "Lightweight State Verification" in `../SKILL.md` and must not call `instance-detail` or `get-task-detail`; when only proving that subsequent tasks were generated, you must query active tasks by instance and must not call `get-task-detail`; query `instance-detail` only when complete approval routing must be verified. Do not promise final business status when evidence is insufficient.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `instanceId` | String | ✅ | The approval flow instance ID. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `instanceId` non-empty | Required parameter |
