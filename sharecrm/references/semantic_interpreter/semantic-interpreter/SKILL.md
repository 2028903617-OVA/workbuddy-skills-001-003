---
name: "semantic-interpreter"
description: "Mandatory primary skill and sole entry point for ALL natural-language CRM data queries, record searches, aggregations, and analytics. Use this skill whenever the user asks in natural language to: 1) Search, find, list, or retrieve CRM object records under specific filter conditions (e.g., 'Find all opportunities created in the last 5 days', 'Show unconverted leads for Customer A'). 2) Answer metric, aggregation, or statistical questions such as counts, sums, averages, maximums, or minimums (e.g., 'What is the total deal amount for Customer A?', 'How many follow-up leads do I have?'). 3) Query CRM metadata, object descriptions, field definitions, object relationships, reports, or business rules. This skill completely replaces and supersedes 'semantic-data-query' and 'data-read'; do NOT route to or use those legacy skills for any natural-language queries."
metadata: ""
apiName: "semantic_interpreter"
---
# Semantic Interpreter

## Global Constraints & Hard Red Lines

- **Semantic Interpretation Requirement**: semantic-interpreter is mandatory for the initial semantic pass, and must be called again whenever later steps still require semantic parsing, disambiguation, or re-grounding.
- **Parameter Contract Principles**:
    - Parameter names and payload structure must follow the current tool contract exactly.
    - Execution-critical semantic identifiers must come from semantic grounding, not from invention. This includes `object_api_name`, exact field API names, relation paths, `from_entity`, metrics, and dimensions.
    - Among them, `object_api_name` and exact field API names are authoritative execution identifiers and must never be fabricated from labels, display names, business phrases, translations, semantic similarity, or memory.
    - If a required execution-critical semantic identifier is still unresolved, do not guess and do not execute.
- **Zero Hallucination Policy**: Never invent semantic facts such as metric formulas, SOP steps, rule thresholds, or relation paths. Use `semantic-interpreter` results as the primary confirmed source for semantic knowledge.
- **Frame Adaptation Rule**: When a semantic frame is matched, use its dataQueryParams as a capability template, not a mandatory execution plan. Strip any JOINs, fields, and filters that are not required by the user’s actual request semantics. frameId is for attribution only.
- **Strict Time Normalization**: Normalize relative time expressions (e.g., "last 6 months") into explicit, absolute time ranges based strictly on the current runtime date before execution. Do not invent alternate anchor dates.
- **Current Employee Context**: For first-person semantics such as "I", "my", "owned by me", or "my department", use the employee and primary department information from the runtime `currentEmployeeInfo` directly. Do not query this context again or use it to resolve a third party.
- **Relation Navigation over Guessing**: Use the `semantic-interpreter` returned `semantic_graphs` to discover the correct object associations and relation candidates first. Then fetch only the selected ontology nodes or metadata needed for deeper reasoning and execution. DO NOT blind-guess JOIN conditions or fabricate relation paths outside the semantic graph evidence.
- **Semantic Item Category Contract**: When you prepare `semanticContext.confirmed`, `pending`, and `excluded`, `category` must be exactly one of `anchoring`, `value_resolution`, or `interpretation`. The detailed category selection rules and examples are defined in State 1 below.
- **Special Object Mapping Rules**:
    - Any employee type or personnel type field must be anchored to `PersonnelObj` only. `EmployeeObj` and any other object are invalid for this semantic type.
- **No Retry on Empty Results**: If an execution tool returns a successful terminal-empty result, treat it as final and do not retry by changing identifiers, filters, fields, relation paths, objects, or query mode. Determine emptiness by the execution tool's own explicit empty-result signals, not by semantic doubt, internal guesses, or a business metric value of `0`. Tool-specific empty-result signals are defined in each execution tool section below.
- **Bounded Result Policy**: Normal final data queries must use `limit` with a default of `20` and a maximum of `50`. Return limited sample rows/groups plus `total`, `totalNum`, or an equivalent count when available, and clearly distinguish total matches from returned samples in the final answer.
- **Large-Result Handoff**: When the user requires a complete list, export, download, or file-based analysis and the result is known or reasonably expected to exceed 50 detail rows, read `references/large-result-query.md` before execution. If a bounded query confirms more than 50 matches, stop immediately and switch to the governed script. Never paginate with `offset` or use an ad-hoc Python/Shell export script.


