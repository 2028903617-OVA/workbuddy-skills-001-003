# Delete Approval Reply

> **CLI**: `sharecrm approval runtime delete-reply`
>

## Purpose and Scenario

Delete reply content in a specified approval task or approval activity feed.

## Operation Boundaries and Execution Rules

Deleting a reply removes the specified approval communication content. First confirm the reply to delete and its owning task, instance, or activity feed; do not guess `replyId` from text content. After execution, check the server write response and do not read details by default.


## Operation Type

Non-Read

## Primary Target

Approval reply

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default. You must confirm a trusted `replyId` and its ownership; deletion is irreversible. When trusted `replyId` or ownership is missing, task details or the approval activity feed may be read before writing to identify one reply; when multiple candidates exist, the user must select and you must not guess.

## CLI Example

```bash
sharecrm approval runtime delete-reply --replyId <trusted-reply-id> --taskId <task-id> --instanceId <instance-id> --feedId <feed-id>
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

Check the write response; report that the reply was deleted only when `success == true && code == 'OK'`. Do not call `get-task-detail` for default post-write verification. Execute it as an independent read only when the user explicitly asks to view remaining replies, confirm that the reply is absent from the activity feed, or view the approval activity feed.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `replyId` | String | Optional | The approval reply ID to delete. |
| `taskId` | String | Optional | The approval task ID, used to locate the current approval task. |
| `instanceId` | String | Optional | The approval flow instance ID. |
| `feedId` | String | Optional | The approval activity feed ID, used to locate the reply to delete. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| None | No required parameters |
