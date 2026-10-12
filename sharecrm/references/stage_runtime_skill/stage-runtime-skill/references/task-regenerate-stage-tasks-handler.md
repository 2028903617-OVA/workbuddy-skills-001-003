# Regenerate Stage Task Assignees

> **CLI**: `sharecrm stage runtime regenerate-stage-tasks-handler`

## Operation Type

Non-Read

## Primary Target

`regenerate-stage-tasks-handler`: Regenerate stage task assignees

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime regenerate-stage-tasks-handler --stageTaskId "<stage-task-id>" --opinion "<confirmed-opinion>"
```

## Confirmation Requirements

Confirm the stage task and the specified opinion before submitting.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Check whether the response is successful and verify the target status with a read-only query; do not treat request acceptance as final success.

### Retained API, Groovy Background, and Parameter Table

### Purpose and Scenario

Regenerate assignees

### API
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Task.regenerateHandlerByStageTaskId(
    stageTaskId,
    opinion
)
```

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `stageTaskId` | String | ✅ | Stage task ID |
| `opinion` | String | Optional | opinion |

### Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `stageTaskId` non-empty | Required parameter |

> This operation uses `stageTaskId`, not the runtime `taskId`, instance ID, or stage ID.

### Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Task.regenerateHandlerByStageTaskId(
    ""  // stageTaskId,
    ""  // opinion
)
```