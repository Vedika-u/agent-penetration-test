"""Manual smoke-test CLI: chat with the target agent's HTTP API from the terminal.

Usage:
    uv run python scripts/chat.py [session_id]
"""

import sys

import httpx

API_URL = "http://localhost:8000/chat"


def main() -> None:
    session_id = sys.argv[1] if len(sys.argv) > 1 else "cli-session"
    print(f"Chatting with target agent (session_id={session_id!r}). Ctrl+C to quit.\n")
    while True:
        try:
            message = input("you> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not message:
            continue
        resp = httpx.post(
            API_URL, json={"session_id": session_id, "message": message}, timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        for call in data["tool_calls"]:
            print(f"  [tool:{call['name']}] {call['content']}")
        if data["verification"]:
            for flag in data["verification"]:
                print(f"  [verify] {flag}")
        print(f"agent> {data['response']}\n")


if __name__ == "__main__":
    main()
