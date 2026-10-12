# Complete Task

> **CLI**: `sharecrm stage runtime complete`

## Operation Type

Non-Read

## Primary Target

`complete`: Complete task

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime complete --taskId "<task-id>" --comment "<confirmed-comment>" --data '{"field":"value"}' --ignoreNoBlockValidate false
```

## Confirmation Requirements

Confirm the exact task, comment, and data changes before submitting.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Check whether the response is successful and verify the target status with a read-only query; do not treat request acceptance as final success.

### Retained API, Groovy Background, and Parameter Table

### Operation Properties

- **Type**: Write.
- **Primary target**: `taskId` (runtime task ID).
- **Side effects**: Completes the task and advances the subsequent flow; may include a comment and associated data selection/creation.
- **Confirmation**: Display the task, comment, associated data summary, and completion impact before execution, and obtain explicit confirmation.

### CLI Call Contract

First run `sharecrm stage runtime complete --help` to verify the local CLI; currently available flags:

```bash
sharecrm stage runtime complete \
  --taskId "<taskId>" \
  --comment "<comment>" \
  --data '<json-object>' \
  --ignoreNoBlockValidate false
```

| CLI flag | API Parameter | Type | Business Required | Description |
| --- | --- | --- | --- | --- |
| `--taskId` | `taskId` | String | ✅ | The runtime task ID to complete. |
| `--comment` | `comment` | String | Optional | Completion comment. |
| `--data` | `data` | JSON object | Optional | Associated data selection/creation information; not a business field update JSON. |
| `--ignoreNoBlockValidate` | `ignoreNoBlockValidate` | Boolean | Optional | Skip non-blocking validation; defaults to omitted or `false`. |

`--data` must be a single valid JSON object, e.g., `--data '{"relatedObjectId":"<id>"}'`; actual keys may only use structures explicitly provided by task details or the operation definition.

### API

```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Task.completeTask(
    taskId,
    comment,
    data,
    ignoreNoBlockValidate
)
```

### Prerequisites and Safety Defaults

- Only used for completion without updating business fields; for updating default layout fields and completing, use `task-update-and-complete.md`.
- `taskId` must come from a locked target. When associated data requirements are unclear, first read `task-get-task-by-id.md`; do not fabricate `data` without actual returned fields/association requirements.
- Do not pass `ignoreNoBlockValidate` by default. Only pass `true` when the user explicitly requests skipping this validation, understands the impact, and confirms the flag a second time.

### Success and Verification

Only `success == true && code == 'OK'` is considered success. After completion, use `task-get-task-by-id.md` to read-only check the task status; if the response cannot prove the final status, report insufficient verification and do not re-submit the completion request.