# Get Approval Activity Feed Details

> **CLI**: `sharecrm approval runtime get-task-detail`
>

## Purpose and Scenario

Query the details of an approval task, to-do, or approval activity feed.

## Operation Boundaries

This is a read-only query. It is only used to locate or understand approval instances, tasks, buttons, forms, progress, rejectable targets, or retrieval conditions; it must not auto-complete, edit, reject, retrieve, withdraw, cancel, remind, transfer, add sign-off nodes, or retry based on returned results.


## Operation Type

Read

## Primary Target

Approval task details

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Only use authorized, non-sensitive identifiers.

This command may return complete forms, approval activity feeds, and business data. After calling, only extract the minimal facts needed for the current purpose and discard the rest; unless the user explicitly requests to view details, do not display, restate, or use the full response as context for subsequent operations. If the response includes the current task's `executionType`, it may be reused during layout identification to map the ExtraData `buttonType`; do not construct it from another task, an activity feed, or a default, and do not call this command specifically to obtain `executionType`. It cannot replace specialized queries such as buttons, rejectable targets, or retrieval checks.

## CLI Example

```bash
sharecrm approval runtime get-task-detail --taskId <task-id>
```

## Confirmation Requirements

May be executed directly; must not auto-escalate to Non-Read operations based on results.

## Verification

Check the returned data; it is only query evidence and is insufficient to confirm the final business status.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | Optional | The approval task ID, used to locate the current approval task. |
| `todoId` | String | Optional | The to-do ID, used to locate the task or approval activity feed. |
| `workflowInstanceId` | String | Optional | The workflow instance ID, used to locate the task or approval activity feed. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| None | No required parameters |
