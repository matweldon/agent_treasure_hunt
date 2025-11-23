#!/usr/bin/env python3
"""Extract conversation from Claude Code JSONL log, excluding thinking blocks."""

import json
import sys

def extract_conversation(input_file, output_file):
    """Extract user and assistant messages, excluding thinking."""
    messages = []

    with open(input_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                obj = json.loads(line)
                msg_type = obj.get('type')

                if msg_type == 'user':
                    # Extract user message
                    message = obj.get('message', {})
                    text = message.get('content', '')
                    if isinstance(text, list):
                        # Content might be a list of content blocks
                        text = ' '.join([
                            item.get('text', '') if isinstance(item, dict) else str(item)
                            for item in text
                        ])
                    messages.append({
                        'role': 'user',
                        'text': text,
                        'line': line_num
                    })

                elif msg_type == 'assistant':
                    # Extract assistant message, filtering out thinking
                    message = obj.get('message', {})
                    content = message.get('content', [])
                    texts = []
                    tools = []

                    for item in content:
                        if isinstance(item, dict):
                            if item.get('type') == 'text':
                                texts.append(item.get('text', ''))
                            elif item.get('type') == 'tool_use':
                                tools.append({
                                    'name': item.get('name'),
                                    'input': item.get('input', {})
                                })
                            # Skip 'thinking' type

                    if texts or tools:
                        messages.append({
                            'role': 'assistant',
                            'text': '\n\n'.join(texts),
                            'tools': tools,
                            'line': line_num
                        })

                elif msg_type == 'system':
                    # Include system messages for context
                    text = obj.get('text', '')
                    if text:
                        messages.append({
                            'role': 'system',
                            'text': text,
                            'line': line_num
                        })

            except json.JSONDecodeError:
                print(f"Warning: Could not parse line {line_num}", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Error on line {line_num}: {e}", file=sys.stderr)

    # Write to output
    with open(output_file, 'w') as f:
        json.dump(messages, f, indent=2)

    print(f"Extracted {len(messages)} messages to {output_file}")
    return messages

if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'claude-conversation/2025-11-07.jsonl'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'conversation_extracted.json'

    extract_conversation(input_file, output_file)
