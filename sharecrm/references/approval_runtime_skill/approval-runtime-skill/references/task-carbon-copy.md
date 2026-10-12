# Mark Approval Carbon-Copy Task as Read

> **CLI**: `sharecrm approval runtime carbon-copy`
>

## Purpose and Scenario

Mark the current user's received approval carbon-copy task as read. This operation does not add carbon-copy recipients, send anything to other people, or modify the approval flow's carbon-copy scope.

## Operation Boundaries and Execution Rules

Use this reference only to mark a task as read. First confirm the current user's target approval task and `replyMessage.feedId`; do not ask for, guess, or pass recipients, carbon-copy scope, or visible scope. The actual execution must pass a non-empty `replyMessage` through `--data`: for mark-as-read only, pass empty `content`, empty `attachments`, and fixed `source: 1`. Do not pass `opinion` or use the flat `--replyMessage` flag. When the user wants to post an approval reply, use `task-reply.md` instead; do not attach reply content or files to this operation.


## Operation Type

Non-Read

## Primary Target

Read status of the current user's received approval carbon-copy task

## Prerequisites

Confirm `taskId` and the `feedId` for the current carbon-copy task from trusted current context or an appropriate read-only query. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default. When `feedId` is missing, prefer `CARBON_BUTTON` ExtraData for the same task or an approval activity explicitly selected by the user; do not read `get-task-detail` by default for this purpose. When multiple feed candidates exist, the user must select one and you must not guess. The complete request body and a non-empty `replyMessage` must be passed through `--data`; do not pass `opinion` or split the nested `replyMessage` into a flat flag. For mark-as-read only, always pass `content: ""`, `attachments: []`, and `source: 1`.

## CLI Example

```bash
sharecrm approval runtime carbon-copy --data '{"type":"approvalflow","taskId":"<task-id>","instanceId":"<instance-id>","replyMessage":{"feedId":"<trusted-feed-id>","content":"","attachments":[],"source":1}}'
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. The final preview shows only the target task, instance context, target feed, and mark-as-read state impact; do not show recipients, carbon-copy scope, or outbound body content. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

Check the write response; report that the current approval carbon-copy task was marked as read only when `success == true && code == 'OK'`. Do not call `get-task-detail` for default post-write verification; execute it as an independent read only when the user explicitly asks to view approval activity.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `type` | String | Optional | Approval-flow compatibility field; the example uses fixed value `approvalflow`. This field does not identify recipients or carbon-copy scope. |
| `taskId` | String | ✅ | The approval task ID used to locate the current task; pass it as a `--data` request-body field. |
| `instanceId` | String | Optional | Trusted approval flow instance ID. Pass it in the `--data` request body when current context provides it, but it cannot replace `taskId` or `replyMessage.feedId`. |
| `replyMessage` | Map | ✅ | The target feed object for mark-as-read. Pass it in the `--data` request body with `feedId`, `content`, `attachments`, and `source`. For mark-as-read only, pass empty `content` and `attachments: []`; `source` is always `1`. Do not use the flat `--replyMessage` flag. |

## `replyMessage` Format

```json
{
  "feedId": "<trusted-feed-id>",
  "content": "",
  "attachments": [],
  "source": 1
}
```

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |
