# Probing Tools

Read this reference when semantic grounding is complete but execution still
lacks object, field, relation, record, or value evidence.

## General Probing Rules

Use probing only to fill missing execution evidence after semantic grounding.
If the missing problem is still semantic interpretation, return to
`semantic-interpreter` with updated `semanticContext` instead of switching to
side tools.

- Probe only for missing execution evidence such as object evidence, field evidence, value-binding evidence, or relation evidence.
- Use `sharecrm data describe identify-with-describe` only when object candidates are already narrow and current evidence still cannot stably decide the object or field semantics.
- Use `sharecrm data describe get` only when the object is already sufficiently clear and execution still lacks field metadata, object-level rules, or few-shot evidence that is not already evidenced in the current run or preserved context.
- Use describe only after the object API name is already semantically confirmed. Describe may confirm exact field API names under that confirmed object, but must not be used to guess the object itself or to invent execution identifiers.
- Use `sharecrm data record query-by-name` or `sharecrm data record query-id-by-name` only when execution needs reliable name-based record evidence or exact id binding.
- Use `sharecrm data record get-by-id` only when a reliable id already exists and execution still needs record-detail evidence.
- Probe only for the minimum evidence required to execute reliably; do not use these tools for exploratory expansion or extra validation once the execution plan is already stable.
- Do not call these tools after an execution tool has already returned an empty terminal result; the No Retry on Empty Results rule still applies.

### `sharecrm data describe identify-with-describe`

Purpose: Narrow object candidates while retrieving object-level describe evidence.

Use when:

- `semantic-interpreter` has already narrowed the object semantics, but object-level schema, field meaning, or object-level `few_shots` are still materially needed to narrow the candidate further.
- The object scope is already narrowed enough to inspect candidate describes, but not yet stable enough for direct execution.

Avoid when:

- As a replacement for the first `semantic-interpreter` pass.
- When the object is already sufficiently clear and you only need the describe for that confirmed object; use `GetObjectDescribe` instead.
- When current evidence already makes the object choice and required field semantics stable enough for execution.
- After an execution query has already returned an empty terminal result.

Input:

`sharecrm data describe identify-with-describe --data '{"query":"<original user question or short candidate-narrowing phrase>","include_few_shots":true,"few_shot_type":"nl_filter"}'`

Note:

- Prefer the original user question as the lookup text; do not rewrite the user intent through this tool.
- Returned `few_shots` are object-level query policy supplements, not display material. If they conflict with schema or confirmed semantics, follow schema and confirmed semantics.

### `sharecrm data describe get`

Purpose: Fetch the detailed metadata describe for a sufficiently clear object API name.

Use when:

- The object is already sufficiently clear, and execution still needs field lists, field meaning, object-level rules, or `few_shots` evidence that is not already available from prior tool evidence, the selected semantic frame, or preserved context.
- Before `object-data-query`, when you still need to confirm missing field evidence or object-level query policy for a confirmed object.

Avoid when:

- As a replacement for `semantic-interpreter` object identification.
- When the needed field API names or object-level rules are already evidenced well enough to execute.
- When you only need a concrete record rather than object metadata.

Input:

Lightweight describe:
`sharecrm data describe get --object_api_name <ObjectApiName> --simple_describe true`

When object-level rules are also needed:
`sharecrm data describe get --object_api_name <ObjectApiName> --simple_describe true --include_few_shots true --few_shot_type nl_filter`

Note:

- Do not fetch describe just to re-confirm fields or rules that are already evidenced in the current run.
- `simple_describe` is suitable for lightweight field confirmation; add `include_few_shots=true` only when object-level rules are still missing.
- Returned `few_shots` are object-level query policy supplements; uncovered parts fall back to the main Skill's general rules.

### `sharecrm data record query-by-name`

Purpose: Query records by visible name to obtain record-hit evidence; if multiple records match and the choice would affect the final result, clarify first instead of picking one silently.

Use when:

- The user request already contains a concrete entity name, and execution needs record-hit evidence to confirm a filter value, detail target, or entity evidence.

Avoid when:

- The user did not provide a concrete entity name and you only want exploratory expansion.
- An execution query has already returned an empty terminal result and you want to try a different value for the same request.

Input:

`sharecrm data record query-by-name --data '{"name":"<entity display name>"}'`

### `sharecrm data record query-id-by-name`

Purpose: Query exact record ids by name to obtain reliable id-binding evidence when field semantics require executable id values rather than visible names.

Use when:

- You need to bind a visible name to an exact id to construct a reliable executable filter.
- This is especially useful for referenced objects, people, departments, and similar id-sensitive filters.

Avoid when:

- As a replacement for `semantic-interpreter` value semantics.
- An execution query has already returned an empty terminal result and you want to retry the same request by switching from name to id.

Input:

`sharecrm data record query-id-by-name --data '{"apiNames":["<ObjectApiName>"],"query":"<name keyword>"}'`

### `sharecrm data record get-by-id`

Purpose: Fetch record detail by a reliable record id.

Use when:

- The user explicitly asks for the detail of a specific record.
- A reliable id already exists and execution still needs record-detail evidence or field detail.

Avoid when:

- As a replacement for name lookup or object identification.
- Only because a previous object query returned an empty result and you want to continue side-path probing.

Input:

`sharecrm data record get-by-id --object_api_name <ObjectApiName> --id <_id>`
