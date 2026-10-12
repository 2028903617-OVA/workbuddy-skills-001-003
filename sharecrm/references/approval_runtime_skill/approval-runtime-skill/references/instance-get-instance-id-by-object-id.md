# Query Approval Instance ID by Business Object

> **CLI**: `sharecrm approval runtime get-approval-instance-id-by-object`
>

## Purpose and Scenario

Query the corresponding approval instance ID based on an associated business record.

## Operation Boundaries

This is a read-only query. It is only used to locate or understand approval instances, tasks, buttons, forms, progress, rejectable targets, or retrieval conditions; it must not auto-complete, edit, reject, retrieve, withdraw, cancel, remind, transfer, add sign-off nodes, or retry based on returned results.


## Operation Type

Read

## Primary Target

Current instance of a business object

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Only use authorized, non-sensitive identifiers.

Before constructing this command, bind each value by meaning. Do not infer the binding from the user-provided order, ID appearance, or similar-looking field names:

| Command parameter | Required value | Accepted source | Must never contain |
| --- | --- | --- | --- |
| `entityId` | The business object API name, for example `NewOpportunityObj` | The current object's `apiName`/`objectApiName` or a confirmed object definition | A business-record `_id`, to-do, approval-instance, or task ID |
| `objectId` | The `_id` of a record in that same business object. When the source is an approval to-do or task, use exactly that `ApprovalTaskObj.object_data_id`; its value is the associated business-record `_id` | The same `ApprovalTaskObj.object_data_id`, or the `_id` returned after uniquely querying a business record by that `entityId` | `ApprovalTaskObj._id`, `ApprovalInstanceObj._id`, task ID, instance ID, business object API name, business number, name, or title |

When only two unlabeled strings are available, or they cannot be proven to belong to the same business object, stop and request their source or perform a read-only query first. Do not retry by swapping parameters. Before execution, verify that `entityId` is the API name and `objectId` is `ApprovalTaskObj.object_data_id`, or a business-record `_id` queried by that `entityId`, rather than a task or instance `_id`; then construct this command in its real flag order: `--objectId`, followed by `--entityId`.

## CLI Example

```bash
sharecrm approval runtime get-approval-instance-id-by-object --objectId "<object-id>" --entityId "<entity-api-name>"
```

## Confirmation Requirements

May be executed directly; must not auto-escalate to Non-Read operations based on results.

## Verification

Check the returned data; it is only query evidence and is insufficient to confirm the final business status.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `objectId` | String | ✅ | The `_id` of the business record associated with the approval. In a to-do or task context, use only the value of the same `ApprovalTaskObj.object_data_id`; do not use that task's `ApprovalTaskObj._id` or any `ApprovalInstanceObj._id`. Only when `object_data_id` is absent may you use the read-only path defined by `data-read` to uniquely query a business record by `entityId` and take that business record's returned `_id`. A user-provided business number, name, or title must not be passed as `objectId`. |
| `entityId` | String | ✅ | The identifier of the business object associated with the approval, e.g., the business object API name. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `entityId` non-empty | Required parameter |
| `objectId` non-empty | Required parameter |
| Semantic binding verified | Execute only when `entityId` is the object API name and `objectId` is that object's record `_id`; they are not interchangeable |
