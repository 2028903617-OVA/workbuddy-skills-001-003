# Complete Returned Task

> **CLI**: `sharecrm stage runtime complete-back-to-task`
>
> **Note**: The `async` default value for this operation is `true` (asynchronous acceptance), unlike other stage operations (which default to not passing `async`). To execute synchronously, you must explicitly pass `--async false`.

## Operation Type

Non-Read

## Primary Target

`complete-back-to-task`: Complete returned task

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Before actual rollback, first execute `instance-back-to-validate.md`; stop and report the result if it fails, and only after it passes may you show the final preview for this operation. A successful validation is not execution authorization. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime complete-back-to-task --workflowInstanceId "<workflow-instance-id>" --stageId "<stage-id>" --noBlockValidate false --async false --data '{"field":"value"}' --flowLayoutEditData '{"taskId":"<task-id>","objectData":"{}"}'
```

## Confirmation Requirements

Confirm the instance, stage, data changes, and whether flow layout editing applies before submitting; `instance-back-to-validate.md` must already have passed.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Check whether the response is successful and verify the target status with a read-only query; do not treat request acceptance as final success. When using `--async true`, acceptance or `jobId` does not represent final success.

### Retained API, Groovy Background, and Parameter Table

### Operation Properties

- **Type**: Write, may be asynchronous.
- **Primary target**: `workflowInstanceId` + explicit `stageId`.
- **Side effects**: Completes the returned task and moves to a stage; may update default layout or flow layout data.
- **Confirmation**: Display the instance, target stage, data diffs, async selection, and all risk flags, then obtain explicit confirmation.

### CLI Call Contract

```bash
sharecrm stage runtime complete-back-to-task \
  --workflowInstanceId "<workflowInstanceId>" \
  --stageId "<stageId>" \
  --noBlockValidate false \
  --async false \
  --data '<json-object>' \
  --flowLayoutEditData '<json-object>'
```

| CLI flag | API Parameter | Type | Business Required | Description |
| --- | --- | --- | --- | --- |
| `--workflowInstanceId` | `workflowInstanceId` | String | ✅ | The stage instance ID to which the returned task belongs. |
| `--stageId` | `stageId` | String | ✅ | The explicit target stage ID to move to after completion. |
| `--noBlockValidate` | `noBlockValidate` | Boolean | Optional | Skip non-blocking validation; defaults to omitted or `false`. |
| `--async` | `async` | Boolean | Optional | Default value is `true`, i.e., asynchronous acceptance; to execute synchronously, you must explicitly pass `false`. |
| `--data` | `data` | JSON object | Optional | Default layout data; structure must come from the confirmed task/form contract. |
| `--flowLayoutEditData` | `flowLayoutEditData` | JSON object | Optional | Flow layout edit data, see table below. |

### `flowLayoutEditData` Data Contract

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | The runtime task ID for saving flow layout data. |
| `objectData` | JSON string | ✅ | Edited main object JSON string. |
| `details` | JSON string | Optional | Edited detail JSON string. |
| `optionInfo` | Object | Optional | Edit extended configuration. |
| `notValidate` | Boolean | Optional | Skip required-field validation; defaults to omitted or `false`. |
| `originalData` | JSON string | Optional | Pre-edit main object data, used for concurrency control. |
| `originalDetails` | JSON string | Optional | Pre-edit detail data, used for concurrency control. |
| `instanceId` | String | Optional | Workflow instance ID. |

Nested JSON strings and the outer JSON must both be correctly escaped. Field structure may only use the form/data actually returned in task details, or values explicitly provided by the user.

### API

```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Task.completeBackToTask(
    workflowInstanceId, stageId, noBlockValidate, async, data, flowLayoutEditData
)
```

### Prerequisites and Safety Defaults

- `workflowInstanceId` and `stageId` are not marked as required in CLI help, but are both business-critical; do not guess the target stage.
- `noBlockValidate=true` is not the default behavior. Only enable it when the user explicitly requests bypassing non-blocking validation, understands the impact, and individually confirms the flag.
- `flowLayoutEditData.notValidate` also defaults to omitted or `false`; do not automatically change it to `true` due to validation failures.
- `async` defaults to `true`, meaning asynchronous acceptance; to execute synchronously, you must explicitly pass `--async false`. Both synchronous and asynchronous choices must be explicitly confirmed in the final preview.

### Asynchrony and Verification

`async=true` returns a `jobId` that only indicates acceptance. This Skill does not provide a corresponding result query command for this operation; do not report `jobId` as completion and do not resubmit. You may read task/instance-related information for best-effort verification; when the terminal state cannot be proven, report "accepted, final status unverified."

### Success and Verification

Only `success == true && code == 'OK'` is considered synchronous success. After execution, use task details or query tasks by instance/stage for read-only verification; do not re-submit writes when verification cannot prove the status.
