# BpmGetTaskInfo

> **CLI**: `sharecrm bpm runtime get-task-by-id`
>
> **API**: `Fx.bpm.Task.getTaskInfo`

## Purpose and Scenario

Get task information. Before editing and completing a task, use returned `layoutType` to select the write path.

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.getTaskInfo(
    id,
    applyButtons,
    notGetData,
    includeTaskFeedDetailConfig
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | String | Optional | Business flow task ID, used to locate the task to query. |
| `applyButtons` | Boolean | Optional | Whether to also return available operation buttons when querying the task. |
| `notGetData` | Boolean | Optional | Whether to not return business data when querying the task. |
| `includeTaskFeedDetailConfig` | Boolean | Optional | Whether to include task feed detail display config when querying the task. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| No fixed required parameters | Provide parameters as needed per the business scenario |

> This operation uses `id` as the task ID parameter. Do not substitute a workflow instance ID, business record ID, or lane ID for the task ID.

## Code Example
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.getTaskInfo(
    ""  // id,
    false  // applyButtons,
    false  // notGetData,
    false  // includeTaskFeedDetailConfig
)
```

## Operation Type

Read

## Primary Target

The business flow task identified by the command-specific `id`.

## Prerequisites

Obtain the task ID required by this command; the actual CLI flag is `--id`, not `--taskId`.

## CLI Example

```bash
sharecrm bpm runtime get-task-by-id --id <task-id>
```

## Confirmation Requirements

Read-only operations require no confirmation; confirm the task when the provided `id` is ambiguous.


Follow the read-only boundaries in `../SKILL.md`: may be executed directly, but must not auto-escalate to writes.
## Verification

Check the returned task metadata, form data, and optional buttons. When editing and completing a task, route only from `layoutType` returned for the same task: use `task-update-data-and-complete-task.md` for `defaultLayout`, and `task-edit.md` followed by `task-complete-task.md` for `objectFlowLayout`; stop when the field is missing, has another value, or conflicts. This query does not verify subsequent task or business state changes.
