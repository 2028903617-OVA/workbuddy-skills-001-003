# BpmGetInstanceList

> **CLI**: `sharecrm bpm runtime get-instances-by-object`
>
> **API**: `Fx.bpm.Instance.getInstanceListByObject`

## Purpose and Scenario

Get an instance list by object. When a selected instance's task ID, name, or status must be located, prefer `instance-get-instance-log.md`; do not use an instance form to locate tasks.

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Instance.getInstanceListByObject(
    pageSize,
    pageNumber,
    orderBy,
    asc,
    objectId,
    state
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `pageSize` | Integer | Optional | Number of records returned per page (integer). |
| `pageNumber` | Integer | Optional | Page number (integer). |
| `orderBy` | String | Optional | Sort field for the instance list. |
| `asc` | Boolean | Optional | Whether to sort in ascending order; `true` for ascending, `false` for descending. |
| `objectId` | String | ✅ | The associated business record `_id` (the internal system ID, not a business number or name). When only a business number is available, first use `sharecrm data record query-by-name` to obtain its `_id`. |
| `state` | String | Optional | Status value used to filter instances, using a status supported by the current business flow. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `objectId` non-empty | Required parameter |

## Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Instance.getInstanceListByObject(
    0  // pageSize,
    0  // pageNumber,
    ""  // orderBy,
    false  // asc,
    ""  // objectId,
    ""  // state
)
```

## Operation Type

Read

## Primary Target

Business record and its associated business flow instances.

## Prerequisites

Obtain the business record `objectId`; optionally determine pagination, sorting, and status filtering. When the goal is to locate a task through a business record, first obtain and select one instance with this operation, then use `instance-get-instance-log.md` to retrieve the tasks under that instance.

## CLI Example

```bash
sharecrm bpm runtime get-instances-by-object --pageSize <page-size> --pageNumber <page-number> --objectId <object-id>
```

## Confirmation Requirements

Read-only operations require no confirmation; confirm the target when there are multiple business record candidates.


Follow the read-only boundaries in `../SKILL.md`: may be executed directly, but must not auto-escalate to writes.
## Verification

Check the returned list, pagination, and filter criteria. The list is only query evidence and cannot verify subsequent state changes; retrieve task IDs, names, and statuses through `instance-get-instance-log.md` for the selected instance.
