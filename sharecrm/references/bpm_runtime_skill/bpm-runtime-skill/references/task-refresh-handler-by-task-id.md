# BpmTaskRefreshHandler

> **CLI**: `sharecrm bpm runtime regenerate-task-handler`
>
> **API**: `Fx.bpm.Task.refreshHandlerByTaskId`

## Purpose and Scenario

Refresh task handler

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.refreshHandlerByTaskId(
    taskId
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | Business flow task ID, used to locate the current task. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |

## Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.refreshHandlerByTaskId(
    ""  // taskId
)
```

## Operation Type

Non-Read

## Primary Target

Business flow task handler calculation.

## Prerequisites

Obtain and confirm the task ID, and clarify that this is recalculating the handler, not manually specifying a person.

## CLI Example

```bash
sharecrm bpm runtime regenerate-task-handler --taskId <task-id>
```

## Confirmation Requirements

Confirm the task, handler recalculation action, `taskId`, and potential personnel/routing impact. This operation is not a manual handler change.


Follow the write secondary confirmation rules in `../SKILL.md`.
## Verification

Use `task-get-task-info.md` to check the returned handler info when available. Only report returned evidence; do not promise the assignment is complete.