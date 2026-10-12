# Edit Approval Task Form

> **CLI**: `sharecrm approval runtime edit`
>
> **Action API**: `ApprovalTaskFormEdit`
>

## Purpose and Scenario

Edit approval task form data in a flow layout, without completing the approval task. Default-layout editing must use `ApprovalTaskDefaultFormEdit` through `task-update-approval-content.md`.

## Operation Boundaries and Execution Rules

This operation only saves a flow-layout form or associated business data and does not itself complete the task. Do not use it for default-layout editing; a default layout must use `ApprovalTaskDefaultFormEdit`. When the user requests approval-task completion and ExtraData for the same task returns `approvalForm.objectFlowLayoutExists == true`, this operation is the first step of the fixed "save, then complete" sequence; the complete sequence must be stated in one final preview and covered by a subsequent explicit confirmation, and `task-complete.md` may execute only after this operation succeeds, otherwise stop. Outside that sequence, do not split it into an unconfirmed "save first, then complete" two-step operation. The string content of `objectData`, `details`, `originalData`, and `originalDetails` must be valid JSON. When editing the main business object, `objectData` contains only the `_id` copied from the real record associated with the current task and the real object field API names for which the user explicitly provided new values; do not fabricate, infer, or include unmodified fields. Do not pass a full-record snapshot in `originalData` by default. Only when the current task, form contract, or object service requires original data, pass the smallest trusted original subset from the same record: `_id`, the `version` copied verbatim from the pre-edit response when available (neither the value nor the JSON type may change), and the pre-edit values of the fields being changed. When the server explicitly requires other original fields, follow that contract; do not guess, fabricate, pass unmodified fields, or use an empty object as a bypass. `details` and `originalDetails` are only real detail data and must not mix in main object fields. When record, version, field structure, or original values are missing/conflicting, use only the narrowest trusted read-only path explicitly required by this reference; extra data does not guarantee these facts. Do not fabricate or bypass with `notValidate=true`.


### Rejection Form Priority Rule

When this flow-layout edit prepares a subsequent rejection, use `REJECT_BUTTON` for ExtraData and pass `actionType=reject`. For reject and end flow, run `task-complete.md` with `actionType=reject` only after this save succeeds. For reject to a specified preceding task, run `task-reject-to-before-task.md` only after this save succeeds and omit form data from that second operation. This rule takes precedence over the `AGREE_BUTTON` / `COMPLETE_BUTTON` `editForm` mapping, which only applies to the agree/complete side.

## Operation Type

Non-Read

## Primary Target

Approval task form data in a flow layout

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. When the current operation context already contains a trusted, explicit `buttonType` for the same `taskId`, `instanceId`, and edit action, use it verbatim; do not derive, override, or query it again. Only when no trusted `buttonType` exists, reuse `executionType` only when a trusted value already exists in the current context; do not read task details to obtain it. Use `COMPLETE_BUTTON` only when it explicitly equals `update`; for every other value, including a missing value, use `AGREE_BUTTON` directly. Missing `executionType` is not a blocker and must not trigger another query. Stop when no trusted `buttonType` is provided and the action has no confirmed mapping; do not guess. If a valid ExtraData for the same task with that mapped `buttonType` has already returned `approvalForm.objectFlowLayoutExists == true`, reuse that result directly to select this reference; do not re-read task details, re-derive `executionType`, or call ExtraData again; do not select a flow layout solely because the user said "edit", from the task name, or from `get-task-detail`, and do not use the Unknown fallback to identify the layout. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default. Determine this edit's required `actionType` from the confirmed final action: agree, pass, or complete uses `agree`; rejection uses `reject`. `get-task-buttons` only verifies button availability and cannot supply an `actionType` value.

When the current task, form contract, or object service requires `originalData` and requires its `version` or the pre-edit values of changed fields, you must run `sharecrm data record get-by-id --objectApiName <object-api-name> --recordId <record-id> --raw`. `--raw` is required: the default response does not return `version`; `get-task-extra-data` and `object-data-query` are not valid sources of `version` either. Copy only the required `_id`, `version`, and pre-edit values of changed fields from the raw response; do not change the JSON type of `version`. For example, keep a string value `"6"` as `"6"` and a number `6` as `6`. When it is not required, omit `originalData`; do not construct a full snapshot or an empty object for it.

For a final rejection, determine `actionType` from the confirmed final action, not from a button code: use `reject`. The `AGREE_BUTTON` / `COMPLETE_BUTTON` mapping in this reference is only for the agree/complete side. `get-task-buttons` may verify button availability but cannot supply an `actionType` value.

## CLI Example

Only when `originalData` is required, read the record's `_id`, `version`, and pre-edit values of changed fields:

```bash
sharecrm data record get-by-id --objectApiName <object-api-name> --recordId <record-id> --raw
```

Then construct the edit command:

```bash
# Edit then agree, pass, or complete
sharecrm approval runtime edit --taskId <task-id> --objectData '{"_id":"<task-linked-record-id>","<actual-object-field-api-name>":"<explicit-user-provided-new-value>"}' --originalData '{"_id":"<task-linked-record-id>","version":<version-json-literal-copied-from-raw-response>,"<actual-object-field-api-name>":"<pre-edit-value-copied-from-raw-response>"}' --actionType agree

# Edit then reject
sharecrm approval runtime edit --taskId <task-id> --objectData '{"_id":"<task-linked-record-id>","<actual-object-field-api-name>":"<explicit-user-provided-new-value>"}' --originalData '{"_id":"<task-linked-record-id>","version":<version-json-literal-copied-from-raw-response>,"<actual-object-field-api-name>":"<pre-edit-value-copied-from-raw-response>"}' --actionType reject
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

Check the write response; report that the save succeeded only when `success == true && code == 'OK'`. `get-task-extra-data` with matching `buttonType` is only for pre-write layout and task-fact confirmation and must not be queried again as default post-write verification. Do not call `get-task-detail` for ordinary edit verification; execute it as an independent read only when the user explicitly asks to view the edited task details, form, or approval activity feed.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | The approval task ID, used to locate the current approval task. |
| `details` | String | Optional | The detail data JSON string in the approval form. |
| `objectData` | String | Optional | When editing the main object, contains the real associated record `_id` and the real field API names with new values explicitly provided by the user; do not pass unmodified fields. |
| `originalData` | String | Optional | Do not pass a full snapshot by default. Only when the current task, form contract, or object service requires it, pass the smallest trusted original subset: `_id`, the verbatim `version` when available, and pre-edit values of changed fields; follow the server contract if it explicitly requires other fields. |
| `originalDetails` | String | Optional | The original detail data JSON string before editing, used for change validation. |
| `optionInfo` | Map | Optional | Field option or form configuration object; pass a valid JSON object. |
| `actionType` | String | Optional | Pass only when this form save must bind a subsequent approval action. Use `agree` for edit then agree, pass, or complete; use `reject` for edit then reject. Do not pass `AGREE_BUTTON`, `REJECT_BUTTON`, `COMPLETE_BUTTON`, or another `buttonType`. |
| `notValidate` | Boolean | Optional | Whether to skip validation. Do not pass `true` by default; only use after explicit user confirmation. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |
