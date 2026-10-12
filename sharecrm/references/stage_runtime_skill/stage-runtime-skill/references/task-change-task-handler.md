# Change Task Handler

> **CLI**: `sharecrm stage runtime change-task-handler`

## Operation Type

Non-Read

## Primary Target

`change-task-handler`: Change task handler

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime change-task-handler --data '{"taskId":"<task-id>","candidateIds":["<confirmed-user-id>"]}'
```

## Confirmation Requirements

`candidateIds` must be a confirmed, closed user ID list; do not use names or expand the list after confirmation.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Check whether the response is successful and verify the target status with a read-only query; do not treat request acceptance as final success.

### Retained API, Groovy Background, and Parameter Table

### Purpose and Scenario

Change task handler

### API
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Task.changeTaskHandler(
    taskId,
    candidateIds
)
```

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | Task ID |
| `candidateIds` | List | ✅ | Array of modified handler user IDs. Pass it in the complete JSON request body through `--data`; do not use a flat flag. |

### Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |
| `candidateIds` non-empty | Required parameter |

> `candidateIds` only accepts a list of user ID strings; do not pass names, task IDs, or instance IDs. Put the array in the `--data` JSON request body, e.g. `{"candidateIds":["10001"]}`; do not use a flat flag.

### Code Example

```groovy
def taskId = '<confirmed-task-id>'
def candidateIds = ['<confirmed-user-id>']

def (Boolean error, Map result, String msg) = Fx.stage.Task.changeTaskHandler(taskId, candidateIds)
```
