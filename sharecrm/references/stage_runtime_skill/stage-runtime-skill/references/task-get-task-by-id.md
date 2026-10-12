# Query Task by ID

> **CLI**: `sharecrm stage runtime task`

## Operation Type

Read

## Primary Target

`task`: Query task by ID

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime task --taskId "<task-id>" --activityId "<activity-id>"
```

## Confirmation Requirements

Read-only query, no write confirmation needed; a successful read does not authorize subsequent writes.

Read-only operations can be executed directly without secondary confirmation; read or asynchronous result reads must not automatically escalate to non-read-only operations.
## Verification

Record the read-only result; the result is only used to identify or validate the target and cannot serve as authorization for executing a write.

### Retained API, Groovy Background, and Parameter Table

### Operation Properties and CLI Contract

- **Type**: Read-only; primary target is `taskId`, `activityId` is optional context.

```bash
sharecrm stage runtime task --taskId "<taskId>" --activityId "<activityId>"
```

| flag | Type | Required | Description |
| --- | --- | --- | --- |
| `--taskId` | String | ✅ | Runtime task ID. |
| `--activityId` | String | Optional | Activity ID used when retrieving buttons for tasks that failed to create. |

### Usage Boundaries

Only read and use the task status, form/fields, required fields, available buttons, and association/concurrency information that actually appear in the response. Do not claim that this API guarantees any fields that are not present, and do not automatically escalate read results into edit, complete, or other write operations.

### API

```groovy
Fx.stage.Task.getById(taskId, activityId)
```