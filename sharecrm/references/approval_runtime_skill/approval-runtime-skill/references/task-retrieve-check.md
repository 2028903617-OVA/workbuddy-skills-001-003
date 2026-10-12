# Check if Approval Is Retrievable

> **CLI**: `sharecrm approval runtime retrieve-check`
>

## Purpose and Scenario

Check whether a specified approval task meets the retrieval conditions. A successful response only means the eligibility check passed; the response body may be empty and does not provide `previousTaskId`, `showDeleteOpinion`, or a retrieval target. Do not infer, construct, or select `previousTaskId` from this result.

## Operation Boundaries

This is a read-only query. It is only used to locate or understand approval instances, tasks, buttons, forms, progress, rejectable targets, or retrieval conditions; it must not auto-complete, edit, reject, retrieve, withdraw/cancel an instance, remind, transfer, add sign-off nodes, cancel, or retry based on returned results.


## Operation Type

Read

## Primary Target

Approval withdrawal eligibility

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Only use authorized, non-sensitive identifiers.

## CLI Example

```bash
sharecrm approval runtime retrieve-check --instanceId <instance-id> --currentTaskId <current-task-id>
```

## Confirmation Requirements

May be executed directly; must not auto-escalate to Non-Read operations based on results.

## Verification

Check the returned data; it is only query evidence for retrieval eligibility. A successful response is not execution authorization and is insufficient to confirm the final business status. Obtain `previousTaskId` separately through `task-get-task-extra-data.md` for the same `instanceId` and `currentTaskId` with `buttonType=RETRIEVE_BUTTON`.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `instanceId` | String | ✅ | The approval flow instance ID. |
| `currentTaskId` | String | ✅ | The current approval task ID. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `currentTaskId` non-empty | Required parameter |
| `instanceId` non-empty | Required parameter |
