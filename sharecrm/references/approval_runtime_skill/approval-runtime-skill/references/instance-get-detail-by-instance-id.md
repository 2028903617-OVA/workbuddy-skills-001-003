# Get Approval Instance Details

> **CLI**: `sharecrm approval runtime instance-detail`
>

## Purpose and Scenario

Query the details of a specified approval instance, including approval status, nodes, and associated business information.

## Operation Boundaries

This is a read-only query. It is only used to locate or understand approval instances, tasks, buttons, forms, progress, rejectable targets, or retrieval conditions; it must not auto-complete, edit, reject, retrieve, withdraw, cancel, remind, transfer, add sign-off nodes, or retry based on returned results.


## Operation Type

Read

## Primary Target

Approval instance

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Only use authorized, non-sensitive identifiers. If the response includes an item in `formInfoList[]` with `executionType` that can be uniquely associated with the current `taskId`, it may be reused during layout identification; do not call this command specifically to obtain `executionType`. Do not use when there are multiple candidates, no association fact, a missing field, or conflicting values; do not select by array order, node name, or task name.

## CLI Example

```bash
sharecrm approval runtime instance-detail --instanceId <instance-id>
```

## Confirmation Requirements

May be executed directly; must not auto-escalate to Non-Read operations based on results.

## Verification

Check the returned data; it is only query evidence and is insufficient to confirm the final business status.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `instanceId` | String | ✅ | The approval flow instance ID. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `instanceId` non-empty | Required parameter |
