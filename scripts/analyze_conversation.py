#!/usr/bin/env python3
"""Analyze the extracted conversation statistics."""

import json
from collections import Counter
from pathlib import Path


def analyze_conversation(json_path: str):
    """Extract statistics from the conversation JSON."""
    with open(json_path, 'r') as f:
        conversation = json.load(f)

    # Count messages by role
    user_messages = 0
    assistant_messages = 0
    tool_calls_by_type = Counter()
    total_tool_calls = 0

    for entry in conversation:
        role = entry.get('role')

        if role == 'user':
            user_messages += 1
        elif role == 'assistant':
            assistant_messages += 1

            # Count tool calls
            tools = entry.get('tools', [])
            for tool in tools:
                tool_calls_by_type[tool] += 1
                total_tool_calls += 1

    # Print statistics
    print("=" * 70)
    print("CONVERSATION STATISTICS")
    print("=" * 70)
    print()
    print(f"Total conversation entries: {len(conversation)}")
    print(f"User messages: {user_messages}")
    print(f"Assistant messages: {assistant_messages}")
    print()
    print(f"Total tool calls: {total_tool_calls}")
    print()
    print("Tool calls by type:")
    print("-" * 70)
    for tool, count in sorted(tool_calls_by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tool:30s}: {count:4d}")
    print()

    return {
        'total_entries': len(conversation),
        'user_messages': user_messages,
        'assistant_messages': assistant_messages,
        'total_tool_calls': total_tool_calls,
        'tool_calls_by_type': dict(tool_calls_by_type)
    }


if __name__ == '__main__':
    json_path = Path(__file__).parent / 'claude-conversation' / 'conversation_extracted.json'
    analyze_conversation(str(json_path))
