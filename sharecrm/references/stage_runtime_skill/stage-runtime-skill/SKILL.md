---
name: "stage-runtime-skill"
description: "Used to query or process existing stage accelerator instances, stages, and tasks. Use when the user mentions stage status, stage tasks, completion, submit after filling, save flow layout form, terminal-state prerequisite task, returned task, move to stage, trigger, reactivate, cancel, change handler, recalculate assignees, disassociate, asynchronous move-to result, or rollback validation. First select a unique reference by intent; changes must confirm the target and parameters; queries or validations must not automatically perform changes."
apiName: "stage_runtime_skill"
---
# Stage Accelerator Runtime

## Goal

Provide a safe, auditable, CLI-contract-driven runtime operation layer for existing stage accelerator instances: route each intent to one operation, read before changing, obtain explicit confirmation for every Non-Read operation, and report only verified outcomes. Never guess targets, parameters, stages, or commands, and never treat asynchronous acceptance as business success.

## What I Need From You

### Required

- **User intent**: A clear operation on an existing instance or task, such as moving to a specified stage, completing a task, or checking whether rollback is possible.
- **Primary target identifier**: Supply the `workflowInstanceId` + `stageId`, `taskId`, `stageTaskId`, or `entityId` + `objectId` required by the routing matrix. Triggering also requires a verified `sourceWorkflowId`.

### Optional

- **Comment or reason**: A note or cancellation reason required by the operation reference or requested by the user.
- **Change data**: Explicit field values or form data for edit, update-and-complete, and similar operations.
- **Execution options**: An asynchronous choice where the reference supports it. Any validation or version bypass must be explicitly requested by the user.

### When Information Is Missing

- Clarify an ambiguous ID type, target stage, required data, or operation intent. Never infer internal IDs from names or display values, and never guess a "previous stage."
- Bind "the first one" or "number N" only to the most recently displayed list of the same type in this session. Otherwise, request a unique identifier.
- Stop and state the gap when the reference is missing, CLI `--help` cannot be verified, or the server state conflicts.

## WhenToUse

### Use This Skill For

- "Move this instance to stage X," "complete this stage task," or "submit this task after filling it in."
- "Check whether it can roll back to stage Y," "reactivate this instance," or "query the async move result."
- "Cancel this stage instance," "trigger the stage workflow for this business record," or "change/recalculate the task handler."
- "View this task's details," "disassociate the task from a business record," or "only save the flow layout form."

### Do Not Use This Skill For

- Creating, editing, publishing, starting/stopping, or deleting stage accelerator definitions, nodes, or configuration.
- Querying the current user's stage todos, completed tasks, or personal task list. Use the parent `flow_tasks_skill` todo-query path.
- Guessing a runtime target from a name, status, page number, or default value when it cannot be uniquely bound.

## Scope and Reference Rules

Only handle existing stage accelerator instances, stages, tasks, and their runtime data; do not handle stage accelerator definitions, nodes, publishing, start/stop, or configuration deletion.

1. First select a unique operation from the table below, then read `references/<file>.md`. The reference is the sole authority for that operation's boundaries, parameter semantics, and verification basis.
2. Before executing, verify the actual CLI subcommand, flag spelling, and parameter types with `sharecrm stage runtime <command> --help`; never infer CLI flags from API/Groovy parameter names. When the reference's `CLI Call Contract` conflicts with the current `--help`, follow the current `--help` and stop writing until the documentation is corrected before executing.
3. Arrays and objects are passed as valid JSON strings; strings as text; booleans only as `true` or `false`. Omit the CLI flag for unused optional parameters; never pass a literal `null`; stop when required parameters are missing or a required collection/object is empty. Do not treat JSON as plain text, and do not guess the structure of dynamic fields.
4. Only `success == true && code == 'OK'` is reported as success. The `jobId` in an asynchronous response only indicates the request was accepted, not business success.
5. Stop and explain the gap when there is no unique reference, the target ID type is unclear, required fields/stages are unknown, CLI help cannot be verified, or the server state conflicts; never fabricate commands, parameters, stageIds, pagination, or default values.

## ToolsList

All commands are under `sharecrm stage runtime`. This table identifies subcommands only; their complete parameters, prerequisites, confirmation requirements, and verification paths are defined by the matching `references/<file>.md` in the routing matrix. Run that subcommand's `--help` before execution and never infer flags from this table.

