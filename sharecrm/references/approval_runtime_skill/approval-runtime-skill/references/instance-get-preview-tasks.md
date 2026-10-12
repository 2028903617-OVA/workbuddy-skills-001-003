# Preview Approval Tasks to Be Created

> **CLI**: `sharecrm approval runtime preview-tasks`
>

## Purpose and Scenario

Preview approval tasks that may be generated based on the approval flow and node information, used to understand subsequent handlers before an operation.

## Operation Boundaries

This is a read-only query. It is only used to locate or understand approval instances, tasks, buttons, forms, progress, rejectable targets, or retrieval conditions; it must not auto-complete, edit, reject, retrieve, withdraw, cancel, remind, transfer, add sign-off nodes, or retry based on returned results.


## Operation Type

Read

## Primary Target

Preview tasks for a flow node

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Only use authorized, non-sensitive identifiers.

## CLI Example

```bash
sharecrm approval runtime preview-tasks --workflowId <workflow-id> --activityId <activity-id> --applicantId <applicant-id> --objectId <object-id>
```

## Confirmation Requirements

May be executed directly; must not auto-escalate to Non-Read operations based on results.

## Verification

Check the returned data; it is only query evidence and is insufficient to confirm the final business status.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `workflowId` | String | ✅ | The approval flow definition ID. |
| `activityId` | String | ✅ | The activity node ID in the approval flow. |
| `applicantId` | String | Optional | The applicant user ID used when previewing tasks; determined by the flow context when not provided. |
| `objectId` | String | ✅ | The ID of the business data record associated with the approval. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `activityId` non-empty | Required parameter |
| `objectId` non-empty | Required parameter |
| `workflowId` non-empty | Required parameter |