## Workflow

The workflow is a strict state machine:

`Interpret -> Probe & Scout -> Re-check Semantic Sufficiency -> (Clarify | Execute) -> Complete`

Treat semantic grounding, value validation, and final execution as distinct sequential phases. Do not skip ahead to execution while key semantics or value bindings are still unresolved.

### State 1: Interpret Required Semantics

Turn the user's natural language intent into concrete hypotheses across the semantic categories.

#### Purpose:

- Construct the caller-side request for the first `semantic-interpreter` call.
- Decompose the raw user request into structured semantic items rather than answering the user or executing the final query.
- Extract both business concepts and concrete values from the raw request before the first `semantic-interpreter` call.
- For explanation-seeking requests, preserve the original explanatory phrase as an `interpretation` item instead of rewriting it into an execution-oriented object, field, or value phrase.


#### Request Contract:

```json
{
  "query": "<original user request>",
  "semanticContext": {
    "confirmed": [],
    "pending": [],
    "excluded": []
  }
}
```

- `query`: always pass the full raw user request text. Do not replace it with only a summary or only extracted semantic items
- `confirmed`: stable context already known and worth preserving in this turn.
- `pending`: current parsing targets that should be actively normalized, matched, disambiguated, or bound now.
- `excluded`: rejected prior interpretations that should not be preferred again.
- In the first pass, prefer `pending` over `confirmed` unless the context is already stable and worth preserving.
- In the first pass, prefer keeping uncertain semantics in `pending` rather than prematurely promoting them into `confirmed`.

Each item in `confirmed`, `pending`, and `excluded` uses the same caller-side shape:
- required: `category`, `name`, `translations`
- optional: `type`, `properties`
- `translations` is a required caller-side cross-language recall field and must not be empty.
- `type` is an optional weak hint only.
- `properties` is an optional structured hints object.
- Do not prefill response-side fields such as `normalized`, `status`, `confidence`, or `candidates`.

#### Item filling rules:

- `query`: always pass the full raw user request text. Do not replace it with only a summary or only extracted semantic items.
- `name`: keep the user's original phrase whenever possible.
- `translations`: provide 1 to 3 short cross-language recall phrases for the same phrase. Their primary job is to bridge cross-language recall, especially Chinese request phrases to English semantic recall vocabulary. Keep them recall-oriented and close to the original phrase. Do not turn them into explanations, category labels, loosely related search terms, or business guesses.
- `type`: use only as a weak hint; omit it when uncertain.
- `properties`: use only for explicit machine-readable hints that are already known. Keep it flat and structured. Do not put free-form notes, explanations, or guessed formulas in it.
- `properties.valueType`: for `value_resolution`, use `entity`, `enum`, or `time` only when already known.
- `properties.decorateScope`: use it for the original object or field phrase modified by this value. If that phrase already appears as another semantic item, reuse that item's `name`.
- `properties.object_candidates`: use only when object scope is already known. Pass a list of object API names such as `["AccountObj"]` or `["SalesOrderObj", "SalesOrderLineObj"]`.
- `properties.field_candidates` and `properties.top_k`: use only when these hints are already known and intentionally needed.

#### Category Selection:

