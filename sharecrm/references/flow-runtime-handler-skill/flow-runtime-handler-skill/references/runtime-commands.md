# Flow Runtime Command Reference

Use this file only to map a confirmed user intent to a ShareCRM runtime command. Run the command's `--help` when flags or payload shape may have changed.

## Contents

- [Command Pattern](#command-pattern)
- [Approval Flow](#approval-flow)
- [BPM Business Flow](#bpm-business-flow)
- [Stage Accelerator](#stage-accelerator)
- [Intent Mapping](#intent-mapping)
- [Execution Notes](#execution-notes)

## Command Pattern

```bash
sharecrm <approval|bpm|stage> runtime <operation> [flags] [--data '<json>']
```

Prefer flat flags for simple IDs and `--data` for nested payloads. Confirm writes before execution.

## Approval Flow

| Intent | Command shape | Required inputs |
| --- | --- | --- |
| Approve | `approval runtime complete --data '{"taskId":"<TASK_ID>","actionType":"agree","objectId":"<RECORD_ID>","opinion":"<COMMENT>"}'` | `taskId`, `objectId` |
| Reject | `approval runtime complete --data '{"taskId":"<TASK_ID>","actionType":"reject","objectId":"<RECORD_ID>","opinion":"<REASON>"}'` | `taskId`, `objectId` |
| Change handler | `approval runtime change-task-handler --taskId <TASK_ID> --persons <USER_IDS>` | `taskId`, comma-separated `persons` |
| Remind | `approval runtime remind --data '{"taskId":"<TASK_ID>","remindPersons":[],"content":"<TEXT>"}'` | `taskId` |
| Add approver | `approval runtime add-extra-node --data '{"taskId":"<TASK_ID>","extraNodeAssignee":[<USER_ID>],"addNodeReason":"<REASON>"}'` | `taskId`, approver IDs, reason |
| Send back | `approval runtime reject-to-before-task --data '{"currentTaskId":"<TASK_ID>","rejectToTaskId":"<TARGET_TASK_ID>","rejectOpinion":"<COMMENT>"}'` | current task, target previous task |
| Retrieve | `approval runtime retrieve --instanceId <INSTANCE_ID> --currentTaskId <TASK_ID> --previousTaskId <PREV_TASK_ID> --retrieveOpinion "<REASON>"` | instance, current task, previous task, reason |
| Cancel | `approval runtime cancel --data '{"instanceId":"<INSTANCE_ID>","triggerType":"1","cancelReason":"<REASON>"}'` | instance or record target, trigger type, reason |
| Reply | `approval runtime reply --data '{"taskId":"<TASK_ID>","replyMessage":{"content":"<TEXT>","feedId":"<FEED_ID>"}}'` | `taskId`, reply message |
| Carbon copy | `approval runtime carbon-copy --data '{"taskId":"<TASK_ID>","opinion":"<COMMENT>"}'` | `taskId` |
| Task detail | `approval runtime get-task-detail --taskId <TASK_ID>` | `taskId` |
| Instance detail | `approval runtime instance-detail --instanceId <INSTANCE_ID>` | `instanceId` |
| Progress | `approval runtime progress --entityId <OBJECT_API_NAME> --dataId <RECORD_ID>` | `entityId`, `objectId/dataId` |

## BPM Business Flow

| Intent | Command shape | Required inputs |
| --- | --- | --- |
| Complete task | `bpm runtime complete-task --data '{"taskId":"<TASK_ID>","opinion":"<COMMENT>"}'` | `taskId` |
| Update and complete | `bpm runtime update-and-complete --data '{"taskId":"<TASK_ID>","entityId":"<OBJECT_API_NAME>","objectId":"<RECORD_ID>","opinion":"<COMMENT>","data":{}}'` | `taskId`, `entityId`, `objectId` |
| Change handler | `bpm runtime change-task-handler --taskId <TASK_ID> --candidateIds <USER_IDS>` | `taskId`, comma-separated `candidateIds` |
| Remind | `bpm runtime remind --data '{"taskId":"<TASK_ID>"}'` | `taskId` |
| Cancel instance | `bpm runtime cancel --data '{"id":"<INSTANCE_ID>","reason":"<REASON>"}'` | `instanceId`, reason |
| Suspend task | `bpm runtime operate-task --data '{"taskId":"<TASK_ID>","type":"suspend"}'` | `taskId` |
| Edit task data | `bpm runtime edit --data '{"taskId":"<TASK_ID>","objectData":"<JSON_PAYLOAD>"}'` | `taskId`, payload |
| Trigger instance | `bpm runtime trigger --id <WORKFLOW_DEF_ID> --objectId <RECORD_ID>` | definition ID, record ID |
| Task metadata | `bpm runtime get-task-by-id --id <TASK_ID>` | `taskId` |
| Instance log | `bpm runtime get-instance-log --workflowInstanceId <INSTANCE_ID>` | `instanceId` |

## Stage Accelerator

| Intent | Command shape | Required inputs |
| --- | --- | --- |
| Fetch instance by record | `stage runtime get-instance-by-object --entityId <OBJECT_API_NAME> --objectId <RECORD_ID>` | `entityId`, `objectId` |
| Advance stage | `stage runtime move-to --workflowInstanceId <INSTANCE_ID> --stageId <CURRENT_STAGE_ID> --comment "<COMMENT>"` | `instanceId`, current `stageId` |

## Intent Mapping

| User intent | Runtime action |
| --- | --- |
| approve, agree | `approval complete(actionType=agree)` |
| reject, disagree | `approval complete(actionType=reject)` |
| finish, complete processing | `bpm complete-task` |
| update then finish | `bpm update-and-complete` |
| transfer, reassign, change handler | `approval/bpm change-task-handler` |
| remind, urge, follow up | `approval/bpm remind` |
| add approver, add signatory | `approval add-extra-node` |
| send back, roll back node | `approval reject-to-before-task` |
| withdraw, retrieve | `approval retrieve` |
| cancel, void | `approval/bpm cancel` |
| hold, suspend | `bpm operate-task(type=suspend)` |
| edit task data | `bpm edit` |
| reply, comment | `approval reply` |
| carbon copy, CC | `approval carbon-copy` |
| advance stage | `stage move-to` |
| check progress/detail/log | matching read-only detail command |

## Execution Notes

- Task-query results often expose the task identifier as `_id`; verify before using it.
- Approval approve/reject both use `approval runtime complete`; `actionType` controls the result.
- Business completion uses `bpm runtime complete-task`, not approval `complete`.
- Approval handler changes use `--persons`; BPM handler changes use `--candidateIds`.
- Re-query after writes to verify task state, instance state, progress, or audit log.
- Execute multiple targets one by one with per-target result feedback.
