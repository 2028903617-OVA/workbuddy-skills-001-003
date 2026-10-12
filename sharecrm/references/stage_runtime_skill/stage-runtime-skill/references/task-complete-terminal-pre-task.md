# Complete Task Before Entering Terminal Stage

> **CLI**: `sharecrm stage runtime complete-terminal-pre-task`

## Operation Type

Non-Read

## Primary Target

`complete-terminal-pre-task`: Complete task before entering terminal stage

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime complete-terminal-pre-task --taskId "<task-id>" --data '{"updateJson":"{\"<writable-field-api-name>\":\"<explicit-user-provided-new-value>\"}"}' --flowLayoutEditData '{"taskId":"<task-id>","objectData":"{}"}' --async false
```

## Confirmation Requirements

Confirm the terminal impact and the submitted data before submitting; at least one of `data` or `flowLayoutEditData` must be non-empty.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Check whether the response is successful and verify the target status with a read-only query; do not treat request acceptance as final success. When using `--async true`, acceptance or `jobId` does not represent final success.

### Retained API, Groovy Background, and Parameter Table

### Operation Properties and CLI Contract

- **Type**: Write, may be asynchronous; **Primary target**: `taskId`; **Side effects**: Completes the task before entering the terminal state.
- Before writing, you must display the task, `data.updateJson` / `flowLayoutEditData` field diffs, terminal impact, and async selection, and confirm.

```bash
sharecrm stage runtime complete-terminal-pre-task \
  --taskId "<taskId>" \
  --data '{"updateJson":"{\"<writable-field-api-name>\":\"<explicit-user-provided-new-value>\"}"}' \
  --flowLayoutEditData '<json-object>' --async false
```

| flag | Type | Business Required | Description |
| --- | --- | --- | --- |
| `--taskId` | String | ✅ | Terminal-state prerequisite task ID. |
| `--data` | JSON object | Conditionally required | `CompleteUpdateTaskData` wrapper object; `updateJson` is a JSON string containing actual default layout field updates. |
| `--flowLayoutEditData` | JSON object | Conditionally required | Flow layout edit data; its `taskId` and `objectData` are required, nested `notValidate` defaults to omitted/`false`. |
| `--async` | Boolean | Optional | Defaults to omitted or `false`. |

Although `comment` can be received by the request DTO, the controller and service do not consume it; do not treat it as a valid completion comment, CLI example parameter, or final confirmation item. At least one of `data` and `flowLayoutEditData` must be non-empty. The flow layout's `objectData`, `details`, `originalData`, `originalDetails` are JSON strings; their structure must come from actual task details.

### Asynchrony, Success, and Verification

The `jobId` from `async=true` only indicates acceptance; this Skill does not provide a dedicated result query for this operation, so do not report success or resubmit. Synchronous success requires only `success == true && code == 'OK'`; then verify with task details as a read-only check; report unverified when the terminal state cannot be proven.

### API

```groovy
Fx.stage.Task.completeTerminalPreTask(taskId, data, flowLayoutEditData, async)
```