| Category | Subcommands |
| --- | --- |
| Instance validation and queries | `back-to-validate`, `get-instance-by-object`, `query-move-to-result`, `reactive-validate` |
| Instance changes | `cancel`, `move-to`, `reactive`, `trigger` |
| Task queries | `task`, `task-by-stage-id` |
| Task changes | `change-task-handler`, `complete`, `complete-back-to-task`, `complete-terminal-pre-task`, `disassociate`, `edit`, `regenerate-stage-tasks-handler`, `regenerate-task-handler`, `update-and-complete` |

## Standard Execution Order

**Classify → Bind unique target → Read unique reference → Verify CLI contract → Collect prerequisites → For writes or state-changing validations, present the final desensitized preview and wait for subsequent explicit confirmation → Execute → Read-only verification → Report results**.

Queries are only used to gather facts. `instance-back-to-validate.md` is a pure “can roll back” check that can execute directly and only report its result; it must not automatically roll back or move the instance. Other validations and writes require secondary confirmation and must not auto-escalate to writes. Verification may only use the read-only paths allowed by that operation's reference, and must not chain into a second write operation.

## Operation Routing and Attribute Matrix

| User Intent | Reference | Type | Primary Target | Non-Read Confirmation / Async & Verification |
| --- | --- | --- | --- | --- |
| Validate whether rollback to a target stage is possible | `instance-back-to-validate.md` | Read-only validation (result only, no automatic write) | `workflowInstanceId` + `stageId` | No confirmation; report validation result only |
| Query stage instance by business object | `instance-get-instance-id-by-object-id.md` | Read-only | `entityId` + `objectId` | None; this operation's result |
| Cancel an entire stage instance | `instance-cancel.md` | Non-Read (high-impact write) | `entityId` + `objectId` | Final preview and subsequent explicit confirmation of the cancel reason and full-instance impact; verify via re-query by object when available |
| Move to a specific target stage | `instance-move-to.md` | Non-Read (Write, may be asynchronous) | `workflowInstanceId` + `stageId` | Target stage, comment, impact; only `move-to`'s `jobId` can be queried with `instance-query-move-to-result.md` |
| Query asynchronous move result | `instance-query-move-to-result.md` | Read (asynchronous result query) | `jobId` | None; only applicable to `jobId` returned by `move-to` |
| Validate whether instance reactivation is allowed | `instance-reactive-validate.md` | Non-Read (Validation; result only, no automatic write) | `workflowInstanceId` | None; after passing, still need to re-confirm reactive |
| Reactivate instance and enter a specific stage | `instance-reactive.md` | Non-Read (Write, may be asynchronous) | `workflowInstanceId` + `activeStageId` | Target stage, data, impact; do not report `jobId` as success when no supported generic job query exists |
| Trigger a stage instance for a business object | `instance-trigger.md` | Non-Read (Write) | `entityId` + `objectId` + `sourceWorkflowId` | Trigger scope and verified source workflow; verify via re-query by object when available |
| Manually change task handler | `task-change-task-handler.md` | Non-Read (Write) | `taskId` + `candidateIds` | User ID list and notification impact; task details |
| Complete returned task and move to target stage | `task-complete-back-to-task.md` | Non-Read (Write, may be asynchronous) | `workflowInstanceId` + `stageId` | Stage, data, validation bypass and impact; `async` default value is `true` (asynchronous acceptance); pass `false` explicitly for synchronous execution; do not report asynchronous acceptance as success when no dedicated result query is provided |
| Complete terminal-state prerequisite task | `task-complete-terminal-pre-task.md` | Non-Read (Write, may be asynchronous) | `taskId` | Data and terminal impact; do not report asynchronous acceptance as success when no dedicated result query is provided |
| Directly complete a stage task | `task-complete.md` | Non-Read (Write) | `taskId` | Comment, associated data and impact; task details |
| Disassociate task from specified business records | `task-disassociate.md` | Non-Read (Write) | `taskId` + `objectIds` | Record collection and disassociation scope; task details |
| Only save flow layout form | `task-edit.md` | Non-Read (Write) | `taskId` | Field-level changes, concurrent original data and validation impact; task details |
| View task details | `task-get-task-by-id.md` | Read-only | `taskId` (optional `activityId`) | None; this operation's result |
| View tasks by instance and stage | `task-get-tasks-info-by-instance-id-and-stage-id.md` | Read-only | `workflowInstanceId` + `stageId` | None; this operation's result |
| Recalculate stage task assignees | `task-regenerate-stage-tasks-handler.md` | Non-Read (Write) | `stageTaskId` | Stage task, comment and assignee recalculation impact; task/stage query |
| Recalculate runtime task assignees | `task-regenerate-task-handler.md` | Non-Read (Write) | `taskId` | Task and assignee recalculation impact; task details |
| Complete task after updating default layout fields | `task-update-and-complete.md` | Non-Read (Write) | `taskId` | Field-level changes, comment and completion impact; task details |

