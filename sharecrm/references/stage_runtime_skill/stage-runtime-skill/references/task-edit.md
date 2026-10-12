# Edit Task Data

> **CLI**: `sharecrm stage runtime edit`

## Operation Type

Non-Read

## Primary Target

`edit`: Edit task data

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime edit --taskId "<task-id>" --objectData '{"<writable-field-api-name>":"<explicit-user-provided-new-value>"}'
```

## Confirmation Requirements

Confirm the exact changes to task data before submitting, and retain original values from the read-only result.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Check whether the response is successful and verify the target status with a read-only query; do not treat request acceptance as final success.

### Retained API, Groovy Background, and Parameter Table

### Operation Properties

- **Type**: Write.
- **Primary target**: `taskId` (runtime task ID).
- **Side effects**: Only saves flow layout form data; does not complete the task.
- **Confirmation**: Display field-level changes, original data/concurrency control impact, and validation settings before confirming.

### CLI Call Contract

```bash
sharecrm stage runtime edit \
  --taskId "<taskId>" \
  --objectData '<json-string>' \
  --details '<json-string>' \
  --optionInfo '<json-object>' \
  --notValidate false \
  --originalData '<json-string>' \
  --originalDetails '<json-string>' \
  --instanceId "<instanceId>"
```

`objectData`, `details`, `originalData`, `originalDetails` are CLI string parameters, but each must contain valid JSON; the outer shell quotes and inner JSON escaping must be correct.

| CLI flag | API Parameter | Type | Business Required | Description |
| --- | --- | --- | --- | --- |
| `--taskId` | `taskId` | String | ✅ | The task ID to save. |
| `--objectData` | `objectData` | JSON string | ✅ | Edited main object data. |
| `--details` | `details` | JSON string | Optional | Edited detail data. |
| `--optionInfo` | `optionInfo` | JSON object | Optional | Extended configuration. |
| `--notValidate` | `notValidate` | Boolean | Optional | Skip data/required-field validation; defaults to omitted or `false`. |
| `--originalData` / `--originalDetails` | Same-name parameters | JSON string | Optional | Original data, used for concurrent edit control. |
| `--instanceId` | `instanceId` | String | Optional | Instance context. |

### Prerequisites and Verification

Fields, required fields, and JSON containers may only be determined by the actual response from task details. `notValidate=true` requires separate explicit confirmation; validation failures must not be automatically bypassed. After synchronous success, verify saved data with task details as a read-only check; this operation does not complete the task.

### API

```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Task.edit(
    taskId, details, objectData, optionInfo, notValidate, originalData, originalDetails, instanceId
)
```