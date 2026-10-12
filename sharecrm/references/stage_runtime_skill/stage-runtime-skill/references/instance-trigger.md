# Trigger Source Workflow for Object

> **CLI**: `sharecrm stage runtime trigger`

## Operation Type

Non-Read

## Primary Target

`trigger`: Trigger source workflow for object

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`. A verified source workflow ID (`sourceWorkflowId`) must be provided.

## CLI Example

```bash
sharecrm stage runtime trigger --entityId "<entity-api-name>" --objectId "<object-id>" --sourceWorkflowId "<source-workflow-id>"
```

## Confirmation Requirements

Confirm the exact business object and source workflow ID before submitting to avoid creating an incorrect execution.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Check whether the response is successful and verify the target status with a read-only query; do not treat request acceptance as final success.

### Retained API, Groovy Background, and Parameter Table

### Purpose and Scenario

Trigger

### API
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Instance.trigger(
    entityId,
    objectId,
    sourceWorkflowId
)
```

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `entityId` | String | ✅ | Initiating object apiName |
| `objectId` | String | ✅ | Initiating object objectId |
| `sourceWorkflowId` | String | ✅ | Stage accelerator workflow ID |

### Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `entityId` non-empty | Required parameter |
| `objectId` non-empty | Required parameter |

### Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Instance.trigger(
    ""  // entityId,
    ""  // objectId,
    ""  // sourceWorkflowId
)
```