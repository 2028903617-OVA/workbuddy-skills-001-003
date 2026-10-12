# BpmTaskCompleteCreateRelateTask

> **CLI**: `sharecrm bpm runtime complete-related-task`
>
> **API**: `Fx.bpm.Task.completeAndCreateTaskData`

## Purpose and Scenario

Complete a `batchAddRelatedObject` business-flow task and save the task data for the newly created related object.

This reference applies only when the task has `executionType == batchAddRelatedObject`. It is not the generic “select or create a related object” completion path: for `addRelatedObject`, use `task-complete-task.md` after the related object is selected or created; do not use this reference.

## API
```groovy
def (Boolean error, Map result, String msg) = Fx.bpm.Task.completeAndCreateTaskData(
    taskId,
    activityId,
    activityInstanceId,
    data,
    executionType,
    opinion,
    objectId,
    nextTaskAssignee,
    addOrReplaceNextTaskAssignee,
    needGetNextTaskInfo,
    ignoreNoBlockValidate
)
```

## Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | String | ✅ | Business flow task ID, used to locate the current task. |
| `activityId` | String | ✅ | Activity node ID in the business flow. |
| `activityInstanceId` | Integer | ✅ | Runtime instance sequence number of the activity node (integer). |
| `data` | Map | ✅ | Business data to save or create; pass a valid JSON object. When `executionType == batchAddRelatedObject`, it must be `{ "entityId": "<related-object API name>", "objectId": "<created related-record ID>" }`. `entityId` must equal `data.relatedEntityId` from the task details, and `objectId` must be the real `_id` (or an explicitly returned record ID) of the newly created related record, never the main-record ID, task ID, business number, or name. |
| `executionType` | String | ✅ | Must be the confirmed `batchAddRelatedObject`; other execution types must not use this reference. |
| `opinion` | String | Optional | The opinion or comment entered when processing the current task. |
| `objectId` | String | Optional | Associated business data record ID. |
| `nextTaskAssignee` | Map | Optional | Next node handler configuration, keys are node IDs and values are user ID arrays, pass a valid JSON object. |
| `addOrReplaceNextTaskAssignee` | Integer | Optional | Next node handler processing method (integer): `1` means add, `0` means replace. |
| `needGetNextTaskInfo` | Boolean | Optional | Whether to return next task info after completion; `true` means return. |
| `ignoreNoBlockValidate` | Boolean | Optional | Whether to ignore non-blocking validation. Do not pass `true` by default; only use after explicit user confirmation. |

## Code Example

```groovy
def taskId = '<confirmed-task-id>'
def activityId = '<confirmed-activity-id>'
def activityInstanceId = 1
def data = [entityId: '<confirmed-related-entity-api-name>', objectId: '<created-related-record-id>']
def executionType = 'batchAddRelatedObject'
def opinion = '<explicit-opinion>'
def objectId = '<confirmed-main-record-id>' // optional API argument; not data.objectId
def nextTaskAssignee = ['<confirmed-node-id>': ['<confirmed-user-id>']]
def addOrReplaceNextTaskAssignee = 0
def needGetNextTaskInfo = true
def ignoreNoBlockValidate = false

def (Boolean error, Map result, String msg) = Fx.bpm.Task.completeAndCreateTaskData(
    taskId, activityId, activityInstanceId, data, executionType, opinion, objectId,
    nextTaskAssignee, addOrReplaceNextTaskAssignee, needGetNextTaskInfo, ignoreNoBlockValidate
)
```

## `batchAddRelatedObject` Execution Flow

This execution type corresponds to the frontend “batch create related object” action. The frontend creates the related record through the related-object form and calls `completeAndCreateTaskData` only after creation succeeds; the backend also saves the task data before completing the task. Execute the following closed sequence:

1. **Get task details (read-only)**: Call `get-task-by-id` from `task-get-task-info.md`. Confirm that the same task has `executionType == batchAddRelatedObject`, then read these fields from the returned `data` object:
   - `relatedEntityId`: related-object API name, used as `object_api_name` for `data record create`.
   - `relatedFieldApiName`: object-reference field API name on the related object that points to the main business record.
   - `objectId`: current main business-record ID. This is the record that the relationship field must reference, not the newly created related-record ID.
   Also read `taskId`, `activityId`, and `activityInstanceId` from the task-level response. Stop if a field is missing, the execution type differs, or an ID's meaning cannot be proven.
