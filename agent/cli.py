import os
import sys

# Load .env before importing agent modules
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

sys.path.insert(0, os.path.dirname(__file__))

from agent import run_turn

BANNER = """
╔══════════════════════════════════════════════════╗
║       DRISTI Localization Agent                  ║
║  Ask about missing translations across envs.     ║
║  Environments: dev, qa, demo, prod               ║
║  Type 'exit' or 'quit' to stop.                  ║
╚══════════════════════════════════════════════════╝
"""

EXAMPLE_QUESTIONS = """Example questions:
  - What translations are missing in demo compared to qa?
  - Are prod and demo in sync?
  - Break down the missing translations by module
  - Update demo with the missing translations from qa
"""


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY is not set in agent/.env")
        sys.exit(1)

    print(BANNER)
    print(EXAMPLE_QUESTIONS)

    messages = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye.")
            break

        messages.append({"role": "user", "content": user_input})

        try:
            response_text, messages = run_turn(messages)
            print(f"\nAgent: {response_text}\n")
        except Exception as e:
            print(f"\nError: {e}\n")
            # Remove the failed user message so the conversation stays clean
            messages = messages[:-1]


if __name__ == "__main__":
    main()
