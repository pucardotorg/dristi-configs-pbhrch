import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import anthropic
from tools import TOOLS, dispatch_tool

SYSTEM_PROMPT = """You are a localization assistant for the DRISTI digital courts platform.
You help users understand and manage translation keys across environments: dev, qa, demo, prod.

Default tenant ID: pb

Guidelines:
- For any question about missing or out-of-sync translations, use compare_localization first,
  then get_missing_summary to give a module-level breakdown.
- For "are they in sync?" or "is X up to date with Y?" questions, run compare_localization
  in both directions (A→B and B→A) to check for differences either way.
- NEVER call update_missing_localizations without first:
  1. Telling the user exactly what will happen (how many translations, to which env).
  2. Explicitly asking them to confirm by typing "yes" or "confirm".
  Wait for their confirmation before proceeding.
- If the user asks to update but no comparison has been run, run compare_localization first,
  report the results, and ask for confirmation before updating.
- Be specific in responses: always mention environment names, counts, and module names.
- Keep responses concise and factual.
"""


def run_turn(messages: list) -> tuple[str, list]:
    """
    Runs one full agentic turn (may involve multiple tool calls).

    Returns (final_text, updated_messages).
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        messages = messages + [{"role": "assistant", "content": response.content}]

        if response.stop_reason == "end_turn":
            text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "",
            )
            return text, messages

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result_content = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_content,
                    })
            messages = messages + [{"role": "user", "content": tool_results}]
            continue

        # Unexpected stop reason
        break

    return "", messages