- choose it by the phrase's next semantic job. `category` is the router; never rely on `type` for routing.
- `anchoring`: establish an enterprise-system reference such as an object, field, relation path, source object, target object, metric carrier, event, role, ownership, or other system anchor.
- `value_resolution`: bind a concrete value to a field or filter, such as an entity value, enum/status value, stage label, or time value.
- `interpretation`: request explanatory or descriptive knowledge rather than object/field/value binding, such as definitions, rules, SOPs, processes, permissions, business terminology, metric relations, standard analysis models and algorithms, or strategies.
- For the same business phrase, choose by the next semantic need: use `anchoring` when the next step should locate a system carrier or relation; use `interpretation` when the next step should explain meaning, rule logic, process logic, model logic, or strategy meaning.
- Do not put concrete values into `anchoring`.
- Do not put explanation-seeking rule / SOP / process / permission / definition phrases into `anchoring`.
- Do not put object / field / relation-path discovery into `interpretation`.
- Do not put path or ownership discovery into `value_resolution`.

#### Item examples:

- Category examples:
  `Customer` -> `anchoring`
  `How is Customer related to Order` / `Which object provides approval status` / `Which object contains order time` -> `anchoring`
  `East China Region` / `Unconverted` / `2026-05-01 to 2026-05-31` -> `value_resolution`
  `What does the High-Value Customer Rule mean` / `How does the purchase approval process work` / `What does channel sell-through mean in this industry` / `What is the relation between GMV and sell-through rate` / `Which standard analysis model should be used for pipeline health` / `What is the retention strategy for key accounts` -> `interpretation`
- Field examples:
  `translations: ["Customer"]`
  `properties.valueType: "entity" | "enum" | "time"`
  `properties.decorateScope: "<object or field phrase>"`
  `properties.object_candidates: [objectApiName]`

#### Execution handoff:

- For time/date values, follow the global Strict Time Normalization rule before calling `semantic-interpreter`.
- Do not send an all-empty `semanticContext` unless the request truly yields no extractable semantic phrase.
- After first-pass decomposition, call `semantic-interpreter`.
- In later rounds, keep `semanticContext.confirmed`, `pending`, and `excluded` aligned with the latest preserved context, current parsing targets, and rejected interpretations.


#### Canonical initial semantic-interpreter request example:

```json
{
  "query": "最近30天华东区未成交客户有多少",
  "semanticContext": {
    "confirmed": [],
    "pending": [
      {
        "category": "anchoring",
        "name": "客户",
        "translations": ["customer", "account"]
      },
      {
        "category": "value_resolution",
        "name": "华东区",
        "translations": ["east china region"],
        "properties": {
          "valueType": "entity",
          "decorateScope": "客户"
        }
      },
      {
        "category": "value_resolution",
        "name": "未成交",
        "translations": ["unconverted"],
        "properties": {
          "valueType": "enum",
          "decorateScope": "客户"
        }
      },
      {
        "category": "value_resolution",
        "name": "2026-06-03 to 2026-07-03",
        "translations": ["last 30 days"],
        "properties": {
          "valueType": "time"
        }
      }
    ],
    "excluded": []
  }
}
```

### State 2: Probing & Schema Scouting

Use this state only to fill missing execution evidence after semantic grounding. If the missing problem is still semantic interpretation, return to `semantic-interpreter` with updated `semanticContext` instead of switching to side tools.

When entering this state, read `references/probing-tools.md` before selecting or calling any describe or record lookup tool. Probe only for the minimum evidence required to execute reliably.

### State 3: Re-check Semantic Sufficiency

Check whether the current semantic grounding and execution evidence are sufficient for reliable execution.

Core tasks:

- Before execution, confirm that the result object is stable enough, required fields are evidenced, concrete values are bound, time filters are normalized, and the expected result shape is clear.
- If any required executable parameter is still not explicitly evidenced, do not execute. Return to semantic grounding, probing, or clarification instead of filling it by best effort.
- If important semantics are still ambiguous, incomplete, or unbound, loop back to State 1 or State 2 instead of executing.
- Use `semantic-interpreter` again when new evidence changes the semantic picture rather than merely filling execution evidence.
- If `semantic-interpreter` returns `clarification` and the unresolved gap would affect execution correctness, go to Clarify instead of Execute.

### State 4A: Clarify

