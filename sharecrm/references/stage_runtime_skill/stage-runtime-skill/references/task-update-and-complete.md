# Update Task Data and Complete

> **CLI**: `sharecrm stage runtime update-and-complete`

## Operation Type

Non-Read

## Primary Target

`update-and-complete`: Update task data and complete

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime update-and-complete --taskId "<task-id>" --comment "<confirmed-comment>" --data '{"updateJson":"{\"<writable-field-api-name>\":\"<explicit-user-provided-new-value>\"}"}' --ignoreNoBlockValidate false
```

## Confirmation Requirements

Confirm the task, data changes, comment, and completion effect together before submitting.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Check whether the response is successful and verify the target status with a read-only query; do not treat request acceptance as final success.

### Retained API, Groovy Background, and Parameter Table

### Operation Properties

- **Type**: Write.
- **Primary target**: `taskId` (runtime task ID).
- **Side effects**: Updates default layout business fields and completes the task in the same request.
- **Confirmation**: Display field before/after diffs, comment, completion impact, and risk flags before confirming.

### CLI Call Contract

```bash
sharecrm stage runtime update-and-complete \
  --taskId "<taskId>" \
  --comment "<comment>" \
  --data '{"updateJson":"{\"<writable-field-api-name>\":\"<explicit-user-provided-new-value>\"}"}' \
  --ignoreNoBlockValidate false
```

| CLI flag | API Parameter | Type | Business Required | Description |
| --- | --- | --- | --- | --- |
| `--taskId` | `taskId` | String | ✅ | The runtime task ID to update and complete. |
| `--comment` | `comment` | String | Optional | Completion comment. |
| `--data` | `data` | JSON object | ✅ | `CompleteUpdateTaskData` wrapper object; `updateJson` must be a JSON string containing actual field updates; do not pass empty objects, associated data, or flat field objects. |
| `--ignoreNoBlockValidate` | `ignoreNoBlockValidate` | Boolean | Optional | Skip non-blocking validation; defaults to omitted or `false`. |

### Prerequisites and Safety Defaults

- Only used for default layout "update and complete"; for flow layout saving use `task-edit.md`, and do not split it into an unconfirmed edit followed by complete.
- The string content of `data.updateJson` must be valid JSON; its keys and values must come from editable fields actually returned in task details or field values explicitly provided by the user. When fields are unknown, first query task details; do not guess the structure.
- `ignoreNoBlockValidate=true` may only be used after the user explicitly requests it, understands the impact, and individually confirms the flag.

### Success and Verification

Only `success == true && code == 'OK'` is considered success; then verify with `task-get-task-by-id.md` as a read-only check. When the final status cannot be proven, report insufficient verification and do not resubmit.

### API

```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Task.updateAndCompleteTask(
    taskId, comment, data, ignoreNoBlockValidate
)
```