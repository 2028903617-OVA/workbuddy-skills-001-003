# BpmTaskRemind

> **CLI**: `sharecrm bpm runtime remind`
>
> **API**: `Fx.bpm.Task.remind`

## Purpose and Scenario

Remind

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.remind(
    taskId,
    content,
    remindPersons
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | Business flow task ID, used to locate the current task. |
| `content` | String | Optional | The reminder content sent to the person being reminded. |
| `remindPersons` | List<String> | Optional | Array of user IDs to receive the reminder notification. When specified, pass it in the complete JSON request body through `--data`, e.g. `{"remindPersons":["<user-id>"]}`; do not use a flat flag. When omitted, target personnel is determined by the current business rules. |

## Code Example

```groovy
def taskId = '<confirmed-task-id>'
def content = '<explicit-reminder-content>'
def remindPersons = ['<confirmed-user-id>']

def (Boolean error, Map result, String msg) = Fx.bpm.Task.remind(
    taskId, content, remindPersons
)
```

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |

> `remindPersons` specifies the reminder recipients, pass a list of user ID strings; by default the current task handler is reminded. Do not pass names, task IDs, or workflow instance IDs. Put the array in the `--data` JSON request body, e.g. `{"remindPersons":["1000","1003","1001"]}`; do not use a flat flag or comma-separated string.

## Operation Type

Non-Read

## Primary Target

Business flow task and reminder recipients.

## Prerequisites

Obtain the task ID; collect explicit reminder content; verify the user IDs of recipients when specified.

## CLI Example

```bash
sharecrm bpm runtime remind --data '{"taskId":"<task-id>","content":"<reminder-content>","remindPersons":["<user-id>"]}'
```

## Confirmation Requirements

Confirm the task, remind action, `taskId`, message content, and recipient personnel summary. When no recipient is specified, clarify that the server-side business rules determine it.


Follow the write secondary confirmation rules in `../SKILL.md`.
## Verification

Use `task-get-task-info.md` to check task evidence only when available. A successful command response does not mean the message was delivered or acknowledged by the recipient.
