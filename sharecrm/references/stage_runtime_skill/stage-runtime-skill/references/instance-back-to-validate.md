# Rollback Validation

> **CLI**: `sharecrm stage runtime back-to-validate`

## Operation Type

Read (read-only validation; result only, no automatic write)

## Primary Target

`back-to-validate`: Rollback validation

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime back-to-validate --workflowInstanceId "<workflow-instance-id>" --stageId "<stage-id>"
```

## Confirmation Requirements

No secondary confirmation is required; execute directly once the target is confirmed. This validation only reports results and does not automatically roll back, move the instance, or trigger subsequent operations. An actual rollback still requires a preview and confirmation under the corresponding write reference.

## Verification

Record the read-only result; the result is only used to identify or validate the target and cannot serve as authorization for executing a write.

### Retained API, Groovy Background, and Parameter Table

### Purpose and Scenario

Rollback validation

### API
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Instance.backToValidate(
    workflowInstanceId,
    stageId
)
```

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `workflowInstanceId` | String | ✅ | Instance ID |
| `stageId` | String | ✅ | Stage ID |

### Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `workflowInstanceId` non-empty | Required parameter |
| `stageId` non-empty | Required parameter |

### Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Instance.backToValidate(
    ""  // workflowInstanceId,
    ""  // stageId
)
```
