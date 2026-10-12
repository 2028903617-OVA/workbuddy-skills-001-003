# Update and Complete Approval Task

> **CLI**: `sharecrm approval runtime update-and-complete`
>

## Purpose and Scenario

Update business data and simultaneously complete the current approval task.

## Operation Boundaries and Execution Rules

This operation simultaneously saves the data required by the task and advances the approval. For a default layout, it is the only one-step path to edit fields and then agree, pass, complete, or reject and end the flow; rejecting to a specified preceding task does not use this operation. Use it, regardless of whether the user says "complete," "agree," or "submit," only when ExtraData for the same task queried with a confirmed `buttonType` matching the target completion operation returns `approvalForm.objectFlowLayoutExists == false`, and the completion requires complete, valid, non-empty data. Do not use this operation for a flow layout; follow the flow-layout path instead. Do not use ExtraData returned without `buttonType` to identify the layout. Before entering secondary confirmation, `data` must be complete, valid, and non-empty, and must contain the form/detail data required by trusted details and the confirmed `actionType`. Only when this update modifies the main business object must `data` contain the `_id` of the real record associated with the current task, the `version` returned verbatim from the pre-edit API response of the business record associated with the current task (neither the value nor the JSON type may change), and only the real object field API names for which the user explicitly provided new values; when the current task requires an original snapshot, the real pre-edit `originalData` of the same record must be present. When only submitting form/detail data required by the task, provide the corresponding data per trusted detail requirements; do not baselessly require the main object's `_id`, `version`, or `originalData`. Stop when `data._id` conflicts with `objectId` during main object update, or when required values/records/version/snapshot are missing or non-attributable; do not display a write preview; do not guess fields, values, or versions. This operation supports only a structured `--data` request body: put `entityId`, `objectId`, `taskId`, `actionType`, and every other request parameter in the outer JSON; the business-data field `data` must be a string produced by JSON-serializing the business-data object a second time. Do not use flat flags such as `--entityId`, `--objectId`, `--taskId`, or `--actionType`, and do not pass an unserialized business object directly as the outer `data` value. Do not use empty objects, empty strings, placeholder information, inferred defaults, full replay, version removal, or validation skipping as substitutes. When currently needed record, field structure, original/version snapshot, or ID facts are missing/conflicting, use only the narrowest trusted read-only path explicitly required by this reference; extra data does not guarantee main object facts. The server write response determines write success; use "Lightweight State Verification" only for task or instance state, and the instance active-task query only for listing in-progress tasks after completion. Read task or instance details only when the user explicitly asks to verify complete approval routing.

### ActionType Rule

`actionType` must use a lowercase value for the final approval action: agree, pass, complete, or submit uses `agree`; reject and end flow uses `reject`. `AGREE_BUTTON`, `REJECT_BUTTON`, and `COMPLETE_BUTTON` are ExtraData `buttonType` values only and cannot be used as this operation's `actionType`. Rejecting to a specified preceding task uses `task-reject-to-before-task.md`, not this operation.

## Operation Type

Non-Read

## Primary Target

Approval task and its business data

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query, and confirm that ExtraData fetched for the same task with the confirmed `buttonType` matching the target completion operation returns `approvalForm.objectFlowLayoutExists == false`. When updating the main business object, use the same record's trusted pre-edit value and original JSON type for `data.version` and `originalData`; this operation does not require or default to the `sharecrm data record get-by-id --raw` path that belongs only to `task-edit.md`. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default. Determine `actionType` from the confirmed final action: agree, pass, or complete uses `agree`; reject and end flow uses `reject`. Query `get-task-buttons` only to verify button availability; its returned button code cannot replace `actionType`.

## CLI Example

```bash
# Default layout: edit then agree, pass, or complete
sharecrm approval runtime update-and-complete --data '{"entityId":"<entity-id>","objectId":"<object-id>","taskId":"<task-id>","actionType":"agree","data":"{\"_id\":\"<record-id>\",\"version\":<version-json-literal-copied-verbatim>,\"<field-api-name>\":\"<new-value>\"}"}'

# Default layout: edit then reject and end flow
sharecrm approval runtime update-and-complete --data '{"entityId":"<entity-id>","objectId":"<object-id>","taskId":"<task-id>","actionType":"reject","data":"{\"_id\":\"<record-id>\",\"version\":<version-json-literal-copied-verbatim>,\"<field-api-name>\":\"<new-value>\"}"}'
```