Enter this state only when `semantic-interpreter` returns blocking clarification and the unresolved gap would affect execution correctness.

When entering this state, read `references/clarification.md` for the complete
clarification interaction and semanticContext refill protocol.

### State 4B: Execute

Enter this state only when the request requires data retrieval and State 3 confirms that semantic grounding and execution evidence are sufficient. Pure interpretation or explanatory requests may complete without entering Execute.

#### Execution surface:

- Use `object-data-query` for bounded object-level record/detail queries and object-field aggregations, with `limit` defaulting to 20 and capped at 50.
- Decide the required result shape before executing a detail query. Apply the Global Constraints large-result handoff rule when the request requires a complete list, export, download, or file-based analysis.
- Use `chart-data-query` for BI analytics backed by a BI metric (`BIMetric`) or BI view (`BIView`).
- Switch execution surfaces only when the first successful result still cannot satisfy a user-explicit requirement.

#### Execution context:
- pass the original user request as `question`
- pass `frameId` only as execution attribution when a matched semantic frame was used.
- pass `traceId` unchanged when the Context header already contains it
- Follow the tool-specific parameter rules below when assembling the final query payload.

#### Stop conditions:

- After a successful execution, answer immediately when the result already covers the user-explicit metric, dimension, entity scope, time scope, and result shape.
- If the execution tool returns a successful terminal-empty result, stop and report it.
- Do not continue querying only to double-check, enrich, or restyle an already sufficient result.

#### Failure handling:

- If execution fails because semantic mapping is still insufficient, return to State 2 or `semantic-interpreter` as needed.
- If execution fails because of a parameter or syntax issue under an otherwise stable plan, refine the payload and retry.
- Present final results according to the Final Answer Formatting rules below.

## Final Answer Formatting

### `toolResult` block

- For every successful detail/list `object-data-query` call used to answer any part of the user's request, if the result includes `tool_result_id`, the final answer must include its `toolResult` code block. Omitting it is an output error.
- The block must contain only the exact `tool_result_id`, with no labels, JSON, traces, SQL, or other fields.
- If multiple detail/list `object-data-query` calls are used to answer the request and include `tool_result_id`, output one independent `toolResult` code block for each result.
- For a pure aggregate result, answer the aggregate value directly and do not output a `toolResult` code block, even if the response includes `tool_result_id`.
- If a detail/list result does not include `tool_result_id`, keep the existing answer format and do not add a `toolResult` code block.

Strict `toolResult` format:

````markdown
```toolResult
<tool_result_id>
```
````

### Result presentation

- Keep the final answer stable and business-facing.
- Clearly distinguish total matches from returned samples when both are present.
- For pure aggregate results, answer the aggregate value directly and do not add unrelated detail fields or record lists.
- When presenting multiple independent `object-data-query` results in one answer, explain them separately in the same order as the user's request and do not merge them into one result interpretation.
- For detail/list results, prefer the returned result reference for record display; do not manually expand large row sets into markdown tables or long lists.

## Available Tools

### `sharecrm semantic semantic-interpreter`

Primary semantic parsing and refinement tool. Use it for the initial semantic pass and whenever later steps still require semantic parsing, disambiguation, or re-grounding.

Input:

Pass one valid `--data` JSON object; JSON-escape string values for quotes, backslashes, and control characters such as newlines or tabs.

- Pass `query` as the original user request text.
- Pass `semanticContext` as the caller-prepared semantic state.
- Caller-side items may contain only `category`, `name`, `translations`, optional `type`, and optional `properties`.
- `category` must be one of `anchoring`, `value_resolution`, or `interpretation`.
- Do not use `unknown` for `category`.
- `translations` is required on every caller-side item and is primarily for cross-language recall.
- `properties` must be a flat structured JSON object.
- Allowed `properties` keys include explicit hints such as: `properties.object_candidates`, `properties.field_candidates`, `properties.decorateScope`, `properties.valueType`, `properties.top_k`.
- Do not prefill response-side fields such as `normalized`, `status`, `confidence`, or `candidates`.
- Relative time values must be normalized before the tool call.
- See State 1 for request construction rules and canonical request examples.

