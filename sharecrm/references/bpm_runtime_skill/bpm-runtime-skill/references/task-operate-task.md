# BpmTaskOperate

> **CLI**: `sharecrm bpm runtime operate-task`
>
> **API**: `Fx.bpm.Task.operateTask`

## Purpose and Scenario

Operate on a task

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.operateTask(
    taskId,
    type,
    opinion,
    tagInfo
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | Business flow task ID, used to locate the current task. |
| `type` | String | ✅ | The task operation type to execute; must use a value explicitly provided by the user or obtained from a query of available values. |
| `opinion` | String | Optional | The opinion or comment entered when processing the current task. |
| `tagInfo` | Map | Optional | Additional tag or processing info required when executing the task operation, pass a valid JSON object. |

## Code Example

```groovy
def taskId = '<confirmed-task-id>'
def type = 'suspend' // Only suspend or resume
def opinion = '<explicit-opinion>'
def tagInfo = ['<confirmed-tag-key>': '<confirmed-tag-value>']

def (Boolean error, Map result, String msg) = Fx.bpm.Task.operateTask(
    taskId, type, opinion, tagInfo
)
```

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |
| `type` non-empty | Required parameter |

> `type` only supports `suspend` (pause) or `resume` (continue).

## Operation Type

Non-Read

## Primary Target

Business flow task and the explicitly supported operation type.

## Prerequisites

Obtain the task ID, and obtain the `type` explicitly provided by the user or confirmed via `task-get-button-by-task-id.md`; do not infer from natural-language descriptions.

## CLI Example

```bash
sharecrm bpm runtime operate-task --taskId <task-id> --type <operation-type> --opinion "<opinion>"
```

## Confirmation Requirements

Confirm the task, exact operation type, `taskId`, opinion, tag info, and operation impact before execution.


Follow the write secondary confirmation rules in `../SKILL.md`.
## Verification

Use `task-get-task-info.md`, `task-get-button-by-task-id.md`, or `instance-get-instance-log.md` as needed. When there is no returned evidence, do not promise that the requested operation has changed the business state.