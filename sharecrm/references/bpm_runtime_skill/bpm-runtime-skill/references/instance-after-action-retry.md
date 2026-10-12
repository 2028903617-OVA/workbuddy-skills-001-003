# BpmInstanceAfterActionRetry

> **CLI**: `sharecrm bpm runtime instance-after-action-retry`
>
> **API**: `Fx.bpm.Instance.afterActionRetry`

## Purpose and Scenario

Business flow instance after-action retry

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Instance.afterActionRetry(
    instanceId,
    rowNum,
    executeType
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `instanceId` | String | ✅ | Business flow instance ID. |
| `rowNum` | Integer | Optional | The after-action sequence number to retry (integer). |
| `executeType` | Integer | Optional | After-action processing type (integer): `0` means ignore, `1` means execute. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `instanceId` non-empty | Required parameter |

## Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Instance.afterActionRetry(
    ""  // instanceId,
    0  // rowNum,
    0  // executeType
)
```

## Operation Type

Non-Read

## Primary Target

Business flow instance and the specified after-action.

## Prerequisites

Confirm the business flow instance ID; confirm the after-action row number and execution method before retrying.

## CLI Example

```bash
sharecrm bpm runtime instance-after-action-retry --instanceId <instance-id> --rowNum <row-num> --executeType <execute-type>
```

## Confirmation Requirements

Confirm the instance, retry action, `instanceId`, `rowNum`, `executeType`, and the potential impact of repeated execution.


Follow the write secondary confirmation rules in `../SKILL.md`.
## Verification

Use `instance-get-instance-log.md` after execution to view obtainable log evidence; do not claim the after-action or business result is verified unless the returned data can prove it.