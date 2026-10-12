# Reject Approval Task

> **CLI**: `sharecrm approval runtime reject-to-before-task`
>

## Purpose and Scenario

Reject an approval to a specified preceding task.

## Operation Boundaries and Execution Rules

Rejection changes the approval flow. First confirm `rejectToTaskId` through the rejectable tasks query and query ExtraData for the same task with `REJECT_BUTTON`; inspect current values of fields it explicitly marks required and that are currently visible and editable only when it returns `approvalForm.objectFlowLayoutExists == false` for a default layout. When any required field is missing, stop and request all field values from the user together; do not display a write preview, request secondary confirmation, guess a value, or reject. A flow layout must not be blocked, request fields, or construct data because of this required-field check. Once no required field is missing, confirm the rejection comment and any data modifications involved; do not automatically interpret "reject" as the previous task, and do not skip validation or version checks by default. Do not pass `data` or `originalData` by default; only when the user explicitly requests "reject after modifying data" must `data` contain the `_id` of the real record associated with the current task, the `version` returned verbatim from the pre-edit API response of the business record associated with the current task (neither the value nor the JSON type may change), and only the real object field API names for which the user explicitly provided new values, and `originalData` only copies the real pre-edit snapshot of the same record. Stop when fields, new values, records, version, or snapshot are unclear or `data._id` conflicts with `objectId`; guessing or manual reconstruction is prohibited. After execution, query the task or instance for verification.


Available ExtraData cannot reliably identify required fields or missing values in a flow layout, so this reference does not perform that check. This does not mean that a flow layout has no required fields.

### Layout Rule for Rejecting After Form Changes

When form data is involved, first query ExtraData for the same task with `buttonType=REJECT_BUTTON`. Pass `data` or `originalData` in this operation only when `approvalForm.objectFlowLayoutExists == false`. When `objectFlowLayoutExists == true`, first save the flow-layout rejection form with `task-edit.md` and `actionType=reject`; execute this operation only after that save succeeds, and omit `data`, `originalData`, `details`, and `originalDetails` here. This operation does not accept `actionType`; do not pass `reject`, `REJECT_BUTTON`, or another button code.

## Operation Type

Non-Read

## Primary Target

Current approval task and target preceding task

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default. You must first query `get-can-refuse-tasks`; `rejectToTaskId` must come from that result. Whether or not the user mentioned form data, query ExtraData with `REJECT_BUTTON`, check current visible, editable required fields only for a default layout, and then follow the "Layout Rule for Rejecting After Form Changes."

## CLI Example

```bash
sharecrm approval runtime reject-to-before-task --currentTaskId <current-task-id> --rejectToTaskId <reject-to-task-id-from-query> --rejectOpinion "<reason>"
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

When verifying only task or instance state, you must directly run the task query in "Lightweight State Verification" in `../SKILL.md`, then the instance query when needed, and must not call `get-task-detail` or `instance-detail`; when only confirming that the specified rejection target became the current in-progress task, query active tasks by instance and must not call `get-task-detail`. Query `get-task-detail`, `instance-detail`, or `progress` only when the user explicitly asks to verify complete rejection routing. Do not promise final business status when evidence is insufficient.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `currentTaskId` | String | ✅ | The current approval task ID. |
| `rejectToTaskId` | String | ✅ | The preceding approval task ID to reject to; must be confirmed from the rejectable tasks query result first. |
| `rejectOpinion` | String | Optional | The reason or comment filled in when rejecting the approval. |
| `moveToCurrentActivityWhenReject` | Boolean | Optional | Whether to return to the current activity node when rejecting; only pass per explicit flow rules. |
| `replyMessage` | Map | Optional | The reply message object attached when rejecting. When provided, it must contain `attachments`, and either `content` or `attachments` must be non-empty. Without attachments, pass `attachments: []`; do not omit it or pass `null`, otherwise Feed validation fails. Do not pass `feedId`; the backend fills it. When omitted, reject without a reply. |
| `ignoreNoBlockValidate` | Boolean | Optional | Whether to ignore non-blocking validation. Do not pass `true` by default; only use after explicit user confirmation. |
| `data` | String | Optional | Pass only when the user explicitly modifies data before rejection and ExtraData with `REJECT_BUTTON` confirms `objectFlowLayoutExists == false`. For a flow layout, save with `task-edit.md` first and omit this parameter here. Default-layout data must contain the real associated record `_id`, the `version` copied verbatim from the pre-edit API response of the business record associated with the current task, and the real field API names for which the user explicitly provided new values; stop when the version is missing, conflicting, or non-attributable. |
| `removeVersion` | Boolean | Optional | Whether to remove version validation information; only pass per explicit business rules. |
| `originalData` | String | Optional | Pass only for simultaneous default-layout data modification, copying the same record's real pre-edit snapshot. Omit it for a flow layout; do not manually construct it. |
| `optionInfo` | Map | Optional | Field option or form configuration object; pass a valid JSON object. |
| `entityId` | String | Optional | The identifier of the business object associated with the approval, e.g., the business object API name. |
| `objectId` | String | Optional | The ID of the business data record associated with the approval. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `currentTaskId` non-empty | Required parameter |
| `rejectToTaskId` non-empty | Required parameter |
| `replyMessage.content` or `replyMessage.attachments` non-empty | Applies only when `replyMessage` is provided; at least one must have a value |
| `replyMessage.attachments` present and non-`null` | Applies only when `replyMessage` is provided; use `[]` without attachments |
