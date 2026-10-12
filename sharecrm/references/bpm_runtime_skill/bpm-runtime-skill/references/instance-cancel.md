# BpmInstanceCancel

> **CLI**: `sharecrm bpm runtime cancel`
>
> **API**: `Fx.bpm.Instance.cancelInstance`

## Purpose and Scenario

Cancel an instance

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Instance.cancelInstance(
    id,
    reason,
    data,
    removeVersion,
    originalData,
    optionInfo
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | String | ✅ | Business flow instance ID (workflowInstanceId). Can be obtained via `instance-get-instances-by-object.md` by querying with the business record `objectId`; the `id` field in the returned list is the business flow instance ID. |
| `reason` | String | Optional | The reason for canceling the business flow instance, explicitly provided by the user. |
| `data` | Map | Optional | Business data to save or create, pass a valid JSON object. |
| `removeVersion` | Boolean | Optional | Whether to remove version validation info; do not pass `true` by default, only use per explicit business rules. |
| `originalData` | String | Optional | Original business data JSON string before update, used for change or version validation. |
| `optionInfo` | Map | Optional | Additional option info required for task processing, pass a valid JSON object. |

## Code Example

```groovy
def id = '<confirmed-record-unique-id>'
def reason = '<explicit-cancel-reason>'
def data = ['<writable-field-api-name>': '<explicit-user-provided-new-value>']
def removeVersion = false
def originalData = '{"<writable-field-api-name>":"<verified-original-value>"}'
def optionInfo = ['<confirmed-option-key>': '<confirmed-option-value>']

def (Boolean error, Map result, String msg) = Fx.bpm.Instance.cancelInstance(
    id, reason, data, removeVersion, originalData, optionInfo
)
```

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `id` non-empty | Required parameter |

## Operation Type

Non-Read

## Primary Target

Business flow instance ID (workflowInstanceId) and the associated business flow instance.

## Prerequisites

Confirm that `id` is the business flow instance ID (workflowInstanceId); do not substitute a business flow definition ID, task ID, or business record ID. If the user only provides a business record ID, first query via `instance-get-instances-by-object.md` to obtain the instance ID. Collect the user's explicit cancel reason and business data changes.

## CLI Example

```bash
sharecrm bpm runtime cancel --id <record-unique-id> --reason "<reason>"
```

## Confirmation Requirements

Confirm the target, cancel action, business flow instance ID (`id`), reason, and the instance-wide termination impact. Summarize all submitted data fields; do not set `removeVersion` to true by default.


Follow the write secondary confirmation rules in `../SKILL.md`.
## Verification

Use `instance-get-instance-log.md` when the corresponding workflow instance ID is available. Only report returned results and log evidence; do not promise the business state is verified.