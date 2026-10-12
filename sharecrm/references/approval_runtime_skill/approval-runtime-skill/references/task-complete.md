# Complete Approval Task

> **CLI**: `sharecrm approval runtime complete`
>

## Purpose and Scenario

Complete the current approval task, advancing the approval using a backend-supported action type.

## Operation Boundaries and Execution Rules

Completion advances the approval status. This reference is for direct agree, task completion, or reject-and-end-flow when the current operation does not need to save approval-form or business data, and for the second completion step after a flow layout has successfully saved the required form/business data. Before direct completion, query ExtraData for the same task with the `buttonType` matching the final action. Inspect current values of fields explicitly marked required and currently visible and editable only when `approvalForm.objectFlowLayoutExists == false`. When any such default-layout field is missing, stop and request all field values from the user together; do not display a write preview, request secondary confirmation, guess a value, or call this operation. A flow layout must not be blocked, request fields, or construct data because of this required-field check. Agree, pass, complete, or reject may finish directly only when a default layout has no unfilled required field, or a flow layout is confirmed and the current operation does not save data. When completion must save form or business data, route from the layout identified by the same ExtraData: when `approvalForm.objectFlowLayoutExists == true`, first run `task-edit.md` and run this operation only after it succeeds; when it is `== false`, use `task-update-and-complete.md`. Do not use ExtraData returned without `buttonType` to identify the layout or required fields. `actionType` only represents the approval action; comments cannot replace task-required data; do not pass empty/omitted business data or use risk switches to bypass requirements. Reuse the currently confirmed `taskId`, `objectId`, `actionType`, and form facts; determine `actionType` from the confirmed final action, not from a button code. `ignoreNoBlockValidate` must not be `true` by default. The server write response determines write success; use "Lightweight State Verification" only for task or instance state, and the instance active-task query only for listing in-progress tasks after completion. Read task or instance details only when the user explicitly asks to verify complete approval routing.



Available ExtraData cannot reliably identify required fields or missing values in a flow layout, so this reference does not perform that check. This does not mean that a flow layout has no required fields.

### ActionType Rule

For every use of this reference, `actionType` is the final approval action: agree, pass, or complete uses `agree`; reject and end flow uses `reject`. `get-task-buttons` verifies availability only; never use a returned `AGREE_BUTTON`, `REJECT_BUTTON`, or `COMPLETE_BUTTON` as `actionType`.

## Operation Type

Non-Read

## Primary Target

Current approval task

## Prerequisites

Confirm the required IDs and final approval action from a trusted current context or an appropriate read-only query. Whether or not the user supplied field data, before direct completion query ExtraData for the same task with matching `buttonType`. Inspect current values of fields explicitly marked required and currently visible and editable only when `approvalForm.objectFlowLayoutExists == false`; request missing values from the user only in that case. When `objectFlowLayoutExists == true`, do not block or request fields because of this check. Require the same task's flow-layout marker from ExtraData and a successful result of `task-edit.md` only when this completion must first save flow-layout form or business data; when it is unknown whether the current task requires a data save, do not assume direct completion. Determine `actionType` from the confirmed final action: agree, pass, or complete uses `agree`; reject and end flow uses `reject`. `get-task-buttons` only verifies availability and cannot supply an `actionType` value. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default.

## CLI Example

```bash
# No form or business data save: direct agree, pass, or complete
sharecrm approval runtime complete --objectId <object-id> --actionType agree --taskId <task-id> --opinion "<opinion>"

# No form or business data save: direct reject and end flow
sharecrm approval runtime complete --objectId <object-id> --actionType reject --taskId <task-id> --opinion "<opinion>"

# Flow layout after the required data was saved: agree, pass, or complete
sharecrm approval runtime complete --objectId <object-id> --actionType agree --taskId <task-id> --opinion "<opinion>"

# Flow layout after the required data was saved: reject and end flow
sharecrm approval runtime complete --objectId <object-id> --actionType reject --taskId <task-id> --opinion "<opinion>"
```

## Confirmation Requirements

The internal `taskId`, `objectId`, `actionType` determined from the confirmed final action, and CLI parameters are only for verification and execution. The final preview only states the recognizable approval/business target, approval action, comment, and impact of advancing the approval status; do not display the raw CLI, internal IDs, or raw JSON unless the user explicitly asks. Secondary confirmation, confirmation invalidation, single execution, and retry follow the "Non-Read Secondary Confirmation" in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

When verifying only task or instance state, you must directly run the task query in "Lightweight State Verification" in `../SKILL.md`, then the instance query when needed, and must not call `get-task-detail` or `instance-detail`; when only listing current in-progress tasks after completion, query active tasks by instance and must not call `get-task-detail`. Query `get-task-detail` or `instance-detail` only when the user explicitly asks to verify complete approval routing. Do not promise final business status when evidence is insufficient.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `objectId` | String | ✅ | The ID of the business data record associated with the approval. |
| `actionType` | String | ✅ | Final approval action. Pass `agree` for agree, pass, or complete; pass `reject` for reject and end flow. Do not pass `AGREE_BUTTON`, `REJECT_BUTTON`, `COMPLETE_BUTTON`, or another `buttonType`. |
| `taskId` | String | ✅ | The approval task ID, used to locate the current approval task. |
| `opinion` | String | Optional | The approval comment text attached to the current approval operation. |
| `triggerType` | String | Optional | The trigger type used when canceling or processing the approval, provided per the current task or flow context. |
| `entityId` | String | Optional | The identifier of the business object associated with the approval, e.g., the business object API name. |
| `moveToCurrentActivityWhenReject` | Boolean | Optional | Whether to return to the current activity node when rejecting; only pass per explicit flow rules. |
| `afterTagInfo` | Map | Optional | Tag processing information after completing the approval; pass a valid JSON object. |
| `replyMessage` | Map | Optional | The reply message object attached when completing the approval. When provided, it must contain `attachments`, and either `content` or `attachments` must be non-empty. Without attachments, pass `attachments: []`; do not omit it or pass `null`, otherwise Feed validation fails. Do not pass `feedId`; the backend fills it. When omitted, complete the approval without a reply. |
| `ignoreNoBlockValidate` | Boolean | Optional | Whether to ignore non-blocking validation. Do not pass `true` by default; only use after explicit user confirmation. |
| `blockWithLayout` | Boolean | Optional | Whether to perform blocking validation per layout; only pass per the current task rules. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `actionType` non-empty | Required parameter |
| `objectId` non-empty | Required parameter |
| `taskId` non-empty | Required parameter |
| `replyMessage.content` or `replyMessage.attachments` non-empty | Applies only when `replyMessage` is provided; at least one must have a value |
| `replyMessage.attachments` present and non-`null` | Applies only when `replyMessage` is provided; use `[]` without attachments |
