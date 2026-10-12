# Regenerate Task Assignees

> **CLI**: `sharecrm stage runtime regenerate-task-handler`

## Operation Type

Non-Read

## Primary Target

`regenerate-task-handler`: Regenerate task assignees

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime regenerate-task-handler --taskId "<task-id>"
```

## Confirmation Requirements

Confirm the exact task before submitting.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Check whether the response is successful and verify the target status with a read-only query; do not treat request acceptance as final success.

### Retained API, Groovy Background, and Parameter Table

### Purpose and Scenario

Regenerate assignees

### API
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Task.regenerateHandlerByTaskId(
    taskId
)
```

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | Task ID |

### Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |

### Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Task.regenerateHandlerByTaskId(
    ""  // taskId
)
```