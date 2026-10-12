# BpmGetInstanceForm

> **CLI**: `sharecrm bpm runtime get-instance-form`
>
> **API**: `Fx.bpm.Instance.getInstanceForm`

## Purpose and Scenario

Get a business flow instance-level form of a confirmed type. This is not a current-task-form API and must not be used to locate a task, read current-task writable fields, or derive `taskId`, `workflowId`, or `laneId`.

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Instance.getInstanceForm(
    workflowInstanceId,
    instanceFormType
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `workflowInstanceId` | String | Optional | Business flow instance ID. A confirmed instance ID is required when retrieving a particular instance form. |
| `instanceFormType` | String | Optional | Instance-form type to retrieve. Use only a value explicitly specified by the user or verified as supported; do not guess that it is the current-task, cancellation, or termination form. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| Query an instance form of a particular type | Confirm both `workflowInstanceId` and `instanceFormType` |
| Task-edit prerequisite query | Do not use this API; use a task-query path that uniquely identifies `taskId` |

## Code Example
```groovy
def workflowInstanceId = '<confirmed-workflow-instance-id>'
def instanceFormType = '<confirmed-instance-form-type>'

def (Boolean error, Map result, String msg) = Fx.bpm.Instance.getInstanceForm(
    workflowInstanceId, instanceFormType
)
```

## Operation Type

Read

## Primary Target

A business flow instance-level form explicitly requested by the user.

## Prerequisites

The user explicitly requests an instance form; confirm the matching workflow instance ID and supported instance-form type. Stop when the type is not confirmed; do not interpret "instance form" as the current task form.

## CLI Example

```bash
sharecrm bpm runtime get-instance-form --workflowInstanceId <workflow-instance-id> --instanceFormType <instance-form-type>
```

## Confirmation Requirements

Read-only operations require no confirmation; only confirm when the identifier is ambiguous.


Follow the read-only boundaries in `../SKILL.md`: may be executed directly, but must not auto-escalate to writes.
## Verification

Check the returned form and fields of the specified instance type. An empty response only means this instance did not return that `instanceFormType`; it does not prove that the current task is absent, its form is empty, or the task is not editable.
