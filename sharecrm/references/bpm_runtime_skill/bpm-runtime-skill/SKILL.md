---
name: "bpm-runtime-skill"
description: "Used to query or process existing business flow instances and business flow tasks. Use when the user mentions business flow to-dos, completion, submit after filling, editing task data, batch-creating related objects, executing a specified operation, changing or recalculating handlers, reminding, triggering, canceling, retrying, task details, buttons, lanes, instance forms or logs."
apiName: "bpm_runtime_skill"
---
# Business Flow Runtime

## Goal

Enable the Agent to query or process existing business-flow runtime targets accurately and verifiably: uniquely match the operation and reference, obtain only the minimum trusted facts required by that operation, then report the real result. Sending a command is not success; confirm a write only when `success == true && code == 'OK'`. A query must not escalate into a write.

## What I Need From You

- **Operation and target**: Provide a clear query or processing intent and a target that can be reliably bound by `taskId`, `workflowInstanceId`, `workflowDefinitionId`, `laneId`, `entityId + objectId`, a task selected in the current session, or information that can uniquely locate the target through an allowed read-only path.
- **Operation-specific facts**: Provide the new field values, handlers, opinion, operation `type`, instance-form type, retry scope, or other data required by the selected reference. Personnel values must be real user IDs; a business number, name, or title is not a record `_id`.
- **When information is missing**: First perform the narrowest read-only query allowed by the current reference. When the target cannot be uniquely bound, required data is missing, or results conflict, stop and state the gap; do not guess or fill values. A write operation needs an explicit affirmative in a subsequent message after its complete business preview.

## When to Use

- Use for existing business-flow task, instance, button, lane, instance-form, or log queries; and for completing, editing and completing, batch-creating related objects and completing the task, executing a confirmed operation, changing handlers, recalculating handlers, reminding, triggering, canceling, or retrying an existing business flow.
- Use when a user supplies a task, instance, or workflow-definition ID, or a business object and record, and asks to query or process its related business-flow runtime target.
- Do not use for creating, editing, publishing, enabling, disabling, or deleting business-flow definitions, nodes, lanes, or other configuration; or for ordinary CRM-record reads or field changes unrelated to business-flow runtime.

## Scope

Only handles existing business flow instances, tasks, and their runtime data; does not handle business flow definitions, nodes, lane configuration, publishing, start/stop, or configuration deletion.

This Skill can only handle explicitly identified tasks, instances, lanes, or business objects; it must not disguise detail, instance list, or lane queries as to-do queries.

## Tools List

| CLI | Purpose | Key parameters |
| --- | --- | --- |
| `sharecrm bpm runtime get-task-by-id` | View task information | `--id <task-id>` |
| `sharecrm bpm runtime get-button-by-task-id` | View available buttons | `--data '{"taskIds":["<task-id>"]}'` |
| `sharecrm bpm runtime get-task-info-by-lane-id` | View tasks by lane | `--laneId <lane-id> --workflowId <workflow-id> --instanceId <instance-id>` |
| `sharecrm bpm runtime get-instance-form` | View an instance form of a confirmed type | `--workflowInstanceId <instance-id> --instanceFormType <instance-form-type>` |
| `sharecrm bpm runtime get-instances-by-object` | Query instances by business record | `--objectId <record-id> [--pageSize <page-size>] [--pageNumber <page-number>]` |
| `sharecrm bpm runtime get-instance-log` | View an instance log or locate tasks by instance | `--workflowInstanceId <instance-id>` |
| `sharecrm bpm runtime complete-task` | Complete the current task | `--taskId <task-id> [--opinion <opinion>]` |
| `sharecrm bpm runtime update-and-complete` | Update and complete in a default layout | `--taskId <task-id> --entityId <object-api-name> --objectId <record-id> --data <json>` |
| `sharecrm bpm runtime edit` | Save flow-layout task data | `--taskId <task-id> --objectData <json> [--originalData <json>]` |
| `sharecrm bpm runtime complete-related-task` | Only for `executionType=batchAddRelatedObject`: complete the task and save newly created related data | `--taskId <task-id> --activityId <activity-id> --activityInstanceId <activity-instance-id> --data <json> --executionType batchAddRelatedObject` |
| `sharecrm bpm runtime operate-task` | Execute a specified task operation | `--taskId <task-id> --type <operation-type> [--opinion <opinion>]` |
| `sharecrm bpm runtime cancel` | Cancel a business-flow instance | `--id <workflow-instance-id> [--reason <reason>]` |
| `sharecrm bpm runtime trigger` | Trigger a business-flow instance | `--id <workflow-definition-id> --objectId <record-id>` |
| `sharecrm bpm runtime instance-after-action-retry` | Retry an instance after-action | `--instanceId <instance-id> --rowNum <row-num> --executeType <execute-type>` |
| `sharecrm bpm runtime task-after-retry` | Retry a task after-action | `--taskId <task-id> --rowNum <row-num> --executeType <execute-type>` |
| `sharecrm bpm runtime change-task-handler` | Change the task handler | `--data '{"taskId":"<task-id>","candidateIds":["<user-id>"]}'` |
| `sharecrm bpm runtime regenerate-task-handler` | Recalculate handlers | `--taskId <task-id>` |
| `sharecrm bpm runtime remind` | Send a reminder | `--data '{"taskId":"<task-id>","content":"<content>","remindPersons":["<user-id>"]}'` |
| `sharecrm data record get-by-id` | Read a trusted business-record snapshot for flow-layout task editing | `--objectApiName <object-api-name> --recordId <record-id> --raw` |
| `sharecrm data record query-by-name` | Resolve a business number or name to a record `_id` | Use the permitted data-read path only when the current reference permits it and the real record `_id` is missing. |