The current references do not support querying "the current user's stage to-do tasks, completed tasks, or personal task list." Do not guess command names, statuses, or pagination parameters; such requests are handled by the parent `flow_tasks_skill`'s to-do query path.

## Target Identifier Contract

- `entityId` is the business object API name; `objectId` is the real system `_id` of the target business record under that `entityId`, and may only come from trusted business-record context or the result of uniquely querying a record by that `entityId`. `StageTaskObj._id`, `workflowInstanceId`, `stageId`, `taskId`, and `stageTaskId` cannot be used as `objectId`, and `entityId` and `objectId` must not be swapped based on ID appearance or user input order. They are only used for the corresponding operations of querying instance by object, canceling, and triggering, and cannot replace the instance ID. Triggering must also provide a verified `sourceWorkflowId`.
- `workflowInstanceId` is the stage accelerator instance ID; `stageId` is the explicit move/rollback target stage; `activeStageId` is the stage to enter after reactivation. Do not guess an arbitrary `stageId` from "the previous stage."
- `taskId` is the runtime task ID; `stageTaskId` is the stage task ID; the two are only used for the recalculation operations declared in their respective references and cannot be interchanged.
- `activityId` is only used as optional context for task details; `jobId` is only used for `query-move-to-result`; `candidateIds` and `objectIds` must be a user ID list and a business record ID list, respectively.
- When the user says "the first one / the Nth one," bind that item's ID only based on the most recently displayed list of the same type in this session, and lock the target immediately; do not reinterpret the index due to subsequent queries.

## Completion, Editing, Movement, and Asynchrony

- **Completion**: Use `task-complete.md` when no business fields are changed; its `data` is only for selecting/creating associated data, not a field update JSON. Use `task-update-and-complete.md` to update fields in the default layout and complete. Use `task-edit.md` to only save flow layout data; "edit and complete" are two writes and cannot be automatically chained.
- **Special tasks**: Use `task-complete-terminal-pre-task.md` for terminal-state prerequisite tasks; at least one of `data` and `flowLayoutEditData` must be provided. Use `task-complete-back-to-task.md` to complete a returned task and move to a stage; it cannot be replaced by a regular complete or move-to. Before actual rollback, back-to-validate must also pass; after it passes, show the final preview for that write operation and wait for confirmation.
- **Movement and activation**: Asking "can I roll back" only executes back-to-validate and must not automatically move-to. When the user explicitly requests rollback to a confirmed target stage, first execute back-to-validate directly; stop and report the reason if it fails, and only after it passes show the final preview for the actual move-to and wait for confirmation. A successful validation is not authorization. reactive-validate must be performed before reactive; even after validation passes, `activeStageId`, data, and the activation action must still be confirmed.
- **Flow layout data**: `objectData`, `details`, `originalData`, `originalDetails` are string parameters but their content must be valid JSON as declared in the reference. Field structure should come from the form/data actually returned in task details; when not returned, collect explicit user data or stop — do not fabricate.
- **Asynchrony**: `async` is not passed by default. **Exception: `task-complete-back-to-task.md` has an `async` default value of `true` (asynchronous acceptance); to execute synchronously, you must explicitly pass `--async false`.** Only `move-to` explicitly supports polling its `jobId` with `query-move-to-result`. For other asynchronous operations without a result query contract supported by this Skill, you must report "accepted, final status unverified" and must not retry, resubmit, or report success. Polling details are governed by `instance-query-move-to-result.md`: only continue polling when the service provides `queryIntervalSecond`; otherwise report "accepted, final status unverified" or let the user decide whether to continue.