The outer `--data` is the complete request body; its `data` value is the JSON-serialized business-data string. Replace `<version-json-literal-copied-verbatim>` with the complete JSON literal from the trusted pre-edit response of the same record; do not always treat it as a number. When the source value is the string `"6"`, pass `\"6\"` inside the nested `data`; when it is the number `6`, pass `6`. Do not change the value or JSON type.

## Confirmation Requirements

The internal `entityId`, `taskId`, `objectId`, `actionType` determined from the confirmed final action, `_id`, `version`, `originalData`, and CLI parameters are only for verification and execution. The final preview only states the recognizable approval/business target, field differences, comment, and completion impact; do not display the raw CLI, internal IDs, version, or original data unless the user explicitly asks. Secondary confirmation, confirmation invalidation, single execution, and retry follow the "Non-Read Secondary Confirmation" in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

When verifying only task or instance state, you must directly run the task query in "Lightweight State Verification" in `../SKILL.md`, then the instance query when needed, and must not call `get-task-detail` or `instance-detail`; when only listing current in-progress tasks after completion, query active tasks by instance and must not call `get-task-detail`. Query `get-task-detail` or `instance-detail` only when the user explicitly asks to verify complete approval routing. Do not promise final business status when evidence is insufficient.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `entityId` | String | ✅ | The identifier of the business object associated with the approval, e.g., the business object API name. |
| `objectId` | String | ✅ | The ID of the business data record associated with the approval. |
| `data` | String | ✅ | The business-data field in the outer `--data` request body, which must be a string produced by JSON-serializing the business-data object a second time. Its content must contain the complete and non-empty form/business data required by trusted details; only when updating the main business object must it contain the real associated record `_id`, the `version` copied verbatim from the pre-edit API response of the business record associated with the current task (neither the value nor the JSON type may change), and the real object field API names for which the user explicitly provided new values; stop when the version is missing, conflicting, or non-attributable. |
| `taskId` | String | ✅ | The approval task ID, used to locate the current approval task. |
| `originalData` | String | Optional | Only copies the real pre-edit snapshot of the same record, used for change validation; must not be manually constructed. |
| `optionInfo` | Map | Optional | Field option or form configuration object; pass a valid JSON object. |
| `removeVersion` | Boolean | Optional | Whether to remove version validation information; only pass per explicit business rules. |
| `actionType` | String | ✅ | Final approval action. Pass `agree` for agree, pass, complete, or submit; pass `reject` for reject and end flow. Do not pass `AGREE_BUTTON`, `REJECT_BUTTON`, `COMPLETE_BUTTON`, or another `buttonType`. |
| `opinion` | String | Optional | The approval comment text attached to the current approval operation. |
| `triggerType` | String | Optional | The trigger type used when canceling or processing the approval, provided per the current task or flow context. |
| `moveToCurrentActivityWhenReject` | Boolean | Optional | Whether to return to the current activity node when rejecting; only pass per explicit flow rules. |
| `afterTagInfo` | Map | Optional | Tag processing information after completing the approval; pass a valid JSON object. |
| `replyMessage` | Map | Optional | The reply message object attached when updating and completing the approval. When provided, it must contain `attachments`, and either `content` or `attachments` must be non-empty. Without attachments, pass `attachments: []`; do not omit it or pass `null`, otherwise Feed validation fails. Do not pass `feedId`; the backend fills it. When omitted, update and complete the approval without a reply. |
| `ignoreNoBlockValidate` | Boolean | Optional | Whether to ignore non-blocking validation. Do not pass `true` by default; only use after explicit user confirmation. |
| `blockWithLayout` | Boolean | Optional | Whether to perform blocking validation per layout; only pass per the current task rules. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `entityId` non-empty | Required parameter |
| `actionType` non-empty | Required parameter |
| `taskId` non-empty | Required parameter |
| `objectId` non-empty | Required parameter |
| `data` non-empty | Required parameter |
| `replyMessage.content` or `replyMessage.attachments` non-empty | Applies only when `replyMessage` is provided; at least one must have a value |
| `replyMessage.attachments` present and non-`null` | Applies only when `replyMessage` is provided; use `[]` without attachments |