First select one reference from Routing, then locate its command in this table. The table lists only minimum key parameters; the selected reference is authoritative for requiredness, optional flags, array/object JSON structure, prerequisites, and verification boundaries. Do not combine parameters across rows into a generic request, and do not replace arrays, objects, or nested data with a flat flag unsupported by that reference.

Before calling a CLI, run `--help` for the command in the selected reference to verify the actual subcommand, flags, and parameter types. When `--help` conflicts with the reference, follow `--help` and stop the write.

## Routing

First select the unique operation from the table below, then read the corresponding `references/<file>.md` under the current `bpm-runtime-skill/references/`. A reference with the same name may exist in the approval flow or stage advancer directory and must not be used as a substitute. The reference is the sole authority for that operation's parameters, CLI, JSON structure, prerequisites, and verification boundaries; when there is no unique match, stop and do not fabricate commands, flags, payloads, or operation `type`s.

| Intent | reference | Type | Primary Target |
| --- | --- | --- | --- |
| Complete current task | `task-complete-task.md` | Write | `taskId` |
| Edit and complete, or update fields then complete | First use `task-get-task-info.md`; select `task-update-data-and-complete-task.md`, or `task-edit.md` then `task-complete-task.md`, by `layoutType` | Write | `taskId` + `entityId` + `objectId` |
| Only edit task data | `task-edit.md` | Write | `taskId` |
| Batch-create a related object and complete the task (`executionType=batchAddRelatedObject`) | `task-complete-and-create-task-data.md` | Write | `taskId` + activity ID |
| Execute specified task operation | `task-operate-task.md` | Write | `taskId` + `type` |
| View task details | `task-get-task-info.md` | Read-only | `id` (task ID) |
| View available buttons | `task-get-button-by-task-id.md` | Read-only | `taskIds` |
| View tasks by lane | `task-get-task-info-by-lane-id.md` | Read-only | `laneId` + workflow and instance context |
| View an instance form of a confirmed type | `instance-get-instance-form.md` | Read-only | `workflowInstanceId` + `instanceFormType` |
| Query instances by business record | `instance-get-instances-by-object.md` | Read-only | `objectId` |
| Find tasks by instance or locate a task ID through the instance log | `instance-get-instance-log.md` | Read-only | `workflowInstanceId` |
| View instance log | `instance-get-instance-log.md` | Read-only | `workflowInstanceId` |
| Cancel instance | `instance-cancel.md` | Write | Business flow instance ID (`id` = workflowInstanceId) |
| Trigger instance | `instance-trigger.md` | Write | Business flow definition ID (`id` = workflowDefinitionId) + `objectId` |
| Retry instance after-action | `instance-after-action-retry.md` | Write | `instanceId` |
| Retry task after-action | `task-after-action-retry.md` | Write | `taskId` |
| Manually change handler | `task-change-task-handler.md` | Write | `taskId` + `candidateIds` |
| Recalculate handler | `task-refresh-handler-by-task-id.md` | Write | `taskId` |
| Remind specified handler | `task-remind.md` | Write | `taskId` + `remindPersons` |

### Layout Identification Before Editing and Completing

When the user asks to edit fields and complete the current BPM task, first execute `task-get-task-info.md` and route from `layoutType` returned for that same `taskId`. This read operation may execute directly and does not authorize a write:

| `layoutType` | Path |
| --- | --- |
| `defaultLayout` | Use `task-update-data-and-complete-task.md` to update and complete. |
| `objectFlowLayout` | Use `task-edit.md` to save, then use `task-complete-task.md` to complete. |
| Missing, another value, or a conflict with current context | Stop; do not guess the layout, downgrade to another write path, or use an instance form instead. |

The flow-layout "save, then complete" operation is a closed two-step sequence for the same task and unchanged parameters. The final preview must state the sequence; after one subsequent user confirmation, run `task-edit.md` first and run `task-complete-task.md` only on success. Stop immediately if the first step fails; do not complete or ask for another confirmation.

## Execution Flow

1. Classify and bind a unique target. Stop when the target ID is missing, the type is unclear, the candidate is not unique, the status conflicts, parameters are insufficient, or permissions are insufficient; when needed, only read the narrowest operation that can fill in that fact.
2. Read the unique reference, and before executing, run only the `--help` of the CLI in that reference to verify subcommands, flags, and parameter types; do not explore with global `bpm runtime --help`, the `--help` of an unselected reference, or a to-do query. When `--help` conflicts with the reference, `--help` takes precedence; stop writing and report that the documentation needs correction.
3. Collect the prerequisites required by that reference and the values explicitly provided by the user. Collect an original snapshot, version, or other validation fact only when the reference, verified task/form contract, or service response explicitly requires it. Pass arrays and objects as valid JSON strings; pass strings as text; pass booleans as `true` or `false`. Omit the CLI flag for unused optional parameters; do not pass the literal `null`; stop when a required parameter is missing or a required collection/object is empty.
4. Read-only operations can be executed directly, but only answer or collect facts and must never auto-escalate to writes. Write operations must go through the secondary confirmation below.
5. After writing, only verify via the read-only paths specified by that reference; do not execute a second write operation because of verification. Only the confirmed `objectFlowLayout` closed sequence in "Layout Identification Before Editing and Completing" may run `task-edit.md` followed by `task-complete-task.md`.
6. Only report success when `success == true && code == 'OK'`. `NEED_CONFIRM`, `INVALID_ARGUMENT`, `EXECUTE_FAILED`, asynchronous acceptance, or any other status is not a success.

## Identifiers and Data Contract

- `taskId` is only for task operations; `instanceId` / `workflowInstanceId` is only for instance operations; `laneId` is only for lane queries; `entityId + objectId` describes the business object and record; personnel parameters can only use user IDs. The various IDs are not interchangeable.
- The `--id` in `task-get-task-info.md` is the task ID. The `--id` in `instance-cancel.md` is the business flow instance ID (workflowInstanceId), and the `--id` in `instance-trigger.md` is the business flow definition ID (workflowDefinitionId/outlineId); the two have different semantics and are not interchangeable.
- When the user says "the first one / the Nth one," you can only bind the corresponding `taskId` from the most recently displayed same-type to-do list in this session; do not reinterpret the ordinal through subsequent queries.
- When only completing without updating business fields, use `task-complete-task.md`. When explicit fields are provided and completion is requested, first use `task-get-task-info.md` to confirm `layoutType`: use `task-update-data-and-complete-task.md` for `defaultLayout`, and the fixed `task-edit.md` then `task-complete-task.md` sequence for `objectFlowLayout`. Use `task-edit.md` only to save; ordinary completion must not use "complete and create related data," which applies only to `batchAddRelatedObject`.
- `instance-get-instance-form.md` only retrieves an instance-level form whose type the user explicitly requested and has been confirmed. Do not use it to locate `taskId`, `workflowId`, or `laneId`, or treat its response as the current task form. For a task edit, first obtain one `taskId` through a supported read-only task path, then use `task-get-task-info.md` to verify the current task and writable fields; if the available paths cannot uniquely identify the task, ask the user for the task ID or an unambiguous target.
- When `instance-get-instances-by-object.md` has returned one confirmed `workflowInstanceId` and a task ID, name, or status under that instance must be located, the next step must use `instance-get-instance-log.md`; the instance log is the preferred read-only path for locating tasks by instance. Do not substitute `instance-get-instance-form.md`, global CLI help, or a to-do SQL query.
- The `type` in `task-operate-task.md` must be explicitly provided by the user or confirmed from already-queried buttons; do not guess from natural-language actions. Manual handler change and handler recalculation use change-handler and refresh-handler respectively; instance and task after-action retries must not be mixed either.
- Business fields in business data must only contain user-provided differences that are writable on the current form; however, record metadata explicitly required by the selected reference for the same record must be preserved verbatim from a trusted snapshot. Do not pass unverified entire records, unmodified business fields, query/system fields, empty JSON, or double-encoded JSON. When fields, required metadata, or original data are insufficient, first read the narrowest reliable fact or ask the user to supplement.
- Omit or pass `false` by default for `ignoreNoBlockValidate`, `removeVersion`, `notValidate`, and other parameters that skip validation or version control. Server errors are not a reason to enable them.

