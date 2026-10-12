# BpmTaskUpdateAndComplete

> **CLI**: `sharecrm bpm runtime update-and-complete`
>
> **API**: `Fx.bpm.Task.updateDataAndCompleteTask`

## Purpose and Scenario

Update the writable business fields allowed by the current BPM form and complete the task. When editing and completing a task, use this operation only when the same task's `GetTaskInfo.layoutType == defaultLayout`.

## Operation Boundaries and Execution Rules

This reference corresponds to `UpdateDataAndCompleteTask`. `taskId`, `entityId`, and `objectId` must be passed as separate parameters; `data` is a valid JSON object containing only real fields that are writable on the current BPM form and have new values explicitly provided by the user. Do not wrap the three identifiers and the inner business data into a single `data` envelope, do not double-JSON-encode, and do not pass back entire records, unmodified fields, query fields, or system fields. When editing and completing a task, first require `GetTaskInfo.layoutType == defaultLayout` for the same task; do not use this operation for `objectFlowLayout`, which must use `task-edit.md` then `task-complete-task.md`. The server uses the separate `objectId` to filter writable fields and perform conflict checks; `versionCheckBlocked=false` only means the check did not block, not that data was saved or the task was completed. The legacy interface controller does not consume `originalData` or `optionInfo`; do not describe them as required inputs for conflict checking. Do not pass `ignoreNoBlockValidate=true` or `removeVersion=true` by default; when the record, field structure, or writable scope is unclear, first query the narrowest reliable read-only fact.

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.updateDataAndCompleteTask(
    taskId,
    entityId,
    objectId,
    data,
    nextTaskAssignee,
    addOrReplaceNextTaskAssignee,
    needGetNextTaskInfo,
    result,
    opinion,
    ignoreNoBlockValidate,
    removeVersion,
    originalData,
    optionInfo
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | Business flow task ID, used to locate the current task. |
| `entityId` | String | ✅ | API name of the associated business object. |
| `objectId` | String | ✅ | Associated business data record ID. |
| `data` | Map | Optional | Valid JSON object; only contains real fields writable on the current BPM form with new values explicitly provided by the user; cannot wrap `taskId`, `entityId`, `objectId`, or entire records. |
| `nextTaskAssignee` | Map | Optional | Next node handler configuration, using `person`, `group`, `dept` keys; `person` is a user ID array, pass a valid JSON object. |
| `addOrReplaceNextTaskAssignee` | Integer | Optional | Next node handler processing method (integer): `1` means add, `0` means replace. |
| `needGetNextTaskInfo` | Boolean | Optional | Whether to return next task info after completion; `true` means return. |
| `result` | String | Optional | The processing result when updating and completing the task, using a value supported by the current node. |
| `opinion` | String | Optional | The opinion or comment entered when processing the current task. |
| `ignoreNoBlockValidate` | Boolean | Optional | Whether to ignore non-blocking validation. Do not pass `true` by default; only use after explicit user confirmation. |
| `removeVersion` | Boolean | Optional | Whether to remove version validation info; do not pass `true` by default, only use per explicit business rules. |
| `originalData` | String | Optional | The controller does not consume this parameter; do not describe it as a required input for conflict checking. |
| `optionInfo` | Map | Optional | The controller does not consume this parameter; do not describe it as a required input for conflict checking. |

## Code Example

```groovy
def taskId = '<confirmed-task-id>'
def entityId = '<confirmed-entity-api-name>'
def objectId = '<confirmed-object-id>'
def data = ['<writable-field-api-name>': '<explicit-user-provided-new-value>']
def nextTaskAssignee = [person: ['<confirmed-user-id>']]
def addOrReplaceNextTaskAssignee = 0
def needGetNextTaskInfo = true
def resultValue = '<confirmed-node-result>'
def opinion = '<explicit-opinion>'
def ignoreNoBlockValidate = false
def removeVersion = false
def originalData = '{"<writable-field-api-name>":"<verified-original-value>"}'
def optionInfo = ['<confirmed-option-key>': '<confirmed-option-value>']

def (Boolean error, Map response, String msg) = Fx.bpm.Task.updateDataAndCompleteTask(
    taskId, entityId, objectId, data, nextTaskAssignee,
    addOrReplaceNextTaskAssignee, needGetNextTaskInfo, resultValue, opinion,
    ignoreNoBlockValidate, removeVersion, originalData, optionInfo
)
```

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |
| `entityId` non-empty | Required parameter |
| `objectId` non-empty | Required parameter |

## Operation Type

Non-Read

## Primary Target

Business flow task, associated business record, and updated data.

## Prerequisites

Obtain and confirm `taskId`, `entityId`, `objectId`. When editing and completing, first require `layoutType == defaultLayout` returned by `task-get-task-info.md` for the same task. Collect explicit and valid data object and next task handler selections.

## CLI Example

```bash
sharecrm bpm runtime update-and-complete --taskId <task-id> --entityId <entity-id> --objectId <object-id> --data '{"<writable-field-api-name>":"<explicit-user-provided-new-value>"}'
```

## Confirmation Requirements

Confirm the task, update-and-complete action, required identifiers, field-level data changes, next handler personnel summary, result/opinion, and completion impact. Do not set `ignoreNoBlockValidate` or `removeVersion` to true by default.


Follow the write secondary confirmation rules in `../SKILL.md`.
## Verification

Use `task-get-task-info.md`, `task-get-button-by-task-id.md`, or `instance-get-instance-log.md` as needed. Only report returned evidence; do not promise the final business state is verified.
