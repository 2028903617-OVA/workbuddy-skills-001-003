# Query Instance Stage Tasks

> **CLI**: `sharecrm stage runtime task-by-stage-id`

## Operation Type

Read

## Primary Target

`task-by-stage-id`: Query instance stage tasks

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime task-by-stage-id --workflowInstanceId "<workflow-instance-id>" --stageId "<stage-id>"
```

## Confirmation Requirements

Read-only query, no write confirmation needed; a successful read does not authorize subsequent writes.

Read-only operations can be executed directly without secondary confirmation; read or asynchronous result reads must not automatically escalate to non-read-only operations.
## Verification

Record the read-only result; the result is only used to identify or validate the target and cannot serve as authorization for executing a write.

### Retained API, Groovy Background, and Parameter Table

### Purpose and Scenario

Get task information

### API
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Task.getTasksInfoByInstanceIdAndStageId(
    workflowInstanceId,
    stageId
)
```

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `workflowInstanceId` | String | ✅ | Stage accelerator instance ID |
| `stageId` | String | ✅ | Stage accelerator stage ID |

### Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `workflowInstanceId` non-empty | Required parameter |
| `stageId` non-empty | Required parameter |

### Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Task.getTasksInfoByInstanceIdAndStageId(
    ""  // workflowInstanceId,
    ""  // stageId
)
```