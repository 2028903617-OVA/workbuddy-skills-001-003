# BpmGetTaskListByLane

> **CLI**: `sharecrm bpm runtime get-task-info-by-lane-id`
>
> **API**: `Fx.bpm.Task.getTaskInfoByLaneId`

## Purpose and Scenario

Get task information by lane ID

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.getTaskInfoByLaneId(
    laneId,
    workflowId,
    instanceId,
    objectId,
    entityId,
    notGetDatas,
    applyButtons,
    page,
    pageSize
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `laneId` | String | ✅ | Business flow lane ID. |
| `workflowId` | String | ✅ | Business flow definition ID. |
| `instanceId` | String | ✅ | Business flow instance ID. |
| `objectId` | String | Optional | Associated business data record ID. |
| `entityId` | String | Optional | API name of the associated business object. |
| `notGetDatas` | Boolean | Optional | Whether to not return business data, descriptions, and form info when querying tasks by lane. |
| `applyButtons` | Boolean | Optional | Whether to also return available operation buttons when querying tasks. |
| `page` | Integer | Optional | Page number when querying tasks by lane (integer). |
| `pageSize` | Integer | Optional | Number of records returned per page (integer). |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `laneId` non-empty | Required parameter |
| `workflowId` non-empty | Required parameter |
| `instanceId` non-empty | Required parameter |

> `laneId`, `workflowId`, and `instanceId` must come from the same business flow context; do not use a task ID as a lane ID.

## Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.getTaskInfoByLaneId(
    ""  // laneId,
    ""  // workflowId,
    ""  // instanceId,
    ""  // objectId,
    ""  // entityId,
    false  // notGetDatas,
    false  // applyButtons,
    0  // page,
    0  // pageSize
)
```

## Operation Type

Read

## Primary Target

Tasks within the business flow lane and its workflow instance context.

## Prerequisites

Obtain matching `laneId`, `workflowId`, and `instanceId`; optional business record and entity IDs must come from the same context.

## CLI Example

```bash
sharecrm bpm runtime get-task-info-by-lane-id --laneId <lane-id> --workflowId <workflow-id> --instanceId <instance-id>
```

## Confirmation Requirements

Read-only operations require no confirmation; confirm when the lane, workflow, and instance relationship is ambiguous.


Follow the read-only boundaries in `../SKILL.md`: may be executed directly, but must not auto-escalate to writes.
## Verification

Check returned tasks, pagination, and optional button data. This query cannot prove that any action or state transition has been completed.