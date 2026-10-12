# Get Rejectable Approval Tasks

> **CLI**: `sharecrm approval runtime get-can-refuse-tasks`
>

## Purpose and Scenario

Query the tasks to which the current approval task can be rejected, used to select a clear target before rejection.

## Operation Boundaries

This is a read-only query. It is only used to locate or understand approval instances, tasks, buttons, forms, progress, rejectable targets, or retrieval conditions; it must not auto-complete, edit, reject, retrieve, withdraw, cancel, remind, transfer, add sign-off nodes, or retry based on returned results.


## Operation Type

Read

## Primary Target

Rejectable targets for the current task

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Only use authorized, non-sensitive identifiers.

## CLI Example

```bash
sharecrm approval runtime get-can-refuse-tasks --instanceId <instance-id> --taskId <task-id>
```

## Confirmation Requirements

May be executed directly; must not auto-escalate to Non-Read operations based on results.

## Verification

Check the returned data; it is only query evidence and is insufficient to confirm the final business status.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `instanceId` | String | ✅ | The approval flow instance ID. |
| `taskId` | String | Optional | The approval task ID, used to locate the current approval task. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `instanceId` non-empty | Required parameter |