Output:

- `ontology`: object-centric semantic hits. Objects carry related fields and resolved values.
- `ontologyGraphs`: semantic subgraphs for relation discovery.
- `analytics`: analysis semantics, including metrics, views, and unbound dimensions.
- `knowledge`: explanatory semantics such as rules, processes, terms, and industry terms.
- `playbook`: playbook semantics such as metric relation graphs, standard analysis models, and strategies.
- `semanticFolding`: matched semantic frames.
- `clarification`: focused clarification payload when ambiguity still blocks progress.

Guidance:

- This tool refines caller-prepared semantic hypotheses. It does not replace first-pass decomposition.
- Use `unknown` for `type` only when the phrase is real but its fine-grained type is still unclear.

### `sharecrm semantic object-data-query`

Execute the final query once the request is sufficiently resolved.

When to use:

- Use this tool when the final plan is specific enough for object-level record/detail retrieval or object-field aggregation.
- Do not use it when important semantics are still ambiguous, incomplete, or unbound.

Input:

Pass one valid `--data` JSON object; all fields below are JSON keys, not flattened command-line flags, and string values must be JSON-escaped.

- `question`: original user request text when available.
- `frameId`: optional semantic frame attribution.
- `traceId`: trace id from the current execution context. Optional; pass it unchanged when the Context header already contains it.
- `object_api_name`: root object API name. Required.
- `relations`: ordered join edges as `{ left: "Object.field", right: "Object.field" }`.
- `select_fields`: detail-query return fields. Use only this field. Each item must be `"Object.field"`.
- `aggregates`: aggregate definitions for object-query execution, each as `{ field: "Object.field", function: "COUNT|COUNT_DISTINCT|SUM|AVG|MIN|MAX" }`.
- `groupings`: group-by expressions for object-query execution. Each item must be either an exact `"Object.field"` reference or a time-grouping expression. Supported time-grouping functions are `day`, `week`, `month`, and `year`, using the form `day(Object.field)`, `week(Object.field)`, `month(Object.field)`, or `year(Object.field)`.
- `filters`: array of `{ field: "Object.field", operator: "...", values: [...] }`.
- `having`: array of `{ field: "Object.field", function: "...", operator: "...", values: [...] }`.
- `order_by`: array of `{ field: "Object.field", direction: "ASC|DESC", function?: "..." }`.
- `distinct`: boolean.
- `limit`: integer.

Query mode:

- Aggregate query: use `aggregates`; add `groupings` only when explicit group-by semantics are required.
- Detail query: fill `select_fields`; do not fabricate aggregate metrics just to produce a result.
- If the request does not clearly require aggregates, default to Detail query.
- At least one of `select_fields`, `aggregates`, or `groupings` must be non-empty.

Object-query-specific constraints:

- Do not rename keys, reshape the payload, or carry parameter structure from other tools.
- `object_api_name` must be explicitly evidenced before use. Never fill it from an object label, display name, semantic candidate, business phrase, or semantic similarity.
- Every field reference must be explicitly evidenced. Ordinary field references must use the exact `"Object.field"` form with exactly one dot. A `groupings` item may additionally use `day(Object.field)`, `week(Object.field)`, `month(Object.field)`, or `year(Object.field)`; its inner field must follow the same exact-field and relation-evidence rules. Do not use other functions or nested expressions. Strictly forbid multi-hop or three-segment field syntax such as `"ObjectA.relation_field.fieldB"`. For example, `"NewOpportunityObj.account_id.industry_level1"` is illegal. Any executable `filters.values` must also be explicitly evidenced before use. Do not convert unresolved business phrases into backend-ready values by best effort.
- Typed organization values returned by semantic grounding, such as `user_1001` and `dept_2002`, are backend-ready filter values. Pass them unchanged in `filters.values`; do not add braces, display-name suffixes, or other decoration.
- If the query needs a field from a related object, declare the join explicitly in `relations` using graph-verified edges such as `{ left: "NewOpportunityObj.account_id", right: "AccountObj.id" }`, and then use the target field only in two-segment form inside `groupings`, `filters`, `select_fields`, `aggregates`, `having`, or `order_by`, for example `"AccountObj.industry_level1"`. In a time-grouping expression, the inner field must use that same two-segment form.
- `relations` must form one ordered primary join path starting from `object_api_name`. Every referenced object and every `{left,right}` pair must come from a real graph-verified path. Do not invent bridge objects, join edges, or field pairs. Before execution, verify that every ordinary field used in `select_fields`, `aggregates.field`, `groupings`, `filters.field`, `having.field`, and `order_by.field` contains exactly one dot; for a time-grouping expression, apply this check to its inner field.
- If a needed field cannot be expressed as exact `"Object.field"` plus explicit `relations`, do not guess. Stop and clarify or reground first.
- Use deduplication only when multi-object expansion would otherwise duplicate the result object.