2. **Create the related record (write)**: Use `sharecrm data record create --data`, set `object_api_name` to `data.relatedEntityId`, and set `data.relatedFieldApiName` in `object_data` to the current main-record `data.objectId`, together with any other new fields explicitly supplied by the user. For example:
   ```json
   {
     "object_api_name": "<relatedEntityId>",
     "object_data": {
       "<relatedFieldApiName>": "<current-main-objectId>",
       "<writable-related-field>": "<explicit-value>"
     }
   }
   ```
   Extract the real `_id` of the created related record from a successful response (if the CLI explicitly returns `id`, use that documented record-ID field). Stop if no real ID is returned; do not call the completion endpoint. Do not put `relatedFieldApiName` or the `object_data` payload inside the `complete-related-task` `data` envelope.
3. **Assemble data and complete the task (write)**: Set `data` exactly to `{"entityId":"<relatedEntityId>","objectId":"<created-related-record-id>"}` and call `complete-related-task` with the confirmed task/activity identifiers, `executionType=batchAddRelatedObject`, opinion, and next-handler parameters as applicable. Record creation and task completion are one closed business sequence: show one final preview and obtain one explicit confirmation after both steps are ready; after confirmation, create the record first and complete the task only after the new ID is obtained. Stop on a creation failure, missing ID, or completion failure; do not auto-retry or switch to another completion interface.

`addRelatedObject` does not use this flow. The frontend completes that type with `complete-task` and a `relatedObjectId` after selecting or creating an object. Do not rewrite it as `batchAddRelatedObject` or treat an existing related-record ID as the batch-create `data.objectId`.

## Common Validation Constraints

| Constraint | Description |
| --- | --- |
| `taskId` non-empty | Required parameter |
| `activityId` non-empty | Required parameter |
| `activityInstanceId` non-empty | Required parameter |
| `data` non-empty | Required parameter |
| `executionType` non-empty and equal to `batchAddRelatedObject` | Scope of this reference |
| `data.entityId` and `data.objectId` valid | `entityId` comes from task-detail `data.relatedEntityId`; `objectId` comes from the just-created related record's real ID |

## Operation Type

Non-Read

## Primary Target

Business flow task, activity instance, and related data to be created.

## Prerequisites

Obtain task, activity, and activity instance identifiers; confirm `data.relatedEntityId`, `data.relatedFieldApiName`, and the main-record `objectId` from task details, and confirm `executionType == batchAddRelatedObject`. First create the related object with `data record create`, setting its relationship field to the main record; extract the real related-record ID from the successful response; then pass `{"entityId":"<relatedEntityId>","objectId":"<created-related-record-id>"}` as `data` to complete the task. The two writes must run in order after one final preview and confirmation; if creation fails or no ID is returned, do not complete the task. `addRelatedObject` does not use this flow.

## CLI Example

```bash
sharecrm data record create --data '{"object_api_name":"<related-entity-api-name>","object_data":{"<related-field-api-name>":"<current-main-object-id>","<writable-related-field>":"<explicit-value>"}}'
sharecrm bpm runtime complete-related-task --taskId <task-id> --activityId <activity-id> --activityInstanceId <activity-instance-id> --data '{"entityId":"<related-entity-api-name>","objectId":"<created-related-record-id>"}' --executionType batchAddRelatedObject
```

## Confirmation Requirements

Confirm the task, the closed create-related-record-then-complete action, required identifiers, execution type, the main record targeted by the relationship field, creation-field summary, next-handler personnel summary, and creation/completion impact. Do not set `ignoreNoBlockValidate` to true by default; create and complete only in order after one final confirmation.


Follow the write secondary confirmation rules in `../SKILL.md`.
## Verification

Before the second step, verify that `data record create` returned a real related-record ID. After completion, use `task-get-task-info.md`, `task-get-button-by-task-id.md`, or `instance-get-instance-log.md` as needed. Report only actual returned evidence; do not promise that the relationship or final business state was independently verified.
