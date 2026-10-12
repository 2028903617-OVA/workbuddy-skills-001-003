# Query Approval Instance Progress

> **CLI**: `sharecrm approval runtime progress`
>

## Purpose and Scenario

Query the processing progress and status of the approval instance currently associated with a specified business record.

## Operation Boundaries

This is a read-only query. It is only used to locate or understand approval instances, tasks, buttons, forms, progress, rejectable targets, or retrieval conditions; it must not auto-complete, edit, reject, retrieve, withdraw, cancel, remind, transfer, add sign-off nodes, or retry based on returned results.


## Operation Type

Read

## Primary Target

Approval progress of a business record

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Only use authorized, non-sensitive identifiers.

## CLI Example

```bash
sharecrm approval runtime progress --entityId <entity-id> --dataId <data-id>
```

## Confirmation Requirements

May be executed directly; must not auto-escalate to Non-Read operations based on results.

## Verification

Check the returned data; it is only query evidence and is insufficient to confirm the final business status.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `entityId` | String | ✅ | The identifier of the business object associated with the approval, e.g., the business object API name. |
| `dataId` | String | ✅ | The business data record ID used to query approval progress. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `entityId` non-empty | Required parameter |
| `dataId` non-empty | Required parameter |
