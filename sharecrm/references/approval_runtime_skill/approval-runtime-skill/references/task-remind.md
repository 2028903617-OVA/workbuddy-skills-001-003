# Send Approval Task Reminder

> **CLI**: `sharecrm approval runtime remind`
>

## Purpose and Scenario

Send a reminder message to the handler of a specified approval task.

## Operation Boundaries and Execution Rules

Reminders send notifications to specified personnel. `remindPersons` must be a confirmed list of user IDs; do not pass names, task IDs, or instance IDs; confirm the message content and recipients first, and avoid duplicate sending.


## Operation Type

Non-Read

## Primary Target

Reminder recipients for a specified approval task

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default.

## CLI Example

```bash
sharecrm approval runtime remind --data '{"taskId":"<task-id>","content":"<reminder-content>","remindPersons":["<user-id>"]}'
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

Check the write response; report that the reminder was initiated only when `success == true && code == 'OK'`. Do not call `get-task-detail` for default post-write verification; it cannot reliably prove that recipients received or read the reminder. Execute it as an independent read only when the user explicitly asks to view reminder activity.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | The approval task ID, used to locate the current approval task. |
| `content` | String | Optional | The body of the reminder message. |
| `remindPersons` | List | ✅ | Specifies the persons to remind; defaults to reminding the current approval handler. Pass the user ID string array in the complete JSON request body through `--data`, e.g. `{"remindPersons":["10001"]}`; do not use a flat flag or pass names, task IDs, or approval instance IDs. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `remindPersons` non-empty | Required parameter |
| `taskId` non-empty | Required parameter |
