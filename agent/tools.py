import os
import json
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

from localization_lib import (
    compare_envs,
    update_env_from_csv,
    ComparisonResult,
    VALID_ENVS,
)

# In-memory state: stores the most recent comparison result for follow-up questions
_last_comparison: Optional[ComparisonResult] = None

CSV_DIR = os.path.dirname(os.path.abspath(__file__))


TOOLS = [
    {
        "name": "compare_localization",
        "description": (
            "Compares translation keys between two DRISTI environments and finds "
            "which keys are present in the source but missing from the target. "
            "Saves results to a CSV file. Use this for any question about missing, "
            "out-of-sync, or mismatched translations between environments."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "enum": VALID_ENVS,
                    "description": "The authoritative source environment (dev/qa/demo/prod).",
                },
                "target": {
                    "type": "string",
                    "enum": VALID_ENVS,
                    "description": "The environment to check for missing keys.",
                },
                "source_tenant": {
                    "type": "string",
                    "description": "Tenant ID for the source environment (default: pb).",
                },
                "target_tenant": {
                    "type": "string",
                    "description": "Tenant ID for the target environment (default: pb).",
                },
            },
            "required": ["source", "target"],
        },
    },
    {
        "name": "get_missing_summary",
        "description": (
            "Returns a breakdown of missing translations by module from the most recent "
            "comparison. Call this AFTER compare_localization to answer module-level "
            "questions without re-fetching data from the APIs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "update_missing_localizations",
        "description": (
            "Reads the saved CSV of missing translations and upserts each entry into "
            "the specified target environment. This is a WRITE operation that modifies "
            "live data. Only call this AFTER the user has explicitly confirmed they want "
            "to proceed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "enum": VALID_ENVS,
                    "description": "The environment to push translations into.",
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant ID to use in the upsert payload (default: pb).",
                },
            },
            "required": ["target"],
        },
    },
]


def dispatch_tool(tool_name: str, tool_input: dict) -> str:
    global _last_comparison

    if tool_name == "compare_localization":
        source = tool_input["source"]
        target = tool_input["target"]
        source_tenant = tool_input.get("source_tenant", "pb")
        target_tenant = tool_input.get("target_tenant", "pb")

        result = compare_envs(
            source=source,
            target=target,
            source_tenant=source_tenant,
            target_tenant=target_tenant,
            save_csv=True,
            csv_dir=CSV_DIR,
        )
        _last_comparison = result

        if result.error:
            return json.dumps({"error": result.error})

        return json.dumps({
            "source_env": result.source_env,
            "target_env": result.target_env,
            "source_count": result.source_count,
            "target_count": result.target_count,
            "missing_count": result.missing_count,
            "csv_saved": result.csv_path is not None,
            "csv_path": result.csv_path,
        })

    elif tool_name == "get_missing_summary":
        if _last_comparison is None:
            return json.dumps({
                "error": "No comparison has been run yet. Please run compare_localization first."
            })

        by_module = _last_comparison.by_module()
        return json.dumps({
            "source_env": _last_comparison.source_env,
            "target_env": _last_comparison.target_env,
            "total_missing": _last_comparison.missing_count,
            "by_module": {
                module: len(items)
                for module, items in sorted(
                    by_module.items(), key=lambda x: -len(x[1])
                )
            },
        })

    elif tool_name == "update_missing_localizations":
        target = tool_input["target"]
        tenant_id = tool_input.get("tenant_id", "pb")
        csv_path = os.path.join(CSV_DIR, "missing_translations_in_en_IN.csv")

        result = update_env_from_csv(
            target=target,
            csv_path=csv_path,
            tenant_id=tenant_id,
        )

        if result.error:
            return json.dumps({
                "error": result.error,
                "processed": result.total_processed,
                "upserted": result.total_upserted,
                "failed_at_code": result.failed_code,
            })

        return json.dumps({
            "target_env": result.target_env,
            "total_processed": result.total_processed,
            "total_skipped": result.total_skipped,
            "total_upserted": result.total_upserted,
        })

    return json.dumps({"error": f"Unknown tool: {tool_name}"})
