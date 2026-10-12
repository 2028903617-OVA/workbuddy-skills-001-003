# Query move-to Asynchronous Task

> **CLI**: `sharecrm stage runtime query-move-to-result`

## Operation Type

Read

## Primary Target

`query-move-to-result`: Query move-to asynchronous task

## Prerequisites

Reuse confirmed target IDs, current status, and parameter sources; only use read-only queries to confirm when the target, required fields, or status are missing, ambiguous, or conflicting, when the user requests a refresh, or when the service rejects the current status. Risk flags default to omitted or `false`.

## CLI Example

```bash
sharecrm stage runtime query-move-to-result --jobId "<move-to-job-id>"
```

## Confirmation Requirements

Read-only query, no write confirmation needed; only the `jobId` returned by `move-to --async true` may be queried.

Read-only operations can be executed directly without secondary confirmation; read or asynchronous result reads must not automatically escalate to non-read-only operations.
## Verification

Record the read-only result; the result is only used to identify or validate the target and cannot serve as authorization for executing a write.

### Retained API, Groovy Background, and Parameter Table

### Operation Properties

- **Type**: Read-only asynchronous result query.
- **Primary target**: The `jobId` returned by `move-to --async true`.
- **Boundaries**: Only queries asynchronous move results; do not substitute `jobId` from other operations, and do not trigger new writes.

### CLI Call Contract

```bash
sharecrm stage runtime query-move-to-result --jobId "<jobId>"
```

| CLI flag | API Parameter | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `--jobId` | `jobId` | String | ✅ | The background task ID returned by the move-to acceptance response. |

### Polling Rules

- `jobId` must be non-empty to query. Preferentially follow the `queryIntervalSecond` in the response; when absent, do not guess a fixed interval or poll indefinitely — report waiting for verification or let the user decide whether to continue.
- `success=false` may indicate processing is still in progress; do not immediately judge it as a business failure, and do not re-submit move-to.
- Only a terminal state with `success == true && code == 'OK'` may be reported as move success; explicit failure codes/error messages should be reported as-is as failure.

### API

```groovy
def (Boolean error, Map result, String msg) = Fx.stage.Instance.queryMoveToResult(jobId)
```