Result interpretation:

- A successful empty result is terminal only when the tool explicitly signals no matching data, such as `isEmpty`, `rows: []`, `totalNumber: 0`, or an equivalent final-answer hint.
- An aggregate value of `0` by itself is not an empty-result signal.
- For grouped aggregates, a row such as `{dimension, 0}` is still a valid returned row, not an empty result.
- If the tool returns `errors`, refine semantics or parameters instead of forcing execution.

Mandatory final-output contract (violating any item is an output error):

1. After any successful detail/list `object-data-query` call used to answer any part of the user's request, if its result includes `tool_result_id`, the final answer must output its `toolResult` code block.
    - Put the block immediately after `记录数：N` and before any interpretation or explanatory text.
    - The block content must be only the exact `tool_result_id` returned by `sharecrm`.
    - Do not replace the block or the referenced detail data with a markdown table, list, or textual row expansion.
    - If one request uses multiple detail/list `object-data-query` calls, output one independent block for every result used in the answer that includes `tool_result_id`.
    - Do not omit a result that answers part of the user's request in order to avoid emitting its block.

2. Use this exact format with no variants:

   ````markdown
   ```toolResult
   <tool_result_id>
   ```
   ````

3. Pure aggregate results:
    - Answer a scalar aggregate value directly without a `toolResult` block, even when the response includes `tool_result_id`.
    - For grouped aggregates, output `记录数：N` using the number of returned groups, but do not add a `toolResult` block solely because the response includes `tool_result_id`.

4. Record count:
    - Detail/list and grouped-aggregate results must output `记录数：N`.
    - For detail/list results, use the tool's total-match field (`totalNumber`, `totalNum`, `total`, or its explicit equivalent) when present; otherwise use the actual returned row count.
    - When total matches and returned samples differ, keep the total in `记录数：N` and clearly state the returned sample count without expanding the rows manually.

5. Interpretation:
    - Keep it short and limited to the user's question and the fields actually queried.
    - Give at most three useful next-step suggestions; omit suggestions when none are useful.

Multiple detail/list results must follow this structure in the same order as the user's request:

**Result name**
记录数：N
```toolResult
<tool_result_id>
```
(Brief interpretation of this result)

Never merge, omit, or reuse the `toolResult` blocks for separate results.

Successful bounded result handling:

- If the tool returns fewer sample rows than the total match count because of `limit`, stop after the successful call. Output the total match count and the `toolResult` block; do not paginate to fetch the remaining rows.

Object-query planning rules:

- Determine the expected result shape first: detail list, single-record detail, scalar aggregate, or grouped aggregate.
- Choose the result object by the business entity that must be returned, counted, or grouped, not by the object that only provides filter conditions.
- Prefer a single-object query by default. Expand to multi-object semantics only when a single object cannot cover the required result fields, aggregate fields, or filter meaning.
- Use deduplication only when multi-object expansion would otherwise duplicate the result object.
- For negative semantics such as "no", "not occurred", or "never", execute only when relation and field evidence are already stable enough to express the constraint reliably.
- If the result object, filter-field object, and aggregate-field object differ, stabilize the result object and required field semantics first, then decide whether multi-object expansion is necessary.
- Query only the result, dimensions, and metrics explicitly requested by the user. Do not append trends, distributions, comparisons, drill-downs, or management-style extensions unless explicitly requested.


