# Reactivate Instance

> **CLI**: `sharecrm stage runtime reactive`

## Operation Type

Non-Read

## Primary Target

`reactive`: Reactivate instance

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime reactive --workflowInstanceId "<workflow-instance-id>" --activeStageId "<active-stage-id>" --taskData '{"field":"value"}' --ignoreSkipInNoBlockValidate false --async false
```

## Confirmation Requirements

`reactive-validate` must be performed first on the same `workflowInstanceId`; passing validation does not mean reactivation is done. Confirm the instance, activation stage, and task data before submitting.

Secondary confirmation follows the "Non-Read Operation Confirmation and Safety Boundaries" in `../SKILL.md`.
## Verification

Check whether the response is successful and verify the target status with a read-only query; do not treat request acceptance as final success. When using `--async true`, acceptance or `jobId` does not represent final success.

### Retained API, Groovy Background, and Parameter Table

### Operation Properties and CLI Contract

- **Type**: Write, may be asynchronous; primary target is `workflowInstanceId` + `activeStageId`. `instance-reactive-validate.md` must be completed first; passing validation does not authorize activation.

```bash
sharecrm stage runtime reactive \
  --workflowInstanceId "<workflowInstanceId>" --activeStageId "<activeStageId>" \
  --taskData '<json-object>' --ignoreSkipInNoBlockValidate false --async false
```

`taskData` may contain `updateJson` (JSON string), `originalData` (JSON string), `optionInfo` (object), `ignoreNonBlocking`, `removeVersion`. The latter two and `ignoreSkipInNoBlockValidate` all default to omitted or `false`; any `true` requires the user to explicitly state the impact and confirm a second time.

### Asynchrony and Verification

The `jobId` from `async=true` cannot be queried with `query-move-to-result`; do not report success or resubmit. Synchronous success requires only `success == true && code == 'OK'`; verify with read-only queries by object/task when available, and report unverified when the final status cannot be proven.