## Write Secondary Confirmation

Before writing, you must display a final masked preview and ask, then wait for the user to give an explicit affirmative in a **subsequent message** for the same unchanged operation; the round in which confirmation is requested must not execute the write.

- Treat the user's initial write request as execution intent, not final authorization. First perform only the narrow read operations needed to confirm the target, writable fields, current state, and any actually required original snapshot or version fact. Do not ask for confirmation before the final CLI, field diff, and required parameters are complete, and do not ask for separate confirmations for each read-derived fact.
- During fact collection, do not show a preview or ask "edit?", "execute?", "confirm?", or an equivalent confirmation question. Read results, parameter supplements, and identity confirmation do not create a new confirmation round. Enter the preview-and-confirm state only after the final executable CLI, field diff, and actually required parameters are complete.
- Do not treat optional parameters as fixed requirements. In particular for `task-edit.md`, collect `originalData`, `originalDetails`, or other validation facts only when the reference, verified task/form contract, or service response explicitly requires them. Do not infer, generate, or convert `_id` or `version`, and do not default an empty value to `0`.
- The final CLI, reference, raw flags, JSON, and internal IDs are for Agent verification and execution only; do not display them to the user unless the user explicitly asks to inspect the command or diagnose parameters. The user-facing preview only states the business action, recognizable target, field diff or personnel change, opinion (if any), impact scope, and risk or async impact. Field modifications show field diffs; personnel modifications show personnel summaries.
- The initial request (even with complete parameters), parameter or identity confirmation, read-only results, the preview/question itself, and a generic "continue" do not constitute authorization.
- After the target, ID type, CLI/reference, action, any key parameter, personnel/data/object collection, opinion, scope, action type, or async/risk flag changes, the confirmation immediately becomes invalid; re-preview and wait for a new explicit affirmative.
- After receiving valid authorization meeting the requirements of this section, you must execute that write operation once; do not re-display the preview or ask for confirmation again. The `objectFlowLayout` edit-and-complete preview must explicitly state "save, then complete"; that closed two-step sequence for the same task and unchanged parameters counts as one write: run `task-edit.md` first, run `task-complete-task.md` only after it succeeds, and stop without completing if the first step fails. Only when the user explicitly cancels or corrects the operation, or when any of the above facts change, does the authorization become invalid and require re-preview and re-confirmation.
- After the user gives an explicit authorization in the confirmation round (for example, "confirm", "execute", or "okay"), that authorization remains valid when a trusted read only supplements optional parameters or non-key metadata and only updates the preview. Do not ask for confirmation again; execute directly. Optional parameters or non-key metadata must not change the target, ID type, CLI/reference, action, field/person/object data, opinion, scope, action type, or async/risk flag. A change to any of those facts still requires a new preview and a new explicit affirmative.
- If an actually required fact is discovered only after the final preview, obtain it through the narrowest trusted read when possible, then show one updated final preview and request confirmation again. Do not request confirmation for each prerequisite read.
- By default, process only one task or instance at a time. Multiple targets must be presented as a closed set with the same action in the preview, and the user must explicitly affirm each item or the whole set.
- You may only retry after the user explicitly corrects parameters; each retry must re-preview and confirm.

## Output

- **Query or validation**: Return business results directly relevant to the request. State an empty result, an ambiguous target, or an unverifiable state truthfully; do not broaden the query or perform a write.
- **Missing information**: State all missing business facts and the actionable next step together. Do not expose internal CLI, reference, routing, layout, or raw JSON unless the user explicitly requests diagnosis.
- **Write preview and result**: The preview shows only the business action, recognizable target, field or personnel changes, opinion, impact scope, and risk or async impact. Report the operation actually executed, target, server-side result, and reference-supported read-only evidence. Only `success == true && code == 'OK'` is success; when evidence is insufficient, explicitly state "the final business state was not independently verified" and do not describe a command response, log, or asynchronous acceptance as final business success.
