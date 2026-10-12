# BpmTaskChangeHandler

> **CLI**: `sharecrm bpm runtime change-task-handler`
>
> **API**: `Fx.bpm.Task.changeTaskHandler`

## Purpose and Scenario

Change task handler

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.changeTaskHandler(
    taskId,
    candidateIds,
    modifyOpinion
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | Business flow task ID, used to locate the current task. |
| `candidateIds` | List<String> | ✅ | Array of new task handler user IDs. Pass it in the complete JSON request body through `--data`, e.g. `{"candidateIds":["<user-id>"]}`; do not use a flat flag. |
| `modifyOpinion` | String | Optional | The comment entered when changing the task handler. |

## Code Example

```groovy
def taskId = '<confirmed-task-id>'
def candidateIds = ['<confirmed-user-id>']
def modifyOpinion = '<explicit-change-reason>'

def (Boolean error, Map result, String msg) = Fx.bpm.Task.changeTaskHandler(
    taskId, candidateIds, modifyOpinion
)
```

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |
| `candidateIds` non-empty | Required parameter |

> `candidateIds` can only be a list of user ID strings; do not pass names, task IDs, or workflow instance IDs. Put the array in the `--data` JSON request body and do not use a flat flag.

## Operation Type

Non-Read

## Primary Target

Business flow task and candidate handlers.

## Prerequisites

Obtain the task ID and verified user IDs for all replacement candidates; do not use names in place of user IDs.

## CLI Example

```bash
sharecrm bpm runtime change-task-handler --data '{"taskId":"<task-id>","candidateIds":["<user-id>"],"modifyOpinion":"<reason>"}'
```

## Confirmation Requirements

Confirm the task, handler-change action, `taskId`, candidate user ID list, and personnel change summary (including replacement scope and opinion).


Follow the write secondary confirmation rules in `../SKILL.md`.
## Verification

Use `task-get-task-info.md` to check the task. Only report returned assignment data; do not promise downstream routing is verified.
