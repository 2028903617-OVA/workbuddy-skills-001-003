# Disassociate Confirmed Object Association

> **CLI**: `sharecrm stage runtime disassociate`

## Operation Type

Non-Read

## Primary Target

`disassociate`: Disassociate confirmed object association

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime disassociate --data '{"taskId":"<task-id>","objectIds":["<confirmed-object-id>"]}'
```

## Confirmation Requirements

`objectIds` must be a confirmed, closed set of object IDs; verify each item that will be disassociated.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Check whether the response is successful and verify the target status with a read-only query; do not treat request acceptance as final success.

### Retained API, Groovy Background, and Parameter Table

### Purpose and Scenario

Disassociate

### API
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Task.disassociate(
    taskId,
    objectIds
)
```

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | Task ID |
| `objectIds` | List | ✅ | List of associated data IDs. Pass it in the complete JSON request body through `--data`; do not use a flat flag. |

### Code Example

```groovy
def taskId = '<confirmed-task-id>'
def objectIds = ['<confirmed-object-id>']

def (Boolean error, Map result, String msg) = Fx.stage.Task.disassociate(taskId, objectIds)
```

### Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |
| `objectIds` non-empty | Required parameter |
