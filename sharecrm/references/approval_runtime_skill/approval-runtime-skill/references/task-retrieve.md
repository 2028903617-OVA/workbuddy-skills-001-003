# Retrieve Approval Task for Reconsideration

> **CLI**: `sharecrm approval runtime retrieve`
>

## Purpose and Scenario

Retrieve an already-submitted approval task from the current handler and return it to the previous step for reconsideration.

## Operation Boundaries and Execution Rules

Retrieval changes the approval instance status and may affect the previous task's opinion. First execute `task-get-task-extra-data.md` with `buttonType=RETRIEVE_BUTTON`, obtain a non-empty `previousTaskId` and read `showDeleteOpinion` from the response for the same `instanceId` and `currentTaskId`, then execute retrieve-check for eligibility. The retrieval-check response may be empty and cannot provide or confirm `previousTaskId`. These read results are not execution authorization; show the final preview only after confirming the target, whether to delete the previous opinion, and the retrieval comment. After execution, query according to this reference's verification rules.


## Operation Type

Non-Read

## Primary Target

Current approval task and retrievable preceding task

## Prerequisites

Confirm the required IDs from a trusted current context or an appropriate read-only query. Do not pass `ignoreNoBlockValidate`, `notValidate`, or `removeVersion` by default. You must first query ExtraData with the same `instanceId`, `currentTaskId`, and `buttonType=RETRIEVE_BUTTON` and obtain a non-empty `previousTaskId`, then execute retrieve-check. `previousTaskId` may only come from that ExtraData, never from retrieve-check, any completed task in the instance, task name, order, or creation time. When `showDeleteOpinion == true`, the user must explicitly choose whether to delete the previous opinion; otherwise omit `deletePreviousOpinion`. Stop and do not display a write preview when either prerequisite query fails, returns conflicting facts, or `previousTaskId` is missing.

## CLI Example

```bash
sharecrm approval runtime retrieve --instanceId <instance-id> --currentTaskId <current-task-id> --previousTaskId <previous-task-id-from-retrieve-button-extra-data> --retrieveOpinion "<reason>"
```

## Confirmation Requirements

Follow the Non-Read secondary confirmation flow in `../SKILL.md`. Do not add, guess, or bypass validation beyond the parameters explicitly listed in this reference.

## Verification

When verifying only instance state, you must directly run the instance query in "Lightweight State Verification" in `../SKILL.md` and must not call `instance-detail`, `get-task-detail`, or `progress`; when only listing current in-progress tasks after retrieval, query active tasks by instance and must not call `get-task-detail`. Query `instance-detail`, `get-task-detail`, or `progress` only when the user explicitly asks to verify complete post-retrieval instance state, routing, historical opinions, or approval activity feeds. Do not promise final business status when evidence is insufficient.

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `instanceId` | String | ✅ | The approval flow instance ID. |
| `currentTaskId` | String | ✅ | The current approval task ID. |
| `previousTaskId` | String | ✅ | The preceding approval task ID specified for retrieval; only use the non-empty value returned by `RETRIEVE_BUTTON` ExtraData for the same task. |
| `deletePreviousOpinion` | Boolean | Optional | Pass only when ExtraData has `showDeleteOpinion == true` and the user explicitly chooses it; otherwise omit it. |
| `retrieveOpinion` | String | ✅ | The reason or comment filled in when retrieving the approval. |

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `currentTaskId` non-empty | Required parameter |
| `previousTaskId` non-empty | Required parameter |
| `instanceId` non-empty | Required parameter |
| `retrieveOpinion` non-empty | Required parameter |
