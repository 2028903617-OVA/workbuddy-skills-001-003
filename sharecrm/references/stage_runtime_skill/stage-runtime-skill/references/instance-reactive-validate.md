# Validate Whether Reactivation Is Allowed

> **CLI**: `sharecrm stage runtime reactive-validate`

## Operation Type

Non-Read (Validation; result only, no automatic write)

## Primary Target

`reactive-validate`: Validate whether reactivation is allowed

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime reactive-validate --workflowInstanceId "<workflow-instance-id>"
```

## Confirmation Requirements

Secondary confirmation for non-read validation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`; this validation only reports results and does not reactivate the instance or automatically trigger subsequent operations.

## Verification

Record the read-only result; the result is only used to identify or validate the target and cannot serve as authorization for executing a write.

### Retained API, Groovy Background, and Parameter Table

### Purpose and Scenario

Reactivation validation

### API
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Instance.reactiveValidate(
    workflowInstanceId
)
```

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `workflowInstanceId` | String | ✅ | Instance ID |

### Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `workflowInstanceId` non-empty | Required parameter |

### Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Instance.reactiveValidate(
    ""  // workflowInstanceId
)
```