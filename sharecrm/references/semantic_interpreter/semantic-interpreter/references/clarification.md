# Handling Blocking Clarification

Read this reference when `semantic-interpreter` returns blocking clarification
and the unresolved ambiguity affects execution correctness.

## Resolve the Ambiguity

Use `AskUserQuestion` to resolve the blocking ambiguity.

- Prefer `result.clarification` from `semantic_interpreter` when the tool returns it.
- Keep `query` as the original user request.
- Carry the clarification answer through `semanticContext`, not by rewriting `query`.
- Do not clarify the same `target` more than once.
- If a previously clarified `target` remains unresolved, proceed with best effort or tell the user it cannot be identified.

After the user answers, call `semantic-interpreter` again with the original `query`
and the updated `semanticContext`. Reassess semantic sufficiency before
execution.

## Refill `semanticContext`

`semantic_interpreter` has no separate clarification-answer input. After clarification, call it again with the same `query` and an updated `semanticContext`.

Refill principle:

- Keep `query` unchanged as the original user question.
- Carry the user's clarification answer only through `semanticContext`.
- Match `clarification.items[].target` against a previous `semanticContext.pending[].name`.
- `rewrite_name`: overwrite that pending item's `name` with the user text; keep it in `pending`.
- `fill_decorate_scope`: write the user text into that pending item's `properties.decorateScope`; keep it in `pending`.
- `select_candidate`: move the selected `option.value` (a full semantic item) into `semanticContext.confirmed` and remove the matching `target` from `pending`. Do not put it back into `pending`.
- Empty/missing `options` means text input; non-empty `options` means single select.

Stop condition:

- Do not clarify the same `target` more than once. If it remains unresolved after clarification, proceed with best effort or tell the user it cannot be identified.

Returned clarification shape:

```json
{
  "clarification": {
    "items": [
      {
        "target": "客户",
        "clarificationType": "select_candidate",
        "question": "Please confirm which semantic item \"客户\" refers to.",
        "options": [
          {
            "label": "Object: 客户",
            "value": {
              "category": "anchoring",
              "type": "object",
              "name": "客户",
              "normalized": "AccountObj",
              "properties": { "object": "AccountObj", "objectDisplayName": "客户" }
            }
          }
        ]
      }
    ]
  }
}
```

After the user picks `Object: 客户`, the next call moves that `option.value` into `confirmed`, drops it from `pending`, and keeps `query` unchanged:

```json
{
  "query": "<the original user question, unchanged>",
  "semanticContext": {
    "confirmed": [
      {
        "category": "anchoring",
        "type": "object",
        "name": "客户",
        "normalized": "AccountObj",
        "translations": ["Customer"],
        "properties": { "object": "AccountObj", "objectDisplayName": "客户" }
      }
    ],
    "pending": [],
    "excluded": []
  }
}
```
