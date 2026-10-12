# Large-Result Query

Read this reference when the user explicitly requires a complete list, export,
download, or file-based analysis that may exceed 50 object-detail rows.

## Governed Large-Result File Analysis

Use `scripts/query_object_data_file.py` when the requested output genuinely requires more than 50 object-detail rows, including a complete list, export, download, or file-based analysis. Do not use it merely because the total match count exceeds 50 when a bounded sample, top-N result, single record, or aggregate already answers the question.

Trigger this path before pagination. If the user requests the full result and its size is known or reasonably expected to exceed 50, invoke the script directly. If the size is unknown, one bounded `object-data-query` call may establish the total; once it confirms more than 50 matches, stop bounded execution and invoke the script.

Eligibility constraints:

- Semantic grounding and value resolution must already be complete. The script is an execution surface, not a discovery tool.
- Only a single-object `RECORD` detail query is supported. Do not use it with `relations`, `aggregates`, `groupings`, `having`, or `distinct`.
- `object_api_name`, every `select_fields` entry, every filter value, and every `order_by` entry must satisfy the same evidence and value-resolution rules as `object-data-query`.
- `select_fields` and `order_by` must both be non-empty. Preserve user-requested ordering when provided; metadata adds the object id as a stable tie-breaker.
- The script owns `execution_mode`, `limit`, and `offset`. Never include those keys in `object_data_query`.
- The script owns and enforces its page size plus row, page, time, and file limits, and publishes at most 20,000 rows. Do not work around these limits with repeated script runs or direct pagination loops.

Invocation:

1. Resolve the absolute path of `scripts/query_object_data_file.py` from this skill's installed directory. Never hardcode a sample `/mnt/data/...` path.
2. Resolve the current run workspace directory that already contains `tempfile/` and `releasefile/`. Never create or guess another workspace.
3. Run the script with no command-line arguments and pass exactly one JSON envelope on stdin:

```bash
python3 <absolute-skill-directory>/scripts/query_object_data_file.py <<'EOF'
{
  "workspace_dir": "<current-run-workspace-absolute-path>",
  "object_data_query": {
    "object_api_name": "AccountObj",
    "select_fields": ["AccountObj.name", "AccountObj.created_at"],
    "filters": [],
    "order_by": [{"field": "AccountObj.created_at", "direction": "DESC"}],
    "question": "<original user request>"
  }
}
EOF
```

Result handling:

- `COMPLETED`: present the generated `file_path`, `rows_written`, and `matched_total` as the final result. Do not add a `toolResult` block.
- `PARTIAL`: present the generated file and explicitly state `rows_written`, `matched_total`, and `stop_reason`.
- `COMPLETED` with `stop_reason=EMPTY_RESULT`: report no matching records; no file is produced.
- `FAILED`: report the returned error. Do not fall back to repeated `object-data-query` pagination or an ad-hoc export script.

Before sending the final answer, check every item:

- Semantic grounding and value resolution are complete.
- The request genuinely requires a complete object-detail result rather than a bounded sample, top-N result, single record, or aggregate.
- The query is a single-object `RECORD` detail query without unsupported relation or aggregate features.
- `select_fields`, filters, and ordering use explicitly evidenced identifiers and values.
- The generated file and result status are reported according to the script result.
