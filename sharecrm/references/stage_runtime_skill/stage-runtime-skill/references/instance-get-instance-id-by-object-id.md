# Query Instance by Business Object

> **CLI**: `sharecrm stage runtime get-instance-by-object`

## Operation Type

Read

## Primary Target

`get-instance-by-object`: Query instance by business object

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

Before constructing this command, bind each value by meaning, then pass them strictly in the `--entityId`, `--objectId` order shown in the CLI example below:

| Command parameter | Required value | Accepted source | Must never contain |
| --- | --- | --- | --- |
| `entityId` | The business object API name, for example `NewOpportunityObj` | The current object's `apiName`/`objectApiName` or a confirmed object definition | A business-record `_id`, stage instance, stage, or task ID |
| `objectId` | The real system `_id` of a record in that same business object | Trusted target-business-record context, or the `_id` returned after uniquely querying a business record by that `entityId` | `StageTaskObj._id`, `workflowInstanceId`, `stageId`, `taskId`, `stageTaskId`, business object API name, business number, name, or title |

When only two unlabeled strings are available, or they cannot be proven to belong to the same business object, stop and request their source or perform a read-only query first. Do not swap values based on user input order, ID appearance, or naming intuition, and do not retry by swapping parameters. `StageTaskObj._id`, `workflowInstanceId`, `stageId`, `taskId`, and `stageTaskId` are never valid sources for `objectId`. Before execution, verify that `entityId` is the API name and `objectId` is the business-record `_id` confirmed for that `entityId`.

## CLI Example

```bash
sharecrm stage runtime get-instance-by-object --entityId "<entity-api-name>" --objectId "<object-id>"
```

## Confirmation Requirements

Read-only query, no write confirmation needed. Confirm that `entityId` and `objectId` point to the intended business object.

Read-only operations can be executed directly without secondary confirmation; read or asynchronous result reads must not automatically escalate to non-read-only operations.
## Verification

Record the read-only result; the result is only used to identify or validate the target and cannot serve as authorization for executing a write.

### Retained API, Groovy Background, and Parameter Table

### Purpose and Scenario

Get instance information by object ID

### API
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Instance.getInstanceInfoByObjectId(
    entityId,
    objectId
)
```

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `entityId` | String | ✅ | The apiName of the current object |
| `objectId` | String | ✅ | The real system `_id` of the target business record under the current `entityId`. It may only come from trusted business-record context or the result of uniquely querying a record by that `entityId`; do not use `StageTaskObj._id`, `workflowInstanceId`, `stageId`, `taskId`, or `stageTaskId`. |

### Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `entityId` non-empty | Required parameter |
| `objectId` non-empty | Required parameter |
| Semantic binding verified | Execute only when `entityId` is the object API name and `objectId` is that object's record `_id`; do not substitute a stage instance, stage, or task ID, and do not interchange the two |

> `entityId` takes the business object ApiName (e.g., `NewOpportunityObj`), and `objectId` takes the business record ID; the two cannot be interchanged.

### Code Example
```groovy
def entityId = '<object-api-name>'
def objectId = '<record-id>'

def (Boolean error, Map result, String msg) = Fx.stage.Instance.getInstanceInfoByObjectId(
    entityId,
    objectId
)
```