### `sharecrm semantic chart-data-query`

When to use:

- Use this tool for BI analytics backed by a BI view (`BIView`) or BI metric (`BIMetric`).
- Do not use it for object-level record/detail queries; use `object-data-query` instead.

Input:

Pass one valid `--data` JSON object; all fields below are JSON keys, not flattened command-line flags, and string values must be JSON-escaped.

- `business_type`: `"BIView"` or `"BIMetric"`. Required.
- `traceId`: trace id from the current execution context. Optional; pass it unchanged when the Context header already contains it.
- `from_entity`: required.
    - `BIView`: a BI view (view id like `BI_69a91f12475ddf0007efdcdf`, or a resolvable view name). A view, NOT an object api name.
    - `BIMetric`: the subject/object (e.g. `AccountObj`).
- `metrics`: `BIMetric` only. Array of `{ "field": "<BI field id or resolvable name>", "function": "SUM|AVG|COUNT|COUNT_DISTINCT|MIN|MAX" }`.
- `dimensions`: `BIMetric` only. Grouping fields (BI field id or resolvable name).
- `filters`: optional in both modes. Array of `{ "field": "...", "operator": "...", "values": ["..."] }`.
- `distinct`, `limit`: optional.

Mode selection:

- Choose `business_type` first. It determines the payload shape.
- Use `BIView` when the answer comes from a pre-built BI view.
- Use `BIMetric` when the answer comes from BI metric aggregation over a subject object.

BIView mode:

- Set `business_type` to `BIView`.
- Use a BI view id or resolvable view name in `from_entity`.
- Leave `metrics` and `dimensions` empty.
- If filters are needed, `filters.field` must be a field inside the selected view.

BIMetric mode:

- Set `business_type` to `BIMetric`.
- Use the subject object in `from_entity`.
- Fill `metrics` and/or `dimensions` as needed.
- `function` must be exactly one of `SUM|AVG|COUNT|COUNT_DISTINCT|MIN|MAX`.

chart-query-specific constraints:
- Do not rename keys, reshape the payload, or mix fields, identifiers, or payload habits from the other mode.
- `from_entity`, `metrics.field`, `dimensions`, and `filters.field` must come from semantic grounding and be explicitly evidenced before use.
- Respect identifier roles: a BI view id is valid only as `from_entity` in `BIView`, never in `metrics.field`, `dimensions`, or `filters.field`. A BI field id or grounded resolvable field name may be used only in field positions.
- When the tool contract allows either name or id for a metric or dimension, use only a grounded resolvable name or a grounded id. Never invent either form.
- `filters.values` is always a string array and must contain backend-ready values, not relative phrases such as "本月".

Result interpretation:

- Empty-result:
    - Treat the result as terminal-empty only when the query succeeds and the tool explicitly signals no matching data for the selected BI surface.
    - Do not use a metric value of `0` by itself as an empty-result signal.
    - A returned row or group with metric value `0` is still a valid analytical result unless the tool explicitly marks the result as empty.
- If it returns `errors`, refine semantics or parameters instead of forcing execution.


## Completion Rules & End-Condition Checklist

End the run only when all of the following are true:

- Every required concept from the user's request has an explicit semantic decision.
- If the task requires data retrieval, `object-data-query` or `chart-data-query` has succeeded and the final business answer is ready.
- If the task does not require data retrieval, the required semantics or knowledge have been retrieved and presented.
- No important semantic gap remains unresolved that would still require refinement, clarification, or execution.
- If an execution tool has already returned a successful terminal-empty result, end the run with the empty-result answer.