## Non-Read Operation Confirmation and Safety Boundaries

1. Instances, tasks, forms, buttons, logs, and the “can roll back” check in `instance-back-to-validate.md` are read-only and can be executed directly. That check only reports its result and must not automatically roll back, move the instance, or trigger follow-up operations. Other validations are non-read operations that require secondary confirmation.
2. Before each write or other non-read validation, present the final desensitized preview and ask a question, then wait for the user to give explicit confirmation in a subsequent message for that unchanged operation; the non-read CLI must not be called in the same turn as the confirmation request.
3. The CLI, reference, raw flags, JSON, internal IDs, and internal action values are for Agent verification and execution only; do not display them to the user unless the user explicitly asks to inspect the command or diagnose parameters. The user-facing preview only states the business action, recognizable stage-task/business target, target stage (when applicable), field or personnel/association changes, comment, impact scope, and async or risk impact. Data modifications show field diffs; personnel/association modifications show user or record diffs.
4. The initial request (even if complete), parameter or identity confirmation, read-only results, the preview/question itself, and a generic "continue" are not authorization. Any change to the target, ID type, CLI/reference, action, any key parameter, personnel/data/object collection, comment, scope, target stage/action type, async or risk flag invalidates the pending confirmation and requires a new preview and a subsequent explicit confirmation.
5. After receiving valid authorization matching the preceding preview, you must execute that non-read operation once; do not re-present the preview or re-request confirmation. Authorization is only invalidated and requires re-preview and re-confirmation when the user explicitly cancels or corrects the operation, or when any fact described in step 4 changes.
6. By default, process only one task or instance at a time. Multi-target non-read operations must explicitly enclose the set and the same action in the preview, and must be explicitly confirmed item by item or as a whole in a subsequent message.
7. `ignoreNoBlockValidate`, `ignoreSkipInNoBlockValidate`, `noBlockValidate`, `notValidate`, `taskData.ignoreNonBlocking`, and `taskData.removeVersion` are omitted or `false` by default. Only when the user explicitly requests bypassing the corresponding validation/version handling, understands the impact, and explicitly confirms the specific flag after the final preview, may `true` be passed; server errors are not a reason to automatically enable these parameters.
8. After writing, verify only via the read-only paths supported by the matrix/reference. Stop when permissions are insufficient, the target is ambiguous, state conflicts, or parameters are missing; you may only retry after correcting the explicit parameters, and must re-preview and wait for subsequent explicit confirmation.

## Common Errors

- Mixing up `entityId`, `objectId`, `workflowInstanceId`, `stageId`, `taskId`, and `stageTaskId`.
- Automatically escalating view details, forms, buttons, or validation results into writes, or claiming that task details returned forms/buttons/required fields that were not actually returned.
- Mixing up regular completion, update-and-complete, flow layout editing, terminal-state prerequisite task completion, and returned task completion.
- Guessing "the previous stage," automatically escalating rollback/reactivation validation to move-to/reactive, or treating an asynchronous `jobId` as business success.
- Passing JSON as plain text; treating the associated `data` of a regular complete as field update JSON; calling a special completion that requires data with empty data.
- Using risk parameters to bypass validation/version control, or resubmitting a write while the asynchronous result is pending.

## Output

- **Read or read-only validation**: State the queried or validated target, the material result, and known limitations. Report only facts actually returned.
- **Non-Read preview**: Before execution, present a desensitized business-language summary of the action, target, field/person/association changes, comment, scope, and asynchronous or risk impact, then wait for later explicit confirmation.
- **Non-Read result**: State whether execution occurred, the available read-only verification result, and any reason the final state remains unverified. Report success only when `success == true && code == 'OK'` and the reference-supported verification is complete. For asynchronous work without a result-query contract, report "accepted; final status is unverified."

Do not normally expose CLI commands, internal flags, raw JSON, or internal IDs. Do so only when the user explicitly asks to inspect the command or diagnose parameters.

## Resources

`references/` is this Skill's operation library. It contains 19 reference files, each corresponding to exactly one routing-matrix operation. Select the unique file from the matrix, then read it before preparing a preview or executing; its CLI call contract, prerequisites, confirmation requirements, and read-only verification path are the sole authority for that operation. This entrypoint defines only cross-operation routing, safety boundaries, inputs, and output rules.
