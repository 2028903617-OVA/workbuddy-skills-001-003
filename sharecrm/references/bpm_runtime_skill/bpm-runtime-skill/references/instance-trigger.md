# BpmTrigger

> **CLI**: `sharecrm bpm runtime trigger`
>
> **API**: `Fx.bpm.Instance.triggerInstance`

## Purpose and Scenario

Trigger an instance

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Instance.triggerInstance(
    id,
    objectId
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | String | ✅ | Business flow definition ID (workflowDefinitionId/outlineId), not an instance ID. Provided by the user as a verified business flow definition ID. |
| `objectId` | String | ✅ | Associated business data record ID. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `id` non-empty | Required parameter |
| `objectId` non-empty | Required parameter |

> `id` is the business flow definition ID (workflowDefinitionId/outlineId), and `objectId` is the business record ID; the two are not interchangeable. `id` is not a business flow instance ID.

## Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Instance.triggerInstance(
    ""  // id,
    ""  // objectId
)
```

## Operation Type

Non-Read

## Primary Target

Business flow definition ID (workflowDefinitionId/outlineId) and business record.

## Prerequisites

Confirm that `id` is the business flow definition ID (workflowDefinitionId/outlineId), not an instance ID, task ID, or business record ID; obtain the associated `objectId`.

## CLI Example

```bash
sharecrm bpm runtime trigger --id <record-unique-id> --objectId <object-id>
```

## Confirmation Requirements

Confirm the target, trigger action, business flow definition ID (`id`), `objectId`, and the new instance or downstream processing impact.


Follow the write secondary confirmation rules in `../SKILL.md`.
## Verification

Use `instance-get-instances-by-object.md` with the same `objectId`; use `instance-get-instance-log.md` only after obtaining an instance ID. Do not claim trigger success beyond the returned evidence.