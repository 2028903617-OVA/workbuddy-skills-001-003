# Cancel Instance

> **CLI**: `sharecrm stage runtime cancel`

## Operation Type

Non-Read

## Primary Target

`cancel`: Cancel instance

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime cancel --entityId "<entity-api-name>" --objectId "<object-id>" --cancelReason "<confirmed-cancel-reason>"
```

## Confirmation Requirements

Canceling an entire stage instance is a high-impact write. Confirm the exact object, current instance, and cancel reason before submitting. Present one final business preview that states the whole-instance cancellation and its impact scope, then wait for explicit confirmation in a **subsequent message**. Do not call cancel in the round that requests confirmation. After valid confirmation, execute once and do not ask for confirmation again.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Check whether the response is successful and verify the target status with a read-only query; do not treat request acceptance as final success.

### Retained API, Groovy Background, and Parameter Table

### Purpose and Scenario

Cancel

### API
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Instance.cancel(
    entityId,
    objectId,
    cancelReason
)
```

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `entityId` | String | ✅ | entityId |
| `objectId` | String | ✅ | objectId |
| `cancelReason` | String | Optional | Cancel reason |

### Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `entityId` non-empty | Required parameter |
| `objectId` non-empty | Required parameter |

### Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Instance.cancel(
    ""  // entityId,
    ""  // objectId,
    ""  // cancelReason
)
```
