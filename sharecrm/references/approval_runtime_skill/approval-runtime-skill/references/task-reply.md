# Reply to Approval Comment

> **CLI**: `sharecrm approval runtime reply`
>

## Purpose and Scenario

Post a reply message under a specified approval task or approval activity feed.

## Operation Boundaries and Execution Rules

Replying posts an approval communication message. First confirm the target instance, task, and the `feedId` and body in `replyMessage`; when the user does not mention attachments, pass `attachments: []` directly and do not ask about attachments. `source` is always `1` and must not be requested, guessed, or replaced. `replyMessage` is a nested Map and must be sent in the complete request body through `--data`; do not use the `--replyMessage` flat flag. Do not automatically send a reply after viewing approval details.


## Operation Type

Non-Read

## Primary Target

Reply in an approval task or instance

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default. This operation is considered outbound; the target feed and body in `replyMessage` must be confirmed. When trusted `feedId` is missing, task details or the approval activity feed may be read before writing to identify one target feed; when multiple candidates exist, the user must select and you must not guess. When the user does not mention attachments, pass `attachments: []` directly; do not treat attachments as a fact to collect or confirm. `source` is fixed at `1`. `--data` must contain the complete request body; do not split the nested `replyMessage` into flat flags.

## CLI Example

```bash
sharecrm approval runtime reply --data '{"instanceId":"<instance-id>","taskId":"<task-id>","replyMessage":{"feedId":<feed-id>,"content":"<confirmed-content>","attachments":[],"source":1}}'
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

Check the write response; report that the reply was published only when `success == true && code == 'OK'`. Do not call `get-task-detail` for default post-write verification. Execute it as an independent read only when the user explicitly asks to view the just-published reply or approval activity feed.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `instanceId` | String | Optional | The approval flow instance ID; pass it as a field in the `--data` request body. |
| `taskId` | String | Optional | The approval task ID used to locate the current approval task; pass it as a field in the `--data` request body. |
| `replyMessage` | Map | ✅ | The reply message object; pass it as a field in the `--data` request body, using valid JSON in the format below. |

`--data` must wrap the entire request body. Do not pass `--replyMessage`, because flat flags do not support this nested Map.

## `replyMessage` Format

```json
{
  "feedId": 100002717,
  "content": "<explicit-user-provided-reply-content>",
  "attachments": [],
  "source": 1
}
```

| Field | Type | Description |
| --- | --- | --- |
| `feedId` | Number | The approval activity feed ID to reply to. |
| `content` | String | The reply body explicitly provided by the user. |
| `attachments` | Array | Attachment array; when the user does not mention attachments, pass `[]` directly and do not ask. |
| `source` | Number | Fixed value: `1`. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `replyMessage` non-empty | Required parameter |
