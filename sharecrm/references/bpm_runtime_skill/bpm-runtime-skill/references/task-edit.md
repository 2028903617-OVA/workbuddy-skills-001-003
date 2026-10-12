# BpmTaskFormEdit

> **CLI**: `sharecrm bpm runtime edit`
>
> **API**: `Fx.bpm.Task.edit`

## Purpose and Scenario

Edit task form data without completing the task. When editing and completing a task, it is the first step of the "save, then complete" sequence only when the same task's `GetTaskInfo.layoutType == objectFlowLayout`.

## Operation Boundaries and Execution Rules

The string contents of `objectData`, `details`, `originalData`, and `originalDetails` must be valid JSON; they are JSON strings, do not wrap serialized JSON into another JSON string or object. Do not construct `objectData` from only the user-changed fields: base it on the trusted current snapshot of the record linked to the same task, preserve the record metadata actually required by the service, then apply the explicitly provided new values. A verified BPM edit request includes at least the same record's `_id`, `version`, `record_type`, and `object_describe_api_name` in `objectData`; when present in the current task/form snapshot and required by the current contract, preserve `object_describe_id` and `requestId` unchanged as well. Do not guess, generate, or change the values or JSON types of these fields, and do not add other unverified complete-record fields, query fields, or system fields. `details` and `originalDetails` are only for real detail data and must not mix in main object fields; `originalData` must come from the real pre-edit request snapshot of the same record and must not be replaced with an empty object. The verified minimum `originalData` is `{"_id":"<same-record-id>"}`; when the current task/form contract requires more fields, obtain them verbatim from the trusted snapshot instead of constructing them. When editing and completing a task, use this operation only after the same task's `GetTaskInfo.layoutType == objectFlowLayout`; it must succeed before `task-complete-task.md` in one confirmed closed sequence. Do not use this operation for `defaultLayout`. Do not default an empty value to `0`, and do not fabricate or bypass with `notValidate=true`.

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.edit(
    taskId,
    details,
    objectData,
    optionInfo,
    notValidate,
    originalData,
    originalDetails
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | Business flow task ID, used to locate the current task. |
| `details` | String | Optional | Detail data JSON string in the task form. |
| `objectData` | String | Optional | Main object data JSON string. Build it from the trusted current snapshot of the same record, preserve at least `_id`, `version`, `record_type`, and `object_describe_api_name`, then apply the explicitly provided new values; preserve `object_describe_id` and `requestId` verbatim when required by the current snapshot. Do not pass only changed fields, guess metadata, or double-encode. |
| `optionInfo` | Map | Optional | Additional option info required for task processing, pass a valid JSON object. |
| `notValidate` | Boolean | Optional | Whether to skip validation. Do not pass `true` by default; only use after explicit user confirmation. |
| `originalData` | String | Optional | Pre-edit request snapshot JSON string for the same record, used for change or version validation. The verified minimum structure is `{"_id":"<same-record-id>"}`; when the current contract requires more fields, obtain them verbatim from the trusted snapshot. |
| `originalDetails` | String | Optional | Original detail data JSON string before editing, used for change validation. |

## Code Example

> This example only shows the underlying function's parameter types and order. It does not mean that the CLI must receive every optional parameter. Pass only fields that are actually needed and verified, and omit unused optional flags.

```groovy
def taskId = '<confirmed-task-id>'
def details = '[{"<detail-field-api-name>":"<explicit-user-provided-new-value>"}]'
def objectData = '{"object_describe_id":"<verified-object-describe-id>","requestId":"<verified-request-id>","_id":"<same-record-id>","version":"<verified-version>","record_type":"<verified-record-type>","object_describe_api_name":"<verified-object-api-name>","<writable-field-api-name>":"<explicit-user-provided-new-value>"}'
def optionInfo = ['<confirmed-option-key>': '<confirmed-option-value>']
def notValidate = false
def originalData = '{"_id":"<same-record-id>"}'
def originalDetails = '[{"<detail-field-api-name>":"<verified-original-value>"}]'

def (Boolean error, Map result, String msg) = Fx.bpm.Task.edit(
    taskId, details, objectData, optionInfo, notValidate, originalData, originalDetails
)
```

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |

## Operation Type

Non-Read

## Primary Target

Business flow task form and business data.

## Prerequisites

Obtain the task ID and explicit field-level change sets. Use `sharecrm data record get-by-id --objectApiName <object-api-name> --recordId <record-id> --raw` to read the trusted current full snapshot of the same record and obtain the record metadata required by `objectData` and the `originalData`. The `--raw` flag is required: system fields such as `version` and `record_type` are returned only in the raw response; `object-data-query` and `get-by-id` without `--raw` are not valid sources for those fields. When editing and completing, first require `layoutType == objectFlowLayout` from `task-get-task-info.md` for the same task.

## CLI Example

```bash
sharecrm bpm runtime edit --taskId <task-id> --objectData '{"object_describe_id":"<verified-object-describe-id>","requestId":"<verified-request-id>","_id":"<same-record-id>","version":"<verified-version>","record_type":"<verified-record-type>","object_describe_api_name":"<verified-object-api-name>","<writable-field-api-name>":"<explicit-user-provided-new-value>"}' --originalData '{"_id":"<same-record-id>"}'
```

## Confirmation Requirements

After the internal final CLI, field diff, and actually required parameters are complete, ask the user to confirm the recognizable business target, edit action, field-level data and detail changes, and validation impact. Do not show the raw CLI, `taskId`, raw JSON, or other internal parameters in the preview unless the user explicitly asks to inspect them. Do not set `notValidate` to true by default, and do not request repeated confirmations while collecting individual read-only facts.


Follow the write secondary confirmation rules in `../SKILL.md`.
## Verification

Use `task-get-task-info.md` to check returned task/form data when available. Only report returned evidence; saving data does not mean the business flow transition is verified.
