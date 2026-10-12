# BpmTaskAfterActionRetry

> **CLI**: `sharecrm bpm runtime task-after-retry`
>
> **API**: `Fx.bpm.Task.afterActionRetry`

## Purpose and Scenario

Task after-action retry

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.afterActionRetry(
    taskId,
    rowNum,
    executeType
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | Business flow task ID, used to locate the current task. |
| `rowNum` | Integer | Optional | The after-action sequence number to retry (integer). |
| `executeType` | Integer | Optional | After-action processing type (integer): `0` means ignore, `1` means execute. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |

## Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.afterActionRetry(
    ""  // taskId,
    0  // rowNum,
    0  // executeType
)
```

## Operation Type

Non-Read

## Primary Target

Business flow task and the specified after-action.

## Prerequisites

Obtain and confirm the task ID; confirm the after-action row number and execution method.

## CLI Example

```bash
sharecrm bpm runtime task-after-retry --taskId <task-id> --rowNum <row-num> --executeType <execute-type>
```

## Confirmation Requirements

Confirm the task, retry action, `taskId`, `rowNum`, `executeType`, and the potential impact of repeated execution.


Follow the write secondary confirmation rules in `../SKILL.md`.
## Verification

Use `task-get-task-info.md`, and use `instance-get-instance-log.md` when applicable to check returned evidence. Do not promise the business state is verified.