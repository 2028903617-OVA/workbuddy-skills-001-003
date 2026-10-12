# Get Approval Task Buttons

> **CLI**: `sharecrm approval runtime get-task-buttons`
>

## Purpose and Scenario

Query the operation buttons currently available for a specified approval task.

## Operation Boundaries

This is a read-only query. It is only used to locate or understand approval instances, tasks, buttons, forms, progress, rejectable targets, or retrieval conditions; it must not auto-complete, edit, reject, retrieve, withdraw, cancel, remind, transfer, add sign-off nodes, or retry based on returned results.


## Operation Type

Read

## Primary Target

Available buttons for an approval task

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Only use authorized, non-sensitive identifiers.

## CLI Example

```bash
sharecrm approval runtime get-task-buttons --data '{"taskIds":["<task-id>"]}'
```

## Confirmation Requirements

May be executed directly; must not auto-escalate to Non-Read operations based on results.

## Verification

Check the returned data; it is only query evidence and is insufficient to confirm the final business status.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskIds` | List<String> | Recommended required | A list of approval task IDs. Pass the complete JSON request body through `--data`, for example `{"taskIds":["<task-id>"]}`. Do not use the flat `--taskIds` flag because it treats the array as a string. This operation must not use `--taskId`. When `taskIds` is omitted, all task buttons are queried; this is only for global button verification scenarios. Normal operations must pass the target task ID. |

When providing multiple task IDs, put all IDs into the `taskIds` array of one `--data` JSON body; do not change `--taskIds` to the singular `--taskId`.

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| None | No required parameters |
