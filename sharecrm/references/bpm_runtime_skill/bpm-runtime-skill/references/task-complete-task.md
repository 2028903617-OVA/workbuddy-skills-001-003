# BpmTaskComplete

> **CLI**: `sharecrm bpm runtime complete-task`
>
> **API**: `Fx.bpm.Task.completeTask`

## Purpose and Scenario

Complete a task; only attach `data` when the current task actually requires workflow completion data. When editing and completing a task, it is the second step after successful `task-edit.md` only when the same task's `GetTaskInfo.layoutType == objectFlowLayout`.

## Operation Boundaries and Execution Rules

`data` is the workflow data Map required to complete the current task, not a general-purpose main object form edit payload. Only pass it when the user explicitly requests it and the current task requires it, and only include real fields explicitly provided by the user; do not pass entire business records, unmodified fields, query fields, or system fields, and do not double-JSON-encode. `objectId` is an optional associated record identifier, but this completion interface's service layer call does not use it as the basis for data updates; if the target record or data semantics are unclear, first query the narrowest reliable read-only fact. `nextTaskAssignee` is only for the next node handler configuration: use `person`, `group`, `dept` keys; `person` values are user ID arrays, do not use names, task IDs, or instance IDs. `addOrReplaceNextTaskAssignee` uses `1` for add and `0` for replace. When editing and completing a task, first require `GetTaskInfo.layoutType == objectFlowLayout` for the same task and successful `task-edit.md`; do not use this operation for a `defaultLayout` edit-and-complete, which must use `task-update-data-and-complete-task.md`. Do not pass `ignoreNoBlockValidate=true` by default.

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.completeTask(
    taskId,
    opinion,
    objectId,
    data,
    nextTaskAssignee,
    addOrReplaceNextTaskAssignee,
    needGetNextTaskInfo,
    ignoreNoBlockValidate
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | Business flow task ID, used to locate the current task. |
| `opinion` | String | Optional | The opinion or comment entered when processing the current task. |
| `objectId` | String | Optional | Associated business data record ID; this interface's service layer call does not use it as the basis for data updates. |
| `data` | Map | Optional | Workflow data required to complete the current task; only contains real fields explicitly provided by the user, not full main object form data. |
| `nextTaskAssignee` | Map | Optional | Next node handler configuration, using `person`, `group`, `dept` keys; `person` is a user ID array, pass a valid JSON object. |
| `addOrReplaceNextTaskAssignee` | Integer | Optional | Next node handler processing method (integer): `1` means add, `0` means replace. |
| `needGetNextTaskInfo` | Boolean | Optional | Whether to return next task info after completion; `true` means return. |
| `ignoreNoBlockValidate` | Boolean | Optional | Whether to ignore non-blocking validation. Do not pass `true` by default; only use after explicit user confirmation. |

## Code Example

```groovy
def taskId = '<confirmed-task-id>'
def opinion = '<explicit-opinion>'
def objectId = '<confirmed-object-id>'
def data = ['<writable-field-api-name>': '<explicit-user-provided-new-value>']
def nextTaskAssignee = [person: ['<confirmed-user-id>']]
def addOrReplaceNextTaskAssignee = 0
def needGetNextTaskInfo = true
def ignoreNoBlockValidate = false

def (Boolean error, Map result, String msg) = Fx.bpm.Task.completeTask(
    taskId, opinion, objectId, data, nextTaskAssignee,
    addOrReplaceNextTaskAssignee, needGetNextTaskInfo, ignoreNoBlockValidate
)
```

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |

> `nextTaskAssignee` is the next task handler configuration, not user names; when unable to locate personnel, first obtain the user ID. `addOrReplaceNextTaskAssignee` uses `1` for add, `0` for replace.

## Operation Type

Non-Read

## Primary Target

Business flow task.

## Prerequisites

Obtain and confirm the task ID; collect explicit opinion, associated data, and next task handler selections as needed. When editing and completing, require `GetTaskInfo.layoutType == objectFlowLayout` for the same task and successful `task-edit.md`.

## CLI Example

```bash
sharecrm bpm runtime complete-task --taskId <task-id> --opinion "<opinion>"
```

## Confirmation Requirements

Confirm the task, completion action, `taskId`, opinion, submitted data field summary, next handler personnel summary, and routing impact. Do not set `ignoreNoBlockValidate` to true by default.


Follow the write secondary confirmation rules in `../SKILL.md`.
## Verification

Use `task-get-task-info.md`, `task-get-button-by-task-id.md`, or `instance-get-instance-log.md` as needed. Do not claim the final business state is verified unless the returned data can prove it.
