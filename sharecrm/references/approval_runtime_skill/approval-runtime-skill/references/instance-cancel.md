# Withdraw or Cancel Approval Instance

> **CLI**: `sharecrm approval runtime cancel`
>

## Purpose and Scenario

Withdraw or cancel a specified approval instance, terminating the subsequent uncompleted approval processing for that instance.

## Operation Boundaries and Execution Rules

Withdrawal or cancellation terminates the subsequent uncompleted processing of the approval instance. First confirm the unique approval instance, `triggerType`, and the user-provided cancellation reason; do not auto-escalate "query status" or "can it be canceled" into cancellation. This is not retrieval for reconsideration; do not call `retrieve-check` or `retrieve`. After execution, query the instance status for verification; do not pass `ignoreNoBlockValidate=true` by default.


## Operation Type

Non-Read

## Primary Target

Approval instance

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default.

First bind one unique `instanceId`: use an `instanceId` already confirmed in trusted context, or provide both `entityId` and `objectId`, query `instance-get-instance-id-by-object-id.md`, and obtain the `instanceId` from its unique result. `entityId` must not be used alone to cancel, and neither must `objectId`. The final cancel command must include the bound `instanceId`; do not rely on implicit resolution.

When `instanceId` is provided together with `entityId` and `objectId`, first query the instance for that business object and confirm that the result exactly matches `instanceId`. Stop when they differ, when multiple instances are returned, or when no instance is returned; do not select either ID arbitrarily for cancellation.

## CLI Example

When the instance ID is already confirmed:

```bash
sharecrm approval runtime cancel --triggerType <trigger-type> --cancelReason "<reason>" --instanceId <instance-id>
```

When only the business object and its record are provided, first locate one unique instance, then cancel it:

```bash
sharecrm approval runtime get-approval-instance-id-by-object --objectId <object-id> --entityId <entity-api-name>
sharecrm approval runtime cancel --triggerType <trigger-type> --cancelReason "<reason>" --instanceId <instance-id-from-unique-query-result>
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

When verifying only the instance state after cancellation, you must directly run the instance query in "Lightweight State Verification" in `../SKILL.md` and must not call `instance-detail` or `progress`; query `instance-detail` or `progress` only when the complete post-cancellation approval route or progress must be verified. Do not promise final business status when evidence is insufficient.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `entityId` | String | Conditionally required | The identifier of the business object associated with the approval, e.g., the business object API name. Use it only to locate the instance by business object or validate consistency with `instanceId`; it must be provided together with `objectId`. |
| `objectId` | String | Conditionally required | The `_id` of the business record associated with the approval. In a to-do or task context, use only the value of the same `ApprovalTaskObj.object_data_id`; do not use that task's `ApprovalTaskObj._id` or any `ApprovalInstanceObj._id`. Only when `object_data_id` is absent may you use the read-only path defined by `data-read` to uniquely query a business record by `entityId` and take that business record's returned `_id`. A user-provided business number, name, or title must not be passed as `objectId`. Use it only to locate the instance by business object or validate consistency with `instanceId`; it must be provided together with `entityId`. |
| `triggerType` | String | ✅ | The trigger type used when canceling or processing the approval, provided per the current task or flow context. |
| `cancelReason` | String | ✅ | The reason for canceling the approval instance, explicitly provided by the user. |
| `instanceId` | String | ✅ | The approval flow instance ID directly confirmed or bound from a unique business-object query result; the final cancel command must include it. |
| `ignoreNoBlockValidate` | Boolean | Optional | Whether to ignore non-blocking validation. Do not pass `true` by default; only use after explicit user confirmation. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `cancelReason` non-empty | Required parameter |
| `triggerType` non-empty | Required parameter |
| `instanceId` non-empty | Required by the final cancel command; query and bind one unique instance ID when only a business object is provided |
| `entityId` and `objectId` are paired | Both are required when locating or validating an instance by business object |
| Dual-location results match | When both `instanceId` and business-object identifiers are provided, the query result must equal `instanceId` |
