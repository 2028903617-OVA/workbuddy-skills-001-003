# Update Approval Content

> **CLI**: `sharecrm approval runtime update-approval-content`
>
> **Action API**: `ApprovalTaskDefaultFormEdit`
>

## Purpose and Scenario

Update approval task form data in a default layout, without automatically completing the task. Flow-layout editing must use `ApprovalTaskFormEdit` through `task-edit.md`.

## Operation Boundaries and Execution Rules

This operation only updates business data or an approval form in a default layout and does not complete the task. Do not use it for flow-layout editing; a flow layout must use `ApprovalTaskFormEdit`. `data` must contain complete, valid, and non-empty trusted task-required content. Only when this update modifies the main business object must `data` contain the `_id` of the real record associated with the current task, the `version` returned verbatim from the pre-edit API response of the business record associated with the current task (neither the value nor the JSON type may change), and only the real object field API names for which the user explicitly provided new values; stop when `data._id` conflicts with `objectId`, the version is missing or non-attributable, and `originalData` only copies the real pre-edit snapshot of the same record and cannot be manually reconstructed. When only submitting approval form/detail data, provide the corresponding content per trusted detail requirements; do not baselessly require the main object's `_id`, `version`, or `originalData`. `optionInfo` must follow the JSON structure of the current form. This action supports only the structured `--data` request body. Do not use flat flags such as `--entityId`, `--objectId`, or `--taskId`; they cause `INVALID_ARGUMENT`. Display field-level changes and confirm first; do not use empty data, default version removal, or validation skipping; when currently needed record, field structure, original/version snapshot, or ID facts are missing/conflicting, use only the narrowest trusted read-only path explicitly required by this reference; extra data does not guarantee main object facts. The server write response determines write success; task details are an independent read only when the user explicitly asks to view the edited form or approval activity feed.


## Operation Type

Non-Read

> This operation does not accept `actionType`. `AGREE_BUTTON` or `COMPLETE_BUTTON` is only used before the write to obtain ExtraData and identify the layout; it is not an API parameter of this operation. Do not treat this operation as the final rejection; choose `task-reject-to-before-task.md` or `task-update-and-complete.md` according to whether a rejection target is specified.

## Primary Target

Approval task form data in a default layout

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. When the current operation context already contains a trusted, explicit `buttonType` for the same `taskId`, `instanceId`, and edit action, use it verbatim; do not derive, override, or query it again. Only when no trusted `buttonType` exists, reuse `executionType` only when a trusted value already exists in the current context; do not read task details to obtain it. Use `COMPLETE_BUTTON` only when it explicitly equals `update`; for every other value, including a missing value, use `AGREE_BUTTON` directly. Missing `executionType` is not a blocker and must not trigger another query. Stop when no trusted `buttonType` is provided and the action has no confirmed mapping; do not guess. If a valid ExtraData for the same task with that mapped `buttonType` has already returned `approvalForm.objectFlowLayoutExists == false`, reuse that result directly to select this reference; do not re-read task details, re-derive `executionType`, or call ExtraData again; do not select a default layout solely because the user said "edit", from the task name, or from `get-task-detail`, and do not use the Unknown fallback to identify the layout. When updating the main business object and the contract requires `version` or `originalData`, reuse only a trusted pre-edit snapshot attributable to the same record from the already-read task/instance details; do not apply the `get-by-id --raw` path that is specific to `task-edit.md`; stop when the snapshot is missing or conflicting. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default.

## CLI Example

```bash
sharecrm approval runtime update-approval-content --data '{"entityId":"<entity-id>","objectId":"<object-id>","taskId":"<task-id>","data":"{\"_id\":\"<task-linked-record-id>\",\"version\":<version-json-literal-copied-from-linked-record-pre-edit-response>,\"<actual-object-field-api-name>\":\"<explicit-user-provided-new-value>\"}","originalData":"<real-pre-edit-snapshot-json>"}'
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

Check the write response; report that the save succeeded only when `success == true && code == 'OK'`. `get-task-extra-data` with matching `buttonType` is only for pre-write layout and task-fact confirmation and must not be queried again as default post-write verification. Do not call `get-task-detail` for ordinary edit verification; execute it as an independent read only when the user explicitly asks to view the edited task details, form, or approval activity feed. A trusted pre-edit snapshot already read and attributable to the same record may still be reused under this reference's prerequisites, but this verification rule must not cause a snapshot to be fabricated or read additionally.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `entityId` | String | ✅ | The identifier of the business object associated with the approval, e.g., the business object API name. |
| `objectId` | String | ✅ | The ID of the business data record associated with the approval. |
| `data` | String | ✅ | Must contain complete, valid, and non-empty trusted task-required content; only when updating the main business object must it contain the real associated record `_id`, the `version` copied verbatim from the pre-edit API response of the business record associated with the current task (neither the value nor the JSON type may change), and the real object field API names for which the user explicitly provided new values; stop when the version is missing, conflicting, or non-attributable. |
| `taskId` | String | ✅ | The approval task ID, used to locate the current approval task. |
| `originalData` | String | Optional | Only copies the real pre-edit snapshot of the same record, used for change validation; must not be manually constructed. |
| `optionInfo` | Map | Optional | Field option or form configuration object; pass a valid JSON object. |
| `removeVersion` | Boolean | Optional | Whether to remove version validation information; only pass per explicit business rules. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `entityId` non-empty | Required parameter |
| `objectId` non-empty | Required parameter |
| `taskId` non-empty | Required parameter |
| `data` non-empty | Required parameter |
