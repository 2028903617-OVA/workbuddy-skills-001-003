# BpmGetInstanceLogs

> **CLI**: `sharecrm bpm runtime get-instance-log`
>
> **API**: `Fx.bpm.Instance.getWorkflowInstanceLog`

## Purpose and Scenario

Get the workflow instance log. This is the preferred read-only path when locating a task ID, task name, or task status by instance.

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Instance.getWorkflowInstanceLog(
    workflowInstanceId
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `workflowInstanceId` | String | ✅ | Business flow instance ID. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `workflowInstanceId` non-empty | Required parameter |

## Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Instance.getWorkflowInstanceLog(
    ""  // workflowInstanceId
)
```

## Operation Type

Read

## Primary Target

Business flow workflow instance log.

## Prerequisites

Obtain the workflow runtime instance ID. When locating a task through a business record, first obtain and select one `workflowInstanceId` with `instance-get-instances-by-object.md`, then call this operation; do not substitute an instance form or a to-do query to locate tasks under that instance.

## CLI Example

```bash
sharecrm bpm runtime get-instance-log --workflowInstanceId <workflow-instance-id>
```

## Confirmation Requirements

Read-only operations require no confirmation; confirm when the instance ID is ambiguous.


Follow the read-only boundaries in `../SKILL.md`: may be executed directly, but must not auto-escalate to writes.
## Verification

Check returned log entries and timestamps. When locating tasks, obtain the task IDs, names, and statuses under that instance from returned log entries; logs only provide obtainable evidence and do not themselves guarantee business results.
