# BpmTaskButtons

> **CLI**: `sharecrm bpm runtime get-button-by-task-id`
>
> **API**: `Fx.bpm.Task.getButtonByTaskId`

## Purpose and Scenario

Get task buttons

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.getButtonByTaskId(
    taskIds
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskIds` | List<String> | Optional | List of business flow task IDs. Pass the complete JSON request body through `--data`, e.g. `{"taskIds":["<task-id>"]}`; do not use the flat `--taskIds` flag or the singular `--taskId`. |

## Code Example

```groovy
def taskIds = ['<confirmed-task-id>']

def (Boolean error, Map result, String msg) = Fx.bpm.Task.getButtonByTaskId(taskIds)
```

When there are multiple task IDs, put all IDs in the `taskIds` array of one `--data` JSON body.

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| No fixed required parameters | Provide parameters as needed per the business scenario |

## Operation Type

Read

## Primary Target

Business flow task buttons.

## Prerequisites

Obtain one or more task IDs and construct the `taskIds` array in the `--data` request body.

## CLI Example

```bash
sharecrm bpm runtime get-button-by-task-id --data '{"taskIds":["<task-id>"]}'
```

## Confirmation Requirements

Read-only operations require no confirmation; confirm the selected task ID when there are multiple candidates.


Follow the read-only boundaries in `../SKILL.md`: may be executed directly, but must not auto-escalate to writes.
## Verification

Check the returned available buttons. Button availability is only query evidence; it does not execute or verify any task action.
