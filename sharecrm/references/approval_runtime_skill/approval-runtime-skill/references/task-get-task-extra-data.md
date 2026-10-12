# Get Approval Task Extra Data

> **CLI**: `sharecrm approval runtime get-task-extra-data`
>

## Purpose and Scenario

Query the supplementary data required to execute a specified button operation for an approval task. It selects the corresponding handler by `buttonType`. Before editing an approval form or agreeing, passing, completing, or rejecting an approval task, also use it to read `approvalForm.objectFlowLayoutExists` for layout identification. Check missing current visible, editable required fields only in a default layout; do not do so in a flow layout. Pass the `buttonType` matching the target operation when reading `approvalForm`.

## Operation Boundaries

This is a read-only query. It is only used to locate or understand approval instances, tasks, buttons, forms, progress, rejectable targets, retrieval conditions, or the layout before editing/completing; it must not auto-complete, edit, reject, retrieve, withdraw, cancel, remind, transfer, add sign-off nodes, or retry based on returned results. When the matching `buttonType` result contains `approvalForm`, check missing values from its explicit required markers, current field visibility/editability, and current data only in a default layout where `approvalForm.objectFlowLayoutExists == false`. A flow layout must not be blocked, request fields, or construct data because of this check. Do not require hidden, non-editable, or non-required fields. When a default-layout value is missing, stop and request all missing field values from the user together; do not bypass this with a default, empty value, or risk parameter. When `buttonType` is omitted or does not match, the backend uses the `Unknown` fallback handler: it normally returns only `triggerType`, `unCompletedPersons`, and `candidateIds`; only when `executionType == OPERATION_MULTI` may it additionally return an `approvalForm` containing only `data`. This fallback does not provide the complete form/layout/field editing permissions, opinion configuration, layout rules, `feedId`, `previousOpinion`, or button-specific personnel information. Do not use it to determine the layout, required fields, whether an opinion is required, or whether a form is editable. To identify the layout, pass a confirmed matching `buttonType`; only `approvalForm.objectFlowLayoutExists == true` means flow layout and only `== false` means default layout; stop when the field is missing, non-boolean, or conflicting, and do not guess.


Available ExtraData cannot reliably identify required fields or missing values in a flow layout, so this reference does not perform that check. This does not mean that a flow layout has no required fields.

## Operation Type

Read

## Primary Target

Approval task extra data

## Prerequisites

Confirm the required IDs and the unique target operation from a trusted current context or an appropriate read-only query. When the current operation context already contains a trusted, explicit `buttonType` for the same `taskId`, `instanceId`, and target action, use it verbatim; do not derive, override, or query it again. Only when no trusted `buttonType` exists, determine it from confirmed action rules: for form editing, reuse `executionType` only when a trusted value already exists in the current context; do not read task details to obtain it. Use `COMPLETE_BUTTON` only when it explicitly equals `update`; for every other value, including a missing value, use `AGREE_BUTTON` directly. Missing `executionType` is not a blocker and must not trigger another query; immediately execute this operation once after determining the value, and do not use other read results to re-evaluate or change it. Use the corresponding fixed value in the table below for another confirmed action. When no trusted `buttonType` is provided and the action has no confirmed mapping, do not guess. When only basic trigger or candidate information is needed, `buttonType` may be omitted and only basic results may be used; when `approvalForm`, layout, field editing permissions, opinion configuration, layout rules, or button-specific data is required, stop and report that a confirmable `buttonType` is missing, and do not use an unmatched fallback result to identify the layout. Query `task-get-task-buttons.md` only when the final executable button or write `actionType` must be verified; do not infer it from user wording.

The fixed action mappings below may only be used once the action itself has been uniquely identified; they do not replace actual button verification:

| Action | `buttonType` |
| --- | --- |
| `Reject` | `REJECT_BUTTON` |
| `Agree` | `AGREE_BUTTON` |
| `CompleteTask` | `COMPLETE_BUTTON` |
| `ChangeApprover` | `CHANGE_HANDLER_BUTTON` |
| `AddExtraNode` | `ADD_EXTRA_NODE_BUTTON` |
| `editForm` with `executionType === 'update'` | `COMPLETE_BUTTON` |
| `editForm` with `executionType !== 'update'` (including missing) | `AGREE_BUTTON` |
| `Retrieve` | `RETRIEVE_BUTTON` |
| Carbon copy | `CARBON_BUTTON` |

`buttonType` selects the ExtraData handler and form context only; it does not determine write `actionType`. Agree, pass, and complete writes use `actionType=agree`; rejection writes use `actionType=reject`. `AGREE_BUTTON`, `REJECT_BUTTON`, and `COMPLETE_BUTTON` must not be used as write `actionType`; in particular, completion with `COMPLETE_BUTTON` still uses `agree`.

## Query Modes

| Required information | `buttonType` rule | Usable result |
| --- | --- | --- |
| Basic trigger or candidate information | May be omitted; accept the `Unknown` fallback | `triggerType`, `unCompletedPersons`, `candidateIds`; for `OPERATION_MULTI`, at most an `approvalForm` containing only `data` |
| Form, layout, field editing permissions, current visible editable required fields, opinion configuration, or layout rules | Must pass a confirmed matching value | Only use that handler's returned `approvalForm`, `opinionRequired`, `enableLayoutRules`, and related fields; request values only when a default-layout required field is missing |
| Button-specific data for activity feeds, withdrawal, handler changes, sign-off nodes, carbon copy, reminders, or replies | Must pass the corresponding handler value | Only use that handler's specific fields, such as `feedId`, `previousTaskId`, candidate IDs, or pending-person information |

One valid ExtraData response for the same `taskId`, `instanceId`, and matching `buttonType` completes layout identification. The subsequently selected reference must reuse its `approvalForm.objectFlowLayoutExists`; do not re-read task details, re-derive `executionType`, or call this operation again.

Retrieval for reconsideration must pass `buttonType=RETRIEVE_BUTTON`. Use `previousTaskId` as the retrieval target only when the response for the same `instanceId` and `taskId` contains a non-empty value; `showDeleteOpinion` only indicates whether the user may be asked about deleting the previous opinion. Do not infer the retrieval target from `retrieve-check`, any completed task in the instance, task name, array order, or creation time. Stop and do not retrieve when `previousTaskId` is missing, conflicting, or ExtraData is absent.

## CLI Example

```bash
sharecrm approval runtime get-task-extra-data --instanceId <instance-id> --taskId <task-id> --buttonType <button-type>
```

## Confirmation Requirements

May be executed directly; must not auto-escalate to Non-Read operations based on results.

## Verification

Check the returned data; it is only query evidence and is insufficient to confirm the final business status.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `instanceId` | String | ✅ | The approval flow instance ID. |
| `taskId` | String | ✅ | The approval task ID, used to locate the current approval task. |
| `buttonType` | String | Conditionally required | ExtraData handler selector. Optional when only `triggerType`, `unCompletedPersons`, `candidateIds`, or other basic information is needed; omitting it causes the backend to use the Unknown fallback handler. Required when `approvalForm`, layout identification, field editing permissions, opinion configuration, layout rules, or button-specific data is needed, and must match the uniquely identified target operation. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |
| `instanceId` non-empty | Required parameter |
