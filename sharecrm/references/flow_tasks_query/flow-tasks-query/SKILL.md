---
name: "flow-tasks-query"
description: "Used when the user's request involves pending approval flow, pending business flow, pending stage propeller, pending approval, my to-do, and similar scenarios"
apiName: "flow_tasks_query"
---
# Pending Task Query — Approval Flow / Business Flow / Stage Propeller

When the user mentions pending/to-do approval flow tasks, business flow tasks, or stage propeller tasks, directly execute the corresponding SQL query.

## Core Constraints

- **SQL succeeds but returns 0 records**: Immediately state "Record count: 0" and ask whether to adjust conditions. Never change conditions and retry.
- **SELECT no more than 20 fields**, detail queries return at most 50 records.
- **Query only, no writes**: Only SELECT; reject INSERT/UPDATE/DELETE.

## Process

```
User asks → Determine task type → Get current user info (parse "me" ID)
       → Construct SQL → Execute corresponding command → Format output
```

## Quick Commands

| Command | Purpose | Notes |
| ----------------------------------------------------------- | -------------------------- | ---- |
| `sharecrm approval runtime my-approval-tasks --sql "<SQL>"` | Query pending approval flow tasks | - |
| `sharecrm bpm runtime my-bpm-tasks --sql "<SQL>" --raw`     | Query to-do business flow tasks | **Must add `--raw`** to get `objectApiName` and `objectDataId` |
| `sharecrm stage runtime my-stage-tasks --sql "<SQL>"`       | Query to-do stage propeller tasks | - |

### Determine Task Type

| Keywords | Task Type | Query Command |
| ---------------------------------------------- | ------------------ | --------------------------------------------- |
| Approval flow, pending approval, approval to-do, approval task, needs my approval | Approval flow task | `sharecrm approval runtime my-approval-tasks` |
| Business flow, process to-do, business process, business flow task | Business flow task | `sharecrm bpm runtime my-bpm-tasks` |
| Stage propeller, advance task, stage task, advance to-do | Stage propeller task | `sharecrm stage runtime my-stage-tasks` |
| To-do task, my to-do (no specific type) | Query all three types | Execute all three commands simultaneously |

### Construct SQL and Execute

Get the current user ID from the current context, and execute the corresponding command:

**Approval Flow:**

```bash
sharecrm approval runtime my-approval-tasks \
  --sql "SELECT _id, name, create_time, state, object_api_name, object_data_id FROM ApprovalTaskObj WHERE current_candidate_ids LIKE '%<userId>%' AND state = 'in_progress' ORDER BY create_time DESC LIMIT 50"
```

**Business Flow (must add `--raw`):**

```bash
sharecrm bpm runtime my-bpm-tasks \
  --sql "SELECT _id, name, create_time, state, objectApiName, objectDataId FROM BpmTask WHERE current_candidate_ids LIKE '%<userId>%' AND state = 'in_progress' ORDER BY create_time DESC LIMIT 50" --raw
```

> ⚠️ Business flow queries **must add `--raw`**, otherwise `objectApiName` and `objectDataId` will not be returned.

**Stage Propeller:**

```bash
sharecrm stage runtime my-stage-tasks \
  --sql "SELECT _id, name, create_time, state FROM StageTaskObj WHERE current_candidate_ids LIKE '%<userId>%' AND state = 'in_progress' ORDER BY create_time DESC LIMIT 50"
```

### Output Format

#### Table Columns

| Column | Source Field | Notes |
|------|----------|------|
| # | Sequence number | Starting from 1 |
| Subject | `name` | Use the raw value of the `name` field |
| Creation Time | `create_time` | - |
| Business Record | `object_api_name` + `object_data_id` (approval flow) / `objectApiName` + `objectDataId` (business flow) | Merged into one column, displaying the object's display name with a clickable link |

#### Business Record Link Format

```
https://www.fxiaoke.com/XV/UI/Home?noheader=1&notopnav=1#objdetail/{objectApiName}/{objectDataId}
```

- Approval flow: `object_api_name` and `object_data_id`
- Business flow: `objectApiName` and `objectDataId` (from `--raw` return)

##### Business Record Name Rules

The business record column displays the **name of the associated record itself**, not the object description name. How to obtain it:

- **Business flow**: The `objectApiName__r` returned by `--raw` is already the display name of the associated record (e.g., "R&D Online Inspection Work Order"), use it directly.
- **Approval flow**: `object_api_name` returns the apiName, and `object_data_id` is the record ID. You need to query the associated record via `sharecrm data record get-by-id --object_api_name <apiName> --id <recordId>`, and use the returned `name` or `display name` field as the display name; if neither exists, use the raw value of `object_data_id`.

#### Display Rules

- Display grouped by task type: 🔴 Approval flow to-do → 🟡 Business flow to-do → ⚪ Stage propeller to-do
- Each group first shows the record count, then displays the table
- Detail type: output `Record count: N`, display the latest 50 records in the table. When no results, output `Record count: 0` and explain that nothing was found.
- Statistics type (e.g., "how many are there"): directly output the number; never display non-existent details.
- First provide a brief interpretation of the results, then display the details.
- Do not display the user ID in the output; use natural language like "you" instead.
- Finally provide a summary line: Approval flow N items + Business flow N items + Stage propeller N items.

#### Example Output

```
## 📊 To-Do List (Username · Date)

### 🔴 Approval Flow To-Do — N items

| # | Subject | Creation Time | Business Record |
|---|------|----------|----------|
| 1 | xxx | 2026-xx-xx | [Object Display Name](https://www.fxiaoke.com/XV/UI/Home?noheader=1&notopnav=1#objdetail/xxx/xxx) |

### 🟡 Business Flow To-Do — N items

| # | Subject | Creation Time | Business Record |
|---|------|----------|----------|
| 1 | xxx | 2026-xx-xx | [Object Display Name](https://www.fxiaoke.com/XV/UI/Home?noheader=1&notopnav=1#objdetail/xxx/xxx) |

### ⚪ Stage Propeller To-Do — N items

---

**Summary**: Approval flow N items + Business flow N items + Stage propeller N items.
```

## Runtime Context

- `currentDateTime`: Parse relative time like "today", "this week", "last three days"
- `CurrentEmployeeInfo`: Parse current person semantics like "me", "what I'm responsible for", "assigned to me", includes current user name and user ID
- If the user explicitly provides specific time or specific personnel, use the user's input

## Query Result Handling

| Scenario | Behavior |
| ------------------- | ------------------------------------------------- |
| SQL error | Adjust based on error message and retry |
| SQL succeeds but returns 0 records | State "Record count: 0", ask whether to adjust. **Never** change conditions and retry |

## Common Mistakes

| Mistake | Correct Approach |
| ------------------------ | ------------------------------------------------------------ |
| Writing "me" as a person's name directly | Use current user info to get the ID |
| Using the wrong command | Approval flow uses `my-approval-tasks`, business flow uses `my-bpm-tasks`, stage propeller uses `my-stage-tasks` |
| Querying all fields (SELECT *) | Only select fields the user cares about |
| Changing conditions and re-querying after empty results | Stop immediately and ask the user |
| Not adding `--raw` to business flow query | **Must add `--raw`**, otherwise `objectApiName` and `objectDataId` won't be available |
| Wrong business record link format | Correct format: `https://www.fxiaoke.com/XV/UI/Home?noheader=1&notopnav=1#objdetail/{objectApiName}/{objectDataId}` |