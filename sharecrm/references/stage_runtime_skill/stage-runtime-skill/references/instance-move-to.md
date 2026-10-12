# Move Instance to Specified Stage

> **CLI**: `sharecrm stage runtime move-to`

## Operation Type

Non-Read

## Primary Target

`move-to`: Move instance to specified stage

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. When this `move-to` is an explicit user-requested rollback to an earlier stage, first execute `instance-back-to-validate.md`; stop and report the result if it fails, and only after it passes may you show the final preview for this operation. A successful validation is not execution authorization. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime move-to --workflowInstanceId "<workflow-instance-id>" --stageId "<target-stage-id>" --comment "<confirmed-comment>" --ignoreSkipInNoBlockValidate false --async false
```

## Confirmation Requirements

Confirm the exact target stage, comment, and impact scope before submitting; for a rollback, `instance-back-to-validate.md` must already have passed; do not guess the previous or next stage.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Verify the response and confirm the target status with a read-only query; request acceptance does not mean final success. When using `--async true`, only this operation's `jobId` can be queried with `query-move-to-result`.

### Retained API, Groovy Background, and Parameter Table

### Operation Properties

- **Type**: Write, may be asynchronous.
- **Primary target**: `workflowInstanceId` + explicit `stageId`.
- **Side effects**: Moves the stage instance to the target stage, which may trigger terminal/subsequent logic.
- **Confirmation**: Display the instance, target stage, comment, impact scope, and risk flags before confirming.

### CLI Call Contract

```bash
sharecrm stage runtime move-to \
  --workflowInstanceId "<workflowInstanceId>" \
  --stageId "<stageId>" \
  --comment "<comment>" \
  --ignoreSkipInNoBlockValidate false \
  --async false
```

| CLI flag | API Parameter | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `--workflowInstanceId` | `workflowInstanceId` | String | ✅ | Stage accelerator instance ID. |
| `--stageId` | `stageId` | String | ✅ | Explicit target stage ID. |
| `--comment` | `comment` | String | Optional | Move comment. |
| `--ignoreSkipInNoBlockValidate` | `ignoreSkipInNoBlockValidate` | Boolean | Optional | Skip non-blocking validation for entering the stage; defaults to omitted or `false`. |
| `--async` | `async` | Boolean | Optional | Asynchronous execution; defaults to omitted or `false`. |

### Prerequisites and Safety Defaults

`stageId` must be explicitly provided by the user or uniquely determined from a read-only result; do not guess "the previous stage." `ignoreSkipInNoBlockValidate=true` is only allowed when the user explicitly requests it, understands the impact, and individually confirms it.

### Asynchrony and Verification

The `jobId` returned by `async=true` is only used with `query-move-to-result` for this operation:

```bash
sharecrm stage runtime query-move-to-result --jobId "<jobId>"
```

Poll according to the `queryIntervalSecond` provided in the response (if any); a polling `success=false` may just mean it is not yet complete. Do not re-submit move-to before the result reaches a terminal state. Only a terminal state with `success == true && code == 'OK'` may be reported as success; otherwise report failure/unverified status.

### API

```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Instance.moveToWithTerminal(
    workflowInstanceId, stageId, comment, ignoreSkipInNoBlockValidate, async
)
```
