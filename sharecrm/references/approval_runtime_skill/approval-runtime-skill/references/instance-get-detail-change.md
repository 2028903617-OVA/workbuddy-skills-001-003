# Get Approval Instance Detail Changes

> **CLI**: `sharecrm approval runtime detail-change`
>

## Purpose and Scenario

Query the change details of specified business data in an approval instance, used to understand how data changes during the approval process.

## Operation Boundaries

This is a read-only query. It is only used to locate or understand approval instances, tasks, buttons, forms, progress, rejectable targets, or retrieval conditions; it must not auto-complete, edit, reject, retrieve, withdraw, cancel, remind, transfer, add sign-off nodes, or retry based on returned results.


## Operation Type

Read

## Primary Target

Approval instance details

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Only use authorized, non-sensitive identifiers.

## CLI Example

```bash
sharecrm approval runtime detail-change --instanceId <instance-id> --detailEntityId <detail-entity-id>
```

## Confirmation Requirements

May be executed directly; must not auto-escalate to Non-Read operations based on results.

## Verification

Check the returned data; it is only query evidence and is insufficient to confirm the final business status.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `instanceId` | String | ✅ | The approval flow instance ID. |
| `detailEntityId` | String | ✅ | The detail object identifier for which to query detail changes. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `detailEntityId` non-empty | Required parameter |
| `instanceId` non-empty | Required parameter |
